from django.core.management import BaseCommand

from archives.tasks import extract_archive_flickr_photos


class Command(BaseCommand):
    help = "Download Flickr album photos for all archives and randomize them into Redis."

    def handle(self, *args, **options):
        self.stdout.write("Scheduling task...")
        future = extract_archive_flickr_photos.apply_async()
        self.stdout.write("Waiting for result...")
        future.get(timeout=None)
        self.stdout.write("Done.")
