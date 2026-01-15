"""
Script to create default driver notification template in database.
Run with: python create_driver_template_standalone.py
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from models import EmailTemplate
from django.utils import timezone


def create_driver_template():
    """Create default driver notification template in database from file template"""
    print('\n' + '='*60)
    print('Creating driver notification database template...')
    print('='*60 + '\n')
    
    # Read existing file template
    template_path = 'templates/emails/driver_notification.html'
    
    if not os.path.exists(template_path):
        print(f'❌ ERROR: Template file not found: {template_path}')
        return False
    
    with open(template_path, 'r', encoding='utf-8') as f:
        file_html = f.read()
    
    # Convert Django template syntax to database template variable syntax
    # Replace object attribute access with simple variables
    html_template = (
        file_html
        .replace('{{ driver.full_name }}', '{{ driver_full_name }}')
        .replace('{{ driver.first_name }}', '{{ driver_full_name }}')
        .replace('{{ pickup_location }}', '{{ pickup_location }}')
        # Replace Django template filters with pre-formatted variables
        .replace('{{ pickup_date|date:"l, F j, Y" }}', '{{ pickup_date }}')
        .replace('{{ pickup_time|time:"g:i A" }}', '{{ pickup_time }}')
        .replace('{{ drop_off_location }}', '{{ drop_off_location }}')
        .replace('{{ passenger_name }}', '{{ passenger_name }}')
        .replace('{{ passenger_phone }}', '{{ passenger_phone }}')
        .replace('{{ payment_amount }}', '{{ payment_amount }}')
        .replace('{{ driver_portal_url }}', '{{ driver_portal_url }}')
        .replace('{{ all_trips_url }}', '{{ all_trips_url }}')
    )
    
    try:
        # Create or update template
        template, created = EmailTemplate.objects.update_or_create(
            template_type='driver_notification',
            defaults={
                'name': 'Driver Trip Assignment Notification',
                'description': (
                    'Sent to driver when assigned to a trip. '
                    'Contains pickup details, passenger info, and driver portal links. '
                    'Uses programmable template system for admin editing.'
                ),
                'subject_template': 'New Trip Assignment - {{ pickup_date }}',
                'html_template': html_template,
                'is_active': False,  # Inactive by default for safety
                'send_to_user': False,
                'send_to_admin': False,
                'send_to_passenger': False,
            }
        )
        
        action = 'Created' if created else 'Updated'
        print(f'✓ {action} driver_notification template (ID: {template.id})')
        print(f'  Template Type: {template.template_type}')
        print(f'  Name: {template.name}')
        print(f'  Subject: {template.subject_template}')
        print(f'  Active: {template.is_active}')
        
        if created:
            print('\n' + '='*60)
            print('⚠️  IMPORTANT: Template is INACTIVE by default for safety')
            print('='*60)
            print('\nThe system will continue using the file template until activated.')
            print('\nTo activate the database template:')
            print('  1. Go to Django admin: http://62.169.19.39:8081/admin/bookings/emailtemplate/')
            print('  2. Find "Driver Trip Assignment Notification"')
            print('  3. Review and customize the template if needed')
            print('  4. Check "Is active" checkbox')
            print('  5. Save')
            print('\nTo test before activating:')
            print('  1. Assign a driver to a test booking')
            print('  2. Check that email sends successfully (uses file template)')
            print('  3. Activate database template in admin')
            print('  4. Assign driver to another test booking')
            print('  5. Verify database template renders correctly')
            print('\nAvailable variables for this template:')
            print('  • driver_full_name, driver_email')
            print('  • booking_reference')
            print('  • pickup_location, pickup_date, pickup_time')
            print('  • drop_off_location (optional)')
            print('  • passenger_name, passenger_phone, passenger_email')
            print('  • vehicle_type, trip_type, number_of_passengers')
            print('  • payment_amount (optional)')
            print('  • driver_portal_url, all_trips_url')
            print('  • company_name, support_email, support_phone')
        else:
            print('\n✓ Template updated successfully')
            print(f'  Active: {template.is_active}')
            print(f'  Total sent: {template.total_sent}')
            print(f'  Total failed: {template.total_failed}')
            if template.last_sent_at:
                print(f'  Last sent: {template.last_sent_at}')
        
        print('\n' + '='*60)
        print('✓ Script completed successfully')
        print('='*60 + '\n')
        return True
        
    except Exception as e:
        print(f'\n❌ ERROR: Failed to create template: {e}')
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = create_driver_template()
    sys.exit(0 if success else 1)
