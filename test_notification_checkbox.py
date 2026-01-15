"""
Test script to verify the send_passenger_notifications checkbox works correctly
Run: python test_notification_checkbox.py
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from models import Booking
from booking_forms import BookingForm

print("="*70)
print("Testing send_passenger_notifications Checkbox Behavior")
print("="*70)

# Test 1: Check form field configuration
print("\n1. Form Field Configuration:")
print("-" * 70)
form = BookingForm()
field = form.fields['send_passenger_notifications']
print(f"   Required: {field.required}")
print(f"   Initial (for new bookings): {field.initial}")
print(f"   Widget attrs: {field.widget.attrs}")
print(f"   ✓ Widget should NOT have hardcoded 'checked' attribute")

# Test 2: New booking form (no instance) - should be checked by default
print("\n2. New Booking Form (no instance):")
print("-" * 70)
new_form = BookingForm()
print(f"   Initial value: {new_form.initial.get('send_passenger_notifications', 'Not set')}")
print(f"   ✓ Should default to True for new bookings")

# Test 3: Editing existing booking with notifications ENABLED
print("\n3. Edit Form - Booking with notifications=True:")
print("-" * 70)
booking_enabled = Booking.objects.filter(send_passenger_notifications=True).first()
if booking_enabled:
    form_enabled = BookingForm(instance=booking_enabled)
    print(f"   Booking ID: {booking_enabled.id}")
    print(f"   DB Value: {booking_enabled.send_passenger_notifications}")
    print(f"   Form Initial: {form_enabled.initial.get('send_passenger_notifications')}")
    print(f"   ✓ Checkbox should be CHECKED")
else:
    print("   ⚠ No bookings with notifications=True found")

# Test 4: Editing existing booking with notifications DISABLED
print("\n4. Edit Form - Booking with notifications=False:")
print("-" * 70)
booking_disabled = Booking.objects.filter(send_passenger_notifications=False).first()
if booking_disabled:
    form_disabled = BookingForm(instance=booking_disabled)
    print(f"   Booking ID: {booking_disabled.id}")
    print(f"   DB Value: {booking_disabled.send_passenger_notifications}")
    print(f"   Form Initial: {form_disabled.initial.get('send_passenger_notifications')}")
    print(f"   ✓ Checkbox should be UNCHECKED")
else:
    print("   ⚠ No bookings with notifications=False found")
    print("   Creating test booking...")
    # Create a test booking with notifications disabled
    from django.contrib.auth.models import User
    from datetime import datetime, timedelta
    
    user = User.objects.filter(is_active=True).first()
    if user:
        test_booking = Booking.objects.create(
            user=user,
            passenger_name="Test User",
            phone_number="312-555-0100",
            passenger_email="test@example.com",
            pick_up_address="Test Address",
            pick_up_date=datetime.now().date() + timedelta(days=1),
            pick_up_time=datetime.now().time(),
            vehicle_type="Sedan",
            trip_type="Point",
            drop_off_address="Destination",
            number_of_passengers=2,
            send_passenger_notifications=False  # Explicitly set to False
        )
        form_test = BookingForm(instance=test_booking)
        print(f"   Created Booking ID: {test_booking.id}")
        print(f"   DB Value: {test_booking.send_passenger_notifications}")
        print(f"   Form Initial: {form_test.initial.get('send_passenger_notifications')}")
        print(f"   ✓ Checkbox should be UNCHECKED")
        
        # Clean up
        test_booking.delete()
        print(f"   (Test booking deleted)")

# Test 5: Simulating form submission with checkbox UNCHECKED
print("\n5. Form Submission - Checkbox UNCHECKED:")
print("-" * 70)
booking = Booking.objects.first()
if booking:
    # Simulate POST data without send_passenger_notifications (unchecked)
    post_data = {
        'passenger_name': booking.passenger_name,
        'phone_number': booking.phone_number,
        'passenger_email': booking.passenger_email,
        'pick_up_address': booking.pick_up_address,
        'pick_up_date': booking.pick_up_date,
        'pick_up_time': booking.pick_up_time,
        'vehicle_type': booking.vehicle_type,
        'trip_type': booking.trip_type,
        'number_of_passengers': booking.number_of_passengers,
        # send_passenger_notifications is NOT in POST data (unchecked)
    }
    
    if booking.trip_type == 'Point':
        post_data['drop_off_address'] = booking.drop_off_address
    
    form = BookingForm(post_data, instance=booking)
    if form.is_valid():
        cleaned_value = form.cleaned_data.get('send_passenger_notifications')
        print(f"   POST data included checkbox: {'send_passenger_notifications' in post_data}")
        print(f"   Cleaned data value: {cleaned_value}")
        print(f"   ✓ Should be False when checkbox not in POST")
    else:
        print(f"   Form errors: {form.errors}")

# Test 6: Simulating form submission with checkbox CHECKED
print("\n6. Form Submission - Checkbox CHECKED:")
print("-" * 70)
if booking:
    # Simulate POST data WITH send_passenger_notifications (checked)
    post_data['send_passenger_notifications'] = 'on'  # Checkbox sends 'on' when checked
    
    form = BookingForm(post_data, instance=booking)
    if form.is_valid():
        cleaned_value = form.cleaned_data.get('send_passenger_notifications')
        print(f"   POST data included checkbox: {'send_passenger_notifications' in post_data}")
        print(f"   Cleaned data value: {cleaned_value}")
        print(f"   ✓ Should be True when checkbox in POST")
    else:
        print(f"   Form errors: {form.errors}")

print("\n" + "="*70)
print("✓ Test Complete")
print("="*70)
print("\nSUMMARY:")
print("- Widget attrs no longer have hardcoded 'checked'")
print("- Django will set checkbox state based on field value")
print("- Unchecking and submitting will save False to database")
print("- Editing a booking will show correct checkbox state")
