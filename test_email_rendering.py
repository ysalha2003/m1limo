#!/usr/bin/env python
"""Test email template rendering with Django template engine"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from models import EmailTemplate
from datetime import datetime
from types import SimpleNamespace

# Get round trip confirmed template
template = EmailTemplate.objects.filter(template_type='round_trip_confirmed', is_active=True).first()

if not template:
    print("❌ Round trip confirmed template not found or not active")
    exit(1)

print(f"✅ Found template: {template.name}")
print(f"   Template type: {template.template_type}")
print(f"   Active: {template.is_active}")
print()

# Create mock objects
mock_first_trip = SimpleNamespace(
    pick_up_date=datetime(2026, 1, 20),
    pick_up_time='2:00 PM',
    pick_up_location='123 Main St, New York',
    drop_off_location='456 Airport Rd, JFK'
)

mock_return_trip = SimpleNamespace(
    pick_up_date=datetime(2026, 1, 25),
    pick_up_time='4:00 PM',
    pick_up_location='456 Airport Rd, JFK',
    drop_off_location='123 Main St, New York'
)

mock_company_info = SimpleNamespace(
    logo_url=None,
    phone='+1 (555) 000-0000',
    email='support@m1limo.com',
    dashboard_url='http://62.169.19.39:8081/dashboard'
)

# Create context
context = {
    'booking_id': 'TEST-001',
    'passenger_name': 'John Doe',
    'notification_type': 'confirmed',
    'first_trip': mock_first_trip,
    'return_trip': mock_return_trip,
    'company_info': mock_company_info,
}

print("🔄 Rendering subject...")
try:
    subject = template.render_subject(context)
    print(f"✅ Subject rendered successfully:")
    print(f"   {subject}")
    print()
except Exception as e:
    print(f"❌ Subject rendering failed: {e}")
    import traceback
    traceback.print_exc()
    print()

print("🔄 Rendering HTML body...")
try:
    html = template.render_html(context)
    print(f"✅ HTML rendered successfully!")
    print(f"   Length: {len(html)} characters")
    print()
    
    # Check for Django template tags (should NOT be present)
    if '{%' in html or '{{' in html:
        print("⚠️  WARNING: Django template tags still present in output!")
        print("   This means rendering didn't work properly.")
        # Show first occurrence
        if '{%' in html:
            idx = html.index('{%')
            print(f"   Found '{{%' at position {idx}: {html[idx:idx+50]}...")
        if '{{' in html:
            idx = html.index('{{')
            print(f"   Found '{{{{' at position {idx}: {html[idx:idx+50]}...")
    else:
        print("✅ No Django template tags in output - rendering worked!")
        print()
        
        # Show snippet
        print("📄 HTML Preview (first 500 chars):")
        print("-" * 60)
        print(html[:500])
        print("...")
        print("-" * 60)
        
except Exception as e:
    print(f"❌ HTML rendering failed: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 60)
print("Test complete!")
