from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.contrib.webdesign import lorem_ipsum
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from django.template.defaultfilters import slugify
from django.utils import timezone
from tagging.models import Tag
from zinnia.managers import PUBLISHED
import centers.models
import contest.models
import datetime
import django.db
import itertools
import problems.models
import prologin.languages
import prologin.models
import random
import requests
import team.models
import zinnia.models


# FIXME: this is completely broken by the EnumField refactor

class Command(BaseCommand):
    PASSWORD = "plop"
    GETTY_KEY = "bckeejjtqz7mh8jjtzc5g9xk"
    GETTY_SECRET = "StKZB4jxEG3GKbEGMQUn4kGQDW8wZrJk9hnbdgw9Gwk8M"

    args = "[all|module1 [module2 ...]]"
    help = "Fill the database for the specified modules. Password is '%s'." % PASSWORD

    def fill_users(self):
        User = get_user_model()
        User.objects.all().delete()
        admin_users = ['serialk', 'Tuxkowo', 'bakablue', 'epsilon012', 'Mareo']
        normal_users = ['Zopieux', 'Mickael', 'delroth', 'nispaur', 'ordiclic', 'spider-mario', 'Dettorer', 'Zeletochoy']
        first_names = ['Jean', 'Guillaume', 'Antoine', 'Alex', 'Sophie', 'Natalie', 'Anna', 'Claire']
        last_names = ['Dupond', 'Dujardin', 'Durand', 'Lamartin', 'Moulin', 'Oubel', 'Roubard', 'Sandel', 'Bouchard',
                      'Roudin']
        random.shuffle(first_names)
        random.shuffle(last_names)
        first_names = itertools.cycle(first_names)
        last_names = itertools.cycle(last_names)
        with django.db.transaction.atomic():
            for name in admin_users + normal_users:
                is_staff = name in admin_users
                email = '{}@{}'.format(slugify(name), 'prologin.org' if is_staff else 'hotmail.fr')
                user = User.objects.create_user(name, email, Command.PASSWORD)
                user.first_name = next(first_names)
                user.last_name = next(last_names)
                user.is_active = True
                user.is_staff = is_staff
                user.is_superuser = is_staff
                user.save()

    def fill_profilepics(self):
        sess = requests.Session()
        sess.headers['Api-Key'] = Command.GETTY_KEY
        token = sess.post('https://api.gettyimages.com/oauth2/token', {
            'grant_type': 'client_credentials',
            'client_id': Command.GETTY_KEY,
            'client_secret': Command.GETTY_SECRET}).json()['access_token']
        sess.headers['Authorization'] = 'Bearer %s' % token

        def img_search(query):
            page = random.randint(1, 10)
            while True:
                data = sess.get('https://api.gettyimages.com/v3/search/images', params={
                    'age_of_people': '20-29_years,30-39_years',
                    'compositions': 'headshot,looking_at_camera,portrait',
                    'exclude_nudity': 'true',
                    'fields': 'preview',
                    'file_types': 'jpg,png',
                    'graphical_styles': 'photography',
                    'number_of_people': 'one',
                    'orientations': 'Vertical',
                    'page': page,
                    'phrase': query}).json()
                for item in data['images']:
                    yield item['display_sizes'][0]['uri']
                page += 1

        users = get_user_model().objects.all()
        assert users, "User list is empty; run fill_db users"
        images_man = img_search('man')
        images_woman = img_search('woman')
        with django.db.transaction.atomic():
            for user in users:
                url = next(random.choice((images_man, images_woman)))
                img = NamedTemporaryFile(delete=True)
                img.write(requests.get(url).content)
                img.flush()
                user.avatar = None
                user.picture = None
                attr = user.avatar
                if user.is_staff:
                    attr = random.choice((user.avatar, user.picture))
                attr.save('test.jpg', File(img))
                user.save()

    def fill_teams(self):
        User = get_user_model()
        team.models.TeamMember.objects.all().delete()
        team.models.Role.objects.all().delete()
        roles = (
            # name, rank
            ('Président', 1),
            ('Membre persistant', 14),
            ('Trésorier', 3),
            ('Vice-Président', 2),
            ('Responsable technique', 8),
            ('Membre', 12),
            ('Secrétaire', 4),
        )
        users = list(User.objects.filter(is_staff=True))
        assert users, "User list is empty; run fill_db users"
        random.shuffle(users)
        users = itertools.cycle(users)
        with django.db.transaction.atomic():
            for name, rank in roles:
                team.models.Role(rank=rank, name=name).save()
        with django.db.transaction.atomic():
            for year in range(2010, 2015):
                for name, rank in roles:
                    team.models.TeamMember(
                        year=year,
                        role=team.models.Role.objects.all().filter(rank=rank)[0],
                        user=next(users),
                    ).save()
                member = team.models.Role.objects.all().filter(rank=12)[0]
                for i in range(5):
                    team.models.TeamMember(
                        year=year,
                        role=member,
                        user=next(users),
                    ).save()

    def fill_news(self):
        site = Site.objects.get()
        users = list(zinnia.models.author.Author.objects.all())
        assert users, "User list is empty; run fill_db users"
        random.shuffle(users)
        users = itertools.cycle(users)
        zinnia.models.category.Category.objects.all().delete()
        zinnia.models.entry.Entry.objects.all().delete()
        Tag.objects.all().delete()
        category_names = ["Annonce", "Nouveauté", "Sponsors", "Communauté"]
        categories = [
            zinnia.models.category.Category(title=category, slug=slugify(category))
            for category in category_names
        ]
        with django.db.transaction.atomic():
            for category in categories:  # bulk_create() fails
                category.save()
        tags = ['tech', 'meta', 'team', 'forums', 'qcm', 'sélections', 'régionales', 'finale']
        with django.db.transaction.atomic():
            for i in range(20):
                title = lorem_ipsum.words(random.randint(4, 8), False).title()
                content = "\n\n".join(lorem_ipsum.paragraphs(random.randint(2, 5), False))
                pubdate = timezone.now() + datetime.timedelta(days=random.randint(-30, 30))
                entry = zinnia.models.entry.Entry(
                    status=PUBLISHED, title=title, slug=slugify(title), content=content,
                    creation_date=pubdate,
                )
                entry.save()
        for entry in zinnia.models.entry.Entry.objects.all():
            entry.sites.add(site)
            entry.categories.add(*random.sample(categories, random.randint(0, 2)))
            entry.authors.add(next(users))
            entry.tags = ' '.join(random.sample(tags, random.randint(0, 3)))
            entry.save()

    def fill_sponsors(self):
        with django.db.transaction.atomic():
            for name in ("EPITA", "Éducation nationale", "École Polytechnique", "UPMC", "Délégation Internet"):
                slug = slugify(name)
                prologin.models.Sponsor(name=name, is_active=True, site="http://www.%s.fr" % slug,
                                        contact_email="contact@%s.fr" % slug).save()

    def fill_centers(self):
        center_list = [('ISEG Lyon', '86, bd Marius Vivier Merle', '69003', 'LYON'),
                   ('ISEG Nantes', '8 rue de Bréa', '44000', 'NANTES'),
                   ("Lycée Dumont d'Urville", "212, avenue de l'Amiral JaujardrnBP1404", '83056', 'TOULON'),
                   ('ISEG Strasbourg', '4 rue du Dôme', '67000', 'STRASBOURG'),
                   ('EPITA', '24, rue Pasteur', '94270', 'LE KREMLIN BICETRE'),
                   ('ISEG Lille', '60 Boulevard de la Liberté', '59800', 'LILLE'),
                   ('Université catholique de Louvain', 'Auditoire/Place Sainte Barbe', 'B-134', 'Louvain-la-Neuve (Belgique)'),
                   ('ISEG Toulouse', '14, rue Claire Pauilhac', '31000', 'TOULOUSE'),
                   ('ISEN Toulon', 'Maison Des Technologies, Place Georges Pompidou', '83000', 'Toulon'),
                   ('ISEFAC Bordeaux', '23 rue des Augustins', '33000', 'Bordeaux'),
                   ('ISEFAC Lyon', '32Bis av Félix Faure', '69007', 'Lyon'),
                   ('ESEO', '4, rue Merlet de la Boulaye', '49000', ' Angers'),
                   ('IUT Clermont-Ferrand', '', '', 'Clermont-Ferrand'),
                   ('Polytechnique', 'Route de Saclay', '91120', 'Palaiseau'),
                   ('ISEG Bordeaux', '85 rue du Jardin Public', '33000', 'Bordeaux'),
                   ('EPN Cite des sciences', '30 avenue Corentin Cariou', '75019', 'Paris'),
                   ('Epitech Montpellier', '25 bd Renouvier', '34000', 'Montpellier'),
                   ('ISEG Nantes', '', '44100', 'Nantes')]
        centers.models.Center.objects.all().delete()
        with django.db.transaction.atomic():
            for name, road, postal_code, city in center_list:
                centers.models.Center(
                    name=name, type=centers.models.Center.Type.center.value, is_active=True,
                    address=road, postal_code=postal_code, city=city, lat=0, lng=0,
                ).save()

    def fill_contests(self):
        years = list(range(2010, 2015 + 1))
        contest.models.Edition.objects.all().delete()
        with django.db.transaction.atomic():
            for year in years:
                date_begin = datetime.datetime(year - 1, 9, 20)
                date_end = datetime.datetime(year, 5, 28)
                edition = contest.models.Edition(year=year, date_begin=date_begin, date_end=date_end)
                edition.save()
        centers = list(contest.models.Center.objects.all())
        assert centers, "Center list is empty; run fill_db centers"
        contest.models.Event.objects.all().delete()
        finale_center = contest.models.Center.objects.get(name__icontains='EPITA')
        with django.db.transaction.atomic():
            for edition in contest.models.Edition.objects.all():
                qualif = contest.models.Event(
                    edition=edition, type=contest.models.Event.Type.qualification.value,
                    date_begin=edition.date_begin,
                    date_end=edition.date_begin + datetime.timedelta(days=60),
                )
                qualif.save()
                for center in centers:
                    regionale = contest.models.Event(
                        edition=edition, center=center, type=contest.models.Event.Type.regionale.value,
                        date_begin=qualif.date_end + datetime.timedelta(days=60),
                        date_end=qualif.date_end + datetime.timedelta(days=90),
                    )
                    regionale.save()
                finale = contest.models.Event(
                    edition=edition, center=finale_center, type=contest.models.Event.Type.finale.value,
                    date_begin=regionale.date_end + datetime.timedelta(days=30),
                    date_end=regionale.date_end + datetime.timedelta(days=34),
                )
                finale.save()
                assert finale.date_end <= edition.date_end

    def fill_contestants(self):
        users = get_user_model().objects.filter(is_staff=False)
        staff = list(get_user_model().objects.filter(is_staff=True))
        assert users, "User list is empty; run fill_db users"
        assert staff, "Staff list is empty; run fill_db users"
        contest.models.Contestant.objects.all().delete()

        tshirt_sizes = [k for k, v in contest.models.Contestant.ShirtSize.choices()]
        languages = [l.name for l in prologin.languages.Language]

        with django.db.transaction.atomic():
            for edition in contest.models.Edition.objects.all():
                qualif = contest.models.Event.objects.get(edition=edition, type=contest.models.Event.Type.qualification.value)
                regionales = list(contest.models.Event.objects.filter(edition=edition, type=contest.models.Event.Type.regionale.value))
                finale = contest.models.Event.objects.get(edition=edition, type=contest.models.Event.Type.finale.value)
                for user in users:
                    comments = ""
                    if random.choice((True, False)):
                        comments="Ouais pas mal.\n\nSinon il préfère les pâtes carbo."
                    contestant = contest.models.Contestant(user=user,
                                                           edition=edition,
                                                           tshirt_size=random.choice(tshirt_sizes),
                                                           preferred_language=random.choice(languages),
                                                           correction_by=random.choice(staff),
                                                           correction_comments=comments)
                    contestant.save()
                    # contestant.events.add(qualif)
                    for i, regionale in enumerate(random.sample(regionales, 3)):
                        # contestant.events.add(regionale)
                        contest.models.EventWish(contestant=contestant, event=regionale, order=i, is_approved=(i == 0)).save()
                    # contestant.events.add(finale)
                    # wish to finale (1/2 chance of getting in)
                    contest.models.EventWish(contestant=contestant, event=finale, is_approved=random.choice((True, False))).save()

    def fill_qcms(self):
        import qcm.models  # I have no fucking idea why root level import does not work for this particular one
        qcm.models.Qcm.objects.all().delete()
        events = contest.models.Event.objects.filter(type=contest.models.Event.Type.qualification.value)
        questions = ["Who is the best?", "What is my fate?", "What about peanuts?", "How old is that?", "What is the airspeed velocity of an unladen swallow?", "Was 9/11 a conspiracy?"]
        question_len = len(questions)
        propositions = ["Twenty-two", "The answer to life and the rest", "Whatever dude", "I'm so high right now", "The D answer"]
        proposition_len = len(propositions)
        with django.db.transaction.atomic():
            for event in events:
                qcm.models.Qcm(event=event).save()

        sponsors = list(prologin.models.Sponsor.objects.all())
        assert sponsors, "Sponsor list empty; run fill_db sponsors"
        random.shuffle(sponsors)
        sponsors = itertools.cycle(sponsors)

        with django.db.transaction.atomic():
            for qcmobj in qcm.models.Qcm.objects.all():
                for body in random.sample(questions, random.randint(3, question_len)):
                    qcm.models.Question(qcm=qcmobj, body=body,
                                        for_sponsor=next(sponsors) if random.choice((True, False)) else None).save()

        with django.db.transaction.atomic():
            for question in qcm.models.Question.objects.all():
                all_props = []
                for text in random.sample(propositions, random.randint(2, proposition_len)):
                    prop = qcm.models.Proposition(question=question, text=text, is_correct=False)
                    prop.save()
                    all_props.append(prop)
                prop = random.choice(all_props)
                prop.is_correct = True
                prop.save()

        with django.db.transaction.atomic():
            for qcmobj in qcm.models.Qcm.objects.select_related('event__edition__contestants', 'questions').all():
                for contestant in qcmobj.event.edition.contestants.all():
                    for question in qcmobj.questions.all():
                        prop = random.choice(list(question.propositions.all()))
                        qcm.models.Answer(contestant=contestant, proposition=prop).save()

    def fill_problems(self):
        events = contest.models.Event.objects.filter(type=contest.models.Event.Type.qualification.value)
        titles = ["Prolego™", "Tour de magie", "Croissance", "Hâte", "Repli", "Sabotage", "Vantardise", "Expert-itinérant", "Rond-point", "Syracuse", "Triangles", "Wi-Fi"]
        random.shuffle(titles)
        titles = itertools.cycle(titles)
        problems.models.Challenge.objects.all().delete()
        with django.db.transaction.atomic():
            for event in events:
                for i in range(4):
                    title = next(titles)
                    problems.models.Challenge(
                        event=event, title=title, problem_ref=slugify(title),
                        question="\n".join(lorem_ipsum.paragraphs(2, False)),
                    ).save()

        languages = [l.name for l in prologin.languages.Language]
        with django.db.transaction.atomic():
            for challenge in problems.models.Challenge.objects.all():
                for contestant in challenge.event.edition.contestants.all():
                    problems.models.Answer(
                        challenge=challenge, contestant=contestant,
                        is_final=random.choice((True, True, False)),
                        language=random.choice(languages),
                        code="\n".join(lorem_ipsum.paragraphs(1, False)),
                    ).save()



    def handle(self, *args, **options):
        if len(args) < 1 or args[0] == 'all':
            args = ['users', 'profilepics', 'teams', 'news', 'sponsors', 'centers', 'contests', 'contestants', 'qcms', 'problems']
        for mod in args:
            try:
                method = getattr(self, 'fill_%s' % mod)
            except AttributeError:
                raise CommandError("%s: unknown module" % mod)
            print("Loading data for module %s..." % mod)
            method()
