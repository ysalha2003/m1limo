"""
Script to flush existing reservations and create new demo data
Usage: python flush_and_create_demo.py
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from django.contrib.auth.models import User
from models import Booking, Driver, BookingHistory, FrequentPassenger
from django.utils import timezone
from datetime import datetime, timedelta
import random

def flush_data():
    """Delete all existing bookings and history"""
    print("\n🗑️  FLUSHING EXISTING DATA...")
    booking_count = Booking.objects.count()
    history_count = BookingHistory.objects.count()
    
    Booking.objects.all().delete()
    BookingHistory.objects.all().delete()
    
    print(f"✓ Deleted {booking_count} bookings")
    print(f"✓ Deleted {history_count} history entries\n")

def create_demo_data():
    """Create comprehensive demo data with all trip types"""
    print("Creating demo data...")
    
    # Create admin user
    admin, created = User.objects.get_or_create(
        username='mo',
        email='mo@m1limo.com',
        defaults={
            'is_staff': True,
            'is_superuser': True,
            'first_name': 'Mo',
            'last_name': 'Admin'
        }
    )
    if created:
        admin.set_password('admin123')
        admin.save()
        print(f'✓ Created admin: {admin.email}')
    else:
        print(f'✓ Admin already exists: {admin.email}')

    # Create regular users with new email addresses
    users_data = [
        ('yaser55', 'yaser.salha.se+55@gmail.com', 'James', 'Anderson', '555-0155'),
        ('yaser56', 'yaser.salha.se+56@gmail.com', 'Sarah', 'Williams', '555-0156'),
        ('yaser57', 'yaser.salha.se+57@gmail.com', 'Michael', 'Brown', '555-0157'),
        ('yaser58', 'yaser.salha.se+58@gmail.com', 'Emily', 'Davis', '555-0158'),
        ('yaser59', 'yaser.salha.se+59@gmail.com', 'David', 'Miller', '555-0159'),
        ('yaser60', 'yaser.salha.se+60@gmail.com', 'Jessica', 'Wilson', '555-0160'),
        ('yaser61', 'yaser.salha.se+61@gmail.com', 'Christopher', 'Moore', '555-0161'),
        ('yaser62', 'yaser.salha.se+62@gmail.com', 'Jennifer', 'Taylor', '555-0162'),
        ('yaser63', 'yaser.salha.se+63@gmail.com', 'Daniel', 'Anderson', '555-0163'),
        ('yaser64', 'yaser.salha.se+64@gmail.com', 'Amanda', 'Thomas', '555-0164'),
        ('yaser65', 'yaser.salha.se+65@gmail.com', 'Matthew', 'Jackson', '555-0165'),
        ('yaser66', 'yaser.salha.se+66@gmail.com', 'Ashley', 'White', '555-0166'),
        ('yaser67', 'yaser.salha.se+67@gmail.com', 'Joshua', 'Harris', '555-0167'),
        ('yaser68', 'yaser.salha.se+68@gmail.com', 'Melissa', 'Martin', '555-0168'),
        ('yaser69', 'yaser.salha.se+69@gmail.com', 'Andrew', 'Thompson', '555-0169'),
        ('yaser70', 'yaser.salha.se+70@gmail.com', 'Stephanie', 'Garcia', '555-0170'),
        ('yaser71', 'yaser.salha.se+71@gmail.com', 'Ryan', 'Martinez', '555-0171'),
        ('yaser72', 'yaser.salha.se+72@gmail.com', 'Michelle', 'Robinson', '555-0172'),
        ('yaser73', 'yaser.salha.se+73@gmail.com', 'Brandon', 'Clark', '555-0173'),
        ('yaser74', 'yaser.salha.se+74@gmail.com', 'Nicole', 'Rodriguez', '555-0174'),
    ]

    users = []
    for username, email, first, last, phone in users_data:
        user, created = User.objects.get_or_create(
            username=username,
            email=email,
            defaults={
                'first_name': first,
                'last_name': last,
                'is_staff': False,
                'is_superuser': False
            }
        )
        if created:
            user.set_password('user123')
            user.save()
            print(f'✓ Created user: {user.email}')
        else:
            print(f'✓ User already exists: {user.email}')

        # Set phone number
        user.profile.phone_number = phone
        user.profile.save()
        users.append(user)

    # Create drivers (using separate emails not in customer list)
    drivers_data = [
        ('driver1@m1limo.com', 'Robert Martinez', 'Sedan', 'Toyota Camry', 'ABC-123', '555-1001'),
        ('driver2@m1limo.com', 'Patricia Johnson', 'SUV', 'Chevrolet Suburban', 'DEF-456', '555-1002'),
        ('driver3@m1limo.com', 'Thomas Wilson', 'Sprinter Van', 'Mercedes Sprinter', 'GHI-789', '555-1003'),
        ('driver4@m1limo.com', 'Linda Davis', 'Executive Sedan', 'BMW 7 Series', 'JKL-012', '555-1004'),
        ('driver5@m1limo.com', 'Charles Brown', 'Luxury SUV', 'Cadillac Escalade', 'MNO-345', '555-1005'),
    ]

    drivers = []
    for email, full_name, car_type, car_model, car_number, phone in drivers_data:
        driver, created = Driver.objects.get_or_create(
            email=email,
            defaults={
                'full_name': full_name,
                'phone_number': phone,
                'car_type': car_type,
                'car_number': car_number,
                'notes': f'{car_model}'
            }
        )
        if created:
            print(f'✓ Created driver: {driver.full_name} ({driver.car_type})')
        else:
            print(f'✓ Driver already exists: {driver.full_name}')
        drivers.append(driver)

    # Helper to create bookings
    def create_booking(user, days_offset, **kwargs):
        """Create a booking with specified offset from today"""
        base_date = timezone.now().date() + timedelta(days=days_offset)

        # Determine passengers and appropriate vehicle
        passengers = kwargs.get('number_of_passengers', random.randint(1, 6))
        if passengers <= 2:
            vehicle = 'Sedan'
        elif passengers <= 6:
            vehicle = 'SUV'
        else:
            vehicle = 'Sprinter Van'
        
        defaults = {
            'user': user,
            'passenger_name': f"{user.first_name} {user.last_name}",
            'phone_number': user.profile.phone_number,
            'passenger_email': user.email,
            'pick_up_date': base_date,
            'pick_up_time': kwargs.get('pick_up_time', '09:00'),
            'pick_up_address': kwargs.get('pick_up_address', '123 Main St, City'),
            'drop_off_address': kwargs.get('drop_off_address', '456 Oak Ave, Town'),
            'number_of_passengers': passengers,
            'vehicle_type': kwargs.get('vehicle_type', vehicle),
            'trip_type': kwargs.get('trip_type', 'Point'),
            'status': kwargs.get('status', 'Pending'),
            'linked_booking_id': kwargs.get('linked_booking_id', None),
            'hours_booked': kwargs.get('hours_booked', None),
            'flight_number': kwargs.get('flight_number', None),
            'notes': kwargs.get('notes', ''),
            'is_return_trip': kwargs.get('is_return_trip', False),
        }

        booking = Booking.objects.create(**defaults)

        # Create initial history entry (user created booking)
        BookingHistory.objects.create(
            booking=booking,
            changed_by=user,
            action='created', booking_snapshot={},
            change_reason='Reservation created by customer'
        )

        return booking
    # Create varied bookings with all trip types
    print("\nCreating reservations...")

    # 1. Point to Point - Pending
    for i in range(3):
        user = random.choice(users)
        booking = create_booking(
            user=user,
            days_offset=random.randint(3, 14),
            trip_type='Point',
            pick_up_address=random.choice(['123 Main St, Los Angeles CA', '456 Business Plaza, Santa Monica CA', '789 Residential Ave, Beverly Hills CA']),
            drop_off_address=random.choice(['Downtown Office Tower', 'Shopping Center', 'Restaurant District']),
            status='Pending'
        )
        print(f'✓ Reservation #{booking.id}: Point to Point (Pending) - {user.first_name}')

    # 2. Point to Point - Confirmed with drivers
    for i in range(4):
        user = random.choice(users)
        driver = random.choice(drivers)
        booking = create_booking(
            user=user,
            days_offset=random.randint(1, 10),
            trip_type='Point',
            pick_up_address=f'{random.randint(100, 999)} {random.choice(["Oak", "Pine", "Main", "Elm"])} St, Los Angeles CA',
            drop_off_address=f'{random.randint(100, 999)} {random.choice(["Broadway", "Sunset", "Hollywood", "Wilshire"])} Blvd, LA CA',
            status='Confirmed'
        )
        booking.assigned_driver = driver
        booking.share_driver_info = random.choice([True, False])
        booking.save()

        BookingHistory.objects.create(
            booking=booking,
            changed_by=admin,
            action='status_changed', booking_snapshot={},
            change_reason=f'Status changed from Pending to Confirmed. Driver assigned: {driver.full_name}'
        )
        print(f'✓ Reservation #{booking.id}: Point to Point (Confirmed) - {user.first_name} - {driver.full_name}')

    # 3. Airport Transfer - Pending
    for i in range(2):
        user = random.choice(users)
        is_pickup = random.choice([True, False])
        booking = create_booking(
            user=user,
            days_offset=random.randint(5, 15),
            trip_type='Point',
            pick_up_address='LAX Airport - Terminal ' + str(random.randint(1, 8)) if is_pickup else f'{random.randint(100, 999)} Home Address, Los Angeles CA',
            drop_off_address=f'{random.randint(100, 999)} Home Address, Los Angeles CA' if is_pickup else 'LAX Airport - Terminal ' + str(random.randint(1, 8)),
            flight_number=f'AA{random.randint(100, 999)}' if is_pickup else f'UA{random.randint(100, 999)}',
            status='Pending'
        )
        print(f'✓ Reservation #{booking.id}: Airport Transfer (Pending) - {user.first_name}')

    # 4. Airport Transfer - Confirmed
    for i in range(5):
        user = random.choice(users)
        driver = random.choice(drivers)
        is_pickup = random.choice([True, False])
        booking = create_booking(
            user=user,
            days_offset=random.randint(1, 12),
            trip_type='Point',
            pick_up_address='LAX Airport - Terminal ' + str(random.randint(1, 8)) if is_pickup else f'{random.randint(100, 999)} Residence Dr, Los Angeles CA',
            drop_off_address=f'{random.randint(100, 999)} Residence Dr, Los Angeles CA' if is_pickup else 'LAX Airport - Terminal ' + str(random.randint(1, 8)),
            flight_number=f'{random.choice(["DL", "AA", "UA", "SW"])}{random.randint(100, 999)}',
            status='Confirmed'
        )
        booking.assigned_driver = driver
        booking.share_driver_info = True
        booking.save()

        BookingHistory.objects.create(
            booking=booking,
            changed_by=admin,
            action='status_changed', booking_snapshot={},
            change_reason=f'Airport transfer confirmed. Driver: {driver.full_name}'
        )
        print(f'✓ Reservation #{booking.id}: Airport Transfer (Confirmed) - {user.first_name} - {driver.full_name}')

    # 5. Round Trip - Confirmed
    for i in range(4):
        user = random.choice(users)
        driver = random.choice(drivers)
        outbound_date = timezone.now().date() + timedelta(days=random.randint(5, 15))
        return_date = outbound_date + timedelta(days=random.randint(2, 10))

        # Outbound trip
        outbound = create_booking(
            user=user,
            days_offset=(outbound_date - timezone.now().date()).days,
            trip_type='Point',
            pick_up_address=f'{random.randint(100, 999)} {random.choice(["Main", "Oak", "Pine"])} St, Los Angeles CA',
            drop_off_address='LAX Airport - Terminal ' + str(random.randint(1, 8)),
            flight_number=f'{random.choice(["DL", "AA", "UA"])}{random.randint(100, 999)}',
            status='Confirmed',
            notes='Outbound flight - please arrive 10 minutes early'
        )

        # Return trip
        return_trip = create_booking(
            user=user,
            days_offset=(return_date - timezone.now().date()).days,
            trip_type='Point',
            pick_up_address='LAX Airport - Terminal ' + str(random.randint(1, 8)),
            drop_off_address=outbound.pick_up_address,
            flight_number=f'{random.choice(["DL", "AA", "UA"])}{random.randint(100, 999)}',
            status='Confirmed',
            notes='Return flight pickup',
            is_return_trip=True
        )

        # Link trips (outbound gets linked_booking_id pointing to return)
        outbound.linked_booking_id = return_trip.id
        outbound.assigned_driver = driver
        outbound.share_driver_info = True
        outbound.save()

        # Update return trip with link to outbound
        return_trip.linked_booking_id = outbound.id
        outbound.assigned_driver = driver
        return_trip.share_driver_info = True
        return_trip.save()

        # Admin confirms both
        for booking in [outbound, return_trip]:
            BookingHistory.objects.create(
                booking=booking,
                changed_by=admin,
                action='status_changed', booking_snapshot={},
                change_reason=f'Round trip confirmed. Driver assigned: {driver.full_name}'
            )

        print(f'✓ Round Trip #{outbound.id}/{return_trip.id}: {user.first_name} - {outbound_date.strftime("%b %d")} to {return_date.strftime("%b %d")}')

    # 6. Hourly Service - Pending
    for i in range(2):
        user = random.choice(users)
        hours = random.choice([3, 4, 5])
        booking = create_booking(
            user=user,
            days_offset=random.randint(3, 10),
            trip_type='Hourly',
            pick_up_address=f'{random.randint(100, 999)} {random.choice(["Business", "Corporate", "Office"])} Parkway, Los Angeles CA',
            drop_off_address='As directed by passenger',
            hours_booked=hours,
            status='Pending',
            notes=f'{hours} hour service - multiple stops expected'
        )
        print(f'✓ Reservation #{booking.id}: Hourly ({hours}h) (Pending) - {user.first_name}')

    # 7. Hourly Service - Confirmed
    for i in range(5):
        user = random.choice(users)
        driver = random.choice(drivers)
        hours = random.choice([3, 4, 6, 8])
        booking = create_booking(
            user=user,
            days_offset=random.randint(1, 8),
            trip_type='Hourly',
            pick_up_address=f'{random.randint(100, 999)} {random.choice(["Corporate", "Business", "Executive"])} Center, Los Angeles CA',
            drop_off_address='Multiple stops as directed',
            hours_booked=hours,
            status='Confirmed',
            notes=f'{hours} hour charter service'
        )
        booking.assigned_driver = driver
        booking.share_driver_info = True
        booking.save()

        BookingHistory.objects.create(
            booking=booking,
            changed_by=admin,
            action='status_changed', booking_snapshot={},
            change_reason=f'Hourly service ({hours}h) confirmed. Driver: {driver.full_name}'
        )
        print(f'✓ Reservation #{booking.id}: Hourly ({hours}h) (Confirmed) - {user.first_name} - {driver.full_name}')

    # 8. Past Completed Reservations (all types)
    # Note: Can't create past bookings due to validation, so we'll create recent future completions instead
    past_trips = [
        ('Point', None),
        ('Point', f'AA{random.randint(100, 999)}'),
        ('Hourly', None),
    ]
    
    for trip_type, flight in past_trips:
        user = random.choice(users)
        driver = random.choice(drivers)
        # Use near-future dates instead of past for completed trips
        future_days = random.randint(1, 3)
        
        booking_kwargs = {
            'user': user,
            'days_offset': future_days,
            'trip_type': trip_type,
            'status': 'Trip_Completed',
            'flight_number': flight
        }
        
        if trip_type == 'Hourly':
            booking_kwargs['hours_booked'] = random.choice([3, 4, 6, 8])
            booking_kwargs['pick_up_address'] = 'Corporate Office Downtown'
            booking_kwargs['drop_off_address'] = 'Multiple stops completed'
        elif trip_type == 'Point':
            booking_kwargs['pick_up_address'] = 'LAX Airport'
            booking_kwargs['drop_off_address'] = f'{random.randint(100, 999)} Home Address, LA'
        else:
            booking_kwargs['pick_up_address'] = 'Downtown LA'
            booking_kwargs['drop_off_address'] = 'Santa Monica Pier'
        
        booking = create_booking(**booking_kwargs)
        booking.assigned_driver = driver
        booking.share_driver_info = True
        booking.save()

        # History: confirmed
        BookingHistory.objects.create(
            booking=booking,
            changed_by=admin,
            action='status_changed', booking_snapshot={},
            change_reason=f'Reservation confirmed. Driver: {driver.full_name}',
            changed_at=timezone.now() - timedelta(hours=future_days * 24 + 2)
        )

        # History: completed
        BookingHistory.objects.create(
            booking=booking,
            changed_by=admin,
            action='status_changed', booking_snapshot={},
            change_reason='Trip completed successfully',
            changed_at=timezone.now() - timedelta(hours=future_days * 24 + 1)
        )

        print(f'✓ Reservation #{booking.id}: {trip_type} (Trip_Completed) - {user.first_name} - {booking.pick_up_date}')

    # Summary
    print("\n" + "="*70)
    print("✅ DEMO DATA CREATION COMPLETE")
    print("="*70)
    print(f"📊 Total Users: {User.objects.filter(is_staff=False).count()}")
    print(f"🚗 Total Drivers: {Driver.objects.count()}")
    print(f"📅 Total Reservations: {Booking.objects.count()}")
    print(f"   - Point to Point: {Booking.objects.filter(trip_type='Point', linked_booking_id__isnull=True).count()}")
    print(f"   - Airport Transfers: {Booking.objects.filter(trip_type='Point', linked_booking_id__isnull=True).count()}")
    print(f"   - Round Trips (pairs): {Booking.objects.filter(linked_booking_id__isnull=False).count() // 2}")
    print(f"   - Hourly Services: {Booking.objects.filter(trip_type='Hourly').count()}")
    print(f"📝 Total History Entries: {BookingHistory.objects.count()}")
    print("\n🔑 Login Credentials:")
    print("   Admin: mo@m1limo.com / admin123")
    print("   Users: yaser.salha.se+[55-74]@gmail.com / user123")
    print("="*70)

if __name__ == '__main__':
    flush_data()
    create_demo_data()

