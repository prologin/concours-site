# coding: utf-8

from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.contrib.webdesign import lorem_ipsum
from django.core.management.base import BaseCommand, CommandError
from django.template.defaultfilters import slugify
from django.utils import timezone
from tagging.models import Tag
from team.models import Role, TeamMember
from zinnia.managers import PUBLISHED
import datetime
import itertools
import random
import zinnia.models


class Command(BaseCommand):
    PASSWORD = "plop"

    args = "[all|module1 [module2 ...]]"
    help = "Fill the database for the specified modules. Password is '%s'." % PASSWORD

    def fill_users(self):
        User = get_user_model()
        User.objects.all().delete()
        users = ['serialk', 'Tuxkowo', 'bakablue', 'epsilon012', 'Mareo', 'Zourp', 'kalenz', 'Horgix', 'Vic_Rattlehead', 'Artifère', 'davyg', 'Dettorer', 'pmderodat', 'tycho', 'Zeletochoy', 'Magicking', 'flutchman', 'nico', 'coucou747', 'Oxian', 'LLB', 'è_é']
        first_names = ['Jean', 'Guillaume', 'Antoine', 'Alex', 'Sophie', 'Natalie', 'Anna', 'Claire']
        last_names = ['Dupond', 'Dujardin', 'Durand', 'Lamartin', 'Moulin', 'Oubel', 'Roubard', 'Sandel', 'Bouchard', 'Roudin']
        random.shuffle(first_names)
        random.shuffle(last_names)
        first_names = itertools.cycle(first_names)
        last_names = itertools.cycle(last_names)
        for name in users:
            email = '%s@prologin.org' % slugify(name)
            user = User.objects.create_user(name, email, Command.PASSWORD)
            user.first_name = next(first_names)
            user.last_name = next(last_names)
            user.is_active = True
            user.is_staff = True
            user.is_superuser = True
            user.save()

    def fill_team(self):
        User = get_user_model()
        TeamMember.objects.all().delete()
        Role.objects.all().delete()
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
        users = list(User.objects.all())
        random.shuffle(users)
        users = itertools.cycle(users)
        for name, rank in roles:
            Role(rank=rank, name=name).save()
        for year in range(2010, 2015):
            for name, rank in roles:
                TeamMember(year=year, role=Role.objects.all().filter(rank=rank)[0], user=next(users)).save()
            member = Role.objects.all().filter(rank=12)[0]
            for i in range(5):
                TeamMember(year=year, role=member, user=next(users)).save()

    def fill_news(self):
        site = Site.objects.get()
        users = list(zinnia.models.author.Author.objects.all())
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
        for category in categories:  # bulk_create() fails
            category.save()
        tags = ['tech', 'meta', 'team', 'forums', 'qcm', 'sélections', 'régionales', 'finale']
        for i in range(20):
            title = lorem_ipsum.words(random.randint(4, 8), False).title()
            content = "\n\n".join(lorem_ipsum.paragraphs(random.randint(2, 5), False))
            pubdate = timezone.now() + datetime.timedelta(days=random.randint(-30, 30))
            entry = zinnia.models.entry.Entry(
                status=PUBLISHED, title=title, slug=slugify(title), content=content,
                creation_date=pubdate)
            entry.save()
            entry.sites.add(site)
            entry.categories.add(*random.sample(categories, random.randint(0, 2)))
            entry.authors.add(next(users))
            entry.tags = ' '.join(random.sample(tags, random.randint(0, 3)))
            entry.save()

    def handle(self, *args, **options):
        if len(args) < 1 or args[0] == 'all':
            args = ['users', 'team']
        for mod in args:
            try:
                method = getattr(self, 'fill_%s' % mod)
            except AttributeError:
                raise CommandError("%s: unknown module" % mod)
            print("Loading data for module %s..." % mod)
            method()
