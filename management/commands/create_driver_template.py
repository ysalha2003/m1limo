"""
Management command to create default driver notification template in database.
This converts the existing file template to a database template for admin editing.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
import os


class Command(BaseCommand):
    help = 'Create default driver notification template in database from file template'
    
    def handle(self, *args, **options):
        # Import here to avoid circular dependencies
        from models import EmailTemplate
        
        self.stdout.write(self.style.WARNING('Creating driver notification database template...'))
        
        # Read existing file template
        template_path = 'templates/emails/driver_notification.html'
        
        if not os.path.exists(template_path):
            self.stdout.write(self.style.ERROR(f'Template file not found: {template_path}'))
            return
        
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
            # Also handle any conditional checks
            .replace('{% if drop_off_location %}', '{% if drop_off_location %}')
            .replace('{% if payment_amount %}', '{% if payment_amount %}')
        )
        
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
                'created_at': timezone.now() if created else None,
                'updated_at': timezone.now(),
            }
        )
        
        action = 'Created' if created else 'Updated'
        self.stdout.write(
            self.style.SUCCESS(f'{action} driver_notification template (ID: {template.id})')
        )
        
        if created:
            self.stdout.write('')
            self.stdout.write(self.style.WARNING('⚠️  IMPORTANT: Template is INACTIVE by default for safety'))
            self.stdout.write(self.style.WARNING('   The system will continue using the file template until activated'))
            self.stdout.write('')
            self.stdout.write('To activate the database template:')
            self.stdout.write('  1. Go to Django admin: /admin/bookings/emailtemplate/')
            self.stdout.write('  2. Find "Driver Trip Assignment Notification"')
            self.stdout.write('  3. Review and customize the template if needed')
            self.stdout.write('  4. Check "Is active" checkbox')
            self.stdout.write('  5. Save')
            self.stdout.write('')
            self.stdout.write('To test before activating:')
            self.stdout.write('  1. Assign a driver to a test booking')
            self.stdout.write('  2. Check that email sends successfully (uses file template)')
            self.stdout.write('  3. Activate database template in admin')
            self.stdout.write('  4. Assign driver to another test booking')
            self.stdout.write('  5. Verify database template renders correctly')
            self.stdout.write('')
            self.stdout.write('Available variables for this template:')
            self.stdout.write('  - driver_full_name, driver_email')
            self.stdout.write('  - booking_reference')
            self.stdout.write('  - pickup_location, pickup_date, pickup_time')
            self.stdout.write('  - drop_off_location (optional)')
            self.stdout.write('  - passenger_name, passenger_phone, passenger_email')
            self.stdout.write('  - vehicle_type, trip_type, number_of_passengers')
            self.stdout.write('  - payment_amount (optional)')
            self.stdout.write('  - driver_portal_url, all_trips_url')
            self.stdout.write('  - company_name, support_email, support_phone')
        else:
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('✓ Template updated successfully'))
            self.stdout.write(f'  Active: {template.is_active}')
            self.stdout.write(f'  Total sent: {template.total_sent}')
            self.stdout.write(f'  Total failed: {template.total_failed}')
