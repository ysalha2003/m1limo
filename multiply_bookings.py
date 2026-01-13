"""
Script to multiply existing bookings with Chicago area data.
Creates 4 variations of each existing trip with Chicago locations.

Run with: python multiply_bookings.py
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from models import Booking
from datetime import timedelta
import random


# Chicago area locations
CHICAGO_LOCATIONS = [
    # Downtown Chicago
    'Willis Tower, 233 S Wacker Dr, Chicago, IL 60606',
    'Navy Pier, 600 E Grand Ave, Chicago, IL 60611',
    'The Art Institute, 111 S Michigan Ave, Chicago, IL 60603',
    'Millennium Park, 201 E Randolph St, Chicago, IL 60602',
    'Union Station, 225 S Canal St, Chicago, IL 60606',
    'Water Tower Place, 835 N Michigan Ave, Chicago, IL 60611',
    'Chicago Riverwalk, 450 E Benton Pl, Chicago, IL 60601',
    
    # Hotels
    'The Langham Chicago, 330 N Wabash Ave, Chicago, IL 60611',
    'Palmer House Hilton, 17 E Monroe St, Chicago, IL 60603',
    'Four Seasons Chicago, 120 E Delaware Pl, Chicago, IL 60611',
    'The Drake Hotel, 140 E Walton Pl, Chicago, IL 60611',
    'Hyatt Regency Chicago, 151 E Wacker Dr, Chicago, IL 60601',
    
    # Airports
    "O'Hare International Airport (ORD), Chicago, IL 60666",
    'Midway International Airport (MDW), 5700 S Cicero Ave, Chicago, IL 60638',
    
    # Suburbs - North
    'Evanston Downtown, Davis St & Sherman Ave, Evanston, IL 60201',
    'Glenview Town Center, 2000 Tower Dr, Glenview, IL 60026',
    'Northbrook Court, 2171 Northbrook Ct, Northbrook, IL 60062',
    'Skokie Village Hall, 5127 Oakton St, Skokie, IL 60077',
    
    # Suburbs - West
    'Oak Brook Center, 160 Oakbrook Center, Oak Brook, IL 60523',
    'Naperville Downtown, 23 W Jefferson Ave, Naperville, IL 60540',
    'Schaumburg Convention Center, 1551 N Thoreau Dr, Schaumburg, IL 60173',
    'Wheaton Town Center, 301 W Wesley St, Wheaton, IL 60187',
    
    # Suburbs - South
    'Orland Square Mall, 288 Orland Square Dr, Orland Park, IL 60462',
    'Tinley Park Convention Center, 18451 Convention Center Dr, Tinley Park, IL 60477',
    'Oak Lawn Village Hall, 5252 Dumke Dr, Oak Lawn, IL 60453',
    
    # Business Districts
    'Chicago Board of Trade, 141 W Jackson Blvd, Chicago, IL 60604',
    'Merchandise Mart, 222 W Merchandise Mart Plaza, Chicago, IL 60654',
    'Northwestern Memorial Hospital, 251 E Huron St, Chicago, IL 60611',
    'University of Chicago, 5801 S Ellis Ave, Chicago, IL 60637',
    'Loyola University Chicago, 1032 W Sheridan Rd, Chicago, IL 60660',
    
    # Residential Areas
    'Lincoln Park, 2045 N Lincoln Park West, Chicago, IL 60614',
    'Wicker Park, 1425 N Damen Ave, Chicago, IL 60622',
    'River North, 750 N Orleans St, Chicago, IL 60654',
    'Gold Coast, 1100 N Lake Shore Dr, Chicago, IL 60611',
]

PASSENGER_NAMES = [
    'John Anderson', 'Sarah Martinez', 'Michael Johnson', 'Emily Williams',
    'David Brown', 'Jessica Davis', 'Christopher Wilson', 'Amanda Taylor',
    'Matthew Garcia', 'Ashley Rodriguez', 'Daniel Martinez', 'Jennifer Lee',
    'James Thompson', 'Lisa White', 'Robert Harris', 'Karen Clark',
    'Joseph Lewis', 'Nancy Hall', 'Thomas Walker', 'Betty Young'
]

CONTACT_NUMBERS = [
    '312-555-0101', '312-555-0102', '312-555-0103', '312-555-0104',
    '773-555-0201', '773-555-0202', '773-555-0203', '773-555-0204',
    '630-555-0301', '630-555-0302', '630-555-0303', '630-555-0304',
    '847-555-0401', '847-555-0402', '847-555-0403', '847-555-0404',
]


def multiply_bookings(multiplier=4):
    """Multiply existing bookings with Chicago area data"""
    
    print(f"\n{'='*70}")
    print(f"Multiplying existing bookings by {multiplier}x with Chicago area data...")
    print(f"{'='*70}\n")

    # Get all existing bookings
    existing_bookings = list(Booking.objects.all().order_by('id'))
    
    if not existing_bookings:
        print("❌ No existing bookings found!")
        return

    print(f"Found {len(existing_bookings)} existing bookings\n")
    
    created_count = 0
    
    for booking in existing_bookings:
        print(f"📋 Multiplying Booking #{booking.id} ({booking.trip_type})...")
        
        # Skip if it's a return trip (we'll handle it with the outbound)
        if booking.is_return_trip:
            print(f"  ⏩ Skipping (return trip will be created with outbound)")
            continue
        
        for i in range(multiplier):
            # Create variation of the booking
            new_booking_data = {
                'user': booking.user,
                'passenger_name': random.choice(PASSENGER_NAMES),
                'phone_number': random.choice(CONTACT_NUMBERS),
                'pick_up_address': random.choice(CHICAGO_LOCATIONS),
                'pick_up_date': booking.pick_up_date + timedelta(days=random.randint(1, 30)),
                'pick_up_time': booking.pick_up_time,
                'trip_type': booking.trip_type,
                'vehicle_type': booking.vehicle_type,
                'number_of_passengers': min(booking.number_of_passengers, Booking.VEHICLE_CAPACITY.get(booking.vehicle_type, 6)),
                'status': random.choice(['Pending', 'Confirmed', 'Confirmed']) if booking.status == 'Confirmed' else booking.status,
                'is_return_trip': False,
            }
            
            # Handle trip type specific fields
            if booking.trip_type == 'Hourly':
                new_booking_data['drop_off_address'] = None
                new_booking_data['hours_booked'] = booking.hours_booked or random.choice([3, 4, 5, 6, 8])
            else:
                # Get drop-off from Chicago locations, ensure it's different from pickup
                available_dropoffs = [loc for loc in CHICAGO_LOCATIONS if loc != new_booking_data['pick_up_address']]
                new_booking_data['drop_off_address'] = random.choice(available_dropoffs)
                new_booking_data['hours_booked'] = None
            

            # Create the new booking
            new_booking = Booking.objects.create(**new_booking_data)
            created_count += 1
            
            print(f"  ✓ Created #{new_booking.id}: {new_booking.passenger_name} | "
                  f"{new_booking.pick_up_date} | {new_booking.status} | {new_booking.trip_type}")
    
    print(f"\n{'='*70}")
    print("✅ MULTIPLICATION COMPLETE")
    print(f"{'='*70}")
    print(f"Original bookings: {len(existing_bookings)}")
    print(f"New bookings created: {created_count}")
    print(f"Total bookings now: {Booking.objects.count()}")
    print(f"Multiplier used: {multiplier}x")
    print(f"{'='*70}\n")


if __name__ == '__main__':
    multiplier = 4
    if len(sys.argv) > 1:
        try:
            multiplier = int(sys.argv[1])
        except ValueError:
            print("Usage: python multiply_bookings.py [multiplier]")
            print("Example: python multiply_bookings.py 4")
            sys.exit(1)
    
    multiply_bookings(multiplier)
