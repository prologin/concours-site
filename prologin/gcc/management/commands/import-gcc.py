import argparse
import datetime
import json
from django.contrib.auth import get_user_model
from django.core.management import BaseCommand

import gcc.models as models
from users.models import ProloginUser


class Command(BaseCommand):
    help = "Import datas from the old website"

    def add_arguments(self, parser):
        parser.add_argument('import_file', type=argparse.FileType('rb'))

    def handle(self, *args, **options):
        try:
            data = json.loads(options['import_file'].read())
        except:
            print('Please specify a valid json file')

        #                          _      _   _
        #  _ __   _____      _____| | ___| |_| |_ ___ _ __
        # | '_ \ / _ \ \ /\ / / __| |/ _ \ __| __/ _ \ '__|
        # | | | |  __/\ V  V /\__ \ |  __/ |_| ||  __/ |
        # |_| |_|\___| \_/\_/ |___/_|\___|\__|\__\___|_|
        #
        print('Import Mailing List...')

        for subscriber_data in data['subscribers']:
            fields = subscriber_data['fields']

            if not models.SubscriberEmail.objects.filter(email=fields['mail']):
                models.SubscriberEmail(
                    email=fields['mail'], date=fields['created']
                ).save()
        #
        #   _   _ ___  ___ _ __ ___
        #  | | | / __|/ _ \ '__/ __|
        #  | |_| \__ \  __/ |  \__ \
        #   \__,_|___/\___|_|  |___/
        #
        print('Import Users...')

        users = {}

        for user_data in data['users']:
            fields = user_data['fields']

            if not fields['email'] or fields['is_staff']:
                continue

            try:
                user = ProloginUser.objects.get(email=fields['email'])
            except ProloginUser.DoesNotExist:
                if ProloginUser.objects.filter(username=fields['username']):
                    print(' - Conflicting username for new user',
                        fields['username'])
                    fields['username'] += '-gcc'

                user = ProloginUser(username=fields['username'],
                    email=fields['email'])
                shared_field = ('password', 'last_login', 'first_name',
                    'last_name', 'is_active', 'date_joined')

                for field in shared_field:
                    setattr(user, field, fields[field])

                for profile in data['applications']['profile']:
                    if profile['fields']['user'] == user_data['pk']:
                        profile['fields']['postal_code'] = profile['fields']['zipcode']
                        shared_fields = ('address', 'phone', 'birthday',
                            'country', 'city', 'postal_code')

                        for f in shared_fields:
                            if f == 'phone' and profile['fields'][f] is not None:
                                profile['fields'][f] = profile['fields'][f][:16]

                            if profile['fields'][f] is not None:
                                setattr(user, f, profile['fields'][f])

                user.save()

            users[user_data['pk']] = user

        #       _                            __
        #   ___(_) __ _ _ __  _   _ _ __    / _| ___  _ __ _ __ ___
        #  / __| |/ _` | '_ \| | | | '_ \  | |_ / _ \| '__| '_ ` _ \
        #  \__ \ | (_| | | | | |_| | |_) | |  _| (_) | |  | | | | | |
        #  |___/_|\__, |_| |_|\__,_| .__/  |_|  \___/|_|  |_| |_| |_|
        #         |___/            |_|
        print('Create signup form...')

        questions = [
            models.Question(
                question = 'Sais-tu ce qu\'est un tableau en informatique ?',
                response_type = models.AnswerTypes.multichoice.value,
                meta = {
                    'choices': {
                        '0': 'pas du tout',
                        '1': 'un peu',
                        '2': 'bien',
                        '3': 'très bien'
                    }
                }
            ),
            models.Question(
                question = 'Sais-tu ce qu\'est une fonction récursive ?',
                response_type = models.AnswerTypes.multichoice.value,
                meta = {
                    'choices': {
                        '0': 'pas du tout',
                        '1': 'un peu',
                        '2': 'bien',
                        '3': 'très bien'
                    }
                }
            ),
            models.Question(
                question = 'Depuis quand programmes-tu ?',
                response_type = models.AnswerTypes.multichoice.value,
                meta = {
                    'choices': {
                        '0': 'quelques jours',
                        '1': 'quelques semaines',
                        '2': 'quelques mois',
                        '3': 'un an ou plus',
                        '5': 'pas encore commencé'
                    }
                }
            ),
            models.Question(
                question = 'Est-ce que tu programmes en moyenne...',
                response_type = models.AnswerTypes.multichoice.value,
                meta = {
                    'choices': {
                        '0': 'une fois par an',
                        '1': 'une fois par mois',
                        '2': 'une fois par semaine',
                        '3': 'tous les jours'
                    }
                }
            ),
            models.Question(
                question = 'Quel(s) outil(s) ou langage(s) de programmation as-tu déjà essayé(s) ?',
                response_type = models.AnswerTypes.string.value
            ),
            models.Question(
                question = 'Quel est ton parcours scolaire et as-tu une idée de ce que tu veux faire plus tard ?',
                response_type = models.AnswerTypes.text.value
            ),
            models.Question(
                question = 'Qu\'espères-tu apprendre pendant ce stage ?',
                response_type = models.AnswerTypes.text.value
            ),
            models.Question(
                question = 'Aimerais-tu réaliser un projet en rapport avec l\'informatique ? Si oui, lequel ?',
                response_type = models.AnswerTypes.text.value
            ),
            models.Question(
                question = 'Quel est ton identifiant sur France-ioi ?',
                response_type = models.AnswerTypes.string.value
            ),
        ]

        questions_extfields = ('knows_array', 'knows_recurs', 'experience',
            'frequency', 'languages', 'studies', 'expectations', 'projects',
            'fioi_login')

        form_name = 'OldWebsiteForm'
        try:
            form = models.Form.objects.get(name=form_name)
        except models.Form.DoesNotExist:
            form = models.Form(name='OldWebsiteForm')
            form.save()

        for i in range(len(questions)):
            try:
                questions[i] = models.Question.objects.get(
                    question=questions[i].question)
            except models.Question.DoesNotExist:
                questions[i].save()

            form.question_list.add(questions[i])

        #            _ _ _   _
        #    ___  __| (_) |_(_) ___  _ __  ___
        #   / _ \/ _` | | __| |/ _ \| '_ \/ __|
        #  |  __/ (_| | | |_| | (_) | | | \__ \
        #   \___|\__,_|_|\__|_|\___/|_| |_|___/
        #
        print('Import Editions...')

        editions = {}

        for edition_data in data['applications']['editions']:
            fields = edition_data['fields']

            try:
                edition = models.Edition.objects.get(year=fields['year'])
            except models.Edition.DoesNotExist:
                edition = models.Edition(year=fields['year'], signup_form=form)
                edition.save()

            editions[edition_data['pk']] = edition

        #
        #    __ _ _ __  _____      _____ _ __ ___
        #   / _` | '_ \/ __\ \ /\ / / _ \ '__/ __|
        #  | (_| | | | \__ \\ V  V /  __/ |  \__ \
        #   \__,_|_| |_|___/ \_/\_/ \___|_|  |___/
        #
        print('Import Answers...')

        for application_data in data['applications']['application']:
            fields = application_data['fields']

            if fields['user'] not in users:
                continue

            user = users[fields['user']]
            edition = editions[fields['edition']]
            applicant = models.Applicant.for_user_and_edition(user, edition)

            for i in range(len(questions_extfields)):
                response = str(fields[questions_extfields[i]])

                if response not in [None, '']:
                    # for multichoices, check if the value is valid
                    if questions[i].response_type == models.AnswerTypes.multichoice.value and response not in questions[i].meta['choices']:
                        continue

                    question_exists = bool(models.Answer.objects.filter(
                        applicant=applicant, question=questions[i]))

                    if not question_exists:
                        models.Answer(applicant=applicant,
                            question=questions[i], response=response
                        ).save()

        #                  _
        #    ___ ___ _ __ | |_ ___ _ __ ___
        #   / __/ _ \ '_ \| __/ _ \ '__/ __|
        #  | (_|  __/ | | | ||  __/ |  \__ \
        #   \___\___|_| |_|\__\___|_|  |___/
        #
        print('Import Centers...')

        centers = {}

        for center_data in data['applications']['centers']:
            fields = center_data['fields']

            try:
                center = models.Center.objects.get(name=fields['name'])
            except models.Center.DoesNotExist:
                center = models.Center(
                    name = fields['name'],
                    type = models.Center.Type.center.value)
                shared_fields = ('is_active', 'comments', 'address',
                    'postal_code', 'city', 'country')

                for f in shared_fields:
                    setattr(center, f, fields[f])

                center.save()

            centers[center_data['pk']] = center

        #                        _
        #    _____   _____ _ __ | |_ ___
        #   / _ \ \ / / _ \ '_ \| __/ __|
        #  |  __/\ V /  __/ | | | |_\__ \
        #   \___| \_/ \___|_| |_|\__|___/
        #
        print('Import Events...')

        events = {}

        for event_data in data['applications']['events']:
            fields = event_data['fields']

            try:
                event = models.Event.objects.get(
                    center      = centers[fields['center']],
                    edition     = editions[fields['edition']],
                    event_start = fields['date_begin'])
            except models.Event.DoesNotExist:
                event = models.Event(
                    center       = centers[fields['center']],
                    edition      = editions[fields['edition']],
                    event_start  = fields['date_begin'],
                    event_end    = fields['date_end'],
                    signup_start = fields['date_begin'],
                    signup_end   = fields['date_end'])
                db_event.save()

            events[event_data['pk']] = event.pk

        #            _     _
        #  __      _(_)___| |__   ___  ___
        #  \ \ /\ / / / __| '_ \ / _ \/ __|
        #   \ V  V /| \__ \ | | |  __/\__ \
        #    \_/\_/ |_|___/_| |_|\___||___/
        #
        print('Import Wishes...')

        for application_data in data['applications']['application']:
            fields = application_data['fields']

            if fields['user'] not in users:
                continue

            user = users[fields['user']]
            edition = editions[fields['edition']]
            applicant = models.Applicant.for_user_and_edition(user, edition)

            field_choices = (fields['event_choice1'], fields['event_choice2'],
                fields['event_choice3'])

            for order, choice in enumerate(field_choices):
                if choice is None:
                    continue

                order += 1
                event = events[choice]

                wish_exists = bool(models.EventWish.objects.filter(
                    applicant=applicant, event=event))

                if not wish_exists:
                    models.EventWish(
                        applicant=applicant, event=event, order=order
                    ).save()

            if fields['accepted']:
                event_wish = models.EventWish.objects.filter(
                    applicant=applicant
                ).first()

                if event_wish is None:
                    try:
                        event = models.Event.objects.get(
                            center__name='EPITA Paris', edition=edition)
                    except models.Event.DoesNotExist:
                        center = models.Center.objects.get(name='EPITA Paris')
                        start = '{}-01-01'.format(edition.year)
                        end = '{}-12-31'.format(edition.year)

                        event = models.Event(
                            center=center, edition=edition, event_start=start,
                            event_end=end, signup_start=start, signup_end=end)
                        event.save()

                    event_wish = models.EventWish(applicant=applicant,
                        event=event, order=1)
                    event_wish.save()

                applicant.assignation_event.add(event_wish.event)

        #       _        _
        #   ___| |_ __ _| |_ _   _ ___
        #  / __| __/ _` | __| | | / __|
        #  \__ \ || (_| | |_| |_| \__ \
        #  |___/\__\__,_|\__|\__,_|___/
        #
        print('Update Applications Status...')

        for application_data in data['applications']['application']:
            fields = application_data['fields']

            if fields['user'] not in users:
                continue

            user = users[fields['user']]
            edition = editions[fields['edition']]
            applicant = models.Applicant.for_user_and_edition(user, edition)

            if fields['accepted']:
                if fields['confirmed']:
                    applicant.status = models.ApplicantStatusTypes.confirmed.value
                else:
                    applicant.status = models.ApplicantStatusTypes.accepted.value
            elif fields['accepted'] is False:
                applicant.status = models.ApplicantStatusTypes.rejected.value

            applicant.save()

