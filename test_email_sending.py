"""
Test script to send actual email using active database templates.
"""

import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from django.contrib.auth import get_user_model
from models import Booking, EmailTemplate
from email_service import EmailService

User = get_user_model()

def test_email_sending():
    print("=" * 70)
    print("TESTING EMAIL SENDING WITH ACTIVE DATABASE TEMPLATES")
    print("=" * 70)
    
    # Check template status
    confirmed_template = EmailTemplate.objects.filter(template_type='booking_confirmed').first()
    print(f"\n1. Template Status Check:")
    if confirmed_template:
        print(f"   Template: {confirmed_template.name}")
        print(f"   Active: {confirmed_template.is_active}")
        print(f"   Subject: {confirmed_template.subject_template[:50]}...")
    else:
        print("   ❌ No 'booking_confirmed' template found!")
        return
    
    # Load booking
    booking = Booking.objects.get(id=209)
    print(f"\n2. Booking Details:")
    print(f"   ID: {booking.id}")
    print(f"   Passenger: {booking.passenger_name}")
    print(f"   Email: {booking.passenger_email}")
    print(f"   Status: {booking.status}")
    print(f"   Driver: {booking.assigned_driver}")
    
    # Attempt to send email
    print(f"\n3. Attempting to send 'confirmed' notification...")
    result = EmailService.send_booking_notification(
        booking=booking,
        notification_type='confirmed',
        recipient_email=booking.passenger_email,
        old_status=None,
        is_return=False
    )
    
    print(f"\n4. Send Result:")
    if result:
        print("   ✅ Email sent successfully!")
        
        # Check statistics
        confirmed_template.refresh_from_db()
        print(f"\n5. Template Statistics:")
        print(f"   Total sent: {confirmed_template.total_sent}")
        print(f"   Total failed: {confirmed_template.total_failed}")
        print(f"   Success rate: {confirmed_template.success_rate}%")
        print(f"   Last sent: {confirmed_template.last_sent_at}")
    else:
        print("   ❌ Email sending failed!")
    
    print("\n" + "=" * 70)
    if result:
        print("✅ TEST PASSED - Emails sending with database templates!")
    else:
        print("❌ TEST FAILED - Check logs for details")
    print("=" * 70)

if __name__ == "__main__":
    test_email_sending()
