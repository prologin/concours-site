# coding=utf-8
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.contrib.auth.models import User
from django.utils import timezone
from team.models import Role, TeamMember
from users.models import UserProfile
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
        User.objects.all().delete()
        users = ['serialk', 'Tuxkowo', 'bakablue', 'epsilon012', 'Mareo', 'Zourp', 'kalenz', 'Horgix', 'Vic_Rattlehead', 'Artifère', 'davyg', 'Dettorer', 'pmderodat', 'tycho', 'Zeletochoy', 'Magicking', 'flutchman', 'nico', 'coucou747', 'Oxian', 'LLB', 'è_é']
        for name in users:
            email = name.lower() + '@prologin.org'
            user = User.objects.create_user(name, email, 'plop')
            user.is_active = True
            user.is_staff = True
            user.is_superuser = True
            user.save()

    def fill_team(self):
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
        for name, rank in roles:
            Role(rank=rank, name=name).save()
        for year in range(2010, 2015):
            for name, rank in roles:
                TeamMember(year=year, role=Role.objects.all().filter(rank=rank)[0], user=User.objects.order_by('?')[0]).save()
            member = Role.objects.all().filter(rank=12)[0]
            for i in range(5):
                TeamMember(year=year, role=member, user=User.objects.order_by('?')[0]).save()

    def handle(self, *args, **options):
        modules = {
            'users': self.fill_users,
            'team': self.fill_team,
        }
        if len(args) < 1 or args[0] == 'all':
            args = ['users', 'team']
        for mod in args:
            if mod not in modules:
                raise CommandError('%s: unknown module' % mod)
            self.stdout.write('Loading data for module %s...' % mod)
            modules[mod]()
