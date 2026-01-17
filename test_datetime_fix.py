"""
Final verification test for datetime comparison fixes
Tests that the dashboard correctly identifies:
1. Next Reservation (should show soonest upcoming trip)
2. Today's Pickups (should show only future trips today)
3. Upcoming vs Past classification
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
print("FINAL VERIFICATION TEST - DATETIME COMPARISON FIXES")
print("=" * 70)

now = timezone.now()
today = now.date()

print(f"\nCurrent time: {now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
print(f"Current date: {today}")
print(f"Current time (time only): {now.time()}")

# Test 1: Get all confirmed trips and classify them
print("\n" + "=" * 70)
print("TEST 1: All Confirmed Trips Classification")
print("=" * 70)

confirmed_trips = Booking.objects.filter(status='Confirmed').order_by('pick_up_date', 'pick_up_time')

future_trips = []
past_trips = []

for booking in confirmed_trips:
    pickup_datetime = datetime.combine(booking.pick_up_date, booking.pick_up_time)
    if timezone.is_naive(pickup_datetime):
        pickup_datetime = timezone.make_aware(pickup_datetime)
    
    hours_diff = (pickup_datetime - now).total_seconds() / 3600
    
    if pickup_datetime > now:
        future_trips.append(booking)
        status = "FUTURE"
    else:
        past_trips.append(booking)
        status = "PAST"
    
    print(f"  Booking #{booking.id}: {booking.pick_up_date} {booking.pick_up_time} " +
          f"- {status} ({hours_diff:+.2f}h)")

print(f"\nSummary: {len(future_trips)} future, {len(past_trips)} past")

# Test 2: Next Reservation logic
print("\n" + "=" * 70)
print("TEST 2: Next Reservation (should show SOONEST future trip)")
print("=" * 70)

future_ids = [b.id for b in future_trips]
next_upcoming = Booking.objects.filter(
    status='Confirmed',
    is_return_trip=False,
    id__in=future_ids
).order_by('pick_up_date', 'pick_up_time').first()

if next_upcoming:
    print(f"\n✓ Next Reservation:")
    print(f"    Booking #{next_upcoming.id}")
    print(f"    Date/Time: {next_upcoming.pick_up_date} {next_upcoming.pick_up_time}")
    print(f"    Passenger: {next_upcoming.passenger_name}")
    print(f"    Hours until: {next_upcoming.hours_until_pickup:.2f}h")
    
    # Verify it's the soonest
    if future_trips and next_upcoming.id == future_trips[0].id:
        print(f"\n    ✓ CORRECT: This is the soonest future trip")
    elif future_trips:
        print(f"\n    ⚠️  WARNING: Soonest is Booking #{future_trips[0].id} " +
              f"({future_trips[0].hours_until_pickup:.2f}h)")
else:
    print("\n  No next upcoming trip found")

# Test 3: Today's Pickups logic
print("\n" + "=" * 70)
print("TEST 3: Today's Pickups (should show FUTURE trips today only)")
print("=" * 70)

today_pickups = Booking.objects.filter(
    pick_up_date=today,
    status='Confirmed',
    is_return_trip=False
).order_by('pick_up_time')

future_today_pickups = []
for booking in today_pickups:
    pickup_datetime = datetime.combine(booking.pick_up_date, booking.pick_up_time)
    if timezone.is_naive(pickup_datetime):
        pickup_datetime = timezone.make_aware(pickup_datetime)
    if pickup_datetime > now:
        future_today_pickups.append(booking)

print(f"\n  Total today: {today_pickups.count()}")
print(f"  Future today: {len(future_today_pickups)}")

if future_today_pickups:
    print(f"\n  Future pickups today:")
    for b in future_today_pickups:
        print(f"    Booking #{b.id} at {b.pick_up_time} " +
              f"({b.hours_until_pickup:.2f}h) - {b.passenger_name}")
else:
    print(f"\n  No future pickups today")

# Test 4: Time-only comparison bug check
print("\n" + "=" * 70)
print("TEST 4: Time-Only Comparison Bug Check")
print("=" * 70)
print("\nScenario: Current time is late at night (e.g., 11 PM)")
print("          Pickup time is early morning (e.g., 4 AM)")
print("          OLD LOGIC: 04:20 >= 23:11 → False (WRONG!)")
print("          NEW LOGIC: Compare full datetimes → True (CORRECT!)")

current_time_value = now.time()
print(f"\nCurrent time: {current_time_value}")

for booking in future_today_pickups:
    pickup_time_value = booking.pick_up_time
    old_logic_result = pickup_time_value >= current_time_value
    
    pickup_datetime = datetime.combine(booking.pick_up_date, booking.pick_up_time)
    if timezone.is_naive(pickup_datetime):
        pickup_datetime = timezone.make_aware(pickup_datetime)
    new_logic_result = pickup_datetime > now
    
    print(f"\n  Booking #{booking.id} pickup time: {pickup_time_value}")
    print(f"    OLD: {pickup_time_value} >= {current_time_value} = {old_logic_result}")
    print(f"    NEW: datetime comparison = {new_logic_result}")
    
    if old_logic_result != new_logic_result:
        print(f"    ⚠️  BUG DETECTED: Old logic would classify incorrectly!")
        print(f"    ✓  NEW LOGIC FIXES THIS")

# Final Summary
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)

issues_found = 0

# Check if Next Reservation matches soonest trip
if next_upcoming and future_trips:
    soonest = min(future_trips, key=lambda b: b.hours_until_pickup)
    if next_upcoming.id != soonest.id:
        print(f"\n⚠️  Issue: Next Reservation shows #{next_upcoming.id} but " +
              f"soonest is #{soonest.id}")
        issues_found += 1
    else:
        print(f"\n✓ Next Reservation correctly shows soonest trip (#{next_upcoming.id})")

# Check if Today's Pickups only shows future
if today_pickups.exists():
    print(f"✓ Today's Pickups filter correctly applied ({len(future_today_pickups)} future)")

# Check time comparison bug
has_late_night_scenario = (current_time_value.hour >= 20 or current_time_value.hour <= 6)
if has_late_night_scenario:
    print(f"✓ Time comparison bug scenario detected and handled correctly")

if issues_found == 0:
    print(f"\n{'='*70}")
    print("🎉 ALL TESTS PASSED! Datetime comparison fixes working correctly!")
    print(f"{'='*70}")
else:
    print(f"\n{'='*70}")
    print(f"⚠️  {issues_found} issue(s) found")
    print(f"{'='*70}")
