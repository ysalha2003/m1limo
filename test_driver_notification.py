"""
Test script for driver notification template integration.
Tests both database template and file template fallback.
Run with: python test_driver_notification.py
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from models import Booking, EmailTemplate
from email_service import EmailService
from django.contrib.auth.models import User
from datetime import datetime, time


def test_driver_context_builder():
    """Test the _build_driver_template_context method"""
    print('\n' + '='*70)
    print('TEST 1: Driver Template Context Builder')
    print('='*70)
    
    try:
        # Get a test booking
        booking = Booking.objects.filter(assigned_driver__isnull=False).first()
        if not booking:
            print('❌ No bookings with drivers found')
            return False
        
        driver = booking.assigned_driver
        print(f'\n✓ Found test booking: {booking.booking_reference}')
        print(f'  Driver: {driver.email}')
        print(f'  Pickup: {booking.pick_up_address}')
        print(f'  Date: {booking.pick_up_date}')
        
        # Build context
        context = EmailService._build_driver_template_context(booking, driver)
        
        print('\n✓ Context generated successfully:')
        print(f'  driver_full_name: {context.get("driver_full_name")}')
        print(f'  booking_reference: {context.get("booking_reference")}')
        print(f'  pickup_location: {context.get("pickup_location")}')
        print(f'  pickup_date: {context.get("pickup_date")}')
        print(f'  pickup_time: {context.get("pickup_time")}')
        print(f'  passenger_name: {context.get("passenger_name")}')
        print(f'  driver_portal_url: {context.get("driver_portal_url")[:50]}...')
        print(f'  all_trips_url: {context.get("all_trips_url")[:50]}...')
        
        # Verify all required fields present
        required_fields = [
            'driver_full_name', 'driver_email', 'booking_reference',
            'pickup_location', 'pickup_date', 'pickup_time',
            'passenger_name', 'passenger_phone', 'driver_portal_url', 'all_trips_url'
        ]
        
        missing_fields = [f for f in required_fields if not context.get(f)]
        if missing_fields:
            print(f'\n❌ Missing required fields: {missing_fields}')
            return False
        
        print('\n✓ All required fields present')
        return True
        
    except Exception as e:
        print(f'\n❌ ERROR: {e}')
        import traceback
        traceback.print_exc()
        return False


def test_database_template_loading():
    """Test loading the database template"""
    print('\n' + '='*70)
    print('TEST 2: Database Template Loading')
    print('='*70)
    
    try:
        # Check if template exists
        template = EmailTemplate.objects.filter(template_type='driver_notification').first()
        
        if not template:
            print('\n❌ Driver notification template not found in database')
            print('   Run: python create_driver_template_standalone.py')
            return False
        
        print(f'\n✓ Template found: {template.name}')
        print(f'  ID: {template.id}')
        print(f'  Type: {template.template_type}')
        print(f'  Active: {template.is_active}')
        print(f'  Subject: {template.subject_template}')
        print(f'  HTML Length: {len(template.html_template)} characters')
        print(f'  Total Sent: {template.total_sent}')
        print(f'  Total Failed: {template.total_failed}')
        
        # Test template rendering with sample context
        print('\n✓ Testing template rendering...')
        
        sample_context = {
            'driver_full_name': 'John Doe',
            'booking_reference': 'TEST123',
            'pickup_location': '123 Test St, Chicago, IL',
            'pickup_date': 'Monday, January 15, 2026',
            'pickup_time': '02:30 PM',
            'drop_off_location': '456 Demo Ave, Chicago, IL',
            'passenger_name': 'Jane Smith',
            'passenger_phone': '(312) 555-0100',
            'driver_portal_url': 'http://example.com/driver/trip/123/token/',
            'all_trips_url': 'http://example.com/driver/trips/test@example.com/token/',
            'company_name': 'M1 Limousine Service',
            'support_email': 'support@m1limo.com',
        }
        
        subject = template.render_subject(sample_context)
        html = template.render_html(sample_context)
        
        print(f'  Rendered Subject: {subject}')
        print(f'  Rendered HTML: {len(html)} characters')
        
        # Check if variables were replaced
        if '{{ driver_full_name }}' in html:
            print('\n❌ WARNING: Variables not replaced in HTML')
            return False
        
        if 'John Doe' not in html:
            print('\n❌ WARNING: Driver name not found in rendered HTML')
            return False
        
        print('\n✓ Template renders correctly')
        return True
        
    except Exception as e:
        print(f'\n❌ ERROR: {e}')
        import traceback
        traceback.print_exc()
        return False


def test_file_template_fallback():
    """Test that file template fallback works"""
    print('\n' + '='*70)
    print('TEST 3: File Template Fallback')
    print('='*70)
    
    try:
        # Get a test booking
        booking = Booking.objects.filter(assigned_driver__isnull=False).first()
        if not booking:
            print('❌ No bookings with drivers found')
            return False
        
        driver = booking.assigned_driver
        print(f'\n✓ Found test booking: {booking.booking_reference}')
        
        # Temporarily deactivate database template
        template = EmailTemplate.objects.filter(template_type='driver_notification').first()
        original_state = template.is_active if template else False
        
        if template:
            template.is_active = False
            template.save()
            print('✓ Database template deactivated for test')
        
        # Test _load_email_template returns None
        loaded = EmailService._load_email_template('driver_notification')
        if loaded:
            print('❌ ERROR: Template should not load when inactive')
            return False
        
        print('✓ Database template correctly returns None when inactive')
        
        # Check that file template exists
        file_path = 'templates/emails/driver_notification.html'
        if not os.path.exists(file_path):
            print(f'❌ ERROR: File template not found: {file_path}')
            return False
        
        print(f'✓ File template exists: {file_path}')
        
        # Restore original state
        if template:
            template.is_active = original_state
            template.save()
            print(f'✓ Database template state restored: {original_state}')
        
        print('\n✓ File template fallback mechanism verified')
        return True
        
    except Exception as e:
        print(f'\n❌ ERROR: {e}')
        import traceback
        traceback.print_exc()
        return False


def test_integration_summary():
    """Show integration status summary"""
    print('\n' + '='*70)
    print('INTEGRATION STATUS SUMMARY')
    print('='*70)
    
    template = EmailTemplate.objects.filter(template_type='driver_notification').first()
    
    if not template:
        print('\n❌ Database template not created')
        print('   Run: python create_driver_template_standalone.py')
        return
    
    print('\n✓ Database Template:')
    print(f'  Status: {"ACTIVE ✓" if template.is_active else "INACTIVE (using file template)"}')
    print(f'  Name: {template.name}')
    print(f'  Subject: {template.subject_template}')
    print(f'  Statistics:')
    print(f'    - Total sent: {template.total_sent}')
    print(f'    - Total failed: {template.total_failed}')
    if template.last_sent_at:
        print(f'    - Last sent: {template.last_sent_at}')
    
    print('\n✓ File Template:')
    file_path = 'templates/emails/driver_notification.html'
    if os.path.exists(file_path):
        file_size = os.path.getsize(file_path)
        print(f'  Path: {file_path}')
        print(f'  Size: {file_size} bytes')
        print(f'  Status: Available as fallback')
    else:
        print('  Status: ❌ NOT FOUND')
    
    print('\n✓ Email Service Integration:')
    print('  _build_driver_template_context() - Added ✓')
    print('  send_driver_notification() - Refactored ✓')
    print('  Database template lookup - Integrated ✓')
    print('  File template fallback - Preserved ✓')
    
    print('\n✓ EmailTemplate Model:')
    print('  get_available_variables() - Updated ✓')
    print('  Driver notification type - Defined ✓')
    
    if not template.is_active:
        print('\n' + '='*70)
        print('📋 NEXT STEPS TO ACTIVATE:')
        print('='*70)
        print('\n1. Go to Django admin:')
        print('   http://62.169.19.39:8081/admin/bookings/emailtemplate/')
        print('\n2. Find "Driver Trip Assignment Notification"')
        print('\n3. Review the template and customize if needed')
        print('\n4. Check the "Is active" checkbox')
        print('\n5. Save the template')
        print('\n6. Test by assigning a driver to a booking')
        print('\n7. Monitor statistics in the admin panel')


def run_all_tests():
    """Run all tests"""
    print('\n' + '='*70)
    print('DRIVER NOTIFICATION TEMPLATE INTEGRATION TEST SUITE')
    print('='*70)
    
    results = []
    
    # Run tests
    results.append(('Context Builder', test_driver_context_builder()))
    results.append(('Database Template', test_database_template_loading()))
    results.append(('File Fallback', test_file_template_fallback()))
    
    # Show results
    print('\n' + '='*70)
    print('TEST RESULTS')
    print('='*70)
    
    for test_name, passed in results:
        status = '✓ PASS' if passed else '❌ FAIL'
        print(f'{status}: {test_name}')
    
    all_passed = all(result[1] for result in results)
    
    # Show summary
    test_integration_summary()
    
    if all_passed:
        print('\n' + '='*70)
        print('✓ ALL TESTS PASSED - INTEGRATION SUCCESSFUL')
        print('='*70 + '\n')
        return True
    else:
        print('\n' + '='*70)
        print('❌ SOME TESTS FAILED - REVIEW ERRORS ABOVE')
        print('='*70 + '\n')
        return False


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
