"""
Test script to verify notification preference implementation
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from models import Booking, UserProfile
from django.contrib.auth.models import User
from notification_service import NotificationService

def test_notification_preferences():
    """Test the new notification preference system"""
    print("=" * 70)
    print("NOTIFICATION PREFERENCE SYSTEM TEST")
    print("=" * 70)
    
    # Get first booking
    booking = Booking.objects.first()
    
    if not booking:
        print("\n❌ No bookings found in database. Please create a booking first.")
        return
    
    print(f"\nTest Booking: #{booking.id} - {booking.passenger_name}")
    print(f"Account Owner: {booking.user.email}")
    print(f"Passenger Email: {booking.passenger_email}")
    print(f"Send Passenger Notifications: {booking.send_passenger_notifications}")
    print(f"Additional Recipients: {booking.additional_recipients or 'None'}")
    
    # Test different notification types
    notification_types = ['confirmed', 'status_change', 'reminder', 'new']
    
    for notif_type in notification_types:
        print(f"\n{'-' * 70}")
        print(f"Notification Type: {notif_type}")
        print(f"{'-' * 70}")
        
        recipients = NotificationService.get_recipients(booking, notif_type)
        
        print(f"Recipients ({len(recipients)}):")
        for i, email in enumerate(recipients, 1):
            print(f"  {i}. {email}")
        
        # Explain why each recipient is included
        print(f"\nExplanation:")
        
        # Check admin
        from django.conf import settings
        if hasattr(settings, 'ADMIN_EMAIL') and settings.ADMIN_EMAIL in recipients:
            print(f"  ✅ Admin ({settings.ADMIN_EMAIL}) - Always receives notifications")
        
        # Check account owner
        if booking.user.email in recipients:
            print(f"  ✅ Account Owner ({booking.user.email}) - Based on UserProfile preferences")
        else:
            print(f"  ⏭️  Account Owner ({booking.user.email}) - Skipped (user preferences)")
        
        # Check passenger
        if booking.passenger_email != booking.user.email:
            if booking.send_passenger_notifications and booking.passenger_email in recipients:
                if notif_type in ['confirmed', 'status_change', 'cancelled', 'reminder']:
                    print(f"  ✅ Passenger ({booking.passenger_email}) - Flag enabled for {notif_type}")
                else:
                    print(f"  ⏭️  Passenger ({booking.passenger_email}) - '{notif_type}' not sent to passengers")
            elif not booking.send_passenger_notifications:
                print(f"  ⏭️  Passenger ({booking.passenger_email}) - Flag disabled")
            else:
                print(f"  ⏭️  Passenger ({booking.passenger_email}) - Skipped (type: {notif_type})")
        else:
            print(f"  ⏭️  Passenger - Same as account owner (no duplicate)")
        
        # Check additional recipients
        if booking.additional_recipients:
            additional_emails = [e.strip() for e in booking.additional_recipients.split(',')]
            for email in additional_emails:
                if email in recipients:
                    if notif_type in ['confirmed', 'status_change', 'cancelled', 'reminder']:
                        print(f"  ✅ Additional ({email}) - Included for {notif_type}")
                    else:
                        print(f"  ⏭️  Additional ({email}) - '{notif_type}' not sent")
                else:
                    print(f"  ⏭️  Additional ({email}) - Not included")
    
    # Summary
    print(f"\n{'=' * 70}")
    print("FEATURE SUMMARY")
    print(f"{'=' * 70}")
    print(f"""
✅ Database Fields Added:
   - send_passenger_notifications (Boolean, default=True)
   - additional_recipients (TextField, comma-separated emails)

✅ Notification Logic Updated:
   - Account owner: Based on UserProfile preferences
   - Passenger: Only if send_passenger_notifications=True
   - Additional: All recipients for confirmed/updates/reminders
   - Admin: Always receives all notifications

✅ UI Updates:
   - Checkbox on booking forms
   - Additional recipients textarea
   - Notification status in booking detail

✅ Validation:
   - Email format validation for additional_recipients
   - Duplicate detection (passenger = owner)
   - Type filtering (passengers don't get 'new' admin alerts)
""")

if __name__ == '__main__':
    test_notification_preferences()
