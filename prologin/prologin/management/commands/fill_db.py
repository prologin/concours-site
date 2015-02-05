# coding: utf-8

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from team.models import Role, TeamMember


class Command(BaseCommand):
    args = "[all|module1 [module2 ...]]"
    help = "Fill the database for the specified modules."

    def fill_users(self):
        User = get_user_model()
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
        for name, rank in roles:
            Role(rank=rank, name=name).save()
        for year in range(2010, 2015):
            for name, rank in roles:
                TeamMember(year=year, role=Role.objects.all().filter(rank=rank)[0], user=User.objects.order_by('?')[0]).save()
            member = Role.objects.all().filter(rank=12)[0]
            for i in range(5):
                TeamMember(year=year, role=member, user=User.objects.order_by('?')[0]).save()

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
