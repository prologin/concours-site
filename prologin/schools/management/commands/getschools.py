import csv
import re
import requests

from django.core.management.base import BaseCommand
from schools.models import School

# I don't know how this database is updated, we'll have to figure that
# out manually next time it changes to see how we can retrieve the URL
# automatically
COLLEGESLYCEES_URL = 'https://www.data.gouv.fr/s/resources/adresse-et-geolocalisation-des-etablissements-denseignement-du-premier-et-second-degres/20160526-143453/DEPP-etab-1D2D.csv'
SUPERIEUR_URL = 'https://www.data.gouv.fr/s/resources/etablissements-denseignement-superieur/20160128-153017/etablissement_superieur.csv'

def batch(iterable, n=1):
    l = len(iterable)
    for ndx in range(0, l, n):
        yield iterable[ndx:min(ndx + n, l)]


class Command(BaseCommand):
    help = "Import schools from OpenData websites"

    def get_superieur(self):
        c = requests.get(SUPERIEUR_URL).content.decode('utf-8')
        cr = csv.DictReader(c.splitlines(), delimiter=';')
        res = {}
        for row in cr:
            school = School(uai=row['Code UAI'],
                            name=row['nom'],
                            acronym=row['sigle'],
                            academy=row['académie'],
                            address=row['adresse'],
                            postal_code=row['CP'],
                            city=row['commune'],
                            country='France',
                            lat=row['latitude (Y)'],
                            lng=row['longitude (X)'],
                            type=row["type d'établissement"],
                            imported=True, approved=True,
            )
            try:
                school.lat, school.lng = (float(row['latitude (Y)']),
                                          float(row['longitude (X)']))
            except ValueError:
                pass
            if not school.name:
                pass
            res[school.uai] = school
        return res

    def get_collegeslycees(self):
        c = requests.get(COLLEGESLYCEES_URL).content.decode('latin-1')
        cr = csv.DictReader(c.splitlines(), delimiter=';')
        res = {}
        for row in cr:
            school = School(uai=row['numero_uai'],
                            name=row['appellation_officielle'],
                            address=(row['adresse_uai'] + ' ' +
                                     row['lieu_dit_uai']).strip(),
                            postal_code=row['code_postal_uai'],
                            city=row['localite_acheminement_uai'],
                            country='France',
                            type=row['nature_uai_libe'],
                            imported=True, approved=True,
            )
            try:
                school.lat, school.lng = (float(row['coordonnee_y']),
                                          float(row['coordonnee_x']))
            except ValueError:
                pass
            if not school.name:
                pass
            res[school.uai] = school
        return res

    def handle(self, *args, **options):
        schools = {}
        schools.update(self.get_collegeslycees())
        schools.update(self.get_superieur())
        uais = list(schools.keys())

        for uais_batch in batch(uais, 100):
            School.objects.filter(uai__in=uais_batch).delete()
        School.objects.bulk_create(schools.values())
