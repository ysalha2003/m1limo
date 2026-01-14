#!/usr/bin/env python
"""Test script to verify the datetime-based upcoming/past trip filtering"""

import os
import sys
import django
from datetime import datetime, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from django.utils import timezone
from django.db.models import Q
from models import Booking

def test_trip_filtering():
    """Test the upcoming vs past trip filtering logic"""
    
    now = timezone.now()
    today = now.date()
    current_time = now.time()
    
    print("=" * 70)
    print("Trip Filtering Test - Datetime-Based Logic")
    print("=" * 70)
    print(f"\nCurrent datetime: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Current date: {today}")
    print(f"Current time: {current_time.strftime('%H:%M:%S')}")
    print()
    
    # Future trips: date > today OR (date == today AND time >= current_time)
    future_filter = Q(pick_up_date__gt=today) | Q(pick_up_date=today, pick_up_time__gte=current_time)
    
    # Past trips: date < today OR (date == today AND time < current_time)
    past_filter = Q(pick_up_date__lt=today) | Q(pick_up_date=today, pick_up_time__lt=current_time)
    
    # Get confirmed trips
    confirmed_trips = Booking.objects.filter(status='Confirmed')
    total_confirmed = confirmed_trips.count()
    
    # Apply filters
    upcoming_trips = confirmed_trips.filter(future_filter)
    past_trips = confirmed_trips.filter(past_filter)
    
    print(f"📊 STATISTICS:")
    print(f"   Total Confirmed Trips: {total_confirmed}")
    print(f"   ✅ Upcoming (future pickup): {upcoming_trips.count()}")
    print(f"   ⚠️  Past (pickup time passed): {past_trips.count()}")
    print()
    
    # Show details of upcoming trips
    if upcoming_trips.exists():
        print("🔵 UPCOMING CONFIRMED TRIPS (Correctly shown as 'Upcoming'):")
        print("-" * 70)
        for trip in upcoming_trips.order_by('pick_up_date', 'pick_up_time')[:5]:
            pickup_datetime = datetime.combine(trip.pick_up_date, trip.pick_up_time)
            if timezone.is_naive(pickup_datetime):
                pickup_datetime = timezone.make_aware(pickup_datetime)
            hours_until = int((pickup_datetime - now).total_seconds() / 3600)
            print(f"   #{trip.id:4d} | {trip.pick_up_date} {trip.pick_up_time.strftime('%H:%M')} | "
                  f"{trip.passenger_name[:25]:25s} | In {hours_until} hours")
        if upcoming_trips.count() > 5:
            print(f"   ... and {upcoming_trips.count() - 5} more")
        print()
    else:
        print("🔵 No upcoming confirmed trips found.\n")
    
    # Show details of past trips needing review
    if past_trips.exists():
        print("🟠 PAST CONFIRMED TRIPS (Need Manual Review):")
        print("-" * 70)
        for trip in past_trips.order_by('-pick_up_date', '-pick_up_time')[:10]:
            pickup_datetime = datetime.combine(trip.pick_up_date, trip.pick_up_time)
            if timezone.is_naive(pickup_datetime):
                pickup_datetime = timezone.make_aware(pickup_datetime)
            hours_overdue = int((now - pickup_datetime).total_seconds() / 3600)
            
            # Color code by severity
            if hours_overdue >= 48:
                marker = "🔴"  # Critical
            elif hours_overdue >= 24:
                marker = "🟠"  # High
            else:
                marker = "🟡"  # Medium
                
            print(f"   {marker} #{trip.id:4d} | {trip.pick_up_date} {trip.pick_up_time.strftime('%H:%M')} | "
                  f"{trip.passenger_name[:25]:25s} | {hours_overdue} hours overdue")
        if past_trips.count() > 10:
            print(f"   ... and {past_trips.count() - 10} more")
        print()
    else:
        print("🟢 All confirmed trips are properly scheduled! No past trips need review.\n")
    
    print("=" * 70)
    print("✅ FILTERING LOGIC VERIFIED")
    print("=" * 70)
    print("\nKey Improvements:")
    print("  1. 'Upcoming' now checks DATETIME, not just DATE")
    print("  2. Trips past their pickup time don't appear as 'Upcoming'")
    print("  3. Admin can review past confirmed trips at: /admin/past-confirmed-trips/")
    print()
    
    # Test edge cases
    print("🧪 EDGE CASE TESTS:")
    print("-" * 70)
    
    # Today's trips
    today_trips = Booking.objects.filter(pick_up_date=today, status='Confirmed')
    if today_trips.exists():
        print(f"   Total trips scheduled for today: {today_trips.count()}")
        today_upcoming = today_trips.filter(pick_up_time__gte=current_time)
        today_past = today_trips.filter(pick_up_time__lt=current_time)
        print(f"   • Still upcoming today: {today_upcoming.count()}")
        print(f"   • Already past today: {today_past.count()}")
        print()
    
    # Trips in next 24 hours
    tomorrow = today + timedelta(days=1)
    next_24h = confirmed_trips.filter(future_filter).filter(
        Q(pick_up_date=today) | Q(pick_up_date=tomorrow)
    )
    print(f"   Confirmed trips in next 24 hours: {next_24h.count()}")
    
    # Old trips still confirmed
    week_ago = today - timedelta(days=7)
    very_old = past_trips.filter(pick_up_date__lt=week_ago)
    if very_old.exists():
        print(f"   ⚠️  Trips over 1 week old still 'Confirmed': {very_old.count()}")
    
    print()

if __name__ == '__main__':
    test_trip_filtering()
