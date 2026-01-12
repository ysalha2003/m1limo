"""
Django management command to send automated pickup reminders.

This command should be run via cron job to automatically send pickup reminder
emails at scheduled intervals (e.g., 24 hours, 6 hours, 30 minutes before pickup).

Usage:
    python manage.py send_pickup_reminders --hours 24  # Send reminders for pickups in 24 hours
    python manage.py send_pickup_reminders --hours 6   # Send reminders for pickups in 6 hours
    python manage.py send_pickup_reminders --hours 0.5 # Send reminders for pickups in 30 minutes
"""
import logging
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.apps import apps

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Send pickup reminder emails for upcoming bookings'

    def add_arguments(self, parser):
        parser.add_argument(
            '--hours',
            type=float,
            default=24,
            help='Hours before pickup to send reminder (default: 24)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually sending emails'
        )

    def handle(self, *args, **options):
        # Import models inside handle to avoid import issues
        Booking = apps.get_model('bookings', 'Booking')
        from utils import send_pickup_reminder_email

        hours_before = options['hours']
        dry_run = options['dry_run']

        self.stdout.write(f"\n{'='*60}")
        self.stdout.write(f"Pickup Reminder Job - {hours_before} Hour(s) Before Pickup")
        self.stdout.write(f"{'='*60}\n")

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No emails will be sent\n"))

        # Calculate the target datetime window
        now = timezone.now()
        target_time = now + timedelta(hours=hours_before)

        # Allow a 15-minute window to catch bookings
        # (in case cron doesn't run at exact time)
        window_start = target_time - timedelta(minutes=15)
        window_end = target_time + timedelta(minutes=15)

        self.stdout.write(f"Current time: {now.strftime('%Y-%m-%d %H:%M:%S')}")
        self.stdout.write(f"Looking for pickups between:")
        self.stdout.write(f"  {window_start.strftime('%Y-%m-%d %H:%M:%S')}")
        self.stdout.write(f"  {window_end.strftime('%Y-%m-%d %H:%M:%S')}\n")

        # Find bookings that need reminders
        # Only send reminders for confirmed bookings
        bookings = Booking.objects.filter(
            status='Confirmed',
            pick_up_date__gte=window_start.date(),
            pick_up_date__lte=window_end.date()
        )

        # Filter by time within the window
        eligible_bookings = []
        for booking in bookings:
            # Combine date and time to get full datetime
            pickup_datetime = datetime.combine(booking.pick_up_date, booking.pick_up_time)

            # Make timezone aware if needed
            if timezone.is_naive(pickup_datetime):
                pickup_datetime = timezone.make_aware(pickup_datetime)

            # Check if pickup is within our window
            if window_start <= pickup_datetime <= window_end:
                eligible_bookings.append(booking)

        if not eligible_bookings:
            self.stdout.write(self.style.SUCCESS("\nNo bookings found needing reminders at this time."))
            self.stdout.write(f"{'='*60}\n")
            return

        self.stdout.write(f"Found {len(eligible_bookings)} booking(s) needing reminders:\n")

        success_count = 0
        fail_count = 0

        for booking in eligible_bookings:
            pickup_datetime = datetime.combine(booking.pick_up_date, booking.pick_up_time)
            if timezone.is_naive(pickup_datetime):
                pickup_datetime = timezone.make_aware(pickup_datetime)

            # Determine if this is a return trip
            is_return = booking.is_return_trip

            self.stdout.write(
                f"\nBooking #{booking.id}: {booking.passenger_name} "
                f"({'Return' if is_return else 'Outbound'})"
            )
            self.stdout.write(f"  Pickup: {pickup_datetime.strftime('%Y-%m-%d %H:%M')}")
            self.stdout.write(f"  From: {booking.pick_up_address}")
            self.stdout.write(f"  To: {booking.drop_off_address}")

            if booking.passenger_email:
                self.stdout.write(f"  Email: {booking.passenger_email}")
            if booking.phone_number:
                self.stdout.write(f"  Phone: {booking.phone_number}")

            if dry_run:
                self.stdout.write(self.style.WARNING("  [DRY RUN] Would send reminder email"))
                success_count += 1
            else:
                # Send the reminder
                success = send_pickup_reminder_email(booking, is_return=is_return)

                if success:
                    self.stdout.write(self.style.SUCCESS("  Reminder sent successfully"))
                    success_count += 1
                else:
                    self.stdout.write(self.style.ERROR("  Failed to send reminder"))
                    fail_count += 1

        # Summary
        self.stdout.write(f"\n{'='*60}")
        self.stdout.write("Summary:")
        self.stdout.write(f"  Total bookings found: {len(eligible_bookings)}")
        self.stdout.write(f"  Reminders sent successfully: {success_count}")
        if fail_count > 0:
            self.stdout.write(self.style.ERROR(f"  Failed: {fail_count}"))
        self.stdout.write(f"{'='*60}\n")

        if fail_count > 0:
            self.stdout.write(
                self.style.WARNING(
                    "Some reminders failed to send. Check logs for details."
                )
            )
