# management/commands/import_email_templates.py
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from models import EmailTemplate
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Import existing email templates from HTML files into database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--overwrite',
            action='store_true',
            help='Overwrite existing templates',
        )

    def handle(self, *args, **options):
        overwrite = options['overwrite']
        
        # Get or create a system user for initial creation
        try:
            system_user = User.objects.filter(is_superuser=True).first()
            if not system_user:
                system_user = User.objects.filter(is_staff=True).first()
            if not system_user:
                system_user = User.objects.first()
        except Exception:
            system_user = None
        
        templates_dir = os.path.join(settings.BASE_DIR, 'templates', 'emails')
        
        # Define template mappings
        templates_to_import = [
            {
                'type': 'booking_confirmed',
                'name': 'Booking Confirmation Email',
                'description': 'Sent when a booking is confirmed',
                'subject': 'Trip Confirmed: {passenger_name} - {pick_up_date}',
                'file': 'booking_notification.html',
                'send_to_user': True,
                'send_to_admin': True,
            },
            {
                'type': 'booking_cancelled',
                'name': 'Booking Cancellation Email',
                'description': 'Sent when a booking is cancelled',
                'subject': 'Trip Cancelled: {passenger_name} - {pick_up_date}',
                'file': 'booking_notification.html',
                'send_to_user': True,
                'send_to_admin': True,
            },
            {
                'type': 'booking_status_change',
                'name': 'Booking Status Change Email',
                'description': 'Sent when a booking status changes',
                'subject': 'Trip Update: {old_status} → {new_status} - {passenger_name}',
                'file': 'booking_notification.html',
                'send_to_user': True,
                'send_to_admin': True,
            },
            {
                'type': 'booking_reminder',
                'name': 'Pickup Reminder Email',
                'description': 'Sent 2 hours before pickup time',
                'subject': 'REMINDER: Pickup in 2 Hours - {passenger_name} at {pick_up_time}',
                'file': 'booking_reminder.html',
                'send_to_user': True,
                'send_to_admin': False,
            },
            {
                'type': 'driver_assignment',
                'name': 'Driver Assignment Notification',
                'description': 'Sent when a driver is assigned to a trip',
                'subject': 'Driver Assigned: {driver_name} - {passenger_name}',
                'file': 'driver_notification.html',
                'send_to_user': False,
                'send_to_admin': True,
            },
            {
                'type': 'round_trip_confirmed',
                'name': 'Round Trip Confirmation Email',
                'description': 'Sent when a round trip is confirmed',
                'subject': 'Round Trip Confirmed: {passenger_name} - {pick_up_date} & {return_pick_up_date}',
                'file': 'round_trip_notification.html',
                'send_to_user': True,
                'send_to_admin': True,
            },
            {
                'type': 'round_trip_cancelled',
                'name': 'Round Trip Cancellation Email',
                'description': 'Sent when a round trip is cancelled',
                'subject': 'Round Trip Cancelled: {passenger_name} - {pick_up_date} & {return_pick_up_date}',
                'file': 'round_trip_notification.html',
                'send_to_user': True,
                'send_to_admin': True,
            },
        ]
        
        imported_count = 0
        skipped_count = 0
        error_count = 0
        
        for template_data in templates_to_import:
            template_type = template_data['type']
            
            # Check if template already exists
            existing = EmailTemplate.objects.filter(template_type=template_type).first()
            if existing and not overwrite:
                self.stdout.write(self.style.WARNING(f'Skipping {template_type} - already exists'))
                skipped_count += 1
                continue
            
            # Read HTML file
            html_file_path = os.path.join(templates_dir, template_data['file'])
            if not os.path.exists(html_file_path):
                self.stdout.write(self.style.ERROR(f'File not found: {html_file_path}'))
                error_count += 1
                continue
            
            try:
                with open(html_file_path, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                
                # Convert Django template tags to variable syntax
                html_content = self._convert_template_syntax(html_content)
                
                if existing and overwrite:
                    # Update existing
                    existing.name = template_data['name']
                    existing.description = template_data['description']
                    existing.subject_template = template_data['subject']
                    existing.html_template = html_content
                    existing.send_to_user = template_data['send_to_user']
                    existing.send_to_admin = template_data['send_to_admin']
                    existing.is_active = True
                    if system_user:
                        existing.updated_by = system_user
                    existing.save()
                    self.stdout.write(self.style.SUCCESS(f'Updated template: {template_type}'))
                else:
                    # Create new
                    EmailTemplate.objects.create(
                        template_type=template_type,
                        name=template_data['name'],
                        description=template_data['description'],
                        subject_template=template_data['subject'],
                        html_template=html_content,
                        send_to_user=template_data['send_to_user'],
                        send_to_admin=template_data['send_to_admin'],
                        is_active=True,
                        created_by=system_user,
                        updated_by=system_user,
                    )
                    self.stdout.write(self.style.SUCCESS(f'Created template: {template_type}'))
                
                imported_count += 1
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error importing {template_type}: {str(e)}'))
                error_count += 1
        
        # Summary
        self.stdout.write(self.style.SUCCESS(f'\n=== Import Summary ==='))
        self.stdout.write(self.style.SUCCESS(f'Imported/Updated: {imported_count}'))
        if skipped_count > 0:
            self.stdout.write(self.style.WARNING(f'Skipped: {skipped_count}'))
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f'Errors: {error_count}'))
        
        self.stdout.write(self.style.SUCCESS('\nNote: Templates are imported with basic variable syntax.'))
        self.stdout.write(self.style.SUCCESS('You may need to manually adjust the HTML content in Django admin.'))
    
    def _convert_template_syntax(self, html_content):
        """
        Convert Django template syntax to variable placeholders.
        This is a basic conversion - manual adjustment may be needed.
        """
        # Common conversions
        conversions = {
            '{{ booking.booking_reference }}': '{booking_reference}',
            '{{ booking.passenger_name }}': '{passenger_name}',
            '{{ booking.phone_number }}': '{phone_number}',
            '{{ booking.pick_up_date }}': '{pick_up_date}',
            '{{ booking.pick_up_time }}': '{pick_up_time}',
            '{{ booking.pick_up_address }}': '{pick_up_address}',
            '{{ booking.drop_off_address }}': '{drop_off_address}',
            '{{ booking.vehicle_type }}': '{vehicle_type}',
            '{{ booking.number_of_passengers }}': '{number_of_passengers}',
            '{{ booking.flight_number }}': '{flight_number}',
            '{{ booking.notes }}': '{notes}',
            '{{ booking.status }}': '{status}',
            '{{ booking.user.email }}': '{user_email}',
            '{{ booking.user.username }}': '{user_username}',
            '{{ old_status }}': '{old_status}',
            '{{ new_status }}': '{new_status}',
            '{{ company_info.name }}': '{company_name}',
            '{{ company_info.email }}': '{support_email}',
            '{{ first_trip.pick_up_date }}': '{pick_up_date}',
            '{{ first_trip.pick_up_time }}': '{pick_up_time}',
            '{{ return_trip.pick_up_date }}': '{return_pick_up_date}',
            '{{ return_trip.pick_up_time }}': '{return_pick_up_time}',
        }
        
        for old, new in conversions.items():
            html_content = html_content.replace(old, new)
        
        return html_content
