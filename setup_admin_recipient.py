"""
Setup Admin Recipient for Notifications
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from models import NotificationRecipient

# Check existing recipients
existing = NotificationRecipient.objects.all()
print("=" * 70)
print("CURRENT NOTIFICATION RECIPIENTS")
print("=" * 70)

if existing.exists():
    for recipient in existing:
        print(f"\n  Name: {recipient.name}")
        print(f"  Email: {recipient.email}")
        print(f"  Active: {recipient.is_active}")
        print(f"  Preferences:")
        print(f"    - New bookings: {recipient.notify_new}")
        print(f"    - Confirmed: {recipient.notify_confirmed}")
        print(f"    - Cancelled: {recipient.notify_cancelled}")
        print(f"    - Status changes: {getattr(recipient, 'notify_status_changes', True)}")
else:
    print("\n  ⚠️  No admin recipients configured!")

# Check if admin exists
admin_email = "yaser.salha.us@gmail.com"
admin_exists = NotificationRecipient.objects.filter(email=admin_email).exists()

print("\n" + "=" * 70)
print(f"ADMIN EMAIL: {admin_email}")
print("=" * 70)

if admin_exists:
    admin = NotificationRecipient.objects.get(email=admin_email)
    print(f"✅ Admin recipient exists")
    print(f"   Active: {admin.is_active}")
    print(f"   Preferences: New={admin.notify_new}, Confirmed={admin.notify_confirmed}, Cancelled={admin.notify_cancelled}")
else:
    print(f"❌ Admin recipient NOT configured")
    print("\nWould you like to add this admin? (yes/no): ", end="")
    response = input().strip().lower()
    
    if response == 'yes':
        NotificationRecipient.objects.create(
            name="Admin - Yaser Salha",
            email=admin_email,
            notify_new=True,
            notify_confirmed=True,
            notify_cancelled=True,
            is_active=True
        )
        print(f"✅ Admin recipient created: {admin_email}")
        print("   Preferences: All notifications enabled")
    else:
        print("❌ Admin not added")

print("\n" + "=" * 70)
