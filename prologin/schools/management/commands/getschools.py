import itertools
import json
import requests

from django.core.management.base import BaseCommand
from django.db import transaction

from schools.models import School

# https://data.education.gouv.fr/explore/dataset/fr-en-annuaire-education/export/
COLLEGESLYCEES_URL = 'https://data.education.gouv.fr/explore/dataset/fr-en-annuaire-education/download?format=json&timezone=Europe/Berlin&use_labels_for_header=true'
# https://www.data.gouv.fr/fr/datasets/etablissements-denseignement-superieur-2/
SUPERIEUR_URL = 'https://www.data.gouv.fr/fr/datasets/r/4ebffb45-8b3a-48eb-ac2a-c3b3c886dafa'


class Command(BaseCommand):
    help = "Import schools from OpenData websites"

    @staticmethod
    def cached_request(url, fname):
        try:
            with open(fname) as f:
                return json.load(f)
        except FileNotFoundError:
            data = requests.get(url, timeout=60).json()  # data.education.gouv.fr is slow as hell
            with open(fname, 'w') as f:
                json.dump(data, f)
            return data

    def get_superieur(self):
        c = self.cached_request(SUPERIEUR_URL, 'superieur.json')
        for row in c:
            uai = row['code_uai']
            if not row['nom']:
                self.uai_to_delete.add(uai)
                continue
            school = School(uai=uai,
                            name=row['nom'],
                            acronym=row['sigle'] or '',
                            academy=row['academie'] or '',
                            address=row['adresse'] or '',
                            postal_code=row['cp'] or '',
                            city=row['commune'] or '',
                            country='France',
                            type=row["type_detablissement"] or '',
                            imported=True, approved=True)
            try:
                school.lat = row['latitude_y']
                school.lng = row['longitude_x']
            except KeyError:
                pass
            yield school

    def get_collegeslycees(self):
        c = self.cached_request(COLLEGESLYCEES_URL, 'collegeslycess.json')
        for row in c:
            row = row['fields']
            uai = row['identifiant_de_l_etablissement']
            if not row.get('nom_etablissement'):
                self.uai_to_delete.add(uai)
                continue
            if any(row.get(t, False) for t in ('ecole_maternelle', 'ecole_primaire')):
                self.uai_to_delete.add(uai)
                continue
            if any(t in row['type_etablissement'] for t in ('orientation', 'primaire', 'maternelle')):
                self.uai_to_delete.add(uai)
                continue
            address = ('adresse_%d' % i for i in (1, 2))
            address = ' '.join(row[col] for col in address if col in row).strip()
            school = School(uai=uai,
                            name=row['nom_etablissement'] or '',
                            address=address,
                            postal_code=row['code_postal'] or '',
                            city=row['nom_commune'] or '',
                            country='France',
                            type=row['type_etablissement'] or '',
                            imported=True, approved=True)
            if 'position' in row:
                school.lat = row['position'][0]
                school.lng = row['position'][1]
            yield school

    def handle(self, *args, **options):
        schools = itertools.chain(self.get_collegeslycees(), self.get_superieur())
        self.uai_to_delete = set()

        with transaction.atomic():
            for school in schools:
                defaults = {f.name: getattr(school, f.name) for f in school._meta.fields if f.name not in ('uai', 'id')}
                s, created = School.objects.update_or_create(uai=school.uai, defaults=defaults)
                print("created" if created else "updated", s.uai, s.name)

            School.objects.filter(uai__in=self.uai_to_delete).delete()
