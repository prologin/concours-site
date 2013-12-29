# coding=utf-8
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.contrib.auth.models import User
from django.conf import settings
from users.models import UserProfile
from prologin.utils import get_slug
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
                slug = get_slug(user.username)
                profile = UserProfile(user=user, slug=slug, newsletter=False)
                profile.save()
            except ValueError:
                self.stderr.write('Error: %s (id %d): unable to create UserProfile: short name already taken.' % (user.username, user.id))
        return profile

    def enforce_slug_consistency(self, profile):
        slug = get_slug(profile.user.username)
        if profile.slug != slug:
            self.stdout.write('%s: %s: Invalid short name, changing to "%s".' % (profile.user.username, profile.slug, slug))
            profile.slug = slug
            profile.save()

    def create_avatar_if_missing(self, profile):
        try:
            avatar_dir = os.path.join(settings.MEDIA_ROOT, 'avatars', profile.slug)
            if not os.path.isdir(avatar_dir):
                self.stderr.write('%s: Avatar directory not found, creating it.' % profile.user.username)
                os.makedirs(avatar_dir)
            for size in settings.AVATAR_SIZES:
                avatar_path = os.path.join(avatar_dir, '%s_%s.png' % (profile.slug, size))
                if not os.path.exists(avatar_path):
                    self.stderr.write('%s: %s avatar not found, setting all avatars to default.' % (profile.user.username, size))
                    profile.generate_avatars()
                    break
        except Exception as ex:
            self.stdout.write('Fatal error: user %s: %s' % (profile.user.username, ex))
    
    def handle(self, *args, **options):
        for user in User.objects.all():
            profile = self.create_profile_if_missing(user)
            self.enforce_slug_consistency(profile)
            self.create_avatar_if_missing(profile)
