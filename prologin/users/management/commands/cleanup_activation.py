from django.core.management.base import BaseCommand
import users.models


class Command(BaseCommand):
    help = "Delete all users that have not activated their account in time."

    def handle(self, *args, **options):
        expired_users = users.models.UserActivation.objects.expired_users()
        if not expired_users:
            return
        self.stdout.write("{} expired users:".format(len(expired_users)))
        for user in expired_users:
            self.stdout.write("\t{username:<25} {fullname}".format(username=user.username,
                                                                   fullname=user.get_full_name()))
        expired_users.delete()
