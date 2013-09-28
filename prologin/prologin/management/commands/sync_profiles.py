# coding=utf-8
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.contrib.auth.models import User
from django.conf import settings
from users.models import ProloginUser, UserProfile
from prologin.utils import limit_charset
from users.avatars import generate_avatar
import os

class Command(BaseCommand):
    args = ''
    help = 'Enforce data consistency between the User and UserProfile classes.'

    def create_profile_if_missing(self, user):
        try:
            profile = UserProfile.objects.get(user__pk = user.id)
        except UserProfile.DoesNotExist:
            self.stdout.write('%s: No UserProfile found, creating it.' % user.username)
            try:
                pu = ProloginUser()
                short_name = pu.getShortName(user.username)
                profile = UserProfile(user=user, short_name=short_name, newsletter=False)
                profile.save()
            except ValueError:
                self.stderr.write('Error: %s (id %d): unable to create UserProfile: short name already taken.' % (user.username, user.id))
        return profile

    def enforce_short_name_consistency(self, profile):
        short_name = limit_charset(profile.user.username)
        if profile.short_name != short_name:
            self.stdout.write('%s: %s: Invalid short name, changing to "%s".' % (profile.user.username, profile.short_name, short_name))
            profile.short_name = short_name
            profile.save()

    def create_avatar_if_missing(self, profile):
        try:
            avatar_dir = '%susers/static/users/avatars/%s/' % (settings.SITE_ROOT, profile.short_name)
            if not os.path.isdir(avatar_dir):
                self.stderr.write('%s: Avatar directory not found, creating it.' % profile.user.username)
                os.makedirs(avatar_dir)
            for size in settings.AVATAR_SIZES:
                avatar_path = '%s%s_%s.png' % (avatar_dir, profile.short_name, size)
                if not os.path.exists(avatar_path):
                    self.stderr.write('%s: %s avatar not found, setting all avatars to default.' % (profile.user.username, size))
                    for sz in settings.AVATAR_SIZES:
                        avatar_path = '%s%s_%s.png' % (avatar_dir, profile.short_name, sz)
                        avatar = generate_avatar(profile.short_name, settings.AVATAR_SIZES[sz])
                        avatar.save(avatar_path, 'PNG')
                    break
        except Exception as ex:
            self.stdout.write('Fatal error: user %s: %s' % (profile.user.username, ex))
    
    def handle(self, *args, **options):
        for user in User.objects.all():
            profile = self.create_profile_if_missing(user)
            self.enforce_short_name_consistency(profile)
            self.create_avatar_if_missing(profile)
