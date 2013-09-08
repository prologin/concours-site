# coding=utf-8
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.contrib.auth.models import User
from users.models import ProloginUser, UserProfile
from prologin.utils import limit_charset

class Command(BaseCommand):
    args = ''
    help = 'Enforce data consistency between the User and UserProfile classes.'

    def create_missing_profiles(self):
        for user in User.objects.all():
            try:
                UserProfile.objects.get(user__pk = user.id)
            except UserProfile.DoesNotExist:
                self.stdout.write('%s: No UserProfile found, creating it.' % user.username)
                try:
                    pu = ProloginUser()
                    short_name = pu.getShortName(user.username)
                    profile = UserProfile(user=user, short_name=short_name, newsletter=False)
                    profile.save()
                except ValueError:
                    self.stderr.write('Error: %s (id %d): unable to create UserProfile: short name already taken.' % (user.username, user.id))

    def enforce_short_name_consistency(self):
        for profile in UserProfile.objects.all():
            short_name = limit_charset(profile.user.username)
            if profile.short_name != short_name:
                self.stdout.write('%s: %s: Invalid short name, changing to "%s".' % (profile.user.username, profile.short_name, short_name))
                profile.short_name = short_name
                profile.save()
    
    def handle(self, *args, **options):
        self.create_missing_profiles()
        self.enforce_short_name_consistency()
