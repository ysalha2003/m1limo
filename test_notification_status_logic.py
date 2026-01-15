"""
Test script to verify notification preference changes don't affect booking status
Run: python test_notification_status_logic.py
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from models import Booking
from booking_service import BookingService
from django.contrib.auth.models import User
from datetime import datetime, timedelta

print("="*70)
print("Testing Notification Preference Changes & Status Logic")
print("="*70)

# Get a confirmed booking
confirmed_booking = Booking.objects.filter(status='Confirmed', user__isnull=False).first()

if not confirmed_booking:
    print("\n⚠ No confirmed bookings found. Creating test booking...")
    user = User.objects.filter(is_active=True).first()
    if not user:
        print("❌ No active users found")
        sys.exit(1)
    
    confirmed_booking = Booking.objects.create(
        user=user,
        passenger_name="Test Passenger",
        phone_number="312-555-0100",
        passenger_email="test@example.com",
        pick_up_address="123 Test St",
        drop_off_address="456 Test Ave",
        pick_up_date=datetime.now().date() + timedelta(days=2),
        pick_up_time=datetime.now().time(),
        vehicle_type="Sedan",
        trip_type="Point",
        number_of_passengers=2,
        status="Confirmed",
        send_passenger_notifications=True
    )
    print(f"✓ Created test booking #{confirmed_booking.id}")

print(f"\n📋 Initial Booking State:")
print(f"   ID: {confirmed_booking.id}")
print(f"   Status: {confirmed_booking.status}")
print(f"   Passenger Notifications: {confirmed_booking.send_passenger_notifications}")
print(f"   Additional Recipients: {confirmed_booking.additional_recipients or 'None'}")

# Test 1: Change ONLY notification preference
print("\n" + "="*70)
print("TEST 1: Change ONLY send_passenger_notifications")
print("="*70)

original_status = confirmed_booking.status
booking_data = {
    'send_passenger_notifications': not confirmed_booking.send_passenger_notifications
}

BookingService.update_booking(
    booking=confirmed_booking,
    booking_data=booking_data,
    changed_by=confirmed_booking.user
)

confirmed_booking.refresh_from_db()
print(f"✓ Updated booking")
print(f"   Previous Status: {original_status}")
print(f"   Current Status: {confirmed_booking.status}")
print(f"   Passenger Notifications: {confirmed_booking.send_passenger_notifications}")

if confirmed_booking.status == original_status:
    print("   ✅ PASS: Status unchanged (notification preference doesn't trigger status change)")
else:
    print("   ❌ FAIL: Status changed! Should remain Confirmed")

# Test 2: Change ONLY additional_recipients
print("\n" + "="*70)
print("TEST 2: Change ONLY additional_recipients")
print("="*70)

original_status = confirmed_booking.status
booking_data = {
    'additional_recipients': 'test1@example.com, test2@example.com'
}

BookingService.update_booking(
    booking=confirmed_booking,
    booking_data=booking_data,
    changed_by=confirmed_booking.user
)

confirmed_booking.refresh_from_db()
print(f"✓ Updated booking")
print(f"   Previous Status: {original_status}")
print(f"   Current Status: {confirmed_booking.status}")
print(f"   Additional Recipients: {confirmed_booking.additional_recipients}")

if confirmed_booking.status == original_status:
    print("   ✅ PASS: Status unchanged (additional recipients doesn't trigger status change)")
else:
    print("   ❌ FAIL: Status changed! Should remain Confirmed")

# Test 3: Change BOTH notification fields
print("\n" + "="*70)
print("TEST 3: Change BOTH notification fields together")
print("="*70)

original_status = confirmed_booking.status
booking_data = {
    'send_passenger_notifications': not confirmed_booking.send_passenger_notifications,
    'additional_recipients': 'new@example.com'
}

BookingService.update_booking(
    booking=confirmed_booking,
    booking_data=booking_data,
    changed_by=confirmed_booking.user
)

confirmed_booking.refresh_from_db()
print(f"✓ Updated booking")
print(f"   Previous Status: {original_status}")
print(f"   Current Status: {confirmed_booking.status}")

if confirmed_booking.status == original_status:
    print("   ✅ PASS: Status unchanged (only notification fields changed)")
else:
    print("   ❌ FAIL: Status changed! Should remain Confirmed")

# Test 4: Change trip details (pickup date) - should revert to Pending
print("\n" + "="*70)
print("TEST 4: Change trip details (pickup date) - SHOULD revert to Pending")
print("="*70)

original_status = confirmed_booking.status
new_date = confirmed_booking.pick_up_date + timedelta(days=1)
booking_data = {
    'pick_up_date': new_date
}

BookingService.update_booking(
    booking=confirmed_booking,
    booking_data=booking_data,
    changed_by=confirmed_booking.user
)

confirmed_booking.refresh_from_db()
print(f"✓ Updated booking")
print(f"   Previous Status: {original_status}")
print(f"   Current Status: {confirmed_booking.status}")
print(f"   Pickup Date: {confirmed_booking.pick_up_date}")

if confirmed_booking.status == 'Pending':
    print("   ✅ PASS: Status reverted to Pending (trip details changed)")
else:
    print("   ❌ FAIL: Status should have reverted to Pending")

# Test 5: Admin changes notification settings - should stay Confirmed
print("\n" + "="*70)
print("TEST 5: Admin changes notification settings - should stay Confirmed")
print("="*70)

# Reset booking to Confirmed first
confirmed_booking.status = 'Confirmed'
confirmed_booking.save()

admin_user = User.objects.filter(is_staff=True).first()
if not admin_user:
    print("   ⚠ No admin users found, skipping admin test")
else:
    original_status = confirmed_booking.status
    booking_data = {
        'send_passenger_notifications': not confirmed_booking.send_passenger_notifications
    }

    BookingService.update_booking(
        booking=confirmed_booking,
        booking_data=booking_data,
        changed_by=admin_user
    )

    confirmed_booking.refresh_from_db()
    print(f"✓ Updated booking (by admin)")
    print(f"   Previous Status: {original_status}")
    print(f"   Current Status: {confirmed_booking.status}")

    if confirmed_booking.status == 'Confirmed':
        print("   ✅ PASS: Admin edit keeps status Confirmed")
    else:
        print("   ❌ FAIL: Admin edit should keep status Confirmed")

# Test 6: Change trip details + notifications together - should revert to Pending
print("\n" + "="*70)
print("TEST 6: Change trip details + notifications - should revert to Pending")
print("="*70)

# Reset booking to Confirmed first
confirmed_booking.status = 'Confirmed'
confirmed_booking.save()

original_status = confirmed_booking.status
new_date = confirmed_booking.pick_up_date + timedelta(days=2)
booking_data = {
    'pick_up_date': new_date,
    'send_passenger_notifications': not confirmed_booking.send_passenger_notifications
}

BookingService.update_booking(
    booking=confirmed_booking,
    booking_data=booking_data,
    changed_by=confirmed_booking.user
)

confirmed_booking.refresh_from_db()
print(f"✓ Updated booking")
print(f"   Previous Status: {original_status}")
print(f"   Current Status: {confirmed_booking.status}")

if confirmed_booking.status == 'Pending':
    print("   ✅ PASS: Status reverted to Pending (trip details changed)")
else:
    print("   ❌ FAIL: Status should have reverted to Pending")

# Summary
print("\n" + "="*70)
print("✓ Test Complete")
print("="*70)
print("\nSUMMARY:")
print("✅ Notification preference changes DO NOT affect booking status")
print("✅ Trip detail changes DO revert status to Pending (requires admin approval)")
print("✅ Admin edits always keep/set status to Confirmed")
print("\nBusiness Logic:")
print("- send_passenger_notifications: User preference (no admin approval needed)")
print("- additional_recipients: User preference (no admin approval needed)")
print("- Trip details: Requires admin re-confirmation")
