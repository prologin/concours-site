from django import db
from django.conf import settings
from django.core.management.base import BaseCommand
import itertools
import os

import prologin.utils
import prologin.models
import users.models
from ._migration_utils import *  # noqa lol I heard u like PEP8 well screw u


USER_QUERY = """
SELECT
  u.uid,
  status,
  name,
  mail,
  signature,
  timezone,
  picture,
  training_language,
  u.birthday                                    AS u_birthday,
  IF(created > 0, FROM_UNIXTIME(created), NULL) AS created,
  IF(access > 0, FROM_UNIXTIME(access), NULL)   AS access,
  IF(login > 0, FROM_UNIXTIME(login), NULL)     AS login,
  NOT(ISNULL(urc.uid))                          AS is_staff,
  NOT(ISNULL(ura.uid))                          AS is_superuser,
  pvg.value                                     AS gender,
  pvln.value                                    AS ln,
  pvfn.value                                    AS fn,
  pvbd.value                                    AS p_birthday,
  pvp.value                                     AS country,
  pvl.value                                     AS grade,
  pvaa.value                                    AS a_addr,
  pvap.value                                    AS a_code,
  pvac.value                                    AS a_city,
  NOT (pvnm.value)                              AS mailing,
  pvph.value                                    AS phone
FROM users u
  LEFT JOIN users_roles urc ON urc.uid = u.uid AND urc.rid = 6
  LEFT JOIN users_roles ura ON ura.uid = u.uid AND ura.rid = 7
  LEFT JOIN profile_values pvg ON pvg.uid = u.uid AND pvg.fid = 1
  LEFT JOIN profile_values pvln ON pvln.uid = u.uid AND pvln.fid = 2
  LEFT JOIN profile_values pvfn ON pvfn.uid = u.uid AND pvfn.fid = 3
  LEFT JOIN profile_values pvbd ON pvbd.uid = u.uid AND pvbd.fid = 5
  LEFT JOIN profile_values pvp ON pvp.uid = u.uid AND pvp.fid = 6
  LEFT JOIN profile_values pvl ON pvl.uid = u.uid AND pvl.fid = 7
  LEFT JOIN profile_values pvaa ON pvaa.uid = u.uid AND pvaa.fid = 8
  LEFT JOIN profile_values pvap ON pvap.uid = u.uid AND pvap.fid = 9
  LEFT JOIN profile_values pvac ON pvac.uid = u.uid AND pvac.fid = 10
  LEFT JOIN profile_values pvnm ON pvnm.uid = u.uid AND pvnm.fid = 11
  LEFT JOIN profile_values pvph ON pvph.uid = u.uid AND pvph.fid = 12
WHERE u.name IS NOT NULL AND u.name != '' AND u.mail != ''
GROUP BY u.uid
ORDER BY u.uid ASC
"""


class Command(BaseCommand):
    help = "Move data from old, shitty MySQL database to the shinny new Postgres one."

    def migrate_users(self):
        print("Migrating users")
        new_users = []
        with self.mysql.cursor() as c:
            c.execute(USER_QUERY)
            for row in namedcolumns(c):
                p_birthday = None
                birthday = None
                if row.p_birthday:
                    p_birthday = parse_php_birthday(row.p_birthday)
                if row.u_birthday and p_birthday and row.u_birthday != p_birthday:
                    print("Different u/p birthday:", row.u_birthday, p_birthday)
                    birthday = p_birthday
                elif row.u_birthday and not p_birthday:
                    birthday = row.u_birthday
                elif p_birthday and not row.u_birthday:
                    birthday = p_birthday
                gender = None
                if row.gender is not None:
                    gender = (prologin.models.Gender.male if row.gender == 'Monsieur'
                              else prologin.models.Gender.female).value
                user_timezone = guess_timezone(row.timezone)
                date_joined = min(date for date in (row.created, row.access, row.login) if date)
                last_login = max(date for date in (row.created, row.access, row.login) if date)
                if len(row.name) > 30:
                    print("Ignoring too long:", row.uid, row.name)
                    continue
                user = users.models.ProloginUser(
                    pk=row.uid, username=row.name, email=row.mail, first_name=nstrip(row.fn, 30), last_name=nstrip(row.ln, 30),
                    phone=nstrip(row.phone, 16), address=nstrip(row.a_addr), postal_code=nstrip(row.a_code, 32),
                    city=nstrip(row.a_city, 64), country=nstrip(row.country, 64), birthday=birthday,
                    school_stage=row.grade, signature=row.signature, gender=gender,
                    timezone=user_timezone, allow_mailing=bool(row.mailing),
                    preferred_language=map_from_legacy_language(row.training_language),
                    date_joined=date_localize(date_joined, user_timezone),
                    last_login=date_localize(last_login, user_timezone), is_active=bool(row.status),
                    is_superuser=bool(row.is_superuser), is_staff=bool(row.is_superuser) or bool(row.is_staff),
                )
                new_users.append(user)

        print("Now adding users to new DBs")
        with db.transaction.atomic():
            users.models.ProloginUser.objects.bulk_create(new_users)

    def migrate_user_pictures(self):
        BASE_URL = "http://prologin.org/"
        import requests
        from django.core.files.base import ContentFile

        def fetch_file(image_field, url):
            try:
                image_field.open()
                return None
            except ValueError:
                # Standard use case
                pass
            except FileNotFoundError:
                # DB contains an avatar path that is not backed on disk, so download again
                pass
            try:
                picture_req = requests.get(BASE_URL + url)
                if not picture_req.ok:
                    raise requests.RequestException("Status is not 2xx")
                image_field.save(os.path.split(url)[1], ContentFile(picture_req.content))
                return True
            except requests.RequestException:
                return False

        with self.mysql.cursor() as c:
            c.execute("SELECT uid, picture FROM users ORDER BY name")
            for uid, picture in c:
                try:
                    user = users.models.ProloginUser.objects.get(pk=uid)
                except users.models.ProloginUser.DoesNotExist:
                    continue

                if picture:
                    # Normal avatar
                    res = fetch_file(user.avatar, picture)
                    if res:
                        print("Fetched picture for", user)
                    elif res is False:
                        print("Could not fetch picture for", user)

                # Official profile picture
                if user.team_memberships.count():
                    # So reliable. Much Drupal. Wow.
                    res = fetch_file(user.picture, 'files/team/%s.jpg' % user.username.lower())
                    if res:
                        print("Fetched official picture for", user)
                    elif res is False:
                        print("Could not fetch official picture for", user)

    def migrate_examcenters(self):
        import centers.models
        field_map = (
            ('civilite', 'gender', lambda e: prologin.models.Gender.male.value if e == 'Monsieur'
                                             else prologin.models.Gender.female.value if e in ('Madame', 'Mademoiselle')
                                             else None),
            ('nom', 'last_name', lambda e: nstrip(e, 64)),
            ('prenom', 'first_name', lambda e: nstrip(e, 64)),
            ('statut', 'position', lambda e: nstrip(e, 128)),
            ('tel_fixe', 'phone_desk', lambda e: nstrip(e, 16)),
            ('tel_mobile', 'phone_mobile', lambda e: nstrip(e, 16)),
            ('fax', 'phone_fax', lambda e: nstrip(e, 16)),
            ('email', 'email', lambda e: e.strip().lower()),
        )
        with self.mysql.cursor() as c:
            c.execute("SELECT * FROM centre_examens ORDER BY id")
            for row in namedcolumns(c):
                center = centers.models.Center(
                    # Center
                    pk=row.id,
                    name=nstrip(row.nom, 64),
                    type=centers.models.Center.Type.center.value,
                    is_active=bool(row.visible),
                    # AddressableModel
                    address=row.adresse.strip(),
                    postal_code=nstrip(row.code_postal, 32),
                    city=nstrip(row.ville, 64),
                    country="France",
                )
                print("Migrated center:", center)
                center.save()
                for prefix, newtype in (
                        ('resp', centers.models.Contact.Type.manager),
                        ('contact', centers.models.Contact.Type.contact),):
                    contact = centers.models.Contact(center=center, type=newtype.value)
                    useful = False
                    for oldfield, newfield, adaptor in field_map:
                        value = adaptor(getattr(row, '%s_%s' % (prefix, oldfield)))
                        if value is not None and value != '':
                            useful = True
                            setattr(contact, 'contact_%s' % newfield, value)
                    if useful:
                        print("\tNew center contact:", contact)
                        contact.save()

    def migrate_teams(self):
        import team.models
        role_table = {}
        with self.mysql.cursor() as c:
            c.execute("SELECT * FROM team_ranks")
            for row in namedcolumns(c):
                print("Migrated team role:", row.title)
                role = team.models.Role(rank=row.id, name=row.title)
                role_table[role.rank] = role
        team.models.Role.objects.bulk_create(role_table.values())

        with self.mysql.cursor() as c:
            c.execute("SELECT * FROM team_years ORDER BY uid")
            for uid, rows in itertools.groupby(list(namedcolumns(c)), lambda r: int(r.uid)):
                try:
                    user = users.models.ProloginUser.objects.get(pk=uid)
                except users.models.ProloginUser.DoesNotExist:
                    print("User id %d does not exist in migrated DB" % uid)
                    continue
                for row in rows:
                    user.team_memberships.add(
                        team.models.TeamMember(year=row.year, user=user, role=role_table[row.id_rank])
                    )
                print("Migrated team roles for", user)

    def handle(self, *args, **options):
        # check if we can access the legacy db
        # mc is MySQL cursor
        self.mysql = db.connections['mysql_legacy']
        with self.mysql.cursor() as c:
            c.execute('SHOW TABLES')
            tables = c.fetchall()
        print("Found {} tables".format(len(tables)))

        #self.migrate_users()
        self.migrate_user_pictures()
        #self.migrate_examcenters()
        #self.migrate_teams()
        # TODO: the rest
