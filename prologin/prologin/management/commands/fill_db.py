from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.contrib.webdesign import lorem_ipsum
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
from django.core.management.base import BaseCommand, CommandError
from django.template.defaultfilters import slugify
from django.utils import timezone
from tagging.models import Tag
from zinnia.managers import PUBLISHED
import centers.models
import contest.models
import datetime
import django.db
import itertools
import random
import requests
import team.models
import zinnia.models


class Command(BaseCommand):
    PASSWORD = "plop"
    GETTY_KEY = "bckeejjtqz7mh8jjtzc5g9xk"
    GETTY_SECRET = "StKZB4jxEG3GKbEGMQUn4kGQDW8wZrJk9hnbdgw9Gwk8M"

    args = "[all|module1 [module2 ...]]"
    help = "Fill the database for the specified modules. Password is '%s'." % PASSWORD

    def fill_users(self):
        User = get_user_model()
        User.objects.all().delete()
        admin_users = ['serialk', 'Tuxkowo', 'bakablue', 'epsilon012', 'Mareo', 'Zourp', 'kalenz', 'Horgix', 'Vic_Rattlehead', 'Artifère', 'davyg', 'Dettorer', 'pmderodat', 'tycho', 'Zeletochoy', 'Magicking', 'flutchman', 'nico', 'coucou747', 'Oxian', 'LLB', 'è_é']
        normal_users = ['Zopieux', 'Mickael', 'delroth', 'nispaur']
        first_names = ['Jean', 'Guillaume', 'Antoine', 'Alex', 'Sophie', 'Natalie', 'Anna', 'Claire']
        last_names = ['Dupond', 'Dujardin', 'Durand', 'Lamartin', 'Moulin', 'Oubel', 'Roubard', 'Sandel', 'Bouchard', 'Roudin']
        random.shuffle(first_names)
        random.shuffle(last_names)
        first_names = itertools.cycle(first_names)
        last_names = itertools.cycle(last_names)
        with django.db.transaction.commit_on_success():
            for name in admin_users + normal_users:
                email = '%s@prologin.org' % slugify(name)
                user = User.objects.create_user(name, email, Command.PASSWORD)
                user.first_name = next(first_names)
                user.last_name = next(last_names)
                user.is_active = True
                user.is_staff = name in admin_users
                user.is_superuser = user.is_staff
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
        with django.db.transaction.commit_on_success():
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
        with django.db.transaction.commit_on_success():
            for name, rank in roles:
                team.models.Role(rank=rank, name=name).save()
        with django.db.transaction.commit_on_success():
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
        with django.db.transaction.commit_on_success():
            for category in categories:  # bulk_create() fails
                category.save()
        tags = ['tech', 'meta', 'team', 'forums', 'qcm', 'sélections', 'régionales', 'finale']
        with django.db.transaction.commit_on_success():
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

    def fill_centers(self):
        cities = ["Bordeaux", "Toulouse", "Lyon", "Paris", "Marseille", "Lille"]
        centers.models.Center.objects.all().delete()
        with django.db.transaction.commit_on_success():
            for city in cities:
                centers.models.Center(
                    name=city, city=city, type=centers.models.Center.CenterType.centre.value, is_active=True,
                    address="34 rue des Fleurs", postal_code="12300", lat=0, lng=0,
                ).save()
                if city in ("Lyon", "Paris"):
                    centers.models.Center(
                        name=city + " II", city=city, type=centers.models.Center.CenterType.centre.value, is_active=True,
                        address="34 rue des Fleurs", postal_code="12300", lat=0, lng=0,
                    ).save()

    def fill_contests(self):
        years = list(range(2010, 2015 + 1))
        contest.models.Edition.objects.all().delete()
        with django.db.transaction.commit_on_success():
            for year in years:
                date_begin = datetime.datetime(year - 1, 9, 20)
                date_end = datetime.datetime(year, 5, 28)
                edition = contest.models.Edition(year=year, date_begin=date_begin, date_end=date_end)
                edition.save()
        centers = list(contest.models.Center.objects.all())
        assert centers, "Center list is empty; run fill_db centers"
        contest.models.Event.objects.all().delete()
        with django.db.transaction.commit_on_success():
            for edition in contest.models.Edition.objects.all():
                qualif = contest.models.Event(
                    edition=edition, type=contest.models.Event.EventType.qualification.value,
                    date_begin=edition.date_begin,
                    date_end=edition.date_begin + datetime.timedelta(days=60),
                )
                qualif.save()
                for center in centers:
                    regionale = contest.models.Event(
                        edition=edition, center=center, type=contest.models.Event.EventType.regionale.value,
                        date_begin=qualif.date_end + datetime.timedelta(days=60),
                        date_end=qualif.date_end + datetime.timedelta(days=90),
                    )
                    regionale.save()
                finale = contest.models.Event(
                    edition=edition, type=contest.models.Event.EventType.finale.value,
                    date_begin=regionale.date_end + datetime.timedelta(days=30),
                    date_end=regionale.date_end + datetime.timedelta(days=34),
                )
                finale.save()
                assert finale.date_end <= edition.date_end

    def fill_contestants(self):
        # TODO
        pass

    def handle(self, *args, **options):
        if len(args) < 1 or args[0] == 'all':
            args = ['users', 'profilepics', 'teams', 'news', 'centers', 'contests', 'contestants']
        for mod in args:
            try:
                method = getattr(self, 'fill_%s' % mod)
            except AttributeError:
                raise CommandError("%s: unknown module" % mod)
            print("Loading data for module %s..." % mod)
            method()
