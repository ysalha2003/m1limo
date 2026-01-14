#!/usr/bin/env python
"""Test script to verify booking form works with separate phone and email fields"""

import os
import sys
import django
import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from booking_forms import BookingForm

def test_form_with_both_fields():
    """Test form with both phone and email provided"""
    print("Test 1: Form with both phone and email")
    data = {
        'passenger_name': 'Test User',
        'phone_number': '+1234567890',
        'passenger_email': 'test@example.com',
        'pick_up_address': '123 Test St',
        'pick_up_date': datetime.date.today(),
        'pick_up_time': '10:00',
        'trip_type': 'One',
        'number_of_passengers': 1,
    }
    form = BookingForm(data)
    print(f"  Valid: {form.is_valid()}")
    if not form.is_valid():
        print(f"  Errors: {form.errors}")
    print()

def test_form_missing_phone():
    """Test form with missing phone"""
    print("Test 2: Form with missing phone (should fail)")
    data = {
        'passenger_name': 'Test User',
        'passenger_email': 'test@example.com',
        'pick_up_address': '123 Test St',
        'pick_up_date': datetime.date.today(),
        'pick_up_time': '10:00',
        'trip_type': 'One',
        'number_of_passengers': 1,
    }
    form = BookingForm(data)
    print(f"  Valid: {form.is_valid()}")
    if not form.is_valid():
        print(f"  Errors: {form.errors}")
    print()

def test_form_missing_email():
    """Test form with missing email"""
    print("Test 3: Form with missing email (should fail)")
    data = {
        'passenger_name': 'Test User',
        'phone_number': '+1234567890',
        'pick_up_address': '123 Test St',
        'pick_up_date': datetime.date.today(),
        'pick_up_time': '10:00',
        'trip_type': 'One',
        'number_of_passengers': 1,
    }
    form = BookingForm(data)
    print(f"  Valid: {form.is_valid()}")
    if not form.is_valid():
        print(f"  Errors: {form.errors}")
    print()

def test_form_invalid_phone():
    """Test form with invalid phone format"""
    print("Test 4: Form with invalid phone format (should fail)")
    data = {
        'passenger_name': 'Test User',
        'phone_number': 'abc',
        'passenger_email': 'test@example.com',
        'pick_up_address': '123 Test St',
        'pick_up_date': datetime.date.today(),
        'pick_up_time': '10:00',
        'trip_type': 'One',
        'number_of_passengers': 1,
    }
    form = BookingForm(data)
    print(f"  Valid: {form.is_valid()}")
    if not form.is_valid():
        print(f"  Errors: {form.errors}")
    print()

if __name__ == '__main__':
    print("=" * 60)
    print("Booking Form Validation Tests")
    print("=" * 60)
    print()
    
    test_form_with_both_fields()
    test_form_missing_phone()
    test_form_missing_email()
    test_form_invalid_phone()
    
    print("=" * 60)
    print("Tests complete!")
    print("=" * 60)
