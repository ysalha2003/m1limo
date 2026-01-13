"""
Management command to multiply existing bookings with Chicago area data.
Creates 4 variations of each existing trip with Chicago locations.
Run with: python manage.py multiply_test_data
"""

from django.core.management.base import BaseCommand
from models import Booking
from django.utils import timezone
from datetime import timedelta
import random


class Command(BaseCommand):
    help = 'Multiply existing bookings with Chicago area locations (4x each)'

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

    def add_arguments(self, parser):
        parser.add_argument(
            '--multiplier',
            type=int,
            default=4,
            help='Number of copies to create from each existing booking (default: 4)'
        )

    def handle(self, *args, **options):
        multiplier = options['multiplier']
        
        self.stdout.write(self.style.WARNING(f"\nMultiplying existing bookings by {multiplier}x with Chicago area data..."))
        self.stdout.write("="*70)

        # Get all existing bookings
        existing_bookings = list(Booking.objects.all().order_by('id'))
        
        if not existing_bookings:
            self.stdout.write(self.style.ERROR("No existing bookings found!"))
            return

        self.stdout.write(f"Found {len(existing_bookings)} existing bookings")
        
        created_count = 0
        
        for booking in existing_bookings:
            self.stdout.write(f"\n📋 Multiplying Booking #{booking.id} ({booking.trip_type})...")
            
            # Skip if it's a return trip (we'll handle it with the outbound)
            if booking.is_return_trip:
                self.stdout.write(f"  ⏩ Skipping (return trip will be created with outbound)")
                continue
            
            for i in range(multiplier):
                # Create variation of the booking
                new_booking_data = {
                    'user': booking.user,
                    'passenger_name': random.choice(self.PASSENGER_NAMES),
                    'contact_number': random.choice(self.CONTACT_NUMBERS),
                    'pickup_address': random.choice(self.CHICAGO_LOCATIONS),
                    'pickup_date': booking.pickup_date + timedelta(days=random.randint(1, 30)),
                    'pickup_time': booking.pickup_time,
                    'trip_type': booking.trip_type,
                    'vehicle_type': booking.vehicle_type,
                    'number_of_passengers': random.randint(1, min(6, booking.number_of_passengers + 2)),
                    'status': random.choice(['Pending', 'Confirmed', 'Confirmed']) if booking.status == 'Confirmed' else booking.status,
                    'is_return_trip': False,
                }
                
                # Handle trip type specific fields
                if booking.trip_type == 'Hourly':
                    new_booking_data['drop_off_address'] = None
                    new_booking_data['duration_hours'] = booking.duration_hours or random.choice([3, 4, 5, 6, 8])
                else:
                    # Get drop-off from Chicago locations, ensure it's different from pickup
                    available_dropoffs = [loc for loc in self.CHICAGO_LOCATIONS if loc != new_booking_data['pickup_address']]
                    new_booking_data['drop_off_address'] = random.choice(available_dropoffs)
                    new_booking_data['duration_hours'] = None
                
                # Copy stops if any
                if booking.stops:
                    # Randomly select 0-3 stops from Chicago locations
                    num_stops = random.randint(0, 3)
                    if num_stops > 0:
                        stops = random.sample([loc for loc in self.CHICAGO_LOCATIONS 
                                             if loc != new_booking_data['pickup_address'] 
                                             and loc != new_booking_data.get('drop_off_address')], 
                                            min(num_stops, len(self.CHICAGO_LOCATIONS) - 2))
                        new_booking_data['stops'] = ', '.join(stops)
                
                # Create the new booking
                new_booking = Booking.objects.create(**new_booking_data)
                created_count += 1
                
                self.stdout.write(
                    f"  ✓ Created #{new_booking.id}: {new_booking.passenger_name} | "
                    f"{new_booking.pickup_date} | {new_booking.status} | "
                    f"{new_booking.trip_type}"
                )
                
                # If original was a round trip, create return trip too
                if booking.trip_type == 'Round' and booking.linked_booking:
                    original_return = booking.linked_booking
                    
                    # Create return trip
                    return_booking_data = {
                        'user': new_booking.user,
                        'passenger_name': new_booking.passenger_name,
                        'contact_number': new_booking.contact_number,
                        'pickup_address': new_booking.drop_off_address,  # Swap addresses
                        'drop_off_address': new_booking.pickup_address,
                        'pickup_date': new_booking.pickup_date + timedelta(days=random.randint(1, 7)),
                        'pickup_time': original_return.pickup_time if original_return else new_booking.pickup_time,
                        'trip_type': 'Round',
                        'vehicle_type': new_booking.vehicle_type,
                        'number_of_passengers': new_booking.number_of_passengers,
                        'status': new_booking.status,
                        'is_return_trip': True,
                        'duration_hours': None,
                    }
                    
                    # Copy return stops if any
                    if original_return and original_return.stops:
                        num_stops = random.randint(0, 3)
                        if num_stops > 0:
                            stops = random.sample([loc for loc in self.CHICAGO_LOCATIONS 
                                                 if loc != return_booking_data['pickup_address'] 
                                                 and loc != return_booking_data['drop_off_address']], 
                                                min(num_stops, len(self.CHICAGO_LOCATIONS) - 2))
                            return_booking_data['stops'] = ', '.join(stops)
                    
                    return_booking = Booking.objects.create(**return_booking_data)
                    created_count += 1
                    
                    # Link the trips
                    new_booking.linked_booking = return_booking
                    new_booking.save()
                    
                    return_booking.linked_booking = new_booking
                    return_booking.save()
                    
                    self.stdout.write(
                        f"  ✓ Created #{return_booking.id}: Return trip | "
                        f"{return_booking.pickup_date} | {return_booking.status}"
                    )
        
        self.stdout.write("\n" + "="*70)
        self.stdout.write(self.style.SUCCESS(f"✅ MULTIPLICATION COMPLETE"))
        self.stdout.write("="*70)
        self.stdout.write(f"Original bookings: {len(existing_bookings)}")
        self.stdout.write(f"New bookings created: {created_count}")
        self.stdout.write(f"Total bookings now: {Booking.objects.count()}")
        self.stdout.write(f"Multiplier used: {multiplier}x")
        self.stdout.write("="*70 + "\n")
