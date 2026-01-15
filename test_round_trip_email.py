#!/usr/bin/env python
"""
Test script to verify round trip email template rendering.
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from django.template.loader import render_to_string
from models import Booking
from django.conf import settings

def test_round_trip_template():
    """Test round trip email template with actual booking data"""
    
    print("\n" + "="*80)
    print("ROUND TRIP EMAIL TEMPLATE TEST")
    print("="*80)
    
    # Find a round trip booking
    outbound = Booking.objects.filter(
        trip_type='Round',
        linked_booking__isnull=False
    ).first()
    
    if not outbound:
        print("❌ No round trip bookings found")
        return
    
    return_trip = outbound.linked_booking
    
    print(f"\nTest Data:")
    print(f"Outbound Trip: #{outbound.id}")
    print(f"  Date/Time: {outbound.pick_up_date} at {outbound.pick_up_time}")
    print(f"  Route: {outbound.pick_up_address} → {outbound.drop_off_address}")
    print(f"\nReturn Trip: #{return_trip.id}")
    print(f"  Date/Time: {return_trip.pick_up_date} at {return_trip.pick_up_time}")
    print(f"  Route: {return_trip.pick_up_address} → {return_trip.drop_off_address}")
    
    # Test different notification types
    notification_types = ['new', 'confirmed', 'cancelled', 'status_change']
    
    for notification_type in notification_types:
        print(f"\n" + "-"*80)
        print(f"Testing: {notification_type}")
        print("-"*80)
        
        booking_url = f"{settings.BASE_URL}/reservation/{outbound.id}/"
        
        context = {
            'booking': outbound,
            'first_trip': outbound,
            'return_trip': return_trip,
            'notification_type': notification_type,
            'booking_url': booking_url,
            'old_status': 'Pending' if notification_type == 'status_change' else None,
        }
        
        try:
            html_content = render_to_string('emails/round_trip_notification.html', context)
            
            # Check for key elements
            checks = [
                (outbound.passenger_name in html_content, f"Passenger name: {outbound.passenger_name}"),
                (str(outbound.pick_up_date.strftime('%b')) in html_content, f"Outbound date present"),
                (outbound.pick_up_address in html_content, f"Outbound pickup: {outbound.pick_up_address}"),
                (return_trip.pick_up_address in html_content, f"Return pickup: {return_trip.pick_up_address}"),
                (booking_url in html_content, f"Booking URL: {booking_url}"),
                (f"#{outbound.id}" in html_content, f"Booking ID: #{outbound.id}"),
            ]
            
            all_passed = True
            for passed, description in checks:
                status = "✓" if passed else "✗"
                print(f"  {status} {description}")
                if not passed:
                    all_passed = False
            
            if all_passed:
                print(f"  ✅ All checks passed for {notification_type}")
            else:
                print(f"  ⚠️  Some checks failed for {notification_type}")
                
        except Exception as e:
            print(f"  ❌ Template rendering error: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)
    
    # Save a sample HTML file for inspection
    print("\nSaving sample HTML for manual inspection...")
    context = {
        'booking': outbound,
        'first_trip': outbound,
        'return_trip': return_trip,
        'notification_type': 'confirmed',
        'booking_url': booking_url,
    }
    
    html_content = render_to_string('emails/round_trip_notification.html', context)
    
    output_file = 'test_round_trip_email_output.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ Sample HTML saved to: {output_file}")
    print("   Open this file in a browser to see the rendered email")

if __name__ == '__main__':
    test_round_trip_template()
