from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone, dateparse
import datetime

from contest.models import Edition, Event


class Command(BaseCommand):
    help = "Manage Prologin editions."

    def add_arguments(self, parser):
        """
        :type parser: argparse.ArgumentParser
        """
        sp = parser.add_subparsers(dest="cmd")
        sp.add_parser(name="create", cmd="create",
                      help="create a new Prologin edition")

    def _ask_for(self, question, default=None, validate=None, coerce=None):
        while True:
            answer = input("{}{}: ".format(
                question,
                "" if default is None
                   else " [{}]".format(default)))
            if not answer and default is not None:
                answer = default
            if validate is None or validate(answer):
                return answer if coerce is None else coerce(answer)
            self.stdout.write("enter a valid choice!")

    def _print_begin_end(self, obj):
        local_name = timezone.get_default_timezone_name()
        self.stdout.write("    from UTC {utcd}, {local} {locald}".format(
            local=local_name, utcd=obj.date_begin.astimezone(timezone.utc),
            locald=timezone.localtime(obj.date_begin)))
        self.stdout.write("      to UTC {utcd}, {local} {locald}".format(
            local=local_name, utcd=obj.date_end.astimezone(timezone.utc),
            locald=timezone.localtime(obj.date_end)))

    def handle(self, *args, **options):
        cmd = options['cmd']
        if cmd == 'create':
            def date_with_year(year):
                def coerce(value):
                    value = "{}-{}".format(year, value.split("-", 1)[1])
                    self.stdout.write(value)
                    return dateparse.parse_date(value)
                return coerce

            now = timezone.now()
            year = now.year
            if 5 <= now.month <= 12:
                # if we are between May and December, edition year is current-year + 1
                year += 1

            year = self._ask_for("Edition year", default=year, coerce=int)
            try:
                edition = Edition.objects.get(year=year)
                self.stdout.write("Edition {} already exists:".format(year))
                self._print_begin_end(edition)
                self.stdout.write("You can update it in the admin if needed.")

            except Edition.DoesNotExist:
                edition = Edition(year=year)
                self.stdout.write("All times are expressed in timezone {}"
                                  .format(timezone.get_default_timezone_name()))
                date_begin = self._ask_for("Begins on date ({}-mm-dd)".format(year - 1),
                                           coerce=date_with_year(year - 1))
                time_begin = self._ask_for("Begins on time (hh:mm:ss)",
                                           default="00:00:00", coerce=dateparse.parse_time)
                date_end = self._ask_for("Ends on date ({}-mm-dd)".format(year),
                                         coerce=date_with_year(year))
                time_end = self._ask_for("Ends on time (hh:mm:ss)",
                                         default="00:00:00", coerce=dateparse.parse_time)
                datetime_begin = datetime.datetime.combine(date_begin, time_begin)
                datetime_begin = timezone.make_aware(datetime_begin)
                datetime_end = datetime.datetime.combine(date_end, time_end)
                datetime_end = timezone.make_aware(datetime_end)
                self.stdout.write("")
                if datetime_begin > datetime_end:
                    raise CommandError("End date is anterior to begin date. This makes no sense.")
                edition.date_begin = datetime_begin
                edition.date_end = datetime_end
                edition.save()
                self.stdout.write("Edition {} created:".format(year))
                self._print_begin_end(edition)

            self.stdout.write("")

            event_qualification = Event.objects.filter(edition=edition, type=Event.Type.qualification.value)
            if event_qualification.exists():
                self.stdout.write("Qualification event already exists")
            elif self._ask_for("Do you want to create qualification event", default="n").lower().startswith("y"):
                Event(edition=edition, type=Event.Type.qualification.value).save()

            # TODO: semifinals
            # TODO: final

            return

        raise CommandError("Unknown edition sub-command")
