"""
Master Test Data Generation Script for M1 Limo
================================================

This script will:
1. Flush all existing bookings
2. Generate comprehensive test data with all new features:
   - send_passenger_notifications field
   - additional_recipients field
   - Round trip bookings with proper linking
   - Various statuses and vehicle types
   - Chicago area locations

Usage:
    python reset_and_generate_test_data.py [number_of_trips]
    
Example:
    python reset_and_generate_test_data.py 20
    
VPS Usage:
    cd /opt/m1limo
    source venv/bin/activate
    python reset_and_generate_test_data.py 20

Test Emails: yaser.salha.se+1@gmail.com through yaser.salha.se+20@gmail.com
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


# =============================================================================
# CONFIGURATION
# =============================================================================

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
    'Swissotel Chicago, 323 E Wacker Dr, Chicago, IL 60601',
    
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
    'Wheaton College, 501 College Ave, Wheaton, IL 60187',
    
    # Suburbs - South
    'Orland Square Mall, 288 Orland Square Dr, Orland Park, IL 60462',
    'Tinley Park Convention Center, 18451 Convention Center Dr, Tinley Park, IL 60477',
    
    # Business Districts
    'Chicago Board of Trade, 141 W Jackson Blvd, Chicago, IL 60604',
    'Merchandise Mart, 222 W Merchandise Mart Plaza, Chicago, IL 60654',
    'Northwestern Memorial Hospital, 251 E Huron St, Chicago, IL 60611',
    'University of Chicago, 5801 S Ellis Ave, Chicago, IL 60637',
    'Illinois Institute of Technology, 3300 S Federal St, Chicago, IL 60616',
]

# Passenger names
PASSENGER_NAMES = [
    'John Anderson', 'Sarah Martinez', 'Michael Johnson', 'Emily Williams',
    'David Brown', 'Jessica Davis', 'Christopher Wilson', 'Amanda Taylor',
    'Matthew Garcia', 'Ashley Rodriguez', 'Daniel Martinez', 'Jennifer Lee',
    'James Thompson', 'Lisa White', 'Robert Harris', 'Karen Clark',
    'Thomas Moore', 'Nancy Martin', 'Charles Jackson', 'Betty Thomas',
]

# Contact numbers
CONTACT_NUMBERS = [
    '312-555-0101', '312-555-0102', '312-555-0103', '312-555-0104',
    '773-555-0201', '773-555-0202', '773-555-0203', '773-555-0204',
    '630-555-0301', '630-555-0302', '630-555-0303', '630-555-0304',
    '847-555-0401', '847-555-0402', '708-555-0501', '708-555-0502',
]

# Vehicle types with capacities
VEHICLE_TYPES = ['Sedan', 'SUV', 'Sprinter Van']
VEHICLE_CAPACITY = {'Sedan': 2, 'SUV': 6, 'Sprinter Van': 12}

# Booking statuses
STATUSES = ['Pending', 'Confirmed', 'Confirmed', 'Confirmed']  # Weighted toward Confirmed

# Trip types
TRIP_TYPES = ['Point', 'Point', 'Round', 'Hourly']  # Weighted toward Point-to-Point


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def generate_test_email(number):
    """Generate test email address"""
    return f'yaser.salha.se+{number}@gmail.com'


def generate_additional_recipients(probability=0.3):
    """
    Generate additional recipients with given probability.
    Returns comma-separated email addresses or None.
    """
    if random.random() > probability:
        return None
    
    # 30% chance of additional recipients
    num_recipients = random.randint(1, 3)
    recipients = [generate_test_email(random.randint(1, 20)) for _ in range(num_recipients)]
    return ', '.join(recipients)


def get_random_location():
    """Get a random Chicago location"""
    return random.choice(CHICAGO_LOCATIONS)


def get_random_date_time(base_date, min_days=1, max_days=30):
    """Generate random date and time for booking"""
    date = base_date + timedelta(days=random.randint(min_days, max_days))
    hour = random.choice([6, 7, 8, 9, 10, 11, 14, 15, 16, 17, 18])
    minute = random.choice([0, 15, 30, 45])
    return date, time(hour=hour, minute=minute)


# =============================================================================
# MAIN FUNCTIONS
# =============================================================================

def flush_all_bookings():
    """Delete all existing bookings"""
    count = Booking.objects.count()
    if count > 0:
        print(f"\n⚠️  Deleting {count} existing bookings...")
        Booking.objects.all().delete()
        print(f"✅ Deleted {count} bookings")
    else:
        print("\n✓ No existing bookings to delete")


def create_test_users():
    """Get the existing 'co' user for all bookings"""
    try:
        user = User.objects.get(username='co')
        print(f"✓ Using existing user: {user.username} ({user.email})")
        return [user]  # Return as list for compatibility
    except User.DoesNotExist:
        print("❌ ERROR: User 'co' not found in database")
        print("   Please create the 'co' user first or modify the script.")
        sys.exit(1)


def create_point_to_point_booking(user, base_date, email_index):
    """Create a point-to-point booking"""
    passenger_name = random.choice(PASSENGER_NAMES)
    phone_number = random.choice(CONTACT_NUMBERS)
    vehicle_type = random.choice(VEHICLE_TYPES)
    max_passengers = VEHICLE_CAPACITY[vehicle_type]
    num_passengers = random.randint(1, max_passengers)
    status = random.choice(STATUSES)
    
    # Locations
    pickup = get_random_location()
    available_dropoffs = [loc for loc in CHICAGO_LOCATIONS if loc != pickup]
    dropoff = random.choice(available_dropoffs)
    
    # Date and time
    pickup_date, pickup_time = get_random_date_time(base_date)
    
    # New features
    send_passenger_notifications = random.choice([True, True, True, False])  # 75% True
    passenger_email = generate_test_email(email_index)
    additional_recipients = generate_additional_recipients(0.3)  # 30% chance
    
    booking = Booking.objects.create(
        user=user,
        passenger_name=passenger_name,
        phone_number=phone_number,
        passenger_email=passenger_email,
        pick_up_address=pickup,
        drop_off_address=dropoff,
        pick_up_date=pickup_date,
        pick_up_time=pickup_time,
        trip_type='Point',
        vehicle_type=vehicle_type,
        number_of_passengers=num_passengers,
        status=status,
        send_passenger_notifications=send_passenger_notifications,
        additional_recipients=additional_recipients,
    )
    
    return booking


def create_round_trip_booking(user, base_date, email_index):
    """Create a round trip booking (outbound + return linked)"""
    passenger_name = random.choice(PASSENGER_NAMES)
    phone_number = random.choice(CONTACT_NUMBERS)
    vehicle_type = random.choice(VEHICLE_TYPES)
    max_passengers = VEHICLE_CAPACITY[vehicle_type]
    num_passengers = random.randint(1, max_passengers)
    status = random.choice(STATUSES)
    
    # Locations
    pickup = get_random_location()
    available_dropoffs = [loc for loc in CHICAGO_LOCATIONS if loc != pickup]
    dropoff = random.choice(available_dropoffs)
    
    # Outbound date/time
    outbound_date, outbound_time = get_random_date_time(base_date, min_days=2, max_days=20)
    
    # Return date/time (1-7 days after outbound)
    return_date = outbound_date + timedelta(days=random.randint(1, 7))
    return_hour = random.choice([9, 10, 11, 12, 15, 16, 17])
    return_time = time(hour=return_hour, minute=random.choice([0, 15, 30]))
    
    # New features
    send_passenger_notifications = random.choice([True, True, True, False])  # 75% True
    passenger_email = generate_test_email(email_index)
    additional_recipients = generate_additional_recipients(0.25)  # 25% chance for round trips
    
    # Create OUTBOUND booking
    outbound = Booking.objects.create(
        user=user,
        passenger_name=passenger_name,
        phone_number=phone_number,
        passenger_email=passenger_email,
        pick_up_address=pickup,
        drop_off_address=dropoff,
        pick_up_date=outbound_date,
        pick_up_time=outbound_time,
        trip_type='Round',
        vehicle_type=vehicle_type,
        number_of_passengers=num_passengers,
        status=status,
        is_return_trip=False,
        send_passenger_notifications=send_passenger_notifications,
        additional_recipients=additional_recipients,
        # Legacy fields for validation
        return_date=return_date,
        return_time=return_time,
        return_pickup_address=dropoff,
        return_dropoff_address=pickup,
    )
    
    # Create RETURN booking (swap addresses)
    return_booking = Booking.objects.create(
        user=user,
        passenger_name=passenger_name,
        phone_number=phone_number,
        passenger_email=passenger_email,
        pick_up_address=dropoff,  # Swap
        drop_off_address=pickup,   # Swap
        pick_up_date=return_date,
        pick_up_time=return_time,
        trip_type='Round',
        vehicle_type=vehicle_type,
        number_of_passengers=num_passengers,
        status=status,
        is_return_trip=True,
        send_passenger_notifications=send_passenger_notifications,
        additional_recipients=additional_recipients,
    )
    
    # Link the bookings
    outbound.linked_booking = return_booking
    outbound.save()
    
    return_booking.linked_booking = outbound
    return_booking.save()
    
    return outbound, return_booking


def create_hourly_booking(user, base_date, email_index):
    """Create an hourly booking"""
    passenger_name = random.choice(PASSENGER_NAMES)
    phone_number = random.choice(CONTACT_NUMBERS)
    vehicle_type = random.choice(VEHICLE_TYPES)
    max_passengers = VEHICLE_CAPACITY[vehicle_type]
    num_passengers = random.randint(1, max_passengers)
    status = random.choice(STATUSES)
    
    # Location
    pickup = get_random_location()
    
    # Date and time
    pickup_date, pickup_time = get_random_date_time(base_date)
    
    # Hours
    hours_booked = random.choice([3, 4, 5, 6, 8])
    
    # New features
    send_passenger_notifications = random.choice([True, True, True, False])
    passenger_email = generate_test_email(email_index)
    additional_recipients = generate_additional_recipients(0.2)  # 20% chance
    
    booking = Booking.objects.create(
        user=user,
        passenger_name=passenger_name,
        phone_number=phone_number,
        passenger_email=passenger_email,
        pick_up_address=pickup,
        drop_off_address='As Directed',
        pick_up_date=pickup_date,
        pick_up_time=pickup_time,
        trip_type='Hourly',
        vehicle_type=vehicle_type,
        number_of_passengers=num_passengers,
        hours_booked=hours_booked,
        status=status,
        send_passenger_notifications=send_passenger_notifications,
        additional_recipients=additional_recipients,
    )
    
    return booking


def generate_test_data(num_bookings=20):
    """Generate comprehensive test data"""
    
    print(f"\n{'='*70}")
    print(f"GENERATING {num_bookings} TEST BOOKINGS")
    print(f"{'='*70}\n")
    
    # Get the 'co' user for all bookings
    users = create_test_users()
    user = users[0]  # Use the 'co' user for all bookings
    base_date = datetime.now().date() + timedelta(days=1)
    
    created_count = 0
    point_count = 0
    round_count = 0
    hourly_count = 0
    
    # Track email index for unique passenger emails
    email_index = 1
    
    for i in range(num_bookings):
        trip_type = random.choice(TRIP_TYPES)
        
        try:
            if trip_type == 'Point':
                booking = create_point_to_point_booking(user, base_date, email_index)
                created_count += 1
                point_count += 1
                print(f"✓ Point-to-Point #{booking.id}: {booking.passenger_name}")
                print(f"  📍 {booking.pick_up_address[:50]}... → {booking.drop_off_address[:50]}...")
                print(f"  📅 {booking.pick_up_date} @ {booking.pick_up_time} | {booking.vehicle_type} | {booking.status}")
                print(f"  📧 Passenger Email: {booking.passenger_email} (notifications: {'✅' if booking.send_passenger_notifications else '❌'})")
                if booking.additional_recipients:
                    print(f"  📧 Additional: {booking.additional_recipients}")
                print()
                
            elif trip_type == 'Round':
                outbound, return_booking = create_round_trip_booking(user, base_date, email_index)
                created_count += 2
                round_count += 1
                print(f"✓ Round Trip #{outbound.id} (Outbound): {outbound.passenger_name}")
                print(f"  📍 {outbound.pick_up_address[:50]}... → {outbound.drop_off_address[:50]}...")
                print(f"  📅 {outbound.pick_up_date} @ {outbound.pick_up_time}")
                print(f"✓ Round Trip #{return_booking.id} (Return): {return_booking.passenger_name}")
                print(f"  📍 {return_booking.pick_up_address[:50]}... → {return_booking.drop_off_address[:50]}...")
                print(f"  📅 {return_booking.pick_up_date} @ {return_booking.pick_up_time}")
                print(f"  📧 Passenger Email: {outbound.passenger_email} (notifications: {'✅' if outbound.send_passenger_notifications else '❌'})")
                if outbound.additional_recipients:
                    print(f"  📧 Additional: {outbound.additional_recipients}")
                print()
                
            else:  # Hourly
                booking = create_hourly_booking(user, base_date, email_index)
                created_count += 1
                hourly_count += 1
                print(f"✓ Hourly #{booking.id}: {booking.passenger_name}")
                print(f"  📍 {booking.pick_up_address[:50]}... ({booking.hours_booked} hours)")
                print(f"  📅 {booking.pick_up_date} @ {booking.pick_up_time} | {booking.vehicle_type} | {booking.status}")
                print(f"  📧 Passenger Email: {booking.passenger_email} (notifications: {'✅' if booking.send_passenger_notifications else '❌'})")
                if booking.additional_recipients:
                    print(f"  📧 Additional: {booking.additional_recipients}")
                print()
            
            # Increment email index (cycle through 1-20)
            email_index = (email_index % 20) + 1
            
        except Exception as e:
            print(f"❌ Error creating booking {i+1}: {e}\n")
            continue
    
    # Print summary
    print(f"{'='*70}")
    print("✅ TEST DATA GENERATION COMPLETE")
    print(f"{'='*70}")
    print(f"Total bookings created: {created_count}")
    print(f"  Point-to-Point: {point_count}")
    print(f"  Round Trips: {round_count} pairs ({round_count * 2} bookings)")
    print(f"  Hourly: {hourly_count}")
    print(f"\nDatabase Statistics:")
    print(f"  Total in DB: {Booking.objects.count()}")
    print(f"  Confirmed: {Booking.objects.filter(status='Confirmed').count()}")
    print(f"  Pending: {Booking.objects.filter(status='Pending').count()}")
    print(f"  With Additional Recipients: {Booking.objects.exclude(additional_recipients=None).exclude(additional_recipients='').count()}")
    print(f"  Passenger Notifications Enabled: {Booking.objects.filter(send_passenger_notifications=True).count()}")
    print(f"{'='*70}\n")


# =============================================================================
# MAIN EXECUTION
# =============================================================================

if __name__ == '__main__':
    num_bookings = 20
    
    if len(sys.argv) > 1:
        try:
            num_bookings = int(sys.argv[1])
        except ValueError:
            print("Usage: python reset_and_generate_test_data.py [number_of_bookings]")
            print("Example: python reset_and_generate_test_data.py 30")
            sys.exit(1)
    
    print("\n" + "="*70)
    print("M1 LIMO - TEST DATA RESET & GENERATION")
    print("="*70)
    print(f"\nThis will DELETE all existing bookings and create {num_bookings} new test bookings.")
    print("Test emails will use: yaser.salha.se+1@gmail.com through yaser.salha.se+20@gmail.com")
    print("\nPress Ctrl+C to cancel...")
    
    try:
        input("\nPress ENTER to continue or Ctrl+C to cancel: ")
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user\n")
        sys.exit(0)
    
    # Execute
    flush_all_bookings()
    generate_test_data(num_bookings)
    
    print("\n✨ Ready to test! Visit http://localhost:8000/dashboard\n")
