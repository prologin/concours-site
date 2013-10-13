# coding=utf-8
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.utils import timezone
from django.contrib.auth.models import User
from news.models import News
from team.models import Role, Team
from menu.models import MenuEntry
from pages.models import Page
from users.models import ProloginUser, UserProfile
from prologin.utils import get_slug
import datetime
import random

class LipsumWord():
    def __init__(self):
        self.lst = ['a', 'ac', 'accumsan', 'adipiscing', 'aenean', 'aliquam', 'aliquet', 'amet', 'ante', 'arcu', 'at', 'auctor', 'augue', 'bibendum', 'commodo', 'condimentum', 'congue', 'consectetur', 'consequat', 'convallis', 'cras', 'curabitur', 'cursus', 'dapibus', 'diam', 'dictum', 'dolor', 'donec', 'dui', 'duis', 'egestas', 'eget', 'eleifend', 'elementum', 'elit', 'enim', 'erat', 'eros', 'est', 'et', 'etiam', 'eu', 'euismod', 'fames', 'faucibus', 'felis', 'fermentum', 'feugiat', 'fringilla', 'fusce', 'gravida', 'habitant', 'hendrerit', 'iaculis', 'id', 'imperdiet', 'in', 'integer', 'interdum', 'ipsum', 'justo', 'lacinia', 'lacus', 'laoreet', 'lectus', 'libero', 'ligula', 'lobortis', 'lorem', 'luctus', 'maecenas', 'magna', 'malesuada', 'massa', 'mattis', 'mauris', 'metus', 'mi', 'molestie', 'mollis', 'morbi', 'nam', 'nec', 'neque', 'netus', 'nibh', 'nisi', 'nisl', 'non', 'nulla', 'nullam', 'nunc', 'odio', 'orci', 'ornare', 'pellentesque', 'pharetra', 'phasellus', 'placerat', 'porta', 'posuere', 'praesent', 'pretium', 'proin', 'pulvinar', 'purus', 'quam', 'quis', 'quisque', 'rhoncus', 'risus', 'rutrum', 'sagittis', 'sapien', 'scelerisque', 'sed', 'sem', 'semper', 'senectus', 'sit', 'sodales', 'suscipit', 'suspendisse', 'tellus', 'tempor', 'tempus', 'tincidunt', 'tortor', 'tristique', 'turpis', 'ultrices', 'ultricies', 'ut', 'varius', 'vehicula', 'vel', 'velit', 'venenatis', 'vestibulum', 'vitae', 'vivamus', 'viverra', 'volutpat', 'vulputate']
        self.word = random.sample(self.lst, 1)[0]

    def __str__(self):
        return self.word

class LipsumSentence():
    def __init__(self, min_words=3, max_words=15):
        self.str = ''
        for i in range(random.randint(min_words, max_words)):
            w = LipsumWord()
            self.str += ' ' if self.str != '' else ''
            self.str += str(w)
        self.str = self.str.capitalize() + '.'

    def __str__(self):
        return self.str

class LipsumParagraph():
    def __init__(self):
        self.str = ' '.join(str(LipsumSentence()) for _ in range(random.randint(3, 7)))

    def __str__(self):
        return self.str

class Command(BaseCommand):
    args = '<module module ...>'
    help = 'Fill the database for the specified modules.'

    def fill_users(self):
        User.objects.all().filter(is_superuser=False).delete()
        users = ['serialk', 'Tuxkowo', 'bakablue', 'epsilon012', 'Mareo', 'Zourp', 'kalenz', 'Horgix', 'Vic_Rattlehead', 'Artifère', 'davyg', 'Dettorer', 'pmderodat', 'Tycho bis', 'Zeletochoy', 'Magicking', 'flutchman', 'nico', 'coucou747', 'Oxian', 'LLB', 'è_é']
        for name in users:
            email = name.lower() + '@prologin.org'
            pu = ProloginUser()
            pu.register(name, email, 'password', True, True)

    def fill_news(self):
        News.objects.all().delete()
        for i in range(42):
            title = str(LipsumSentence(max_words=6))
            body = ''
            for i in range(2):
                body += str(LipsumParagraph()) + ' '
            News(title=title, body=body).save()

    def fill_team(self):
        Team.objects.all().delete()
        Role.objects.all().delete()
        roles = {
            # name: rank
            'Président': 1,
            'Membre persistant': 14,
            'Trésorier': 3,
            'Vice-Président': 2,
            'Responsable technique': 8,
            'Membre': 12,
            'Secrétaire': 4,
        }
        for name in roles:
            Role(rank=roles[name], role=name).save()
        for year in range(2010, 2015):
            for name in roles:
                r = Role.objects.all().filter(rank=roles[name])[0]
                p = UserProfile.objects.order_by('?')[0]
                Team(year=year, role=r, profile=p).save()
            member = Role.objects.all().filter(rank=12)[0]
            for i in range(5):
                p = UserProfile.objects.order_by('?')[0]
                Team(year=year, role=member, profile=p).save()

    def fill_pages(self):
        Page.objects.all().delete()
        pages = {
            'L\'association': 'prologin',
            'Déroulement des épreuves': 'le_concours',
            'Règlement': 'le_concours',
            'Les vainqueurs': 'le_concours',
            'Questionnaires': 'sentrainer',
            'Exercices machine': 'sentrainer',
            'Épreuves machines': 'documentation',
            'Langages supportés': 'documentation',
            'Mentions légales': None,
            }
        for title in pages:
            ctn = ''
            container = None if pages[title] is None else MenuEntry.objects.get(slug=pages[title])
            for _ in range(5):
                ctn += '\n## %s\n\n' % LipsumSentence()
                ctn += str(LipsumParagraph())
            p = Page(name=title, slug=get_slug(title), content=ctn, container=container, created_by=UserProfile.objects.order_by('?')[0], edited_by=UserProfile.objects.order_by('?')[0], created_on=datetime.datetime.now(), edited_on=datetime.datetime.now(), published=True)
            p.save()

    def fill_menu(self):
        MenuEntry.objects.all().delete()
        entries = [
            {'name': 'Accueil', 'position': 1, 'url': 'home'},
            {'name': 'Prologin', 'position': 2, 'url': '#'},
            {'name': 'Le concours', 'position': 3, 'url': '#'},
            {'name': 'S\'entraîner', 'position': 4, 'url': '#'},
            {'name': 'Documentation', 'position': 5, 'url': '#'},
            {'name': 'Forums', 'position': 6, 'url': '#'},
            {'name': 'Medias', 'position': 7, 'url': '#'},
            {'name': 'Administrer', 'position': 21, 'url': 'admin:index', 'access': 'admin'},
            {'name': 'Mon compte', 'position': 42, 'url': 'users:profile|{{me}}', 'access': 'logged'},
            {'name': 'Se déconnecter', 'position': 69, 'url': 'users:logout', 'access': 'logged'},

            {'name': 'L\'association', 'parent': 1, 'position': 1, 'url': 'pages:show|lassociation'},
            {'name': 'L\'équipe', 'parent': 1, 'position': 2, 'url': 'team:index'},

            {'name': 'Édition {{last_edition}}', 'parent': 2, 'position': 1, 'url': '#'},
            {'name': 'Déroulement des épreuves', 'parent': 2, 'position': 2, 'url': 'pages:show|deroulement_des_epreuves'},
            {'name': 'Règlement', 'parent': 2, 'position': 3, 'url': 'pages:show|reglement'},
            {'name': 'Les vainqueurs', 'parent': 2, 'position': 4, 'url': 'pages:show|les_vainqueurs'},

            {'name': 'Questionnaires', 'parent': 3, 'position': 1, 'url': 'pages:show|questionnaires'},
            {'name': 'Exercices machine', 'parent': 3, 'position': 2, 'url': 'pages:show|exercices_machine'},

            {'name': 'Épreuves machines', 'parent': 4, 'position': 1, 'url': 'pages:show|epreuves_machines'},
            {'name': 'Langages supportés', 'parent': 4, 'position': 2, 'url': 'pages:show|langages_supportes'},

            {'name': 'Photos', 'parent': 6, 'position': 1, 'url': '#'},
            {'name': 'Vidéos', 'parent': 6, 'position': 2, 'url': '#'},
            {'name': 'Affiches', 'parent': 6, 'position': 3, 'url': '#'},
        ]
        for entry in entries:
            e = MenuEntry(name=entry['name'], url=entry['url'], parent=None if 'parent' not in entry else entries[entry['parent']]['elem'], position=entry['position'], access='all' if 'access' not in entry else entry['access'])
            e.save()
            entry['elem'] = e

    def handle(self, *args, **options):
        modules = {
            'users': self.fill_users,
            'news': self.fill_news,
            'team': self.fill_team,
            'pages': self.fill_pages,
            'menu': self.fill_menu,
        }
        if len(args) < 1:
            self.stderr.write('Missing parameter.')
            return
        if args[0] == 'all':
            args = ['users', 'news', 'team', 'menu', 'pages']
        for mod in args:
            if mod not in modules:
                raise CommandError('%s: unknown module' % mod)
            self.stdout.write('Loading data for module %s...' % mod)
            modules[mod]()
