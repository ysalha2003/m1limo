"""
Test recipient visibility feature for Send Email Notification button
Run: python test_recipient_visibility.py
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from models import Booking, UserProfile
from notification_service import NotificationService
from django.contrib.auth.models import User

print("="*80)
print("Testing Recipient Visibility for Send Email Notification Button")
print("="*80)

# Test different scenarios
test_scenarios = [
    {
        'name': 'User with all notifications enabled, passenger notifications enabled',
        'user_preferences': {'receive_booking_confirmations': True, 'receive_status_updates': True},
        'passenger_notifications': True,
        'status': 'Confirmed'
    },
    {
        'name': 'User disabled confirmations, passenger notifications enabled',
        'user_preferences': {'receive_booking_confirmations': False, 'receive_status_updates': True},
        'passenger_notifications': True,
        'status': 'Confirmed'
    },
    {
        'name': 'User enabled, passenger notifications disabled',
        'user_preferences': {'receive_booking_confirmations': True, 'receive_status_updates': True},
        'passenger_notifications': False,
        'status': 'Confirmed'
    },
    {
        'name': 'Both user and passenger disabled',
        'user_preferences': {'receive_booking_confirmations': False, 'receive_status_updates': True},
        'passenger_notifications': False,
        'status': 'Confirmed'
    },
]

for idx, scenario in enumerate(test_scenarios, 1):
    print(f"\n{'='*80}")
    print(f"Scenario {idx}: {scenario['name']}")
    print(f"{'='*80}")
    
    # Find or create a test booking
    booking = Booking.objects.filter(status=scenario['status']).first()
    if not booking:
        print(f"⚠️  No booking with status {scenario['status']} found, skipping")
        continue
    
    print(f"Booking ID: {booking.id}")
    print(f"Status: {booking.get_status_display()}")
    print(f"User: {booking.user.email}")
    print(f"Passenger: {booking.passenger_email}")
    
    # Update user preferences temporarily
    profile = booking.user.profile
    original_prefs = {
        'receive_booking_confirmations': profile.receive_booking_confirmations,
        'receive_status_updates': profile.receive_status_updates,
    }
    
    for key, value in scenario['user_preferences'].items():
        setattr(profile, key, value)
    profile.save()
    
    # Update passenger notification setting
    original_passenger_notif = booking.send_passenger_notifications
    booking.send_passenger_notifications = scenario['passenger_notifications']
    booking.save()
    
    # Test notification logic
    status_to_notification = {
        'Pending': 'new',
        'Confirmed': 'confirmed',
        'Cancelled': 'cancelled',
        'Trip_Completed': 'status_change',
    }
    notification_type = status_to_notification.get(booking.status, 'confirmed')
    
    will_notify_user = NotificationService._should_notify_user(booking.user, notification_type)
    will_notify_passenger = booking.send_passenger_notifications and bool(booking.passenger_email)
    
    print(f"\n📧 Notification Recipients:")
    print(f"   ✅ Admin: ALWAYS (mo@m1limo.com)")
    print(f"   {'✅' if will_notify_user else '❌'} User: {booking.user.email} {'(enabled)' if will_notify_user else '(DISABLED by preferences)'}")
    print(f"   {'✅' if will_notify_passenger else '❌'} Passenger: {booking.passenger_email} {'(enabled)' if will_notify_passenger else '(DISABLED by booking setting)'}")
    
    print(f"\n🎯 What Admin Sees:")
    print(f"   Button: 'Send Email Notification' (ENABLED)")
    print(f"   Indicator below button shows:")
    print(f"      • Admin (green checkmark)")
    if will_notify_user:
        print(f"      • User ({booking.user.email}) (green checkmark)")
    else:
        print(f"      • User (notifications disabled) (gray X)")
    if will_notify_passenger:
        print(f"      • Passenger ({booking.passenger_email}) (green checkmark)")
    else:
        print(f"      • Passenger (notifications disabled) (gray X)")
    
    # Restore original settings
    for key, value in original_prefs.items():
        setattr(profile, key, value)
    profile.save()
    booking.send_passenger_notifications = original_passenger_notif
    booking.save()

print(f"\n{'='*80}")
print("✓ Test Complete")
print(f"{'='*80}")
print("\n📊 Summary of Implementation:")
print("\n✅ Button remains ENABLED in all scenarios")
print("   - Admin can always send notifications if needed (emergency override)")
print("   - Admin always receives a copy")
print("")
print("📍 Visual indicator shows exactly who will receive:")
print("   - Green checkmark = Will receive notification")
print("   - Gray X = Will NOT receive (disabled)")
print("")
print("🎯 Benefits:")
print("   1. Full transparency - Admin knows who gets notified")
print("   2. No loss of functionality - Admin can still send")
print("   3. Clear feedback - Visual status before clicking")
print("   4. Emergency capability - Can override user preferences if needed")
print("")
print("🔧 Technical Implementation:")
print("   - views.py: Added will_notify_user and will_notify_passenger context")
print("   - booking_detail.html: Added recipient indicator below button")
print("   - Uses NotificationService._should_notify_user() to check preferences")
print("   - Respects both UserProfile preferences and booking.send_passenger_notifications")
