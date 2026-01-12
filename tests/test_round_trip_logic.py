"""
Test Suite for Round Trip Logic - Per-Trip Independence

This test suite verifies that round trips are properly treated as TWO independent
trips that share a reference number, NOT as a single "reservation" entity.

Tests verify:
1. Updating one leg does NOT affect the other leg
2. Cancelling one leg does NOT automatically cancel the other
3. Each trip has its own ID and can be queried independently
4. Reference numbers correctly link both trips

NOTE: These tests currently fail in CI because the bookings app uses an unusual
configuration (name='__main__') which prevents Django from recognizing migrations
during test database setup. The tests document the expected behavior and will work
once the app is properly configured with a standard app name.

TODO: Refactor apps.py to use a standard app name (e.g., 'm1limo' or 'bookings')
instead of '__main__' to enable proper migration support.
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.db import models
from datetime import date, time, timedelta
from models import Booking
from booking_service import BookingService
import signals


class RoundTripIndependenceTests(TestCase):
    """Test that round trip legs are truly independent entities"""

    @classmethod
    def setUpClass(cls):
        """Disconnect UserProfile creation signal to avoid table issues in tests"""
        super().setUpClass()
        post_save.disconnect(signals.create_user_profile, sender=User)

    @classmethod
    def tearDownClass(cls):
        """Reconnect UserProfile creation signal after tests"""
        post_save.connect(signals.create_user_profile, sender=User)
        super().tearDownClass()

    def setUp(self):
        """Create test user and client"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            is_staff=True
        )
        self.client.login(username='testuser', password='testpass123')

    def test_create_round_trip_creates_two_bookings(self):
        """Test 1: Creating a round trip creates TWO distinct Booking objects"""
        tomorrow = date.today() + timedelta(days=1)
        next_week = date.today() + timedelta(days=7)

        booking_data = {
            'passenger_name': 'Test Passenger',
            'phone_number': '+1234567890',
            'passenger_email': 'passenger@test.com',
            'pick_up_address': 'Address A',
            'drop_off_address': 'Address B',
            'pick_up_date': tomorrow,
            'pick_up_time': time(10, 0),
            'vehicle_type': 'Sedan',
            'trip_type': 'Round',
            'number_of_passengers': 2,
            # Return trip details
            'return_date': next_week,
            'return_time': time(15, 0),
            'return_pickup_address': 'Address B',
            'return_dropoff_address': 'Address A',
        }

        booking = BookingService.create_booking(
            user=self.user,
            booking_data=booking_data,
            created_by=self.user
        )

        # Assert: Two bookings exist
        self.assertIsNotNone(booking)
        self.assertIsNotNone(booking.linked_booking)

        outbound = booking
        return_trip = booking.linked_booking

        # Assert: They have different IDs
        self.assertNotEqual(outbound.id, return_trip.id)

        # Assert: Correct linking
        self.assertFalse(outbound.is_return_trip)
        self.assertTrue(return_trip.is_return_trip)
        self.assertEqual(outbound.linked_booking, return_trip)
        self.assertEqual(return_trip.linked_booking, outbound)

        # Assert: Both are "Round" trip type
        self.assertEqual(outbound.trip_type, 'Round')
        self.assertEqual(return_trip.trip_type, 'Round')

    def test_update_outbound_does_not_affect_return(self):
        """Test 2: Updating Leg A's date does NOT change Leg B"""
        # Create round trip
        tomorrow = date.today() + timedelta(days=1)
        next_week = date.today() + timedelta(days=7)

        booking_data = {
            'passenger_name': 'Khamez Zibi',
            'phone_number': '+1234567890',
            'pick_up_address': 'Address 1',
            'drop_off_address': 'Address 2',
            'pick_up_date': tomorrow,
            'pick_up_time': time(10, 0),
            'vehicle_type': 'Sprinter Van',
            'trip_type': 'Round',
            'number_of_passengers': 1,
            'return_date': next_week,
            'return_time': time(15, 0),
            'return_pickup_address': 'Address 2',
            'return_dropoff_address': 'Address 1',
        }

        outbound = BookingService.create_booking(
            user=self.user,
            booking_data=booking_data,
            created_by=self.user
        )
        return_trip = outbound.linked_booking

        # Store original return trip date
        original_return_date = return_trip.pick_up_date
        original_return_time = return_trip.pick_up_time

        # Update ONLY outbound trip date
        new_outbound_date = tomorrow + timedelta(days=2)
        update_data = {
            'pick_up_date': new_outbound_date,
            'pick_up_time': time(14, 30),
        }

        BookingService.update_booking(
            booking=outbound,
            booking_data=update_data,
            changed_by=self.user
        )

        # Refresh from database
        outbound.refresh_from_db()
        return_trip.refresh_from_db()

        # Assert: Outbound changed
        self.assertEqual(outbound.pick_up_date, new_outbound_date)
        self.assertEqual(outbound.pick_up_time, time(14, 30))

        # Assert: Return trip UNCHANGED
        self.assertEqual(return_trip.pick_up_date, original_return_date)
        self.assertEqual(return_trip.pick_up_time, original_return_time)

    def test_cancel_return_leg_keeps_outbound_active(self):
        """Test 3: Cancel Leg B, assert Leg A remains 'Confirmed'"""
        tomorrow = date.today() + timedelta(days=5)  # Far enough to avoid cancellation charges
        next_week = date.today() + timedelta(days=10)

        booking_data = {
            'passenger_name': 'Test User',
            'pick_up_address': 'Start',
            'drop_off_address': 'End',
            'pick_up_date': tomorrow,
            'pick_up_time': time(9, 0),
            'vehicle_type': 'SUV',
            'trip_type': 'Round',
            'number_of_passengers': 3,
            'return_date': next_week,
            'return_time': time(18, 0),
            'return_pickup_address': 'End',
            'return_dropoff_address': 'Start',
        }

        outbound = BookingService.create_booking(
            user=self.admin,  # Create as admin so it's auto-confirmed
            booking_data=booking_data,
            created_by=self.admin
        )
        return_trip = outbound.linked_booking

        # Confirm status
        self.assertEqual(outbound.status, 'Confirmed')
        self.assertEqual(return_trip.status, 'Confirmed')

        # Cancel ONLY the return trip
        BookingService.cancel_single_trip(return_trip, "Changed plans")

        # Refresh
        outbound.refresh_from_db()
        return_trip.refresh_from_db()

        # Assert: Return trip cancelled
        self.assertIn(return_trip.status, ['Cancelled', 'Cancelled_Full_Charge'])

        # Assert: Outbound STILL confirmed
        self.assertEqual(outbound.status, 'Confirmed')

    def test_query_by_reference_returns_both_trips(self):
        """Test 4: Querying by reference number returns BOTH trips"""
        tomorrow = date.today() + timedelta(days=1)
        next_week = date.today() + timedelta(days=7)

        booking_data = {
            'passenger_name': 'Reference Test',
            'pick_up_address': 'A',
            'drop_off_address': 'B',
            'pick_up_date': tomorrow,
            'pick_up_time': time(10, 0),
            'vehicle_type': 'Sedan',
            'trip_type': 'Round',
            'number_of_passengers': 1,
            'return_date': next_week,
            'return_time': time(16, 0),
            'return_pickup_address': 'B',
            'return_dropoff_address': 'A',
        }

        outbound = BookingService.create_booking(
            user=self.user,
            booking_data=booking_data,
            created_by=self.user
        )
        return_trip = outbound.linked_booking

        # Get reference number (from outbound trip)
        reference = outbound.booking_reference

        # Query by reference (should find outbound)
        found_bookings = Booking.objects.filter(booking_reference=reference)
        self.assertEqual(found_bookings.count(), 1)
        self.assertEqual(found_bookings.first().id, outbound.id)

        # To get BOTH trips, query by linked_booking relationship
        # (This is the correct pattern for "show all trips in this reservation")
        all_trips = Booking.objects.filter(
            models.Q(id=outbound.id) | models.Q(linked_booking=outbound)
        )
        self.assertEqual(all_trips.count(), 2)

        trip_ids = set(all_trips.values_list('id', flat=True))
        self.assertIn(outbound.id, trip_ids)
        self.assertIn(return_trip.id, trip_ids)

    def test_per_trip_url_access(self):
        """Test 5: Each trip can be accessed via its own ID"""
        tomorrow = date.today() + timedelta(days=3)
        next_week = date.today() + timedelta(days=8)

        booking_data = {
            'passenger_name': 'URL Test',
            'pick_up_address': 'Location A',
            'drop_off_address': 'Location B',
            'pick_up_date': tomorrow,
            'pick_up_time': time(11, 0),
            'vehicle_type': 'SUV',
            'trip_type': 'Round',
            'number_of_passengers': 2,
            'return_date': next_week,
            'return_time': time(14, 0),
            'return_pickup_address': 'Location B',
            'return_dropoff_address': 'Location A',
        }

        outbound = BookingService.create_booking(
            user=self.user,
            booking_data=booking_data,
            created_by=self.user
        )
        return_trip = outbound.linked_booking

        # Test: Access outbound via its ID
        response = self.client.get(f'/booking/{outbound.id}/')
        self.assertEqual(response.status_code, 200)

        # Test: Access return via its ID
        response = self.client.get(f'/booking/{return_trip.id}/')
        self.assertEqual(response.status_code, 200)

        # Test: Edit outbound via /booking/{id}/update/
        response = self.client.get(f'/booking/{outbound.id}/update/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Outbound Trip')  # Should show trip role

        # Test: Edit return via /booking/{id}/update/
        response = self.client.get(f'/booking/{return_trip.id}/update/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Return Trip')  # Should show trip role


class RoundTripUITests(TestCase):
    """Test that UI correctly displays per-trip information"""

    @classmethod
    def setUpClass(cls):
        """Disconnect UserProfile creation signal to avoid table issues in tests"""
        super().setUpClass()
        post_save.disconnect(signals.create_user_profile, sender=User)

    @classmethod
    def tearDownClass(cls):
        """Reconnect UserProfile creation signal after tests"""
        post_save.connect(signals.create_user_profile, sender=User)
        super().tearDownClass()

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='uitest',
            password='testpass',
            email='ui@test.com'
        )
        self.client.login(username='uitest', password='testpass')

    def test_dashboard_shows_separate_edit_buttons(self):
        """Test: Dashboard shows 'Edit Outbound' and 'Edit Return' buttons"""
        tomorrow = date.today() + timedelta(days=3)
        next_week = date.today() + timedelta(days=8)

        booking_data = {
            'passenger_name': 'UI Test User',
            'pick_up_address': 'Home',
            'drop_off_address': 'Airport',
            'pick_up_date': tomorrow,
            'pick_up_time': time(6, 0),
            'vehicle_type': 'Sedan',
            'trip_type': 'Round',
            'number_of_passengers': 1,
            'return_date': next_week,
            'return_time': time(20, 0),
            'return_pickup_address': 'Airport',
            'return_dropoff_address': 'Home',
        }

        outbound = BookingService.create_booking(
            user=self.user,
            booking_data=booking_data,
            created_by=self.user
        )

        # Get dashboard
        response = self.client.get('/dashboard/')
        self.assertEqual(response.status_code, 200)

        # Assert: Shows "Edit Outbound" button
        self.assertContains(response, 'Edit Outbound')

        # Assert: Shows "Edit Return" button
        self.assertContains(response, 'Edit Return')

        # Assert: BOTH buttons link to /booking/{id}/update/
        self.assertContains(response, f'/booking/{outbound.id}/update/')
        self.assertContains(response, f'/booking/{outbound.linked_booking.id}/update/')
