"""
Management command to create comprehensive test data for the booking system.
Run with: python manage.py create_test_data
Run with: python manage.py create_test_data --flush (to delete existing data first)
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from models import Booking, Driver, BookingHistory, FrequentPassenger
from django.utils import timezone
from datetime import datetime, timedelta
import random


class Command(BaseCommand):
    help = 'Create comprehensive test data for the booking system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--flush',
            action='store_true',
            help='Delete all existing bookings before creating new test data',
        )

    def handle(self, *args, **options):
        # Flush existing data if requested
        if options['flush']:
            self.stdout.write(self.style.WARNING("\n🗑️  FLUSHING EXISTING DATA..."))
            booking_count = Booking.objects.count()
            history_count = BookingHistory.objects.count()
            
            Booking.objects.all().delete()
            BookingHistory.objects.all().delete()
            
            self.stdout.write(self.style.SUCCESS(f"✓ Deleted {booking_count} bookings"))
            self.stdout.write(self.style.SUCCESS(f"✓ Deleted {history_count} history entries\n"))
        
        self.stdout.write("Creating test data...")

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
            self.stdout.write(self.style.SUCCESS(f'✓ Created admin: {admin.email}'))
        else:
            self.stdout.write(f'✓ Admin already exists: {admin.email}')

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
                self.stdout.write(self.style.SUCCESS(f'✓ Created user: {user.email}'))
            else:
                self.stdout.write(f'✓ User already exists: {user.email}')

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
                self.stdout.write(self.style.SUCCESS(f'✓ Created driver: {driver.full_name} ({driver.car_type})'))
            else:
                self.stdout.write(f'✓ Driver already exists: {driver.full_name}')
            drivers.append(driver)

        # Create frequent passengers for users
        passenger_names = [
            ('Jennifer', 'Smith'),
            ('William', 'Jones'),
            ('Emily', 'Davis'),
            ('Alexander', 'Martinez'),
        ]

        for user in users[:2]:  # Add passengers for first 2 users
            for first, last in random.sample(passenger_names, 2):
                FrequentPassenger.objects.get_or_create(
                    user=user,
                    first_name=first,
                    last_name=last,
                    defaults={'phone_number': f"555-{random.randint(2000, 2999)}"}
                )

        self.stdout.write(self.style.SUCCESS('✓ Created frequent passengers'))

        # Helper to create bookings
        def create_booking(user, days_offset, **kwargs):
            """Create a booking with specified offset from today"""
            # Map service_type to trip_type for new terminology
            service_type = kwargs.get('service_type', 'Point to Point')
            trip_type_mapping = {
                'Point to Point': 'Point to Point',
                'Airport Transfer': 'Airport',
                'Hourly': 'Hourly'
            }
            trip_type = trip_type_mapping.get(service_type, 'Point to Point')

            defaults = {
                'user': user,
                'pick_up_date': base_date,
                'pick_up_time': kwargs.get('pick_up_time', '09:00'),
                'pick_up_location': kwargs.get('pick_up_location', '123 Main St, City'),
                'drop_off_location': kwargs.get('drop_off_location', '456 Oak Ave, Town'),
                'number_of_passengers': kwargs.get('number_of_passengers', random.randint(1, 4)),
                'number_of_luggage': kwargs.get('number_of_luggage', random.randint(0, 3)),
                'trip_type': trip_type,
                'status': kwargs.get('status', 'Pending'),
                'total_price': kwargs.get('total_price', random.randint(80, 300)),
                'linked_booking_id': kwargs.get('linked_booking_id', None),
                'trip_label': kwargs.get('trip_label', None),
                'hours_booked': kwargs.get('hours_booked', None),
                'flight_number': kwargs.get('flight_number', None),
                'notes': kwargs.get('notes', ''),
            }

            booking = Booking.objects.create(**defaults)

            # Create initial history entry (user created booking)
            BookingHistory.objec with all trip types
        self.stdout.write("\nCreating reservations...")

        # 1. Point to Point - Pending
        for i in range(3):
            user = random.choice(users)
            booking = create_booking(
                user=user,
                days_offset=random.randint(3, 14),
                service_type='Point to Point',
                pick_up_location=random.choice(['123 Main St, Los Angeles CA', '456 Business Plaza, Santa Monica CA', '789 Residential Ave, Beverly Hills CA']),
                drop_off_location=random.choice(['Downtown Office Tower', 'Shopping Center', 'Restaurant District']),
                status='Pending',
                trip_label='Point to Point'
            )
            self.stdout.write(f'✓ Reservation #{booking.id}: Point to Point (Pending) - {user.first_name}')

        # 2. Point to Point - Confirmed with drivers
        for i in range(4):
            user = random.choice(users)
            driver = random.choice(drivers)
            booking = create_booking(
                user=user,
                days_offset=random.randint(1, 10),
                service_type='Point to Point',
                pick_up_location=f'{random.randint(100, 999)} {random.choice(["Oak", "Pine", "Main", "Elm"])} St, Los Angeles CA',
                drop_off_location=f'{random.randint(100, 999)} {random.choice(["Broadway", "Sunset", "Hollywood", "Wilshire"])} Blvd, LA CA',
                status='Confirmed',
                trip_label='Point to Point'
            )
            booking.assigned_driver = driver
            booking.share_driver_info = random.choice([True, False])
            booking.save()

            BookingHistory.objects.create(
                booking=booking,
                changed_by=admin,
                change_type='status_change',
                changes=f'Status changed from Pending to Confirmed. Driver assigned: {driver.full_name}'
            )
            self.stdout.write(f'✓ Reservation #{booking.id}: Point to Point (Confirmed) - {user.first_name} - {driver.full_name}')

        # 3. Airport Transfer - Pending
        for i in range(2):
            user = random.choice(users)
            is_pickup = random.choice([True, False])
            booking = create_booking(
                user=user,
                days_offset=random.randint(5, 15),
                service_type='Airport Transfer',
                pick_up_location='LAX Airport - Terminal ' + str(random.randint(1, 8)) if is_pickup else f'{random.randint(100, 999)} Home Address, Los Angeles CA',
                drop_off_location=f'{random.randint(100, 999)} Home Address, Los Angeles CA' if is_pickup else 'LAX Airport - Terminal ' + str(random.randint(1, 8)),
                flight_number=f'AA{random.randint(100, 999)}' if is_pickup else f'UA{random.randint(100, 999)}',
                status='Pending',
                trip_label='Airport'
            )
            self.stdout.write(f'✓ Reservation #{booking.id}: Airport Transfer (Pending) - {user.first_name}')

        # 4. Airport Transfer - Confirmed
        for i in range(5):
            user = random.choice(users)
            driver = random.choice(drivers)
            is_pickup = random.choice([True, False])
            booking = create_booking(
                user=user,
                days_offset=random.randint(1, 12),
                service_type='Airport Transfer',
                pick_up_location='LAX Airport - Terminal ' + str(random.randint(1, 8)) if is_pickup else f'{random.randint(100, 999)} Residence Dr, Los Angeles CA',
                drop_off_location=f'{random.randint(100, 999)} Residence Dr, Los Angeles CA' if is_pickup else 'LAX Airport - Terminal ' + str(random.randint(1, 8)),
                flight_number=f'{random.choice(["DL", "AA", "UA", "SW"])}{random.randint(100, 999)}',
                status='Confirmed',
                trip_label='Airport'
            )
            booking.assigned_driver = driver
            booking.share_driver_info = True
            booking.save()

            BookingHistory.objects.create(
                booking=booking,
                changed_by=admin,
                change_type='status_change',
                changes=f'Airport transfer confirmed. Driver: {driver.full_name}'
            )
            self.stdout.write(f'✓ Reservation #{booking.id}: Airport Transfer (Confirmed) - {user.first_name} - {driver.full_name}')

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
                service_type='Airport Transfer',
                pick_up_location=f'{random.randint(100, 999)} {random.choice(["Main", "Oak", "Pine"])} St, Los Angeles CA',
                drop_off_location='LAX Airport - Terminal ' + str(random.randint(1, 8)),
                flight_number=f'{random.choice(["DL", "AA", "UA"])}{random.randint(100, 999)}',
                status='Confirmed',
                trip_label='Outbound',
                notes='Outbound flight - please arrive 10 minutes early'
            )

            # Return trip
            return_trip = create_booking(
                user=user,
                days_offset=(return_date - timezone.now().date()).days,
                service_type='Airport Transfer',
                pick_up_location='LAX Airport - Terminal ' + str(random.randint(1, 8)),
                drop_off_location=outbound.pick_up_location,
                flight_number=f'{random.choice(["DL", "AA", "UA"])}{random.randint(100, 999)}',
                status='Confirmed',
                trip_label='Return',
                notes='Return flight pickup'
            )

            # Link trips
            outbound.linked_booking_id = return_trip.id
            outbound.assigned_driver = driver
            outbound.share_driver_info = True
            outbound.save()

            return_trip.linked_booking_id = outbound.id
            return_trip.assigned_driver = driver
            return_trip.share_driver_info = True
            return_trip.save()

            # Admin confirms both
            for booking in [outbound, return_trip]:
                BookingHistory.objects.create(
                    booking=booking,
                    changed_by=admin,
                    change_type='status_change',
                    changes=f'Round trip confirmed. Driver assigned: {driver.full_name}'
                )

            self.stdout.write(f'✓ Round Trip #{outbound.id}/{return_trip.id}: {user.first_name} - {outbound_date.strftime("%b %d")} to {return_date.strftime("%b %d")}')

        # 6. Hourly Service - Pending
        for i in range(2):
            user = random.choice(users)
            hours = random.choice([3, 4, 5])
            booking = create_booking(
                user=user,
                days_offset=random.randint(3, 10),
                service_type='Hourly',
                pick_up_location=f'{random.randint(100, 999)} {random.choice(["Business", "Corporate", "Office"])} Parkway, Los Angeles CA',
                drop_off_location='As directed by passenger',
                hours_booked=hours,
                status='Pending',
                trip_label='Hourly',
                notes=f'{hours} hour service - multiple stops expected'
            )
            self.stdout.write(f'✓ Reservation #{booking.id}: Hourly ({hours}h) (Pending) - {user.first_name}')

        # 7. Hourly Service - Confirmed
        for i in range(5):
            user = random.choice(users)
            driver = random.choice(drivers)
            hours = random.choice([2, 3, 4, 6, 8])
            booking = create_booking(
                user=user,
                days_offset=random.randint(1, 8),
                service_type='Hourly',
                pick_up_location=f'{random.randint(100, 999)} {random.choice(["Corporate", "Business", "Executive"])} Center, Los Angeles CA',
                drop_off_location='Multiple stops as directed',
                hours_booked=hours,
                status='Confirmed',70)
        self.stdout.write(self.style.SUCCESS("✅ TEST DATA CREATION COMPLETE"))
        self.stdout.write("="*70)
        self.stdout.write(f"📊 Total Users: {User.objects.filter(is_staff=False).count()}")
        self.stdout.write(f"🚗 Total Drivers: {Driver.objects.count()}")
        self.stdout.write(f"📅 Total Reservations: {Booking.objects.count()}")
        self.stdout.write(f"   - Point to Point: {Booking.objects.filter(trip_label='Point to Point').count()}")
        self.stdout.write(f"   - Airport Transfers: {Booking.objects.filter(trip_label='Airport').count()}")
        self.stdout.write(f"   - Outbound Trips: {Booking.objects.filter(trip_label='Outbound').count()}")
        self.stdout.write(f"   - Return Trips: {Booking.objects.filter(trip_label='Return').count()}")
        self.stdout.write(f"   - Hourly Services: {Booking.objects.filter(trip_label='Hourly').count()}")
        self.stdout.write(f"📝 Total History Entries: {BookingHistory.objects.count()}")
        self.stdout.write("\n🔑 Login Credentials:")
        self.stdout.write("   Admin: mo@m1limo.com / admin123")
        self.stdout.write("   Users: yaser.salha.se+[55-74]@gmail.com / user123")
        self.stdout.write("="*7n,
                change_type='status_change',
                changes=f'Hourly service ({hours}h) confirmed. Driver: {driver.full_name}'
            )
            self.stdout.write(f'✓ Reservation #{booking.id}: Hourly ({hours}h) (Confirmed) - {user.first_name} - {driver.full_name}')

        # 8. Past Completed Reservations (all types)
        past_trips = [
            ('Point to Point', None, 'Point to Point'),
            ('Airport Transfer', f'AA{random.randint(100, 999)}', 'Airport'),
            ('Hourly', None, 'Hourly'),
        ]
        
        for trip_type, flight, label in past_trips:
            user = random.choice(users)
            driver = random.choice(drivers)
            past_days = random.randint(1, 30)
            
            booking_kwargs = {
                'user': user,
                'days_offset': -past_days,
                'service_type': trip_type,
                'status': 'Completed',
                'trip_label': label,
                'flight_number': flight
            }
            
            if trip_type == 'Hourly':
                booking_kwargs['hours_booked'] = random.choice([2, 3, 4, 6])
                booking_kwargs['pick_up_location'] = 'Corporate Office Downtown'
                booking_kwargs['drop_off_location'] = 'Multiple stops completed'
            elif trip_type == 'Airport Transfer':
                booking_kwargs['pick_up_location'] = 'LAX Airport'
                booking_kwargs['drop_off_location'] = f'{random.randint(100, 999)} Home Address, LA'
            else:
                booking_kwargs['pick_up_location'] = 'Downtown LA'
                booking_kwargs['drop_off_location'] = 'Santa Monica Pier'
            
            booking = create_booking(**booking_kwargs)
            booking.assigned_driver = driver
            booking.share_driver_info = True
            booking.save()

            # History: confirmed
            BookingHistory.objects.create(
                booking=booking,
                changed_by=admin,
                change_type='status_change',
                changes=f'Reservation confirmed. Driver: {driver.full_name}',
                changed_at=timezone.now() - timedelta(days=past_days + 1)
            )

            # History: completed
            BookingHistory.objects.create(
                booking=booking,
                changed_by=admin,
                change_type='status_change',
                changes='Trip completed successfully',
                changed_at=timezone.now() - timedelta(days=past_days - random.randint(0, 1))
            )

            self.stdout.write(f'✓ Reservation #{booking.id}: {label} (Completed)

            # History: completed
            BookingHistory.objects.create(
                booking=booking,
                changed_by=admin,
                change_type='status_change',
                changes='Booking completed successfully',
                changed_at=timezone.now() - timedelta(days=random.randint(1, 5))
            )

            self.stdout.write(f'✓ Booking #{booking.id}: Completed - {user.first_name} - {booking.pick_up_date}')

        self.stdout.write("\n" + "="*60)
        self.stdout.write(self.style.SUCCESS("TEST DATA CREATION COMPLETE"))
        self.stdout.write("="*60)
        self.stdout.write(f"Total Users: {User.objects.filter(is_staff=False).count()}")
        self.stdout.write(f"Total Drivers: {Driver.objects.count()}")
        self.stdout.write(f"Total Bookings: {Booking.objects.count()}")
        self.stdout.write(f"Total History Entries: {BookingHistory.objects.count()}")
        self.stdout.write("\nLogin Credentials:")
        self.stdout.write("  Admin: mo@m1limo.com / admin123")
        self.stdout.write("  Users: yaser.salha.us+[1-3]@gmail.com / user123")
        self.stdout.write("="*60)
