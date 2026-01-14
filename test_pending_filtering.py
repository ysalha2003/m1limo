"""
Test script to verify Pending trip filtering logic.
Shows which Pending trips have future pickups vs past pickups.
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from models import Booking
from django.utils import timezone
from django.db.models import Q
from datetime import datetime

# Get current datetime
now = timezone.now()
today = now.date()
current_time = now.time()

print("=" * 70)
print("PENDING TRIP FILTERING ANALYSIS")
print("=" * 70)
print(f"Current Time: {now.strftime('%Y-%m-%d %H:%M:%S')}")
print()

# Get all Pending trips
all_pending = Booking.objects.filter(status='Pending').order_by('pick_up_date', 'pick_up_time')
print(f"Total Pending Trips: {all_pending.count()}")
print()

# Split into future and past based on datetime
future_filter = Q(pick_up_date__gt=today) | Q(pick_up_date=today, pick_up_time__gte=current_time)
past_filter = Q(pick_up_date__lt=today) | Q(pick_up_date=today, pick_up_time__lt=current_time)

future_pending = all_pending.filter(future_filter)
past_pending = all_pending.filter(past_filter)

print(f"✅ Future Pending (should be in 'Pending' count): {future_pending.count()}")
print(f"⚠️  Past Pending (need admin review): {past_pending.count()}")
print()

if past_pending.exists():
    print("=" * 70)
    print("🕒 PAST PENDING TRIPS (Never Confirmed, Pickup Time Passed)")
    print("=" * 70)
    
    for booking in past_pending:
        pickup_datetime = datetime.combine(booking.pick_up_date, booking.pick_up_time)
        if timezone.is_naive(pickup_datetime):
            pickup_datetime = timezone.make_aware(pickup_datetime)
        
        hours_overdue = int((now - pickup_datetime).total_seconds() / 3600)
        
        # Color code based on severity
        if hours_overdue >= 48:
            icon = "🔴"  # Critical - over 2 days
        elif hours_overdue >= 24:
            icon = "🟠"  # High - over 1 day
        else:
            icon = "🟡"  # Medium - less than 1 day
        
        print(f"{icon} #{booking.id} | {booking.pick_up_date} {booking.pick_up_time.strftime('%H:%M')} | {booking.passenger_name} | {hours_overdue} hours overdue")
    
    print()
    print("💡 Actions Available:")
    print("   - Confirm Anyway: Late confirmation, but trip might still be valid")
    print("   - Cancel: Trip request no longer valid")
    print("   - Trip Not Covered: Outside service area or other constraints")
    print()

if future_pending.exists():
    print("=" * 70)
    print("⏰ FUTURE PENDING TRIPS (Awaiting Confirmation)")
    print("=" * 70)
    
    for booking in future_pending[:10]:  # Show first 10
        pickup_datetime = datetime.combine(booking.pick_up_date, booking.pick_up_time)
        if timezone.is_naive(pickup_datetime):
            pickup_datetime = timezone.make_aware(pickup_datetime)
        
        hours_remaining = int((pickup_datetime - now).total_seconds() / 3600)
        
        # Show if same day or future day
        if booking.pick_up_date == today:
            time_str = f"Today at {booking.pick_up_time.strftime('%H:%M')} ({hours_remaining} hours)"
        else:
            days_away = (booking.pick_up_date - today).days
            time_str = f"In {days_away} day{'s' if days_away != 1 else ''} at {booking.pick_up_time.strftime('%H:%M')}"
        
        print(f"⏳ #{booking.id} | {time_str} | {booking.passenger_name}")
    
    if future_pending.count() > 10:
        print(f"... and {future_pending.count() - 10} more")
    print()

print("=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"✅ Future Pending trips: {future_pending.count()} (show in dashboard 'Pending' count)")
print(f"⚠️  Past Pending trips: {past_pending.count()} (need admin review at /admin/past-pending-trips/)")
print()
print("DateTime filtering ensures accurate stats and prevents expired requests")
print("from inflating the 'Pending' count indefinitely.")
print("=" * 70)
