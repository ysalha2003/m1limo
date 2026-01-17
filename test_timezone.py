"""
Test timezone handling in the application
This script checks timezone configuration and data consistency
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from django.utils import timezone
from django.conf import settings
from models import Booking
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

print("=" * 80)
print("TIMEZONE CONFIGURATION TEST")
print("=" * 80)

# 1. Check Django Settings
print("\n1. DJANGO TIMEZONE SETTINGS:")
print(f"   TIME_ZONE: {settings.TIME_ZONE}")
print(f"   USE_TZ: {settings.USE_TZ}")

# 2. Check current time in different zones
print("\n2. CURRENT TIME COMPARISON:")
utc_now = timezone.now()
chicago_tz = ZoneInfo('America/Chicago')
chicago_now = utc_now.astimezone(chicago_tz)

print(f"   UTC Time:     {utc_now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
print(f"   Chicago Time: {chicago_now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
print(f"   Offset:       {chicago_now.strftime('%z')}")

# 3. Check database bookings
print("\n3. DATABASE BOOKINGS CHECK:")
print("   Checking upcoming bookings with timezone info...")

upcoming_bookings = Booking.objects.filter(
    pick_up_date__gte=timezone.now().date() - timedelta(days=1)
).order_by('pick_up_date', 'pick_up_time')[:5]

if upcoming_bookings.exists():
    for booking in upcoming_bookings:
        print(f"\n   Booking ID: {booking.id}")
        print(f"   Pick-up Date: {booking.pick_up_date}")
        print(f"   Pick-up Time: {booking.pick_up_time}")
        
        # Combine date and time
        pickup_datetime = datetime.combine(booking.pick_up_date, booking.pick_up_time)
        
        # Check if naive
        print(f"   Is Naive: {timezone.is_naive(pickup_datetime)}")
        
        # Make timezone aware
        if timezone.is_naive(pickup_datetime):
            pickup_datetime = timezone.make_aware(pickup_datetime)
        
        # Convert to Chicago time
        pickup_chicago = pickup_datetime.astimezone(chicago_tz)
        
        print(f"   Pickup DateTime (aware): {pickup_datetime.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"   Pickup Chicago: {pickup_chicago.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        
        # Calculate time until pickup
        time_until = pickup_datetime - utc_now
        hours_until = time_until.total_seconds() / 3600
        
        print(f"   Hours Until Pickup: {hours_until:.2f}")
        print(f"   Status: {booking.status}")
else:
    print("   No upcoming bookings found.")

# 4. Test format_time_until_pickup filter
print("\n4. TESTING format_time_until_pickup FILTER:")
from templatetags.booking_filters import format_time_until_pickup

if upcoming_bookings.exists():
    test_booking = upcoming_bookings.first()
    result = format_time_until_pickup(test_booking)
    print(f"   Booking ID: {test_booking.id}")
    print(f"   Filter Result: {result}")
    if result:
        print(f"   - Days: {result.get('days')}")
        print(f"   - Hours: {result.get('hours')}")
        print(f"   - Minutes: {result.get('minutes')}")
        print(f"   - Total Hours: {result.get('total_hours')}")
else:
    print("   No bookings to test.")

# 5. Test JavaScript countdown compatibility
print("\n5. JAVASCRIPT COUNTDOWN DATA:")
if upcoming_bookings.exists():
    test_booking = upcoming_bookings.first()
    date_str = test_booking.pick_up_date.strftime('%Y-%m-%d')
    time_str = test_booking.pick_up_time.strftime('%H:%M:%S')
    print(f"   data-pickup-date: {date_str}")
    print(f"   data-pickup-time: {time_str}")
    
    # Test what JavaScript would receive
    combined_str = f"{date_str}T{time_str}"
    print(f"   Combined (ISO-ish): {combined_str}")
    
    # What timezone does JS use?
    print("\n   JavaScript Considerations:")
    print("   - JS Date() uses browser's local timezone")
    print("   - Need to specify Chicago timezone explicitly")
    print("   - Recommendation: Use moment-timezone.js or similar")

# 6. Recommendations
print("\n" + "=" * 80)
print("RECOMMENDATIONS:")
print("=" * 80)
print("""
1. ✓ Django TIME_ZONE is correctly set to 'America/Chicago'
2. ✓ USE_TZ=True ensures timezone-aware datetimes

3. VERIFY: All datetime operations should use timezone.now() not datetime.now()
4. VERIFY: Frontend JavaScript needs Chicago timezone awareness
5. VERIFY: User inputs should be interpreted as Chicago time

FRONTEND FIX NEEDED:
- JavaScript countdown must account for Chicago timezone
- Use ISO format with timezone: YYYY-MM-DDTHH:MM:SS-06:00 (or -05:00 for DST)
- Or use library like moment-timezone.js with 'America/Chicago'
""")

print("\nTest completed!")
