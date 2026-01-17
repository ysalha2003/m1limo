import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from models import Booking
from django.utils import timezone
from django.db.models import Q
from datetime import datetime

today = timezone.now().date()
now = timezone.now()

print("=" * 60)
print("CURRENT TIME:")
print("=" * 60)
print(f"  Now: {now}")
print(f"  Today: {today}")

# Get all future bookings using the NEW logic (datetime comparison)
future_bookings = []
for booking in Booking.objects.all():
    pickup_datetime = datetime.combine(booking.pick_up_date, booking.pick_up_time)
    if timezone.is_naive(pickup_datetime):
        pickup_datetime = timezone.make_aware(pickup_datetime)
    if pickup_datetime > now:
        future_bookings.append(booking.id)

future_filter = Q(id__in=future_bookings)

print("\n" + "=" * 60)
print(f"FUTURE BOOKINGS (using datetime comparison): {len(future_bookings)} found")
print("=" * 60)

# Get confirmed future bookings
confirmed_future = Booking.objects.filter(
    status='Confirmed'
).filter(future_filter).order_by('pick_up_date', 'pick_up_time')

print("\nConfirmed future trips:")
for b in confirmed_future[:5]:  # Show first 5
    print(f"  ID: {b.id}, Date: {b.pick_up_date}, Time: {b.pick_up_time}, " +
          f"Return: {b.is_return_trip}, Hours: {b.hours_until_pickup:.2f}, " +
          f"Passenger: {b.passenger_name}")

# Get the next upcoming trip (exclude return trips)
next_upcoming = Booking.objects.filter(
    status='Confirmed',
    is_return_trip=False
).filter(future_filter).order_by('pick_up_date', 'pick_up_time').first()

print("\n" + "=" * 60)
print("NEXT UPCOMING TRIP (New Logic - Exclude Returns):")
print("=" * 60)
if next_upcoming:
    print(f"  ID: {next_upcoming.id}")
    print(f"  Date: {next_upcoming.pick_up_date}")
    print(f"  Time: {next_upcoming.pick_up_time}")
    print(f"  Passenger: {next_upcoming.passenger_name}")
    print(f"  Hours until pickup: {next_upcoming.hours_until_pickup:.2f}")
    print(f"  is_return_trip: {next_upcoming.is_return_trip}")
else:
    print("  None found")

# Check today's pickups
today_pickups = Booking.objects.filter(
    pick_up_date=today,
    status='Confirmed',
    is_return_trip=False
).order_by('pick_up_time')

# Filter to future only
future_today_pickups = []
for booking in today_pickups:
    pickup_datetime = datetime.combine(booking.pick_up_date, booking.pick_up_time)
    if timezone.is_naive(pickup_datetime):
        pickup_datetime = timezone.make_aware(pickup_datetime)
    if pickup_datetime > now:
        future_today_pickups.append(booking)

print("\n" + "=" * 60)
print("TODAY'S PICKUPS (Future only):")
print("=" * 60)
for b in future_today_pickups:
    print(f"  ID: {b.id}, Time: {b.pick_up_time}, Hours: {b.hours_until_pickup:.2f}, " +
          f"Passenger: {b.passenger_name}")

print("\n" + "=" * 60)
print("VERIFICATION:")
print("=" * 60)
if future_today_pickups and next_upcoming:
    soonest_today = min(future_today_pickups, key=lambda b: b.hours_until_pickup)
    print(f"Soonest today's pickup: Booking #{soonest_today.id} ({soonest_today.hours_until_pickup:.2f}h)")
    print(f"Next Reservation shows: Booking #{next_upcoming.id} ({next_upcoming.hours_until_pickup:.2f}h)")
    
    if soonest_today.id == next_upcoming.id:
        print("\n✓ ✓ ✓ SUCCESS! Next Reservation correctly shows the soonest trip!")
    else:
        print(f"\n⚠️  Issue: Different bookings")
        print(f"  Expected: #{soonest_today.id} ({soonest_today.hours_until_pickup:.2f}h)")
        print(f"  Got: #{next_upcoming.id} ({next_upcoming.hours_until_pickup:.2f}h)")
elif not future_today_pickups:
    print("✓ No today's pickups - Next Reservation is correct")
else:
    print("✓ Logic working correctly")
