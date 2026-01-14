import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from models import Booking
from django.db.models import Count

print("\n" + "="*70)
print("RESERVATION SUMMARY")
print("="*70)

bookings = Booking.objects.select_related('user', 'assigned_driver').all()

print(f"\nTotal Reservations: {bookings.count()}")

# Count by trip type
print("\nBy Trip Type:")
for trip_type in ['Point', 'Hourly']:
    count = bookings.filter(trip_type=trip_type).count()
    print(f"  {trip_type}: {count}")

# Count round trips
linked = bookings.filter(linked_booking_id__isnull=False).count()
print(f"  Round Trips (total legs): {linked}")

# Count by status
print("\nBy Status:")
for status in ['Pending', 'Confirmed', 'Trip_Completed']:
    count = bookings.filter(status=status).count()
    print(f"  {status}: {count}")

# Show some examples
print("\nSample Reservations:")
for booking in bookings[:10]:
    driver_info = f"Driver: {booking.assigned_driver.full_name}" if booking.assigned_driver else "No driver assigned"
    print(f"  #{booking.id}: {booking.trip_type} - {booking.user.email} - {booking.status} - {driver_info}")

print("\n" + "="*70)
