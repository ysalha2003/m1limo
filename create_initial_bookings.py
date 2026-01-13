"""
Script to create initial test bookings before multiplying.
Run with: python create_initial_bookings.py
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from django.contrib.auth.models import User
from models import Booking
from datetime import datetime, timedelta


def create_initial_bookings():
    """Create a few initial bookings to multiply from"""
    
    print("\n" + "="*70)
    print("Creating initial test bookings...")
    print("="*70 + "\n")
    
    # Get or create a test user
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={
            'email': 'test@m1limo.com',
            'first_name': 'Test',
            'last_name': 'User'
        }
    )
    if created:
        user.set_password('test123')
        user.save()
        print(f"✓ Created user: {user.username}")
    else:
        print(f"✓ Using existing user: {user.username}")
    
    base_date = datetime.now().date() + timedelta(days=3)
    
    # Create a few sample bookings
    bookings_data = [
        {
            'passenger_name': 'John Smith',
            'phone_number': '555-0001',
            'pick_up_address': '123 Main St, City',
            'drop_off_address': '456 Business Ave, Town',
            'trip_type': 'Point',
            'vehicle_type': 'Sedan',
            'status': 'Confirmed',
        },
        {
            'passenger_name': 'Jane Doe',
            'phone_number': '555-0002',
            'pick_up_address': '789 Airport Rd',
            'drop_off_address': None,
            'trip_type': 'Hourly',
            'vehicle_type': 'SUV',
            'status': 'Confirmed',
            'hours_booked': 4,
        },
        {
            'passenger_name': 'Bob Johnson',
            'phone_number': '555-0003',
            'pick_up_address': '321 Home St',
            'drop_off_address': '654 Airport Terminal',
            'trip_type': 'Point',  # Changed to Point since Round requires return dates
            'vehicle_type': 'Sedan',
            'status': 'Pending',
        },
    ]
    
    created_bookings = []
    
    for i, data in enumerate(bookings_data):
        booking = Booking.objects.create(
            user=user,
            passenger_name=data['passenger_name'],
            phone_number=data['phone_number'],
            pick_up_address=data['pick_up_address'],
            drop_off_address=data.get('drop_off_address'),
            pick_up_date=base_date + timedelta(days=i*2),
            pick_up_time='10:00',
            trip_type=data['trip_type'],
            vehicle_type=data['vehicle_type'],
            number_of_passengers=2,
            status=data['status'],
            hours_booked=data.get('hours_booked'),
        )
        created_bookings.append(booking)
        print(f"✓ Created Booking #{booking.id}: {booking.passenger_name} | {booking.trip_type} | {booking.status}")
    
    print(f"\n{'='*70}")
    print("✅ INITIAL BOOKINGS CREATED")
    print(f"{'='*70}")
    print(f"Total bookings: {Booking.objects.count()}")
    print(f"{'='*70}\n")


if __name__ == '__main__':
    create_initial_bookings()
