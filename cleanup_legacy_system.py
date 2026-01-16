"""
Complete System Cleanup - Remove All Legacy Templates
Removes database records, file-based templates, and cleans up code
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from models import EmailTemplate

def cleanup_database_templates():
    """Delete all legacy EmailTemplate records."""
    legacy_types = [
        'booking_new',
        'booking_confirmed',
        'booking_cancelled',
        'booking_status_change',
        'round_trip_new',
        'round_trip_confirmed',
        'round_trip_cancelled',
        'round_trip_status_change',
        'booking_reminder',
        'driver_notification',
        'driver_rejection',
        'driver_completion'
    ]
    
    print("=" * 70)
    print("STEP 1: Cleaning up legacy database templates")
    print("=" * 70)
    
    deleted_count = 0
    for template_type in legacy_types:
        templates = EmailTemplate.objects.filter(template_type=template_type)
        count = templates.count()
        if count > 0:
            # Get info before deleting
            for t in templates:
                print(f"  Deleting: {t.name} (ID: {t.id}, Type: {t.template_type})")
                print(f"    Stats: {t.total_sent} sent, {t.total_failed} failed")
            templates.delete()
            deleted_count += count
    
    print(f"\n✅ Deleted {deleted_count} legacy database templates")
    
    # Show remaining templates (should only be unified ones)
    remaining = EmailTemplate.objects.all()
    print(f"\n✅ Remaining templates: {remaining.count()}")
    for t in remaining:
        print(f"  - {t.name} (Type: {t.template_type}, Active: {t.is_active})")

def list_files_to_delete():
    """List all file-based templates and temporary files to delete."""
    print("\n" + "=" * 70)
    print("STEP 2: Files to be deleted")
    print("=" * 70)
    
    # File-based email templates
    email_templates = [
        'templates/emails/booking_notification.html',
        'templates/emails/booking_reminder.html',
        'templates/emails/driver_notification.html',
        'templates/emails/round_trip_notification.html'
    ]
    
    # Temporary analysis/test files
    temp_files = [
        'analyze_notification_system.py',
        'create_unified_customer_template.py',
        'create_all_unified_templates.py',
        'test_unified_template.py',
        'test_unified_email.py',
        'unified_template_sample.html',
        'FILE_BASED_TEMPLATES_INVENTORY.md',
        'UNIFIED_NOTIFICATION_PROPOSAL.md',
        'UNIFIED_TEMPLATE_PROGRESS.md',
        'show_summary.py',
        'show_templates.py',
        'test_email_rendering.py'
    ]
    
    print("\nFile-based email templates (4 files):")
    for f in email_templates:
        path = os.path.join('c:\\m1\\m1limo', f)
        exists = "✓ EXISTS" if os.path.exists(path) else "✗ NOT FOUND"
        print(f"  {exists} - {f}")
    
    print("\nTemporary analysis/test files (12 files):")
    for f in temp_files:
        path = os.path.join('c:\\m1\\m1limo', f)
        exists = "✓ EXISTS" if os.path.exists(path) else "✗ NOT FOUND"
        print(f"  {exists} - {f}")
    
    print("\n⚠️  These files will be deleted by the cleanup script.")

def delete_files():
    """Delete all file-based templates and temporary files."""
    print("\n" + "=" * 70)
    print("STEP 3: Deleting files")
    print("=" * 70)
    
    base_path = 'c:\\m1\\m1limo'
    
    # File-based email templates
    email_templates = [
        'templates\\emails\\booking_notification.html',
        'templates\\emails\\booking_reminder.html',
        'templates\\emails\\driver_notification.html',
        'templates\\emails\\round_trip_notification.html'
    ]
    
    # Temporary analysis/test files
    temp_files = [
        'analyze_notification_system.py',
        'create_unified_customer_template.py',
        'create_all_unified_templates.py',
        'test_unified_template.py',
        'test_unified_email.py',
        'test_unified_system.py',
        'unified_template_sample.html',
        'FILE_BASED_TEMPLATES_INVENTORY.md',
        'UNIFIED_NOTIFICATION_PROPOSAL.md',
        'UNIFIED_TEMPLATE_PROGRESS.md',
        'show_summary.py',
        'show_templates.py',
        'test_email_rendering.py'
    ]
    
    deleted = 0
    not_found = 0
    
    print("\nDeleting file-based email templates...")
    for f in email_templates:
        path = os.path.join(base_path, f)
        if os.path.exists(path):
            os.remove(path)
            print(f"  ✅ Deleted: {f}")
            deleted += 1
        else:
            print(f"  ⚠️  Not found: {f}")
            not_found += 1
    
    print("\nDeleting temporary analysis/test files...")
    for f in temp_files:
        path = os.path.join(base_path, f)
        if os.path.exists(path):
            os.remove(path)
            print(f"  ✅ Deleted: {f}")
            deleted += 1
        else:
            print(f"  ⚠️  Not found: {f}")
            not_found += 1
    
    print(f"\n✅ Total files deleted: {deleted}")
    print(f"⚠️  Files not found: {not_found}")

def show_code_cleanup_needed():
    """Show what code needs to be cleaned up."""
    print("\n" + "=" * 70)
    print("STEP 4: Code cleanup needed (manual)")
    print("=" * 70)
    
    print("\nemail_service.py - Methods to remove:")
    print("  1. send_booking_notification() - Legacy method (Lines 70-190)")
    print("  2. send_round_trip_notification() - Legacy method (Lines 192-480)")
    print("  3. send_driver_notification() - Legacy method (Lines 482-780)")
    print("  4. _get_template_name() - File template helper (Lines 564-570)")
    print("  5. _get_fallback_message() - Hardcoded HTML helper (Lines 572-592)")
    print("  6. _get_fallback_round_trip_message() - Hardcoded HTML (Lines 533-562)")
    print("  7. All _build_*_context() methods for legacy templates")
    
    print("\nnotification_service.py - Methods to remove:")
    print("  1. send_notification() - Legacy orchestration (Lines ~50-200)")
    print("  2. send_round_trip_notification() - Legacy round trip (Lines ~202-350)")
    print("  3. send_driver_notification() - Legacy driver (Lines ~352-450)")
    print("  4. send_driver_rejection_notification() - Replaced by unified")
    print("  5. send_driver_completion_notification() - Replaced by unified")
    
    print("\n⚠️  These will be removed in the next step to keep only unified methods.")

if __name__ == '__main__':
    print("🧹 M1Limo Legacy System Cleanup")
    print("=" * 70)
    print("This script will:")
    print("  1. Delete 12 legacy EmailTemplate database records")
    print("  2. Delete 4 file-based email templates")
    print("  3. Delete 12+ temporary analysis/test files")
    print("  4. Show code that needs manual cleanup")
    print("=" * 70)
    
    response = input("\n⚠️  This is PERMANENT. Continue? (yes/no): ")
    if response.lower() != 'yes':
        print("❌ Cleanup cancelled.")
        exit(0)
    
    # Execute cleanup
    cleanup_database_templates()
    list_files_to_delete()
    delete_files()
    show_code_cleanup_needed()
    
    print("\n" + "=" * 70)
    print("✅ CLEANUP COMPLETE!")
    print("=" * 70)
    print("\nNext steps:")
    print("  1. Review email_service.py and remove legacy methods")
    print("  2. Review notification_service.py and remove legacy methods")
    print("  3. Test unified system to ensure everything still works")
    print("  4. Deploy to production")
