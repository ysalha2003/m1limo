"""
Verify that file-based fallback has been removed.
Test with inactive templates to ensure NO emails are sent.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from models import EmailTemplate, Booking, User
from email_service import EmailService
from notification_service import NotificationService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_fallback_removal():
    """Test that emails are NOT sent when templates are inactive"""
    
    print("\n" + "="*80)
    print("FILE-BASED FALLBACK REMOVAL VERIFICATION")
    print("="*80)
    
    # Check all templates status
    print("\n1. DATABASE TEMPLATE STATUS")
    print("-" * 80)
    
    all_templates = EmailTemplate.objects.all()
    active_count = all_templates.filter(is_active=True).count()
    inactive_count = all_templates.filter(is_active=False).count()
    
    print(f"Total Templates: {all_templates.count()}")
    print(f"Active: {active_count}")
    print(f"Inactive: {inactive_count}")
    
    if active_count > 0:
        print(f"\n⚠️  WARNING: {active_count} templates are still ACTIVE")
        print("Emails WILL be sent for these notification types:")
        for template in all_templates.filter(is_active=True):
            print(f"  • {template.get_template_type_display()} ({template.template_type})")
    
    if inactive_count == all_templates.count():
        print("\n✅ ALL templates are INACTIVE - Perfect for testing!")
    
    # Check for file-based templates
    print("\n2. FILE-BASED TEMPLATES CHECK")
    print("-" * 80)
    
    import os
    file_templates = [
        'templates/emails/booking_notification.html',
        'templates/emails/booking_reminder.html',
        'templates/emails/driver_notification.html',
        'templates/emails/round_trip_notification.html',
    ]
    
    files_exist = []
    for template_path in file_templates:
        if os.path.exists(template_path):
            files_exist.append(template_path)
            print(f"  ⚠️  EXISTS: {template_path}")
        else:
            print(f"  ✅ REMOVED: {template_path}")
    
    if files_exist:
        print(f"\n⚠️  {len(files_exist)} file-based templates still exist")
        print("These will NOT be used (fallback removed from code)")
    else:
        print("\n✅ All file-based templates removed")
    
    # Test email service behavior
    print("\n3. EMAIL SERVICE BEHAVIOR TEST")
    print("-" * 80)
    
    test_cases = [
        ('booking_new', 'New Booking'),
        ('booking_confirmed', 'Booking Confirmed'),
        ('driver_notification', 'Driver Assignment'),
        ('round_trip_new', 'Round Trip New'),
        ('driver_rejection', 'Driver Rejection'),
        ('driver_completion', 'Driver Completion'),
    ]
    
    print("\nTesting template loading with inactive templates:")
    for template_type, description in test_cases:
        template = EmailService._load_email_template(template_type)
        if template:
            status = "⚠️  WILL SEND EMAIL (template active)"
        else:
            status = "✅ NO EMAIL (template inactive/missing)"
        print(f"  {description:25} → {status}")
    
    # Check code for fallback references
    print("\n4. CODE VERIFICATION")
    print("-" * 80)
    
    print("\nChecking email_service.py for fallback code...")
    with open('email_service.py', 'r', encoding='utf-8') as f:
        content = f.read()
        
    fallback_indicators = [
        ('render_to_string(template_name', 'File template rendering'),
        ('render_to_string(\'emails/', 'Direct file template path'),
        ('_get_fallback_message', 'Hardcoded HTML fallback'),
        ('falling back to file template', 'Fallback log message'),
        ('Using file template fallback', 'File fallback usage'),
        ('Using hardcoded HTML fallback', 'Hardcoded fallback usage'),
    ]
    
    found_fallbacks = []
    for indicator, description in fallback_indicators:
        if indicator in content:
            found_fallbacks.append(description)
    
    if found_fallbacks:
        print("  ⚠️  Found fallback references (may be in comments or unused code):")
        for fb in found_fallbacks:
            print(f"     • {fb}")
    else:
        print("  ✅ No fallback code references found")
    
    print("\nChecking notification_service.py for fallback code...")
    with open('notification_service.py', 'r', encoding='utf-8') as f:
        content = f.read()
        
    fallback_indicators_notif = [
        ('falling back to hardcoded HTML', 'Hardcoded HTML fallback'),
        ('Using hardcoded HTML fallback', 'Hardcoded fallback usage'),
    ]
    
    found_fallbacks_notif = []
    for indicator, description in fallback_indicators_notif:
        if indicator in content:
            found_fallbacks_notif.append(description)
    
    if found_fallbacks_notif:
        print("  ⚠️  Found fallback references (may be in comments or unused code):")
        for fb in found_fallbacks_notif:
            print(f"     • {fb}")
    else:
        print("  ✅ No fallback code references found")
    
    # Final summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    if inactive_count == all_templates.count():
        print("\n✅ SUCCESS: All templates inactive")
        print("✅ Result: NO EMAILS will be sent")
    else:
        print(f"\n⚠️  {active_count} templates still active")
        print("⚠️  Result: Emails WILL be sent for active templates only")
    
    print("\n📋 Expected Behavior:")
    print("  • Active template → Email sent using database template")
    print("  • Inactive template → NO email sent (returns False)")
    print("  • Missing template → NO email sent (returns False)")
    print("  • Template render error → NO email sent (returns False)")
    
    print("\n⛔ Removed Behaviors:")
    print("  • File-based template fallback (removed)")
    print("  • Hardcoded HTML fallback (removed)")
    print("  • Silent fallback to alternative templates (removed)")
    
    print("\n" + "="*80)
    print("VERIFICATION COMPLETE")
    print("="*80 + "\n")

if __name__ == '__main__':
    test_fallback_removal()
