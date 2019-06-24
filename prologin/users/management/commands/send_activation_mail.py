# Copyright (C) <2018> Association Prologin <association@prologin.org>
# SPDX-License-Identifier: GPL-3.0+

from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand
from django.db.models import Q

from users.views import send_activation_email


class Command(BaseCommand):
    help = "Send (or re-send) an activation mail for the given username or email."

    def add_arguments(self, parser):
        parser.add_argument('--no-check-active', action='store_true',
                            help="skip checking if the account is already activated")
        parser.add_argument('--yes', action='store_true', help="do NOT confirm, send email right away")
        parser.add_argument('username_or_email', help="the username or email to send")

    def handle(self, *args, **options):
        query = options['username_or_email']
        qs = get_user_model().objects.filter(Q(username__iexact=query) | Q(email__iexact=query))
        try:
            user = qs.get()
        except ObjectDoesNotExist:
            self.stderr.write("No such username or email: {}".format(query))
            return

        if user.is_active and not options['no_check_active']:
            self.stderr.write("User already active: {} / {}".format(user.username, user.email))
            return

        question = "Send activation mail to {} / {}? [y/n]".format(user.username, user.email)
        if options['yes'] or input(question).startswith('y'):
            send_activation_email(user)
            self.stdout.write("Email sent")
