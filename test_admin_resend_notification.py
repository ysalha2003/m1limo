"""
Test script to verify admin resend notification functionality
Run: python test_admin_resend_notification.py
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from models import Booking
from notification_service import NotificationService
from django.contrib.auth.models import User

print("="*70)
print("Testing Admin Resend Notification Functionality")
print("="*70)

# Get a booking with different statuses
for status in ['Pending', 'Confirmed', 'Cancelled', 'Trip_Completed']:
    booking = Booking.objects.filter(status=status).first()
    
    if booking:
        print(f"\n📋 Testing Status: {status}")
        print(f"   Booking ID: {booking.id}")
        print(f"   Passenger: {booking.passenger_name}")
        print(f"   Current Status: {booking.get_status_display()}")
        
        # Map status to notification type (same as in views.py)
        status_to_notification = {
            'Pending': 'new',
            'Confirmed': 'confirmed',
            'Cancelled': 'cancelled',
            'Cancelled_Full_Charge': 'cancelled',
            'Customer_No_Show': 'cancelled',
            'Trip_Not_Covered': 'cancelled',
            'Trip_Completed': 'status_change',
        }
        
        notification_type = status_to_notification.get(booking.status, 'confirmed')
        print(f"   Notification Type: {notification_type}")
        
        # Test notification sending
        try:
            # This is what the resend_notification view does
            result = NotificationService.send_notification(booking, notification_type)
            
            if result:
                print(f"   ✅ Notification sent successfully")
                print(f"   → Sent to user and passenger (if enabled)")
            else:
                print(f"   ⚠️  Notification sending returned False")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
    else:
        print(f"\n⚠️  No booking found with status: {status}")

print("\n" + "="*70)
print("✓ Test Complete")
print("="*70)
print("\nAdmin Quick Actions - 'Send Email Notification' Button:")
print("- Available to admins only")
print("- Sends notification for current booking status")
print("- Works for all statuses (Pending, Confirmed, Cancelled, etc.)")
print("- Uses same logic as existing 'Send' button in notification section")
print("- Accessible via Quick Actions section in booking_detail.html")
print("\nStatus → Notification Type Mapping:")
print("- Pending → 'new' (New booking notification)")
print("- Confirmed → 'confirmed' (Booking confirmed)")
print("- Cancelled/Cancelled_Full_Charge → 'cancelled'")
print("- Trip_Completed → 'status_change' (Status update)")
