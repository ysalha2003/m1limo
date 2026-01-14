"""
Management command to fix existing bookings with NULL contact information.
Sets default values for phone_number and passenger_email where NULL.
"""

from django.core.management.base import BaseCommand
from models import Booking


class Command(BaseCommand):
    help = 'Fix existing bookings with NULL contact information'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        # Find bookings with NULL phone_number
        null_phone_bookings = Booking.objects.filter(phone_number__isnull=True)
        null_phone_count = null_phone_bookings.count()

        # Find bookings with NULL passenger_email
        null_email_bookings = Booking.objects.filter(passenger_email__isnull=True)
        null_email_count = null_email_bookings.count()

        self.stdout.write(f"\nFound {null_phone_count} bookings with NULL phone_number")
        self.stdout.write(f"Found {null_email_count} bookings with NULL passenger_email\n")

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN - No changes will be made\n"))
            
            if null_phone_count > 0:
                self.stdout.write("Would update phone_number to 'N/A' for:")
                for booking in null_phone_bookings:
                    self.stdout.write(f"  - Booking #{booking.id}: {booking.passenger_name}")
            
            if null_email_count > 0:
                self.stdout.write("\nWould update passenger_email to 'noreply@m1limo.com' for:")
                for booking in null_email_bookings:
                    self.stdout.write(f"  - Booking #{booking.id}: {booking.passenger_name}")
        else:
            # Update NULL phone_number values
            if null_phone_count > 0:
                updated_phones = null_phone_bookings.update(phone_number='N/A')
                self.stdout.write(
                    self.style.SUCCESS(f"Updated {updated_phones} bookings with phone_number='N/A'")
                )

            # Update NULL passenger_email values
            if null_email_count > 0:
                updated_emails = null_email_bookings.update(passenger_email='noreply@m1limo.com')
                self.stdout.write(
                    self.style.SUCCESS(f"Updated {updated_emails} bookings with passenger_email='noreply@m1limo.com'")
                )

            if null_phone_count == 0 and null_email_count == 0:
                self.stdout.write(
                    self.style.SUCCESS("No bookings need updating - all have contact information!")
                )
