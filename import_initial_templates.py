"""
Import initial email templates from HTML files
Run this on the server to populate the EmailTemplate table
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from models import EmailTemplate
from django.contrib.auth import get_user_model

User = get_user_model()

def import_template_from_file(template_type, name, description, subject_template, html_file_path):
    """Import a single template from HTML file"""
    
    # Check if template already exists
    if EmailTemplate.objects.filter(template_type=template_type, is_active=True).exists():
        print(f"⚠ Active template already exists for {template_type} - skipping")
        return None
    
    # Read HTML file
    try:
        with open(html_file_path, 'r', encoding='utf-8') as f:
            html_body = f.read()
    except FileNotFoundError:
        print(f"✗ File not found: {html_file_path}")
        return None
    
    # Create template
    template = EmailTemplate.objects.create(
        template_type=template_type,
        name=name,
        description=description,
        subject_template=subject_template,
        html_body=html_body,
        is_active=True,
        created_by=User.objects.filter(is_superuser=True).first()
    )
    
    print(f"✓ Imported: {name}")
    return template


print("="*70)
print("IMPORTING INITIAL EMAIL TEMPLATES")
print("="*70)

# Template 1: Booking Confirmation
import_template_from_file(
    template_type='booking_confirmed',
    name='Booking Confirmation Email',
    description='Sent to passengers when their booking is confirmed',
    subject_template='Trip Confirmed: {passenger_name} - {pick_up_date}',
    html_file_path='templates/emails/booking_notification.html'
)

# Template 2: Booking Reminder
import_template_from_file(
    template_type='booking_reminder',
    name='Booking Reminder Email (24h)',
    description='Sent 24 hours before pickup as a reminder',
    subject_template='Reminder: Your pickup tomorrow at {pick_up_time}',
    html_file_path='templates/emails/booking_reminder.html'
)

# Count templates
total = EmailTemplate.objects.count()
active = EmailTemplate.objects.filter(is_active=True).count()

print("="*70)
print(f"IMPORT COMPLETE")
print(f"Total templates: {total}")
print(f"Active templates: {active}")
print("="*70)
print("\nNext steps:")
print("1. Access admin: http://your-domain.com/admin/bookings/emailtemplate/")
print("2. Review imported templates")
print("3. Customize them for your brand")
print("4. Use 'Preview Template' to test")
print("5. Create templates for other notification types")
