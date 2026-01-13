"""
Quick diagnostic script to check Email Template system status
Run this on the server to diagnose 500 errors
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

print("="*70)
print("EMAIL TEMPLATE SYSTEM DIAGNOSTIC")
print("="*70)

# Check 1: Can we import the model?
print("\n1. Checking EmailTemplate model import...")
try:
    from models import EmailTemplate
    print("   ✓ EmailTemplate model imports successfully")
except Exception as e:
    print(f"   ✗ ERROR importing EmailTemplate: {e}")
    exit(1)

# Check 2: Does the table exist?
print("\n2. Checking if bookings_emailtemplate table exists...")
try:
    from django.db import connection
    cursor = connection.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='bookings_emailtemplate'")
    result = cursor.fetchone()
    if result:
        print(f"   ✓ Table exists: {result[0]}")
    else:
        print("   ✗ Table does NOT exist - need to create it!")
        print("\n   ACTION REQUIRED:")
        print("   Run on server: python create_email_template_table.py")
        exit(1)
except Exception as e:
    print(f"   ✗ ERROR checking table: {e}")
    exit(1)

# Check 3: Can we query EmailTemplate?
print("\n3. Checking if EmailTemplate can be queried...")
try:
    count = EmailTemplate.objects.count()
    print(f"   ✓ EmailTemplate query works - {count} templates found")
except Exception as e:
    print(f"   ✗ ERROR querying EmailTemplate: {e}")
    exit(1)

# Check 4: Check admin registration
print("\n4. Checking admin registration...")
try:
    from django.contrib import admin
    if EmailTemplate in admin.site._registry:
        print("   ✓ EmailTemplate registered in admin")
    else:
        print("   ✗ EmailTemplate NOT registered in admin")
except Exception as e:
    print(f"   ✗ ERROR checking admin: {e}")

# Check 5: Check imports in admin.py
print("\n5. Checking admin.py imports...")
try:
    from admin import EmailTemplateAdmin
    print("   ✓ EmailTemplateAdmin imports successfully")
except Exception as e:
    print(f"   ✗ ERROR importing EmailTemplateAdmin: {e}")
    print(f"   This might be the 500 error cause!")
    exit(1)

# Check 6: Check mark_safe import
print("\n6. Checking mark_safe import...")
try:
    from django.utils.safestring import mark_safe
    print("   ✓ mark_safe imports successfully")
except Exception as e:
    print(f"   ✗ ERROR importing mark_safe: {e}")

# Check 7: Test template rendering
print("\n7. Testing template rendering...")
try:
    if EmailTemplate.objects.exists():
        template = EmailTemplate.objects.first()
        context = {'passenger_name': 'Test', 'pick_up_date': 'Test Date'}
        subject = template.render_subject(context)
        print(f"   ✓ Template rendering works")
        print(f"   Sample subject: {subject[:50]}...")
    else:
        print("   ⚠ No templates to test (table empty)")
except Exception as e:
    print(f"   ✗ ERROR testing rendering: {e}")

print("\n" + "="*70)
print("DIAGNOSTIC COMPLETE")
print("="*70)

# Summary
print("\nIf all checks passed, the system is working.")
print("If table doesn't exist, run: python create_email_template_table.py")
print("If imports fail, check for syntax errors in admin.py or models.py")
print("\nTo check server logs:")
print("  - Check Apache/Nginx error logs")
print("  - Check Django logs in logs/ directory")
