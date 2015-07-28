import itertools
import os

from django import db
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.core.management.base import LabelCommand, CommandError
from django.template.defaultfilters import slugify
from django.utils import timezone

import prologin.models
from ._migration_utils import *  # noqa

User = get_user_model()
CURRENT_TIMEZONE = timezone.get_current_timezone()

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
  u.pass                                        AS password,   # pass is a reserved keyword
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
WHERE u.name IS NOT NULL AND u.name != '' AND u.mail != '' AND u.pass != ''
GROUP BY u.uid
ORDER BY u.uid ASC
"""


class Command(LabelCommand):
    help = "Move data from old, shitty MySQL/Drupal database to the shinny new Postgres/Django one."

    def migrate_users(self):
        self.stdout.write("Migrating users")

        def looks_like_bot(user):
            if '[url=' in user.signature:
                return '[url] in signature', user.signature[:100]
            if user.signature.count('http://') + user.signature.count('https://') >= 5:
                return 'many URLs in signature', user.signature[:100]
            if 'noong' in user.address.lower():
                return 'noong in address', user.address
            if 'yahoo.com' in user.email and user.username.startswith('rose'):
                return 'rose/yahoo', user.username, user.email
            if ('http://' in user.signature or 'https://' in user.signature) and '.ru' in user.signature:
                # russians h4ck3rs
                return '.ru website', user.signature[:100]
            suspicious = any((user.username == user.first_name,
                              user.username == user.last_name,
                              user.last_name == user.first_name))
            if suspicious and user.phone == '123456':
                return '123456 phone',
            if suspicious and '@gmail' in user.email and user.email.split('@', 1)[0].count('.') >= 4:
                # savi.pr.e.c.h.e.y.sh.aqe.milk@gmail.com
                return 'GMail dot trickery', user.email
            return None

        new_users = []
        ignored_bots = set()
        with self.mysql.cursor() as c:
            c.execute(USER_QUERY)
            for row in namedcolumns(c):
                p_birthday = None
                birthday = None
                if row.p_birthday:
                    p_birthday = parse_php_birthday(row.p_birthday)
                if row.u_birthday and p_birthday and row.u_birthday != p_birthday:
                    self.stdout.write("Different u/p birthday: {} {}".format(row.u_birthday, p_birthday))
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
                    self.stdout.write("Ignoring too long:".format(row.uid, row.name))
                    continue
                try:
                    language = map_from_legacy_language(row.training_language).name
                except AttributeError:
                    language = ''
                user = User(
                    pk=row.uid, username=row.name, email=row.mail, first_name=nstrip(row.fn, 30),
                    legacy_md5_password=row.password, last_name=nstrip(row.ln, 30), phone=nstrip(row.phone, 16),
                    address=nstrip(row.a_addr), postal_code=nstrip(row.a_code, 32), city=nstrip(row.a_city, 64),
                    country=nstrip(row.country, 64), birthday=birthday, school_stage=row.grade, signature=row.signature,
                    gender=gender, timezone=user_timezone, allow_mailing=bool(row.mailing),
                    preferred_language=language,
                    date_joined=date_localize(date_joined, user_timezone),
                    last_login=date_localize(last_login, user_timezone), is_active=bool(row.status),
                    is_superuser=bool(row.is_superuser), is_staff=bool(row.is_superuser) or bool(row.is_staff),
                )
                spam = looks_like_bot(user)
                if spam is not None:
                    reason, *data = spam
                    ignored_bots.add(user.pk)
                    self.stdout.write("Ignoring bot: {}: {!r}".format(reason, data))
                    continue
                new_users.append(user)

        with self.mysql.cursor() as c:
            c.execute('SELECT user_id FROM resultat_qcms GROUP BY user_id')
            ids = set(u.user_id for u in namedcolumns(c))
            self.stdout.write("Bot users intersected with users who sent a QCM "
                              "(should be empty):\n{}".format(ids & ignored_bots))

        self.stdout.write("Committing users to new database")
        with db.transaction.atomic():
            User.objects.bulk_create(new_users)

    def migrate_user_pictures(self):
        import requests
        from concurrent.futures import ThreadPoolExecutor
        from django.core.files.base import ContentFile

        BASE_URL = "http://prologin.org/"
        QUERY = """
        SELECT u.uid, u.picture, COUNT(DISTINCT ty.year) AS years
        FROM users u
        LEFT JOIN team_years ty ON ty.uid = u.uid
        GROUP BY u.uid
        HAVING u.picture != '' OR years > 0
        ORDER BY u.uid
        """
        session = requests.Session()

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
                picture_req = session.get(BASE_URL + url)
                if not picture_req.ok:
                    raise requests.RequestException("Status is not 2xx")
                image_field.save(os.path.split(url)[1], ContentFile(picture_req.content))
                return True
            except requests.RequestException:
                return False

        def handle_user(item):
            uid, picture = item.uid, item.picture
            try:
                user = User.objects.prefetch_related('team_memberships').get(pk=uid)
            except User.DoesNotExist:
                return

            self.stdout.write("Handling {}".format(item.uid))
            if picture:
                # Normal avatar
                res = fetch_file(user.avatar, picture)
                if res:
                    self.stdout.write("Fetched picture for {}".format(user))
                elif res is False:
                    self.stdout.write("Could not fetch picture for {}".format(user))

            # Official profile picture
            if user.team_memberships.count():
                # So reliable. Much Drupal. Wow.
                res = fetch_file(user.picture, 'files/team/%s.jpg' % user.username.lower())
                if res:
                    self.stdout.write("Fetched official picture for {}".format(user))
                elif res is False:
                    self.stdout.write("Could not fetch official picture for {}".format(user))

        self.stdout.write("Migrating user avatars and official pictures")
        with self.mysql.cursor() as c:
            c.execute(QUERY)
            users = list(namedcolumns(c))
            with ThreadPoolExecutor(max_workers=4) as executor:
                executor.map(handle_user, users)

    def migrate_examcenters(self):
        import centers.models

        field_map = (
            ('civilite', 'gender', lambda e:
                prologin.models.Gender.male.value if e == 'Monsieur'
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

        self.stdout.write("Migrating exam centers")
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
                self.stdout.write("Migrated center: {}".format(center))
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
                        self.stdout.write("\tNew center contact: {}".format(contact))
                        contact.save()

    def migrate_teams(self):
        import team.models
        self.stdout.write("Migrating teams")
        role_table = {}
        with self.mysql.cursor() as c:
            c.execute("SELECT MAX(id) AS m FROM team_ranks")
            max_id = next(namedcolumns(c)).m
            c.execute("SELECT * FROM team_ranks")
            for row in namedcolumns(c):
                self.stdout.write("Migrated team role: {}".format(row.title))
                role = team.models.Role(id=row.id, significance=max_id - row.id, name=row.title)
                role_table[role.id] = role
        team.models.Role.objects.bulk_create(role_table.values())

        with db.transaction.atomic():
            with self.mysql.cursor() as c:
                c.execute("SELECT * FROM team_years ORDER BY uid")
                for uid, rows in itertools.groupby(list(namedcolumns(c)), lambda r: int(r.uid)):
                    try:
                        user = User.objects.get(pk=uid)
                    except User.DoesNotExist:
                        self.stdout.write("User id {} does not exist in migrated DB".format(uid))
                        continue
                    for row in rows:
                        user.team_memberships.add(
                            team.models.TeamMember(year=row.year, user=user, role=role_table[row.id_rank])
                        )
                    self.stdout.write("Migrated team roles for {}".format(user))

    def migrate_problem_submissions(self, code_archive_path):
        """
        Migrate problem submissions and code snippets.

        :param code_archive_path: the path to the archive folder containing all the code files.
                                  the file naming scheme is 'challenge-problem-user.ext'.
        """
        import problems.models
        import chardet  # so we can still use a nice TextField(), not a BinaryField(), to store codes

        self.stdout.write("Migrating problem submissions")

        def get_codes(user, submission):
            pattern = '{}-{}-{}'.format(submission.challenge, submission.problem, user.username)
            pattern = os.path.join(code_archive_path, pattern)
            for ext, lang in map_from_legacy_language.mapping.items():
                fname = pattern + ext
                if os.path.exists(fname):
                    yield (fname, lang.name)

        with self.mysql.cursor() as c:
            c.execute("SELECT * FROM training_access ORDER BY uid")
            for uid, rows in itertools.groupby(list(namedcolumns(c)), lambda r: int(r.uid)):
                try:
                    user = User.objects.get(pk=uid)
                except User.DoesNotExist:
                    self.stdout.write("User id {} does not exist in migrated DB".format(uid))
                    continue

                for row in rows:
                    # is_dst not available in Django 1.8 make_aware(). Fuck this.
                    # date = timezone.make_aware(row.timestamp, CURRENT_TIMEZONE, is_dst=True)
                    date = CURRENT_TIMEZONE.localize(row.timestamp, is_dst=True)
                    submission, created = problems.models.Submission.objects.get_or_create(
                        user=user,
                        challenge=row.challenge,
                        problem=row.problem)
                    if not created:
                        continue

                    submission.score_base = row.score
                    submission.malus = row.malus
                    submission.save()
                    with db.transaction.atomic():
                        i = 0
                        for i, (fname, lng) in enumerate(get_codes(user, submission)):
                            with open(fname, 'rb') as f:
                                code = f.read()
                                try:
                                    code = code.decode(chardet.detect(code)['encoding'])
                                except TypeError:  # 'encoding' is None
                                    self.stdout.write("{}: chardet could not detect encoding".format(fname))
                                    continue
                                except UnicodeDecodeError:
                                    self.stdout.write("{}: chardet made a mistake".format(fname))
                                    continue

                            submission_code, created = problems.models.SubmissionCode.objects.get_or_create(
                                submission=submission,
                                code=code,
                                language=lng,
                                date_submitted=date)
                            submission_code.save()

                        if i:
                            self.stdout.write("{} {}: {}".format(user.username, submission, i))

    def migrate_news(self):
        from zinnia.models import Entry
        from zinnia.models.author import Author
        from zinnia.managers import PUBLISHED, HIDDEN

        self.stdout.write("Migrating news")
        main_site = Site.objects.get()

        query = '''
          SELECT n.nid, n.promote, n.uid, nr.title, nr.body, nr.teaser, n.created, n.changed, n.comment FROM node n
          INNER JOIN node_revisions nr ON nr.nid = n.nid
          WHERE n.type = 'story' AND n.status = 1 AND nr.title != '' AND nr.body != ''
          GROUP BY n.nid
          ORDER BY n.created ASC
        '''

        Entry.objects.all().delete()
        with self.mysql.cursor() as c:
            c.execute(query)
            with db.transaction.atomic():
                for row in namedcolumns(c):
                    date_created = CURRENT_TIMEZONE.localize(datetime.datetime.fromtimestamp(row.created), is_dst=True)
                    date_changed = CURRENT_TIMEZONE.localize(datetime.datetime.fromtimestamp(row.changed), is_dst=True)
                    entry = Entry(
                        id=row.nid,
                        title=row.title,
                        slug=slugify(row.title),
                        status=PUBLISHED if row.promote else HIDDEN,
                        publication_date=date_created,
                        start_publication=date_created,
                        creation_date=date_created,
                        last_update=date_changed,
                        content=row.body,
                        comment_enabled=row.comment == 2,
                        lead='' if row.body == row.teaser else row.teaser,
                    )
                    entry.save()
                    entry.sites.add(main_site)
                    try:
                        a = Author.objects.get(pk=row.uid)
                        entry.authors.add(a)
                    except Author.DoesNotExist:
                        self.stdout.write("Unknown author: {}".format(row.uid))

    # TODO: forum
    # TODO: news comments

    def handle_label(self, label, **options):
        args = []
        if label == 'problem_submissions':
            self.stdout.write("Provide the absolute path to the `archive` folder (with contestant \n"
                              "latest submissions):")
            args = [input("`archive` folder absolute path: ")]

        try:
            func = getattr(self, 'migrate_{}'.format(label))
        except AttributeError:
            import inspect
            labels = (_[0].split('_', 1)[1]
                      for _ in inspect.getmembers(self,
                                                  lambda e: inspect.ismethod(e) and e.__name__.startswith('migrate_')))
            self.stderr.write("Available migrations: {}".format(", ".join(labels)))
            raise CommandError("No such migration: {}".format(label))

        # check if we can access the legacy db
        self.mysql = db.connections['mysql_legacy']
        with self.mysql.cursor() as c:
            c.execute('SHOW TABLES')
            tables = c.fetchall()
        self.stdout.write("Found {} tables".format(len(tables)))

        func(*args)