from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
import centers.models
import geopy.geocoders


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--force', action='store_true', dest='force', default=False,
                    help="Force the geocoding of centers with a non-zero lat/lng"),
        make_option('--suffix', dest='suffix', default=', FRANCE',
                    help="Suffix to happen to all address before querying"),
        )
    help = "Geocode centers from their human address"

    def handle(self, *args, **options):
        g = geopy.geocoders.GoogleV3()
        center_list = centers.models.Center.objects.filter(is_active=True)
        for center in center_list:
            if options['force'] or not center.has_valid_geolocation:
                try:
                    addr = "{name}, {addr}, {code} {city} {suffix}".format(
                        name=center.name, addr=center.address, code=center.postal_code, city=center.city,
                        suffix=options['suffix'],
                    )
                    _, (lat, lng) = g.geocode(addr)
                    center.lat = lat
                    center.lng = lng
                    center.save()
                    print("[FOUND] {addr} → {lat} {lng}".format(addr=addr, lat=lat, lng=lng))
                except Exception:
                    print("[ERROR] {addr} → no lat/lng found".format(addr=addr))
            else:
                print("[SKIP ] {name} is already geocoded (use --force to geocode again)".format(name=center.name))
