"""
Script to generate round trip bookings with proper Chicago area data.
Run with: python create_round_trips.py [number_of_trips]
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from django.contrib.auth.models import User
from models import Booking
from datetime import datetime, timedelta, time
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
    
    # Suburbs - West
    'Oak Brook Center, 160 Oakbrook Center, Oak Brook, IL 60523',
    'Naperville Downtown, 23 W Jefferson Ave, Naperville, IL 60540',
    'Schaumburg Convention Center, 1551 N Thoreau Dr, Schaumburg, IL 60173',
    
    # Suburbs - South
    'Orland Square Mall, 288 Orland Square Dr, Orland Park, IL 60462',
    'Tinley Park Convention Center, 18451 Convention Center Dr, Tinley Park, IL 60477',
    
    # Business Districts
    'Chicago Board of Trade, 141 W Jackson Blvd, Chicago, IL 60604',
    'Merchandise Mart, 222 W Merchandise Mart Plaza, Chicago, IL 60654',
    'Northwestern Memorial Hospital, 251 E Huron St, Chicago, IL 60611',
    'University of Chicago, 5801 S Ellis Ave, Chicago, IL 60637',
]

PASSENGER_NAMES = [
    'John Anderson', 'Sarah Martinez', 'Michael Johnson', 'Emily Williams',
    'David Brown', 'Jessica Davis', 'Christopher Wilson', 'Amanda Taylor',
    'Matthew Garcia', 'Ashley Rodriguez', 'Daniel Martinez', 'Jennifer Lee',
    'James Thompson', 'Lisa White', 'Robert Harris', 'Karen Clark',
]

CONTACT_NUMBERS = [
    '312-555-0101', '312-555-0102', '312-555-0103', '312-555-0104',
    '773-555-0201', '773-555-0202', '773-555-0203', '773-555-0204',
    '630-555-0301', '630-555-0302', '630-555-0303', '630-555-0304',
]


def create_round_trips(num_trips=5):
    """Create round trip bookings"""
    
    print(f"\n{'='*70}")
    print(f"Creating {num_trips} Round Trip bookings with Chicago data...")
    print(f"{'='*70}\n")
    
    # Get or create user
    try:
        user = User.objects.get(username='testuser')
    except User.DoesNotExist:
        user = User.objects.create_user(
            username='testuser',
            email='test@m1limo.com',
            password='test123'
        )
        print(f"✓ Created user: {user.username}")
    
    base_date = datetime.now().date() + timedelta(days=3)
    created_count = 0
    
    for i in range(num_trips):
        # Random details
        passenger_name = random.choice(PASSENGER_NAMES)
        phone_number = random.choice(CONTACT_NUMBERS)
        vehicle_type = random.choice(['Sedan', 'SUV', 'Sprinter Van'])
        
        # Get max passengers for vehicle
        max_passengers = Booking.VEHICLE_CAPACITY.get(vehicle_type, 6)
        num_passengers = random.randint(1, max_passengers)
        
        # Pick locations
        pickup = random.choice(CHICAGO_LOCATIONS)
        available_dropoffs = [loc for loc in CHICAGO_LOCATIONS if loc != pickup]
        dropoff = random.choice(available_dropoffs)
        
        # Dates
        outbound_date = base_date + timedelta(days=random.randint(1, 20))
        return_date = outbound_date + timedelta(days=random.randint(1, 7))
        
        # Times
        outbound_time = time(hour=random.choice([8, 9, 10, 11, 14, 15, 16]), minute=random.choice([0, 15, 30]))
        return_time = time(hour=random.choice([9, 10, 11, 12, 15, 16, 17]), minute=random.choice([0, 15, 30]))
        
        status = random.choice(['Pending', 'Confirmed', 'Confirmed'])
        
        try:
            # Create OUTBOUND trip with legacy return fields
            outbound = Booking.objects.create(
                user=user,
                passenger_name=passenger_name,
                phone_number=phone_number,
                pick_up_address=pickup,
                drop_off_address=dropoff,
                pick_up_date=outbound_date,
                pick_up_time=outbound_time,
                trip_type='Round',
                vehicle_type=vehicle_type,
                number_of_passengers=num_passengers,
                status=status,
                is_return_trip=False,
                # Legacy fields required for validation
                return_date=return_date,
                return_time=return_time,
                return_pickup_address=dropoff,  # Swap addresses for return
                return_dropoff_address=pickup,
            )
            created_count += 1
            
            print(f"✓ Created Outbound #{outbound.id}: {passenger_name}")
            print(f"  📍 {pickup[:50]}... → {dropoff[:50]}...")
            print(f"  📅 {outbound_date} @ {outbound_time} | {vehicle_type} | {status}")
            
            # Create RETURN trip
            return_booking = Booking.objects.create(
                user=user,
                passenger_name=passenger_name,
                phone_number=phone_number,
                pick_up_address=dropoff,  # Swap addresses
                drop_off_address=pickup,
                pick_up_date=return_date,
                pick_up_time=return_time,
                trip_type='Round',
                vehicle_type=vehicle_type,
                number_of_passengers=num_passengers,
                status=status,
                is_return_trip=True,
            )
            created_count += 1
            
            # Link the trips
            outbound.linked_booking = return_booking
            outbound.save()
            
            return_booking.linked_booking = outbound
            return_booking.save()
            
            print(f"✓ Created Return #{return_booking.id}: {passenger_name}")
            print(f"  📍 {dropoff[:50]}... → {pickup[:50]}...")
            print(f"  📅 {return_date} @ {return_time}\n")
            
        except Exception as e:
            print(f"❌ Error creating round trip {i+1}: {e}\n")
            continue
    
    print(f"{'='*70}")
    print("✅ ROUND TRIPS CREATED")
    print(f"{'='*70}")
    print(f"Round trips created: {num_trips}")
    print(f"Total bookings created: {created_count}")
    print(f"Total bookings in DB: {Booking.objects.count()}")
    print(f"Round trip bookings: {Booking.objects.filter(trip_type='Round').count()}")
    print(f"{'='*70}\n")


if __name__ == '__main__':
    num_trips = 5
    if len(sys.argv) > 1:
        try:
            num_trips = int(sys.argv[1])
        except ValueError:
            print("Usage: python create_round_trips.py [number_of_trips]")
            print("Example: python create_round_trips.py 10")
            sys.exit(1)
    
    create_round_trips(num_trips)
