"""
Test the Next Reservation rotation feature
Verify that multiple trips at the same time are returned correctly
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from models import Booking
from django.utils import timezone
from django.db.models import Q
from datetime import datetime

print("=" * 70)
print("NEXT RESERVATION ROTATION TEST")
print("=" * 70)

now = timezone.now()
today = now.date()

# Get all future bookings
future_bookings = []
for booking in Booking.objects.all():
    pickup_datetime = datetime.combine(booking.pick_up_date, booking.pick_up_time)
    if timezone.is_naive(pickup_datetime):
        pickup_datetime = timezone.make_aware(pickup_datetime)
    if pickup_datetime > now:
        future_bookings.append(booking.id)

future_filter = Q(id__in=future_bookings)

# Get the next upcoming trip
next_upcoming = Booking.objects.filter(
    status='Confirmed',
    is_return_trip=False
).filter(future_filter).order_by('pick_up_date', 'pick_up_time').first()

print(f"\n✓ Next Upcoming Trip:")
if next_upcoming:
    print(f"    Booking #{next_upcoming.id}")
    print(f"    Date: {next_upcoming.pick_up_date}")
    print(f"    Time: {next_upcoming.pick_up_time}")
    print(f"    Passenger: {next_upcoming.passenger_name}")
    print(f"    Hours until: {next_upcoming.hours_until_pickup:.2f}h")
    
    # Get ALL trips at the same time
    same_time_trips = Booking.objects.filter(
        status='Confirmed',
        is_return_trip=False,
        pick_up_date=next_upcoming.pick_up_date,
        pick_up_time=next_upcoming.pick_up_time
    ).filter(future_filter).order_by('passenger_name')
    
    print(f"\n✓ All Trips at Same Time ({same_time_trips.count()} total):")
    for i, trip in enumerate(same_time_trips, 1):
        print(f"    {i}. Booking #{trip.id} - {trip.passenger_name}")
        print(f"       Location: {trip.pick_up_address[:50]}...")
        print(f"       Vehicle: {trip.vehicle_type}")
    
    if same_time_trips.count() > 1:
        print(f"\n✅ ROTATION FEATURE WILL ACTIVATE!")
        print(f"   Card will rotate between {same_time_trips.count()} trips every 3 seconds")
        print(f"   Counter will show: 1/{same_time_trips.count()}, 2/{same_time_trips.count()}, etc.")
    else:
        print(f"\n   Single trip - no rotation needed")
else:
    print("    No upcoming trips found")

print("\n" + "=" * 70)
