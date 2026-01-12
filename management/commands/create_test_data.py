"""
Management command to create comprehensive test data for the booking system.
Run with: python manage.py create_test_data
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from models import Booking, Driver, BookingHistory, FrequentPassenger
from django.utils import timezone
from datetime import datetime, timedelta
import random


class Command(BaseCommand):
    help = 'Create comprehensive test data for the booking system'

    def handle(self, *args, **options):
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

        # Create regular users
        users_data = [
            ('yaser1', 'yaser.salha.us+1@gmail.com', 'Yaser', 'Johnson', '555-0101'),
            ('yaser2', 'yaser.salha.us+2@gmail.com', 'Sarah', 'Williams', '555-0102'),
            ('yaser3', 'yaser.salha.us+3@gmail.com', 'Michael', 'Brown', '555-0103'),
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

        # Create drivers
        drivers_data = [
            ('yaser.salha.se+1@gmail.com', 'James Driver', 'Sedan', 'Toyota Camry', 'ABC-123', '555-1001'),
            ('yaser.salha.se+2@gmail.com', 'Robert Smith', 'SUV', 'Chevrolet Suburban', 'DEF-456', '555-1002'),
            ('yaser.salha.se+3@gmail.com', 'David Wilson', 'Sprinter Van', 'Mercedes Sprinter', 'GHI-789', '555-1003'),
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
            base_date = timezone.now().date() + timedelta(days=days_offset)

            defaults = {
                'user': user,
                'pick_up_date': base_date,
                'pick_up_time': kwargs.get('pick_up_time', '09:00'),
                'pick_up_location': kwargs.get('pick_up_location', '123 Main St, City'),
                'drop_off_location': kwargs.get('drop_off_location', '456 Oak Ave, Town'),
                'number_of_passengers': kwargs.get('number_of_passengers', random.randint(1, 4)),
                'number_of_luggage': kwargs.get('number_of_luggage', random.randint(0, 3)),
                'service_type': kwargs.get('service_type', 'Point to Point'),
                'status': kwargs.get('status', 'Pending'),
                'total_price': kwargs.get('total_price', random.randint(80, 300)),
                'is_round_trip': kwargs.get('is_round_trip', False),
                'is_return_trip': kwargs.get('is_return_trip', False),
                'number_of_hours': kwargs.get('number_of_hours', None),
            }

            booking = Booking.objects.create(**defaults)

            # Create initial history entry (user created booking)
            BookingHistory.objects.create(
                booking=booking,
                changed_by=user,
                change_type='created',
                changes='Booking created by customer'
            )

            return booking

        # Create varied bookings
        self.stdout.write("\nCreating bookings...")

        # 1-5: Pending bookings (user-created, awaiting admin confirmation)
        for i in range(5):
            user = random.choice(users)
            booking = create_booking(
                user=user,
                days_offset=random.randint(3, 14),
                service_type=random.choice(['Point to Point', 'Airport Transfer']),
                pick_up_location=random.choice(['LAX Airport', '123 Business St', '789 Hotel Blvd']),
                drop_off_location=random.choice(['456 Conference Center', 'Downtown Plaza', '321 Residence Ave']),
                status='Pending'
            )
            self.stdout.write(f'✓ Booking #{booking.id}: Pending - {user.first_name} - {booking.pick_up_date}')

        # 6-12: Confirmed bookings with assigned drivers
        for i in range(7):
            user = random.choice(users)
            driver = random.choice(drivers)
            booking = create_booking(
                user=user,
                days_offset=random.randint(1, 10),
                service_type=random.choice(['Point to Point', 'Airport Transfer']),
                status='Confirmed'
            )

            # Admin confirms and assigns driver
            booking.status = 'Confirmed'
            booking.assigned_driver = driver
            booking.share_driver_info = random.choice([True, False])
            booking.save()

            # Create history for admin confirmation
            BookingHistory.objects.create(
                booking=booking,
                changed_by=admin,
                change_type='status_change',
                changes=f'Status changed from Pending to Confirmed. Driver assigned: {driver.full_name}'
            )

            self.stdout.write(f'✓ Booking #{booking.id}: Confirmed - {user.first_name} - Driver: {driver.full_name}')

        # 13-15: Round trip bookings
        for i in range(3):
            user = random.choice(users)
            driver = random.choice(drivers)
            outbound_date = timezone.now().date() + timedelta(days=random.randint(5, 12))
            return_date = outbound_date + timedelta(days=random.randint(1, 7))

            # Outbound trip
            outbound = create_booking(
                user=user,
                days_offset=(outbound_date - timezone.now().date()).days,
                service_type='Airport Transfer',
                pick_up_location='123 Home Address',
                drop_off_location='LAX Airport',
                status='Confirmed',
                is_round_trip=True
            )

            # Return trip
            return_trip = create_booking(
                user=user,
                days_offset=(return_date - timezone.now().date()).days,
                service_type='Airport Transfer',
                pick_up_location='LAX Airport',
                drop_off_location='123 Home Address',
                status='Confirmed',
                is_return_trip=True
            )

            # Link trips
            outbound.is_round_trip = True
            outbound.return_trip = return_trip
            outbound.assigned_driver = driver
            outbound.share_driver_info = True
            outbound.save()

            return_trip.is_return_trip = True
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

            self.stdout.write(f'✓ Round Trip #{outbound.id}/{return_trip.id}: {user.first_name} - {outbound_date} to {return_date}')

        # 16-18: Hourly service bookings
        for i in range(3):
            user = random.choice(users)
            driver = random.choice(drivers)
            hours = random.choice([2, 4, 6, 8])
            booking = create_booking(
                user=user,
                days_offset=random.randint(2, 8),
                service_type='Hourly',
                pick_up_location='Corporate Office - 555 Business Parkway',
                drop_off_location='Multiple stops as directed',
                number_of_hours=hours,
                status='Confirmed'
            )

            booking.assigned_driver = driver
            booking.share_driver_info = True
            booking.save()

            BookingHistory.objects.create(
                booking=booking,
                changed_by=admin,
                change_type='status_change',
                changes=f'Hourly service confirmed. Driver: {driver.full_name}'
            )

            self.stdout.write(f'✓ Booking #{booking.id}: Hourly ({hours}h) - {user.first_name} - Driver: {driver.full_name}')

        # 19-20: Past completed bookings
        for i in range(2):
            user = random.choice(users)
            driver = random.choice(drivers)
            booking = create_booking(
                user=user,
                days_offset=-random.randint(1, 14),  # Past dates
                service_type=random.choice(['Point to Point', 'Airport Transfer']),
                status='Completed'
            )

            booking.assigned_driver = driver
            booking.share_driver_info = True
            booking.save()

            # History: confirmed
            BookingHistory.objects.create(
                booking=booking,
                changed_by=admin,
                change_type='status_change',
                changes=f'Booking confirmed. Driver: {driver.full_name}',
                changed_at=timezone.now() - timedelta(days=random.randint(2, 15))
            )

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
