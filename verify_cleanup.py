"""
Verification Script - System Cleanup Status
Shows the current state of the unified notification system
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from models import EmailTemplate

print("=" * 70)
print("✅ M1LIMO UNIFIED NOTIFICATION SYSTEM - VERIFICATION")
print("=" * 70)

# Check active templates
print("\n📧 ACTIVE EMAIL TEMPLATES:")
print("-" * 70)

templates = EmailTemplate.objects.filter(is_active=True).order_by('template_type')
for t in templates:
    print(f"  ✅ {t.template_type.upper()}")
    print(f"     Name: {t.name}")
    print(f"     Stats: {t.total_sent} sent, {t.total_failed} failed")
    if t.total_sent + t.total_failed > 0:
        success_rate = (t.total_sent / (t.total_sent + t.total_failed)) * 100
        print(f"     Success Rate: {success_rate:.1f}%")
    print()

# Check for legacy templates
legacy_count = EmailTemplate.objects.filter(is_active=False).count()
legacy_types = [
    'booking_new', 'booking_confirmed', 'booking_cancelled', 'booking_status_change',
    'round_trip_new', 'round_trip_confirmed', 'round_trip_cancelled', 'round_trip_status_change',
    'booking_reminder', 'driver_notification', 'driver_rejection', 'driver_completion'
]

remaining_legacy = EmailTemplate.objects.filter(template_type__in=legacy_types)

print("\n🗑️  LEGACY TEMPLATES:")
print("-" * 70)
if remaining_legacy.exists():
    print(f"  ⚠️  WARNING: {remaining_legacy.count()} legacy templates still exist")
    for t in remaining_legacy:
        print(f"     - {t.name} (Type: {t.template_type})")
else:
    print("  ✅ All legacy templates deleted")

# Check file-based templates
print("\n📁 FILE-BASED TEMPLATES:")
print("-" * 70)

email_template_dir = os.path.join('templates', 'emails')
if os.path.exists(email_template_dir):
    files = [f for f in os.listdir(email_template_dir) if f.endswith('.html')]
    if files:
        print(f"  ⚠️  WARNING: {len(files)} template files found:")
        for f in files:
            print(f"     - {f}")
    else:
        print("  ✅ No file-based templates (directory empty)")
else:
    print("  ✅ Templates directory doesn't exist")

# Check code files
print("\n📝 CODE FILE SIZES:")
print("-" * 70)

files_to_check = ['email_service.py', 'notification_service.py']
for filename in files_to_check:
    if os.path.exists(filename):
        size = os.path.getsize(filename)
        lines = len(open(filename, 'r', encoding='utf-8').readlines())
        print(f"  ✅ {filename}: {lines} lines ({size:,} bytes)")
    else:
        print(f"  ❌ {filename}: NOT FOUND")

# Summary
print("\n" + "=" * 70)
print("📊 SYSTEM STATUS SUMMARY")
print("=" * 70)

active_count = templates.count()
total_sent = sum(t.total_sent for t in templates)
total_failed = sum(t.total_failed for t in templates)

print(f"\n  Active Templates: {active_count}")
print(f"  Legacy Templates: {remaining_legacy.count()}")
print(f"  Total Emails Sent: {total_sent}")
print(f"  Total Emails Failed: {total_failed}")

if total_sent + total_failed > 0:
    overall_success = (total_sent / (total_sent + total_failed)) * 100
    print(f"  Overall Success Rate: {overall_success:.1f}%")

print("\n" + "=" * 70)
if active_count == 5 and remaining_legacy.count() == 0 and not files:
    print("✅ SYSTEM STATUS: CLEAN - 100% UNIFIED TEMPLATE SYSTEM")
else:
    print("⚠️  SYSTEM STATUS: NEEDS ATTENTION")
print("=" * 70)
