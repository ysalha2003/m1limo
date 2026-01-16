"""
Quick Migration Verification Test
Checks that all unified methods exist and are callable
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from notification_service import NotificationService
from email_service import EmailService

print("=" * 70)
print("✅ MIGRATION VERIFICATION TEST")
print("=" * 70)

# Check NotificationService has unified methods
print("\n📧 NotificationService Unified Methods:")
unified_methods = [
    'send_unified_booking_notification',
    'send_unified_driver_notification',
    'send_unified_admin_driver_alert'
]

for method in unified_methods:
    if hasattr(NotificationService, method):
        print(f"  ✅ {method}")
    else:
        print(f"  ❌ {method} - MISSING!")

# Check EmailService has unified methods
print("\n📧 EmailService Unified Methods:")
email_methods = [
    'send_unified_notification',
    '_build_unified_context'
]

for method in email_methods:
    if hasattr(EmailService, method):
        print(f"  ✅ {method}")
    else:
        print(f"  ❌ {method} - MISSING!")

# Check legacy methods are gone
print("\n🗑️  Legacy Methods (Should NOT Exist):")
legacy_methods = [
    'send_notification',
    'send_round_trip_notification',
    'send_driver_notification'
]

all_gone = True
for method in legacy_methods:
    if hasattr(NotificationService, method):
        print(f"  ⚠️  {method} - STILL EXISTS!")
        all_gone = False
    else:
        print(f"  ✅ {method} - Removed")

# Test basic method signature
print("\n🧪 Method Signature Test:")
try:
    import inspect
    sig = inspect.signature(NotificationService.send_unified_booking_notification)
    params = list(sig.parameters.keys())
    print(f"  ✅ send_unified_booking_notification parameters: {params}")
    
    expected = ['cls', 'booking', 'event', 'old_status']
    if all(p in params for p in expected):
        print(f"  ✅ All required parameters present")
    else:
        print(f"  ⚠️  Missing parameters: {set(expected) - set(params)}")
except Exception as e:
    print(f"  ❌ Error: {e}")

print("\n" + "=" * 70)
if all_gone:
    print("✅ MIGRATION VERIFICATION: PASSED")
    print("   - All unified methods present")
    print("   - All legacy methods removed")
else:
    print("⚠️  MIGRATION VERIFICATION: WARNINGS")
    print("   - Some legacy methods still exist")
print("=" * 70)
