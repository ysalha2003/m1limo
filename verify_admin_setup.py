"""
Verify Admin Recipient Configuration
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from models import NotificationRecipient

admin_email = "yaser.salha.us@gmail.com"

print("=" * 70)
print("ADMIN RECIPIENT VERIFICATION")
print("=" * 70)

try:
    admin = NotificationRecipient.objects.get(email=admin_email)
    
    print(f"\n✅ Admin Found: {admin.name}")
    print(f"   Email: {admin.email}")
    print(f"   Active: {admin.is_active}")
    print(f"\n📧 Notification Preferences:")
    print(f"   - notify_new: {admin.notify_new}")
    print(f"   - notify_confirmed: {admin.notify_confirmed}")
    print(f"   - notify_cancelled: {admin.notify_cancelled}")
    print(f"   - notify_status_changes: {admin.notify_status_changes}")
    print(f"   - notify_reminders: {admin.notify_reminders}")
    
    # Test what would happen for a status_change event
    print(f"\n🧪 TEST: Would receive status_change notification?")
    if admin.is_active and admin.notify_status_changes:
        print(f"   ✅ YES - Admin would receive status_change notifications")
    else:
        if not admin.is_active:
            print(f"   ❌ NO - Admin is not active")
        if not admin.notify_status_changes:
            print(f"   ❌ NO - notify_status_changes is disabled")
    
    # Show what _get_admin_recipients would return
    from notification_service import NotificationService
    from models import Booking
    
    print(f"\n🔍 Testing _get_admin_recipients() method:")
    
    # Get a sample booking
    booking = Booking.objects.first()
    if booking:
        for event in ['new', 'confirmed', 'cancelled', 'status_change']:
            recipients = NotificationService._get_admin_recipients(booking, event)
            print(f"   Event '{event}': {len(recipients)} recipients")
            if recipients:
                for r in recipients:
                    print(f"      - {r}")
    
except NotificationRecipient.DoesNotExist:
    print(f"\n❌ Admin recipient not found: {admin_email}")

print("\n" + "=" * 70)
