"""
Test script to verify all notifications use programmable templates.
This script checks if database templates are being loaded for all notification types.
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from models import EmailTemplate, Booking, User
from email_service import EmailService
from notification_service import NotificationService
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_template_loading():
    """Test if all template types can be loaded from database"""
    
    print("\n" + "="*80)
    print("NOTIFICATION TEMPLATE SYSTEM TEST")
    print("="*80)
    
    # All expected template types
    template_types = [
        ('booking_new', 'New Booking (Trip Request)'),
        ('booking_confirmed', 'Booking Confirmed'),
        ('booking_cancelled', 'Booking Cancelled'),
        ('booking_status_change', 'Status Change'),
        ('booking_reminder', 'Pickup Reminder'),
        ('driver_notification', 'Driver Assignment'),
        ('driver_rejection', 'Driver Rejection (Admin Alert)'),
        ('driver_completion', 'Driver Trip Completion (Admin Alert)'),
        ('round_trip_new', 'Round Trip - New'),
        ('round_trip_confirmed', 'Round Trip - Confirmed'),
        ('round_trip_cancelled', 'Round Trip - Cancelled'),
        ('round_trip_status_change', 'Round Trip - Status Change'),
    ]
    
    print("\n1. DATABASE TEMPLATE AVAILABILITY CHECK")
    print("-" * 80)
    
    results = []
    for template_type, description in template_types:
        template = EmailService._load_email_template(template_type)
        
        if template:
            status = "✅ FOUND"
            active = "ACTIVE" if template.is_active else "INACTIVE"
            sent_count = template.total_sent
            result = {
                'type': template_type,
                'description': description,
                'status': 'found',
                'active': template.is_active,
                'sent': sent_count,
                'name': template.name
            }
        else:
            status = "❌ NOT FOUND"
            active = "N/A"
            sent_count = 0
            result = {
                'type': template_type,
                'description': description,
                'status': 'missing',
                'active': False,
                'sent': 0,
                'name': 'N/A'
            }
        
        results.append(result)
        print(f"{description:45} | {status:12} | {active:8} | Sent: {sent_count:4}")
    
    # Summary
    print("\n" + "="*80)
    found_count = sum(1 for r in results if r['status'] == 'found')
    active_count = sum(1 for r in results if r['status'] == 'found' and r['active'])
    missing_count = sum(1 for r in results if r['status'] == 'missing')
    
    print(f"SUMMARY:")
    print(f"  Total Template Types: {len(template_types)}")
    print(f"  ✅ Found in Database: {found_count}")
    print(f"  🟢 Active Templates:  {active_count}")
    print(f"  ❌ Missing Templates: {missing_count}")
    
    # Check notification type mapping
    print("\n2. NOTIFICATION TYPE MAPPING CHECK")
    print("-" * 80)
    
    notification_mappings = [
        ('new', 'booking_new', 'Trip Request'),
        ('confirmed', 'booking_confirmed', 'Trip Confirmed'),
        ('cancelled', 'booking_cancelled', 'Trip Cancelled'),
        ('status_change', 'booking_status_change', 'Status Update'),
        ('reminder', 'booking_reminder', 'Pickup Reminder'),
    ]
    
    for notif_type, template_type, description in notification_mappings:
        template = EmailService._load_email_template(template_type)
        if template and template.is_active:
            print(f"  {description:25} | notification_type='{notif_type:15}' → {template_type:25} ✅")
        else:
            print(f"  {description:25} | notification_type='{notif_type:15}' → {template_type:25} ❌ FALLBACK TO FILE")
    
    # Admin notification check
    print("\n3. ADMIN NOTIFICATION CHECK")
    print("-" * 80)
    
    admin_templates = [
        ('driver_rejection', 'Driver Rejection Alert'),
        ('driver_completion', 'Driver Completion Alert'),
    ]
    
    for template_type, description in admin_templates:
        template = EmailService._load_email_template(template_type)
        if template and template.is_active:
            print(f"  {description:35} | {template_type:25} ✅ PROGRAMMABLE")
        else:
            print(f"  {description:35} | {template_type:25} ⚠️  WILL USE HARDCODED HTML")
    
    # Check if Trip Request is using programmable template
    print("\n4. TRIP REQUEST NOTIFICATION CHECK")
    print("-" * 80)
    
    trip_request_template = EmailService._load_email_template('booking_new')
    if trip_request_template:
        if trip_request_template.is_active:
            print(f"  ✅ Trip Request notifications WILL USE programmable template")
            print(f"     Template Name: {trip_request_template.name}")
            print(f"     Total Sent: {trip_request_template.total_sent}")
            print(f"     Success Rate: {trip_request_template.success_rate}%")
        else:
            print(f"  ⚠️  Trip Request template exists but is INACTIVE")
            print(f"     Will fall back to file template: templates/emails/booking_notification.html")
    else:
        print(f"  ❌ Trip Request template NOT FOUND in database")
        print(f"     Will use file template: templates/emails/booking_notification.html")
    
    print("\n" + "="*80)
    
    # Recommendations
    if missing_count > 0 or active_count < found_count:
        print("\n⚠️  RECOMMENDATIONS:")
        if missing_count > 0:
            print(f"  • Upload {missing_count} missing templates via Django Admin → Email Templates")
        if active_count < found_count:
            inactive_count = found_count - active_count
            print(f"  • Activate {inactive_count} inactive templates to use programmable templates")
        print(f"  • Location: http://62.169.19.39:8081/admin/bookings/emailtemplate/")
    
    if trip_request_template is None or not trip_request_template.is_active:
        print("\n⚠️  TRIP REQUEST ISSUE:")
        print("  • Trip Request (booking_new) template is not using programmable template")
        print("  • Create/activate the 'New Booking' template in Django Admin")
        print("  • Template Type: 'booking_new'")
    
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80 + "\n")

if __name__ == '__main__':
    test_template_loading()
