import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from models import Booking
from django.utils import timezone
from django.db.models import Q

today = timezone.now().date()
now = timezone.now()

# Check today's pickups
pickups = Booking.objects.filter(
    pick_up_date=today,
    status='Confirmed'
).order_by('pick_up_time')

print("=" * 60)
print("TODAY'S PICKUPS (Confirmed):")
print("=" * 60)
for b in pickups:
    print(f"  ID: {b.id}")
    print(f"  Time: {b.pick_up_time}")
    print(f"  is_return_trip: {b.is_return_trip}")
    print(f"  Passenger: {b.passenger_name}")
    print(f"  Hours until pickup: {b.hours_until_pickup:.2f}")
    print("-" * 60)

# Build future filter
current_time = now.time()
future_filter = Q(pick_up_date__gt=today) | Q(pick_up_date=today, pick_up_time__gte=current_time)

# Get next trip EXCLUDING returns (current logic)
next_trip_no_returns = Booking.objects.filter(
    status='Confirmed',
    is_return_trip=False
).filter(future_filter).order_by('pick_up_date', 'pick_up_time').first()

print("\n" + "=" * 60)
print("NEXT UPCOMING TRIP (EXCLUDING RETURNS - CURRENT LOGIC):")
print("=" * 60)
if next_trip_no_returns:
    print(f"  ID: {next_trip_no_returns.id}")
    print(f"  Date: {next_trip_no_returns.pick_up_date}")
    print(f"  Time: {next_trip_no_returns.pick_up_time}")
    print(f"  is_return_trip: {next_trip_no_returns.is_return_trip}")
    print(f"  Passenger: {next_trip_no_returns.passenger_name}")
    print(f"  Hours until pickup: {next_trip_no_returns.hours_until_pickup:.2f}")
else:
    print("  None found")

# Get next trip INCLUDING returns (fixed logic)
next_trip_all = Booking.objects.filter(
    status='Confirmed'
).filter(future_filter).order_by('pick_up_date', 'pick_up_time').first()

print("\n" + "=" * 60)
print("NEXT UPCOMING TRIP (INCLUDING ALL - FIXED LOGIC):")
print("=" * 60)
if next_trip_all:
    print(f"  ID: {next_trip_all.id}")
    print(f"  Date: {next_trip_all.pick_up_date}")
    print(f"  Time: {next_trip_all.pick_up_time}")
    print(f"  is_return_trip: {next_trip_all.is_return_trip}")
    print(f"  Passenger: {next_trip_all.passenger_name}")
    print(f"  Hours until pickup: {next_trip_all.hours_until_pickup:.2f}")
    if next_trip_all.linked_booking:
        print(f"  Linked to: Booking #{next_trip_all.linked_booking.id}")
else:
    print("  None found")

print("\n" + "=" * 60)
print("ANALYSIS:")
print("=" * 60)
if next_trip_no_returns and next_trip_all:
    if next_trip_no_returns.id != next_trip_all.id:
        print("⚠️  ISSUE CONFIRMED: The soonest trip is being excluded!")
        print(f"    Current logic shows trip {next_trip_no_returns.id} ({next_trip_no_returns.hours_until_pickup:.2f}h)")
        print(f"    Should show trip {next_trip_all.id} ({next_trip_all.hours_until_pickup:.2f}h)")
    else:
        print("✓ Both queries return the same trip")
