import concurrent.futures
import enum
import itertools
import operator

from django.db import transaction, connections, IntegrityError
from django.db.models import Prefetch
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import LabelCommand, CommandError
from django.template.defaultfilters import slugify

import prologin.models
from ._migration_utils import *  # noqa

User = get_user_model()
DRUPAL_SITE_BASE_URL = "http://prologin.org/"  # For downloading content (mainly files/)

"""
TODO:
    - forum (categories, messages)
    - news comments
"""


class Command(LabelCommand):
    help = "Move data from old, shitty MySQL/Drupal database to the shinny new Postgres/Django one."

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mysql = connections['mysql_legacy']

    def migrate_users(self):
        user_query = """
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
        ORDER BY u.uid
        """

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
            c.execute(user_query)
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
                gender = parse_gender(row.gender)
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
            c.execute("""SELECT user_id FROM resultat_qcms GROUP BY user_id""")
            ids = set(u.user_id for u in namedcolumns(c))
            self.stdout.write("Bot users intersected with users who sent a QCM "
                              "(should be empty):\n{}".format(ids & ignored_bots))

        self.stdout.write("Committing users to new database")
        with transaction.atomic():
            User.objects.bulk_create(new_users)

    def migrate_user_pictures(self):
        query = """
        SELECT u.uid, u.picture, COUNT(DISTINCT ty.year) AS years
        FROM users u
        LEFT JOIN team_years ty ON ty.uid = u.uid
        GROUP BY u.uid
        HAVING u.picture != '' OR years > 0
        ORDER BY u.uid
        """
        session = requests.Session()

        def handle_user(item):
            uid, picture = item.uid, item.picture
            try:
                user = User.objects.prefetch_related('team_memberships').get(pk=uid)
            except User.DoesNotExist:
                return

            self.stdout.write("Handling {}".format(item.uid))
            if picture:
                # Normal avatar
                res = field_fetch_file(session, user.avatar, '{}{}'.format(DRUPAL_SITE_BASE_URL, picture))
                if res:
                    self.stdout.write("Fetched picture for {}".format(user))
                elif res is False:
                    self.stderr.write("Could not fetch picture for {}".format(user))

            # Official profile picture
            if user.team_memberships.count():
                # So reliable. Much Drupal. Wow.
                res = field_fetch_file(session, user.picture, '{}files/team/{}.jpg'.format(DRUPAL_SITE_BASE_URL,
                                                                                           user.username.lower()))
                if res:
                    self.stdout.write("Fetched official picture for {}".format(user))
                elif res is False:
                    self.stderr.write("Could not fetch official picture for {}".format(user))

        self.stdout.write("Migrating user avatars and official pictures")
        with self.mysql.cursor() as c:
            c.execute(query)
            users = list(namedcolumns(c))
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            executor.map(handle_user, users)

    def migrate_examcenters(self):
        import centers.models

        field_map = (
            ('civilite', 'gender', parse_gender),
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

        with transaction.atomic():
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

    def migrate_legacy_problem_submissions(self):
        """
        Migrate oldish (pre-2007) problem submissions and code snippets.
        """
        import problems.models
        from difflib import SequenceMatcher
        from collections import defaultdict

        # First pass: map plain text problem names to problems/ names

        query = """
        SELECT DISTINCT id, nom, description
        FROM sujets
        WHERE nom != '' AND description != ''
        ORDER BY nom, description
        """

        challenge_problems = defaultdict(list)
        problem_mapping = {}

        with self.mysql.cursor() as c:
            c.execute(query)
            for row in namedcolumns(c):
                if row.id == 106:
                    # hey! let's copy paste a problem from demi 2002 in demi 2006
                    # without changing the name! lol such fun!
                    challenge_name = 'demi2006'
                else:
                    challenge_name = row.nom.split('.', 1)[0].lower()

                try:
                    challenge = problems.models.Challenge.by_low_level_name(challenge_name)
                    challenge_problems[challenge].append(row)
                except ObjectDoesNotExist:
                    continue

        for challenge, legacy_problems in challenge_problems.items():
            new_problem_pool = list(challenge.problems)

            for legacy_problem in legacy_problems:
                if not new_problem_pool:
                    self.stderr.write("Could not find an existing problem for {!r}; skipped".format(legacy_problem))
                    continue

                def distance(problem):
                    title = legacy_problem.description.lower().replace('qcm', '').replace('demi-finale', '')
                    return SequenceMatcher(None, title, problem.title.lower()).ratio()

                found = max(new_problem_pool, key=distance)
                new_problem_pool.remove(found)
                problem_mapping[legacy_problem.id] = found

            if new_problem_pool:
                self.stderr.write("Problems not tackled by any submission: {!r}".format(new_problem_pool))

        # We got the mapping. Let's actually import the code snippets.

        submission_query = """
        SELECT user_id, sujet_id, date, language, source
        FROM sujet_soumissions
        ORDER BY user_id, sujet_id, date
        """

        with self.mysql.cursor() as c:
            c.execute(submission_query)
            with transaction.atomic():
                for user_id, rows in itertools.groupby(namedcolumns(c), key=lambda r: r.user_id):
                    try:
                        user = User.objects.get(pk=user_id)
                    except User.DoesNotExist:
                        self.stderr.write("Unknown user: {}".format(user_id))
                        continue

                    for sujet_id, rows in itertools.groupby(rows, key=lambda r: r.sujet_id):
                        try:
                            problem = problem_mapping[sujet_id]
                        except KeyError:
                            self.stderr.write("Unknown challenge/problem: {}".format(sujet_id))
                            continue

                        # we don't know the score base nor malus
                        submission, created = (problems.models.Submission
                                               .objects.get_or_create(user=user,
                                                                      challenge=problem.challenge.name,
                                                                      problem=problem.name))
                        if created:
                            submission.save()
                        for row in rows:
                            language = Language.guess(row.language.strip('_.')) or Language['pseudocode']
                            code = problems.models.SubmissionCode(submission=submission,
                                                                  code=row.source,
                                                                  language=language.name,
                                                                  date_submitted=localize(row.date))
                            code.save()

    def migrate_problem_submissions(self, code_archive_path):
        """
        Migrate problem submissions and code snippets.

        :param code_archive_path: the path to the archive folder containing all the code files.
                                  the file naming scheme is 'challenge-problem-user.ext'.
        """
        import problems.models
        from collections import Counter
        import chardet  # so we can still use a nice TextField(), not a BinaryField(), to store codes

        submission_query = """
        SELECT uid, challenge, problem,
               MAX(score) AS score,
               MAX(malus) AS malus,
               MAX(timestamp) AS timestamp
        FROM training_access
        GROUP BY uid, challenge, problem
        ORDER BY uid, challenge, problem
        """

        self.stdout.write("Migrating problem submissions")

        code_archive_path = os.path.abspath(code_archive_path)
        all_files = set(os.listdir(code_archive_path))
        lang_stats = Counter()
        chardet_stats = Counter()

        if len(all_files) < 100:
            self.stderr.write("There are less than 100 files in {}. You must have given the wrong path."
                              .format(code_archive_path))
            return

        self.stdout.write("Found {} files".format(len(all_files)))

        def get_codes(user, submission):
            pattern = '{}-{}-{}'.format(submission.challenge, submission.problem, user.username)
            for lang in Language:
                for ext in lang.extensions():
                    fname = pattern + ext
                    if fname in all_files:
                        yield (fname, lang.name)

        def retrieve_submissions():
            with self.mysql.cursor() as c:
                c.execute(submission_query)
                user_to_rows = {uid: list(rows)
                                for uid, rows
                                in itertools.groupby(list(namedcolumns(c)), lambda r: int(r.uid))}
                for user in User.objects.filter(pk__in=user_to_rows.keys()):
                    for row in user_to_rows[user.pk]:
                        yield user, row

        def handle_submission(args):
            user, row = args
            submission = problems.models.Submission(user=user,
                                                    challenge=row.challenge,
                                                    problem=row.problem,
                                                    score_base=row.score,
                                                    malus=row.malus)
            submission.save()
            date = localize(row.timestamp)
            return user, submission, date

        def handle_submission_codes(args):
            user, submission, date = args
            i = 0
            file_names = set()
            for i, (file_name, lang) in enumerate(get_codes(user, submission)):
                with open(os.path.join(code_archive_path, file_name), 'rb') as f:
                    code = f.read()
                try:
                    encoding = chardet.detect(code)['encoding']
                    code = code.decode(encoding)
                    chardet_stats[encoding] += 1
                    lang_stats[lang] += 1
                except TypeError:  # 'encoding' is None
                    self.stderr.write("{}: chardet could not detect encoding".format(file_name))
                    continue
                except UnicodeDecodeError:
                    self.stderr.write("{}: chardet made a mistake".format(file_name))
                    continue

                submission_code = problems.models.SubmissionCode(submission=submission,
                                                                 code=code,
                                                                 language=lang,
                                                                 date_submitted=date)
                submission_code.save()
                file_names.add(file_name)
            if i:
                self.stdout.write("{} {}: {}".format(user.username, submission, i))
            return file_names

        user_submissions = retrieve_submissions()

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            self.stdout.write("Creating submissions")
            with transaction.atomic():
                submissions = executor.map(handle_submission, user_submissions)
            self.stdout.write("Submission committed. Creating submission codes")
            with transaction.atomic():
                used_fname_sets = executor.map(handle_submission_codes, submissions)
            self.stdout.write("Codes committed.")

        used_fnames = functools.reduce(operator.or_, used_fname_sets)
        unused_fnames = all_files - used_fnames
        self.stdout.write("\n{} source code files were rejected or unused.\n".format(len(unused_fnames)))
        self.stdout.write("Source encoding stats: {!r}\n".format(chardet_stats))
        self.stdout.write("Source language stats: {!r}".format(lang_stats))

    def migrate_news(self):
        from zinnia.models import Entry
        from zinnia.models.author import Author
        from zinnia.managers import PUBLISHED, HIDDEN

        self.stdout.write("Migrating news")
        main_site = Site.objects.get()

        query = """
          SELECT n.nid, n.promote, n.uid, nr.title, nr.body, nr.teaser, n.created, n.changed, n.comment FROM node n
          INNER JOIN node_revisions nr ON nr.nid = n.nid
          WHERE n.type = 'story' AND n.status = 1 AND nr.title != '' AND nr.body != ''
          GROUP BY n.nid
          ORDER BY n.created
        """

        with self.mysql.cursor() as c:
            c.execute(query)
            with transaction.atomic():
                for row in namedcolumns(c):
                    date_created = localize(datetime.datetime.fromtimestamp(row.created))
                    date_changed = localize(datetime.datetime.fromtimestamp(row.changed))
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

    def migrate_events(self):
        import contest.models
        import centers.models

        query = """
        SELECT c.id, c.annee, c.debut, c.fin, LOWER(TRIM(c.type)) AS type,
        c.centre_examen_id AS centre_id, centre.nom AS centre_nom
        FROM concours c
        LEFT JOIN centre_examens centre ON centre.id = c.centre_examen_id
        ORDER BY c.annee
        """

        with self.mysql.cursor() as c:
            c.execute(query)
            rows = list(namedcolumns(c))

        class DateType(enum.Enum):
            begin = 'debut'
            end = 'fin'

        def get_date_or_guess(year, event, date_type):
            """Guess date of event where it's not available in database."""
            date = getattr(event, date_type.value)
            if date:
                return date
            self.stderr.write("No date for year {} type {}, using guess".format(year, date_type.name))
            if event.type == 'qcm':
                if date_type == DateType.begin:
                    return datetime.date(year - 1, 10, 1)
                else:
                    return datetime.date(year, 1, 1)
            elif event.type == 'demifinale':
                if date_type == DateType.begin:
                    return datetime.date(year, 2, 1)
                else:
                    return datetime.date(year, 2, 1)
            elif event.type == 'finale':
                if date_type == DateType.begin:
                    return datetime.date(year, 5, 1)
                else:
                    return datetime.date(year, 5, 3)
            raise ValueError("Unknown event type: {}".format(event.type))

        # Create the editions
        with transaction.atomic():
            for year, events in itertools.groupby(rows, key=lambda e: e.annee):
                events = list(events)
                date_begin = localize(min(get_date_or_guess(year, event, DateType.begin) for event in events))
                date_end = localize(max(get_date_or_guess(year, event, DateType.end) for event in events))
                edition = contest.models.Edition(year=year, date_begin=date_begin, date_end=date_end)
                try:
                    edition.save()
                except IntegrityError:
                    self.stdout.write("Edition {} already exists".format(year))

        self.stdout.write("There are {} editions.".format(contest.models.Edition.objects.count()))

        # Create the edition events
        with transaction.atomic():
            for year, events in itertools.groupby(rows, key=lambda e: e.annee):
                try:
                    edition = contest.models.Edition.objects.get(year=year)
                except contest.models.Edition.DoesNotExist:
                    self.stderr.write("No such edition: {}".format(year))
                    continue

                for row in events:
                    kwargs = {}
                    if row.type == 'qcm':
                        type = contest.models.Event.Type.qualification
                    elif row.type == 'demifinale':
                        type = contest.models.Event.Type.semifinal
                        try:
                            kwargs['center'] = centers.models.Center.objects.get(pk=row.centre_id)
                        except centers.models.Center.DoesNotExist:
                            self.stderr.write("Warning: exam center (ID {}, name {}) does not exist for semifinal {}"
                                              .format(row.centre_id, row.centre_nom, edition))
                    elif row.type == 'finale':
                        type = contest.models.Event.Type.final
                    else:
                        self.stderr.write("Unknown event type: {}".format(row.type))
                        continue
                    date_begin = get_date_or_guess(year, row, DateType.begin)
                    date_end = get_date_or_guess(year, row, DateType.end)
                    event, created = contest.models.Event.objects.get_or_create(
                        pk=row.id, edition=edition, type=type.value,
                        date_begin=date_begin, date_end=date_end, **kwargs)
                    event.save()

        # Consistency checks
        for type in (contest.models.Event.Type.qualification, contest.models.Event.Type.final):
            editions = (contest.models.Edition.objects
                        .prefetch_related(Prefetch('events',
                                                   to_attr='the_events',
                                                   queryset=contest.models.Event.objects.filter(type=type.value))))
            for edition in editions:
                l = len(edition.the_events)
                if l == 0:
                    self.stderr.write("Consistency warning: edition {} has no {} event".format(edition, type.name))
                elif l > 1:
                    self.stderr.write("Consistency warning: edition {} has {} {} events".format(edition, l, type.name))

        editions = (contest.models.Edition.objects
                    .prefetch_related(Prefetch('events',
                                               to_attr='semifinals',
                                               queryset=contest.models.Event.objects.filter(
                                                   type=contest.models.Event.Type.semifinal.value))))
        for edition in editions:
            if not edition.semifinals:
                self.stderr.write("Consistency warning: edition {} has no semifinal events".format(edition))

    def migrate_contest_results(self):
        import contest.models

        # We merge resultat_qcms and resultat_demi_finales so we can retrieve everything
        # using one big query. Each row is processed according to 'type' with is either
        # 'qualif' or 'semi'.
        # We don't use COALESCE() for the dates because sometimes, it's equal to 0 (which
        # is not NULL) so COALESCE() returns 0 instead of trying the next one. Hence the
        # nested IF()s for 'date'.
        # Finale results are ignored because there is nothing relevant in the table
        # 'resultat_finales'.
        query = """
        SELECT
          r.type,
          r.user_id,
          r.commentaires,
          r.correcteur,
          r.date,
          r.note1,
          r.note2,
          r.note3,
          r.note_finale,
          r.choix_demis,
          r.assignation,
          r.size,
          r.langage,
          ev.annee AS year
        FROM (
               SELECT
                 'qualif'                                                 AS type,
                 r.user_id,
                 r.qcm_id                                                 AS event_id,
                 r.commentaires,
                 r.correcteur,
                 IF(r.date_correction IS NOT NULL AND r.date_correction != 0,
                    r.date_correction,
                    IF(r.updated_on IS NOT NULL AND r.updated_on != 0,
                       r.updated_on,
                       r.created_on))                                     AS date,
                 r.note_qcm                                               AS note1,
                 r.note_algo                                              AS note2,
                 r.note_bonus                                             AS note3,
                 r.note_finale                                            AS note_finale,
                 CONCAT_WS(',', r.choix_demi_1, r.choix_demi_2, r.choix_demi_3) AS choix_demis,
                 rdf.demi_finale_id                                       AS assignation,
                 r.size                                                   AS size,
                 r.langage                                                AS langage
               FROM resultat_qcms r
               LEFT JOIN resultat_demi_finales rdf ON rdf.id = r.resultat_demi_finale_id
               UNION
               SELECT
                 'semi'                     AS type,
                 user_id,
                 demi_finale_id             AS event_id,
                 commentaires,
                 correcteur,
                 IF(updated_on IS NOT NULL AND updated_on != 0,
                    updated_on, created_on) AS date,
                 note_entretien             AS note1,
                 note_algo                  AS note2,
                 note_prog                  AS note3,
                 note_finale                AS note_finale,
                 NULL                       AS choix_demis,
                 NULL                       AS assignation,
                 NULL                       AS size,
                 NULL                       AS langage
               FROM resultat_demi_finales
             ) r
          INNER JOIN concours ev ON ev.id = r.event_id
        ORDER BY ev.annee, r.type, r.user_id
        """

        @functools.lru_cache(2000)
        def get_user(user_id):
            return User.objects.get(pk=user_id)

        @functools.lru_cache(128)
        def get_edition(year):
            return contest.models.Edition.objects.get(year=year)

        with self.mysql.cursor() as c:
            c.execute(query)
            with transaction.atomic():
                for row in namedcolumns(c):
                    try:
                        contestant, created = contest.models.Contestant.objects.get_or_create(
                            edition=get_edition(row.year), user=get_user(row.user_id))
                    except User.DoesNotExist:
                        self.stderr.write("User {} does not exist".format(row.user_id))
                        continue

                    if row.type == 'qualif':
                        # We have to keep the order of the wishes, so we first take all the
                        # relevant Event objects and store them in a dict for later querying.
                        semi_wish_pks = [int(e) for e in row.choix_demis.split(',') if e != '-1']
                        if semi_wish_pks:
                            event_wishes = {
                                e.pk: e
                                for e in contest.models.Event.objects.filter(
                                    type=contest.models.Event.Type.semifinal.value,
                                    edition__year=row.year,
                                    pk__in=semi_wish_pks,
                                )}
                        # T-shirt size
                        if row.size:
                            contestant.shirt_size = contest.models.Contestant.ShirtSize[row.size.lower().strip()].value
                        # Preferred language. This used to be a simple text <input/> so we don't try too hard to
                        # guess the language.
                        if row.langage:
                            try:
                                contestant.preferred_language = prologin.models.Language.guess(row.langage).name
                            except AttributeError:
                                self.stderr.write("Contestant {}: language could not be guessed: {}".format(
                                    contestant, row.langage))
                        # The event where contestant was actually assigned.
                        if row.assignation:
                            try:
                                contestant.assigned_event = contest.models.Event.objects.get(
                                    type=contest.models.Event.Type.semifinal.value,
                                    edition__year=row.year,
                                    pk=row.assignation,
                                )
                            except contest.models.Event.DoesNotExist:
                                self.stderr.write("Contestant {}: assignation: event {} does exist".format(
                                    contestant, row.assignation))

                        # note1, note2, note3 = qcm, algo, bonus
                        changes = {
                            'score_qualif_qcm': row.note1,
                            'score_qualif_algo': row.note2,
                            'score_qualif_bonus': row.note3,
                        }

                    elif row.type == 'semi':
                        # note1, note2, note3 = entretien, algo, prog
                        changes = {
                            'score_semifinal_interview': row.note1,
                            'score_semifinal_written': row.note2,
                            'score_semifinal_machine': row.note3,
                        }

                    else:
                        raise ValueError("Fix your query")

                    # Update notes on contestant model
                    for k, v in changes.items():
                        setattr(contestant, k, v)

                    contestant.save()

                    # Have to be done after contestant.save()
                    if row.type == 'qualif':
                        for n, pk in enumerate(semi_wish_pks):
                            try:
                                contest.models.EventWish(contestant=contestant,
                                                         event=event_wishes[pk],
                                                         order=n).save()
                            except KeyError:
                                self.stderr.write("Contestant {}: event whish #{} ID {} does not exist "
                                                  "or is not a semifinal".format(contestant, n, pk))

                    correction = contest.models.ContestantCorrection(contestant=contestant)
                    if row.correcteur is not None:
                        correction.author = User.objects.filter(username__icontains=row.correcteur).first()
                    correction.comment = row.commentaires or ''
                    correction.date_added = localize(row.date)
                    correction.event_type = (contest.models.Event.Type.qualification if row.type == 'qcm'
                                             else contest.models.Event.Type.semifinal).value
                    correction.changes = changes
                    correction.save()
                    self.stdout.write("Contestant {} was {}".format(contestant, "created" if created else "updated"))

    def migrate_quizz(self):
        import contest.models
        import qcm.models
        import sponsor.models

        query = """
        SELECT DISTINCT qcm.annee, question.id, question.question, question.commentaires, question.reponse,
          question.proposition_1, question.proposition_2, question.proposition_3, question.proposition_4,
          IF(sid.id IS NOT NULL, sid.id, skey.id) AS sponsor_id
        FROM epreuve_qcms question
        INNER JOIN concours qcm ON question.qcm_id = qcm.id
        LEFT JOIN sponsors sid  ON sid.id   = question.sponsor -- \ because you can query by ID or by 'key', genius!
        LEFT JOIN sponsors skey ON skey.cle = question.sponsor -- /
        WHERE TRIM(LOWER(qcm.type)) = 'qcm'
          AND TRIM(question.proposition_2) != ''
          AND reponse != '0'
          AND question.qcm_id < 1990 -- lol. half the QCM questions have the edition year as their qcm_id,
                                     -- instead of a real foreign to concours.id
        ORDER BY qcm.annee, question.ordre
        """

        self.stdout.write("Migrating QCM quizzes (questions and propositions)")

        with self.mysql.cursor() as c:
            c.execute(query)
            with transaction.atomic():
                for year, questions in itertools.groupby(namedcolumns(c), key=lambda e: e.annee):
                    event = contest.models.Event.objects.get(edition__year=year,
                                                             type=contest.models.Event.Type.qualification.value)
                    qcm_obj = qcm.models.Qcm(event=event)
                    qcm_obj.save()
                    for order, question in enumerate(questions):
                        q_obj = qcm.models.Question(pk=question.id,
                                                    qcm=qcm_obj,
                                                    body=question.question,
                                                    verbose=question.commentaires,
                                                    order=order)
                        if question.sponsor_id:
                            try:
                                q_obj.for_sponsor = sponsor.models.Sponsor.objects.get(pk=question.sponsor_id)
                            except sponsor.models.Sponsor.DoesNotExist:
                                self.stderr.write("Question {}: sponsor ID {} does not exist".format(
                                    q_obj, question.sponsor_id))
                        q_obj.save()

                        for n in range(1, 4 + 1):
                            prop = getattr(question, 'proposition_{}'.format(n))
                            if not prop:
                                continue
                            qcm.models.Proposition(question=q_obj, text=prop,
                                                   is_correct=str(n) in str(question.reponse)).save()

        self.stdout.write("Migrating user answers to QCM quizzes")

        query = """
        SELECT DISTINCT c.annee AS year, results.user_id, question.id AS question_id, answers.reponse
        FROM resultat_qcm_reponses answers
        INNER JOIN resultat_qcms results ON results.id = answers.resultat_qcm_id
        INNER JOIN epreuve_qcms question ON question.id = answers.epreuve_qcm_id
        INNER JOIN concours c ON c.id = question.qcm_id
        WHERE TRIM(LOWER(c.type)) = 'qcm'
          AND TRIM(question.proposition_2) != ''
          AND answers.reponse != '0'
          AND question.qcm_id < 1990
        ORDER BY answers.epreuve_qcm_id /* = question.id */
        """

        @functools.lru_cache(2000)
        def get_contestant(year, user_id):
            return contest.models.Contestant.objects.get(edition__year=year, user__pk=user_id)

        with self.mysql.cursor() as c:
            c.execute(query)
            with transaction.atomic():
                for question_id, answers in itertools.groupby(namedcolumns(c), key=lambda e: e.question_id):
                    propositions = qcm.models.Proposition.objects.filter(question__pk=question_id).order_by('pk')
                    for answer in answers:
                        try:
                            contestant = get_contestant(answer.year, answer.user_id)
                        except contest.models.Contestant.DoesNotExist:
                            self.stderr.write("Contestant user ID {} does not exist".format(answer.user_id))
                            continue
                        for sub_answer in str(answer.reponse):
                            ind = int(sub_answer) - 1
                            if ind == 4:
                                # « Ne pas répondre »
                                self.stdout.write("Ignored 'do not answer' for question {}, user {}".format(
                                    question_id, answer.user_id))
                                continue
                            try:
                                proposition = propositions[ind]  # this is fragile but fuck it
                            except IndexError:
                                self.stderr.write("Index error. Should not happen.")
                                self.stderr.write("{} {} {}".format(answer, question_id, propositions))
                                raise
                            try:
                                qcm.models.Answer(contestant=contestant, proposition=proposition).save()
                            except IntegrityError:
                                self.stderr.write("Integrity error. Should not happen.")
                                self.stderr.write("{} {} {}".format(answer, question_id, propositions))
                                raise

    def migrate_sponsors(self):
        import sponsor.models
        query = """SELECT DISTINCT * FROM sponsors"""
        session = requests.Session()
        with self.mysql.cursor() as c:
            c.execute(query)
            with transaction.atomic():
                for row in namedcolumns(c):
                    contact_name = row.contact.strip().split()
                    fn = ln = ''
                    if contact_name:
                        particle = contact_name[0].lower()
                        if particle.endswith('.') or particle in ('m', 'mme', 'mlle', 'mr'):
                            contact_name.pop(0)
                        try:
                            fn, *ln = contact_name
                        except ValueError:
                            try:
                                fn = contact_name[0]
                            except IndexError:
                                fn = ''
                            ln = []
                        ln = ' '.join(ln)
                    site = 'http://' + row.web if not row.web.startswith('http') else row.web
                    sponsor_obj = sponsor.models.Sponsor(pk=row.id, name=row.nom, is_active=row.actif, site=site,
                                                         description=row.descriptif, comment=row.commentaires,
                                                         address=row.adresse, postal_code=row.code_postal,
                                                         city=row.ville,
                                                         contact_position=row.statut, contact_email=row.email,
                                                         contact_first_name=fn, contact_last_name=ln,
                                                         contact_phone_desk=row.tel_fixe or row.tel_direct,
                                                         contact_phone_mobile=row.tel_mobile, contact_phone_fax=row.fax)
                    ok = field_fetch_file(session, sponsor_obj.logo,
                                          '{}files/images/sponsors/{}'.format(DRUPAL_SITE_BASE_URL, row.image))
                    if ok:
                        self.stdout.write("Downladed image for {}".format(sponsor_obj))
                    else:
                        self.stderr.write("Unable to downlad image for {}".format(sponsor_obj))
                    sponsor_obj.save()

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

        func(*args)
