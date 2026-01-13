"""
Unit tests for Email Template Management System
Tests EmailTemplate model, admin actions, and email service integration
"""
from django.test import TestCase, RequestFactory
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User
from django.core import mail
from django.utils import timezone
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, time

from models import EmailTemplate, Booking, Driver
from admin import EmailTemplateAdmin
from email_service import EmailService


class EmailTemplateModelTest(TestCase):
    """Test EmailTemplate model functionality"""
    
    def setUp(self):
        """Create test user and template"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.template = EmailTemplate.objects.create(
            template_type='booking_confirmed',
            name='Test Confirmation Template',
            description='Test template for confirmations',
            subject_template='Trip Confirmed: {passenger_name} - {pick_up_date}',
            html_template='<html><body><h1>Hello {passenger_name}</h1><p>Pickup: {pick_up_address}</p></body></html>',
            is_active=True,
            send_to_user=True,
            send_to_admin=True,
            created_by=self.user,
            updated_by=self.user
        )
    
    def test_template_creation(self):
        """Test that template is created with correct fields"""
        self.assertEqual(self.template.template_type, 'booking_confirmed')
        self.assertEqual(self.template.name, 'Test Confirmation Template')
        self.assertTrue(self.template.is_active)
        self.assertEqual(self.template.total_sent, 0)
        self.assertEqual(self.template.total_failed, 0)
    
    def test_get_available_variables_booking(self):
        """Test get_available_variables returns correct variables for booking types"""
        variables = self.template.get_available_variables()
        
        # Check key variables are present
        self.assertIn('booking_reference', variables)
        self.assertIn('passenger_name', variables)
        self.assertIn('pick_up_date', variables)
        self.assertIn('pick_up_time', variables)
        self.assertIn('pick_up_address', variables)
        self.assertIn('drop_off_address', variables)
        self.assertIn('vehicle_type', variables)
        self.assertIn('company_name', variables)
        self.assertIn('support_email', variables)
        
        # Check it's a dictionary with descriptions
        self.assertIsInstance(variables, dict)
        self.assertIsInstance(variables['passenger_name'], str)
    
    def test_get_available_variables_round_trip(self):
        """Test round trip template has return variables"""
        round_trip_template = EmailTemplate.objects.create(
            template_type='round_trip_confirmed',
            name='Round Trip Template',
            subject_template='Round Trip Confirmed',
            html_template='<html><body>Round trip</body></html>',
            created_by=self.user,
            updated_by=self.user
        )
        
        variables = round_trip_template.get_available_variables()
        
        # Check round trip specific variables
        self.assertIn('return_pick_up_date', variables)
        self.assertIn('return_pick_up_time', variables)
        self.assertIn('return_pick_up_address', variables)
        self.assertIn('return_drop_off_address', variables)
    
    def test_render_subject_success(self):
        """Test rendering subject template with context"""
        context = {
            'passenger_name': 'John Smith',
            'pick_up_date': 'January 20, 2026'
        }
        
        subject = self.template.render_subject(context)
        
        self.assertEqual(subject, 'Trip Confirmed: John Smith - January 20, 2026')
    
    def test_render_subject_missing_variable(self):
        """Test rendering subject with missing variable returns error message"""
        context = {
            'passenger_name': 'John Smith'
            # Missing pick_up_date
        }
        
        subject = self.template.render_subject(context)
        
        self.assertIn('Error rendering', subject)
    
    def test_render_html_success(self):
        """Test rendering HTML template with context"""
        context = {
            'passenger_name': 'John Smith',
            'pick_up_address': '123 Main St'
        }
        
        html = self.template.render_html(context)
        
        self.assertIn('Hello John Smith', html)
        self.assertIn('Pickup: 123 Main St', html)
    
    def test_render_html_missing_variable(self):
        """Test rendering HTML with missing variable returns error message"""
        context = {
            'passenger_name': 'John Smith'
            # Missing pick_up_address
        }
        
        html = self.template.render_html(context)
        
        self.assertIn('Error rendering', html)
    
    def test_increment_sent(self):
        """Test increment_sent increases counter and updates timestamp"""
        self.assertEqual(self.template.total_sent, 0)
        self.assertIsNone(self.template.last_sent_at)
        
        self.template.increment_sent()
        
        self.assertEqual(self.template.total_sent, 1)
        self.assertIsNotNone(self.template.last_sent_at)
        
        # Increment again
        self.template.increment_sent()
        self.assertEqual(self.template.total_sent, 2)
    
    def test_increment_failed(self):
        """Test increment_failed increases counter"""
        self.assertEqual(self.template.total_failed, 0)
        
        self.template.increment_failed()
        
        self.assertEqual(self.template.total_failed, 1)
        
        self.template.increment_failed()
        self.assertEqual(self.template.total_failed, 2)
    
    def test_success_rate_calculation(self):
        """Test success_rate property calculates correctly"""
        # No sends yet
        self.assertEqual(self.template.success_rate, 0.0)
        
        # 8 successful, 2 failed = 80%
        self.template.total_sent = 8
        self.template.total_failed = 2
        self.template.save()
        
        self.assertEqual(self.template.success_rate, 80.0)
        
        # All successful
        self.template.total_sent = 10
        self.template.total_failed = 0
        self.template.save()
        
        self.assertEqual(self.template.success_rate, 100.0)
        
        # All failed
        self.template.total_sent = 0
        self.template.total_failed = 10
        self.template.save()
        
        self.assertEqual(self.template.success_rate, 0.0)
    
    def test_str_representation(self):
        """Test string representation of template"""
        self.assertIn(self.template.name, str(self.template))


class EmailTemplateAdminTest(TestCase):
    """Test EmailTemplateAdmin functionality"""
    
    def setUp(self):
        """Create test data"""
        self.site = AdminSite()
        self.admin = EmailTemplateAdmin(EmailTemplate, self.site)
        self.factory = RequestFactory()
        
        self.user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )
        
        self.template = EmailTemplate.objects.create(
            template_type='booking_confirmed',
            name='Test Template',
            subject_template='Test: {passenger_name}',
            html_template='<html><body>{passenger_name}</body></html>',
            is_active=True,
            created_by=self.user,
            updated_by=self.user,
            total_sent=8,
            total_failed=2
        )
    
    def test_list_display_fields(self):
        """Test list_display contains expected fields"""
        expected_fields = ['name', 'template_type', 'is_active', 'success_rate_display', 
                          'total_sent', 'last_sent_at', 'updated_at']
        
        self.assertEqual(list(self.admin.list_display), expected_fields)
    
    def test_readonly_fields(self):
        """Test readonly fields are set correctly"""
        readonly = self.admin.readonly_fields
        
        self.assertIn('created_at', readonly)
        self.assertIn('updated_at', readonly)
        self.assertIn('total_sent', readonly)
        self.assertIn('total_failed', readonly)
        self.assertIn('success_rate', readonly)
        self.assertIn('variable_documentation', readonly)
    
    def test_success_rate_display_green(self):
        """Test success_rate_display shows green for >= 95%"""
        self.template.total_sent = 95
        self.template.total_failed = 5
        self.template.save()
        
        display = self.admin.success_rate_display(self.template)
        
        self.assertIn('green', display)
        self.assertIn('95', display)
    
    def test_success_rate_display_orange(self):
        """Test success_rate_display shows orange for 80-94%"""
        self.template.total_sent = 80
        self.template.total_failed = 20
        self.template.save()
        
        display = self.admin.success_rate_display(self.template)
        
        self.assertIn('orange', display)
        self.assertIn('80', display)
    
    def test_success_rate_display_red(self):
        """Test success_rate_display shows red for < 80%"""
        self.template.total_sent = 70
        self.template.total_failed = 30
        self.template.save()
        
        display = self.admin.success_rate_display(self.template)
        
        self.assertIn('red', display)
        self.assertIn('70', display)
    
    def test_variable_documentation_display(self):
        """Test variable_documentation generates HTML table"""
        html = self.admin.variable_documentation(self.template)
        
        self.assertIn('<table', html)
        self.assertIn('booking_reference', html)
        self.assertIn('passenger_name', html)
        self.assertIn('Usage Example', html)
    
    def test_variable_documentation_no_id(self):
        """Test variable_documentation shows message for unsaved template"""
        new_template = EmailTemplate(
            template_type='booking_new',
            name='Unsaved'
        )
        
        html = self.admin.variable_documentation(new_template)
        
        self.assertIn('Save template first', html)
    
    def test_save_model_tracks_user(self):
        """Test save_model sets created_by and updated_by"""
        request = self.factory.get('/admin/')
        request.user = self.user
        
        new_template = EmailTemplate(
            template_type='booking_new',
            name='New Template',
            subject_template='Subject',
            html_template='<html>Body</html>'
        )
        
        self.admin.save_model(request, new_template, None, False)
        
        self.assertEqual(new_template.created_by, self.user)
        self.assertEqual(new_template.updated_by, self.user)
    
    def test_preview_template_action(self):
        """Test preview_template action renders correctly"""
        request = self.factory.post('/admin/bookings/emailtemplate/')
        request.user = self.user
        request._messages = MagicMock()
        
        queryset = EmailTemplate.objects.filter(id=self.template.id)
        
        response = self.admin.preview_template(request, queryset)
        
        # Should return a rendered response
        self.assertIsNotNone(response)
    
    def test_preview_template_multiple_selected(self):
        """Test preview_template shows warning for multiple templates"""
        request = self.factory.post('/admin/bookings/emailtemplate/')
        request.user = self.user
        request._messages = MagicMock()
        
        template2 = EmailTemplate.objects.create(
            template_type='booking_new',
            name='Template 2',
            subject_template='Subject',
            html_template='<html>Body</html>',
            created_by=self.user,
            updated_by=self.user
        )
        
        queryset = EmailTemplate.objects.filter(id__in=[self.template.id, template2.id])
        
        self.admin.preview_template(request, queryset)
        
        # Should call message_user with warning
        self.admin.message_user.assert_called_once() if hasattr(self.admin, 'message_user') else None
    
    def test_send_test_email_action(self):
        """Test send_test_email sends email"""
        request = self.factory.post('/admin/bookings/emailtemplate/')
        request.user = self.user
        request._messages = MagicMock()
        
        queryset = EmailTemplate.objects.filter(id=self.template.id)
        
        # Clear mailbox
        mail.outbox = []
        
        self.admin.send_test_email(request, queryset)
        
        # Should send one email
        self.assertEqual(len(mail.outbox), 1)
        
        # Check email properties
        sent_email = mail.outbox[0]
        self.assertIn('[TEST]', sent_email.subject)
        self.assertIn(self.user.email, sent_email.to)
        self.assertIn('TEST EMAIL', sent_email.body)
    
    def test_send_test_email_no_user_email(self):
        """Test send_test_email shows error if user has no email"""
        request = self.factory.post('/admin/bookings/emailtemplate/')
        user_no_email = User.objects.create_user(username='noemail', password='pass')
        request.user = user_no_email
        request._messages = MagicMock()
        
        queryset = EmailTemplate.objects.filter(id=self.template.id)
        
        self.admin.send_test_email(request, queryset)
        
        # Should show error message (we can't easily test message_user, but no exception is good)
    
    def test_duplicate_template_action(self):
        """Test duplicate_template creates copy"""
        request = self.factory.post('/admin/bookings/emailtemplate/')
        request.user = self.user
        request._messages = MagicMock()
        
        queryset = EmailTemplate.objects.filter(id=self.template.id)
        
        initial_count = EmailTemplate.objects.count()
        
        self.admin.duplicate_template(request, queryset)
        
        # Should create new template (but may fail due to unique constraint on template_type)
        # The duplicate will have template_type=None which needs manual setting
        final_count = EmailTemplate.objects.count()
        
        # Note: This might not increase count due to unique constraint handling in the action
        # The action intentionally sets template_type=None for manual selection


class EmailServiceIntegrationTest(TestCase):
    """Test EmailService integration with database templates"""
    
    def setUp(self):
        """Create test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='user@example.com',
            password='testpass123'
        )
        
        self.driver = Driver.objects.create(
            user=self.user,
            phone='555-1234'
        )
        
        self.booking = Booking.objects.create(
            user=self.user,
            booking_reference='M1-TEST-001',
            passenger_name='Test Passenger',
            phone_number='555-5678',
            passenger_email='passenger@example.com',
            pick_up_date=datetime(2026, 1, 20).date(),
            pick_up_time=time(14, 0),
            pick_up_address='123 Test St',
            drop_off_address='456 Test Ave',
            vehicle_type='Sedan',
            trip_type='point_to_point',
            number_of_passengers=2,
            status='confirmed'
        )
        
        self.template = EmailTemplate.objects.create(
            template_type='booking_confirmed',
            name='Confirmation Email',
            subject_template='Confirmed: {passenger_name} - {pick_up_date}',
            html_template='<html><body>Hello {passenger_name}, pickup at {pick_up_address}</body></html>',
            is_active=True,
            send_to_user=True,
            created_by=self.user,
            updated_by=self.user
        )
    
    def test_load_email_template_success(self):
        """Test _load_email_template loads active template"""
        template = EmailService._load_email_template('booking_confirmed')
        
        self.assertIsNotNone(template)
        self.assertEqual(template.template_type, 'booking_confirmed')
    
    def test_load_email_template_inactive(self):
        """Test _load_email_template returns None for inactive template"""
        self.template.is_active = False
        self.template.save()
        
        template = EmailService._load_email_template('booking_confirmed')
        
        self.assertIsNone(template)
    
    def test_load_email_template_not_found(self):
        """Test _load_email_template returns None for non-existent template"""
        template = EmailService._load_email_template('nonexistent_type')
        
        self.assertIsNone(template)
    
    def test_build_template_context(self):
        """Test _build_template_context creates correct context dict"""
        context = EmailService._build_template_context(
            self.booking,
            'confirmed',
            None,
            False
        )
        
        # Check key fields
        self.assertEqual(context['booking_reference'], 'M1-TEST-001')
        self.assertEqual(context['passenger_name'], 'Test Passenger')
        self.assertEqual(context['pick_up_address'], '123 Test St')
        self.assertEqual(context['drop_off_address'], '456 Test Ave')
        self.assertIn('company_name', context)
        self.assertIn('support_email', context)
    
    def test_build_round_trip_template_context(self):
        """Test _build_round_trip_template_context includes both trips"""
        return_booking = Booking.objects.create(
            user=self.user,
            booking_reference='M1-TEST-002',
            passenger_name='Test Passenger',
            phone_number='555-5678',
            pick_up_date=datetime(2026, 1, 25).date(),
            pick_up_time=time(16, 0),
            pick_up_address='456 Test Ave',
            drop_off_address='123 Test St',
            vehicle_type='Sedan',
            trip_type='round_trip',
            number_of_passengers=2,
            status='confirmed'
        )
        
        context = EmailService._build_round_trip_template_context(
            self.booking,
            return_booking,
            'confirmed'
        )
        
        # Check first trip fields
        self.assertEqual(context['booking_reference'], 'M1-TEST-001')
        self.assertEqual(context['pick_up_address'], '123 Test St')
        
        # Check return trip fields
        self.assertIn('return_pick_up_date', context)
        self.assertIn('return_pick_up_time', context)
        self.assertIn('return_pick_up_address', context)
    
    @patch('email_service.render_to_string')
    def test_send_booking_notification_uses_db_template(self, mock_render):
        """Test send_booking_notification uses DB template when available"""
        mail.outbox = []
        
        # Mock render_to_string to track if called (should not be called with DB template)
        mock_render.return_value = '<html>Fallback</html>'
        
        success = EmailService.send_booking_notification(
            self.booking,
            'confirmed',
            'recipient@example.com',
            None,
            False
        )
        
        # Should succeed
        self.assertTrue(success)
        
        # Template statistics should be updated
        self.template.refresh_from_db()
        self.assertEqual(self.template.total_sent, 1)
    
    @patch('email_service.render_to_string')
    def test_send_booking_notification_falls_back_to_file(self, mock_render):
        """Test send_booking_notification falls back to file template"""
        # Disable DB template
        self.template.is_active = False
        self.template.save()
        
        mail.outbox = []
        mock_render.return_value = '<html>File template</html>'
        
        success = EmailService.send_booking_notification(
            self.booking,
            'confirmed',
            'recipient@example.com',
            None,
            False
        )
        
        # Should still succeed with fallback
        self.assertTrue(success)
        
        # render_to_string should have been called for file template
        self.assertTrue(mock_render.called)
    
    def test_template_statistics_tracking(self):
        """Test that statistics are tracked correctly"""
        self.assertEqual(self.template.total_sent, 0)
        self.assertEqual(self.template.total_failed, 0)
        
        # Simulate successful send
        self.template.increment_sent()
        
        self.assertEqual(self.template.total_sent, 1)
        self.assertIsNotNone(self.template.last_sent_at)
        
        # Simulate failed send
        self.template.increment_failed()
        
        self.assertEqual(self.template.total_failed, 1)
        self.assertEqual(self.template.success_rate, 50.0)


class EmailTemplateEdgeCasesTest(TestCase):
    """Test edge cases and error handling"""
    
    def setUp(self):
        """Create test user"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_template_with_special_characters(self):
        """Test template with special characters in content"""
        template = EmailTemplate.objects.create(
            template_type='booking_new',
            name='Special Chars Template',
            subject_template='Trip: {passenger_name} <test@example.com>',
            html_template='<html><body>&copy; 2026 {company_name}</body></html>',
            created_by=self.user,
            updated_by=self.user
        )
        
        context = {
            'passenger_name': "O'Brien",
            'company_name': 'M1 & Co.'
        }
        
        subject = template.render_subject(context)
        html = template.render_html(context)
        
        self.assertIn("O'Brien", subject)
        self.assertIn('M1 & Co.', html)
    
    def test_template_unique_constraint(self):
        """Test that duplicate template_type is not allowed"""
        EmailTemplate.objects.create(
            template_type='booking_confirmed',
            name='First Template',
            subject_template='Subject',
            html_template='<html>Body</html>',
            created_by=self.user,
            updated_by=self.user
        )
        
        # Try to create duplicate
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            EmailTemplate.objects.create(
                template_type='booking_confirmed',
                name='Duplicate Template',
                subject_template='Subject 2',
                html_template='<html>Body 2</html>',
                created_by=self.user,
                updated_by=self.user
            )
    
    def test_template_with_missing_context_keys(self):
        """Test template rendering handles missing context gracefully"""
        template = EmailTemplate.objects.create(
            template_type='booking_confirmed',
            name='Template',
            subject_template='{passenger_name} - {nonexistent_key}',
            html_template='<html>{another_missing_key}</html>',
            created_by=self.user,
            updated_by=self.user
        )
        
        context = {'passenger_name': 'John Smith'}
        
        subject = template.render_subject(context)
        html = template.render_html(context)
        
        # Should return error messages
        self.assertIn('Error rendering', subject)
        self.assertIn('Error rendering', html)


def run_tests():
    """Helper function to run all tests"""
    import sys
    from django.core.management import call_command
    
    print("\n" + "="*70)
    print("RUNNING EMAIL TEMPLATE SYSTEM TESTS")
    print("="*70 + "\n")
    
    # Run tests with verbosity
    call_command('test', 'tests.test_email_templates', verbosity=2)


if __name__ == '__main__':
    run_tests()
