"""
Unit tests for dashboard booking display logic
Tests scenarios: normal round trips, orphaned returns, one-way trips
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from datetime import datetime, timedelta
from unittest.mock import patch
from models import Booking


class DashboardDisplayTest(TestCase):
    """Test dashboard booking display logic"""
    
    @patch('signals.create_user_profile')
    def setUp(self, mock_signal):
        """Set up test user and client"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
        
        # Base datetime for bookings
        self.pickup_date = (datetime.now() + timedelta(days=1)).date()
        self.pickup_time = datetime.now().replace(hour=10, minute=0).time()
    
    def create_booking(self, trip_type='Point', is_return=False, linked=None, status='Confirmed'):
        """Helper to create a booking"""
        return Booking.objects.create(
            user=self.user,
            passenger_name='Test Passenger',
            contact_number='1234567890',
            pickup_address='123 Main St',
            drop_off_address='456 Oak Ave' if trip_type != 'Hourly' else None,
            pickup_date=self.pickup_date,
            pickup_time=self.pickup_time,
            trip_type=trip_type,
            vehicle_type='Sedan',
            number_of_passengers=1,
            status=status,
            is_return_trip=is_return,
            linked_booking=linked
        )
    
    def test_single_one_way_trip(self):
        """Test that a single one-way trip shows correctly"""
        booking = self.create_booking(trip_type='Point')
        
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        
        bookings_list = response.context['bookings']
        self.assertEqual(len(bookings_list), 1)
        self.assertEqual(bookings_list[0].id, booking.id)
    
    def test_normal_round_trip(self):
        """Test that a normal round trip shows only the outbound"""
        outbound = self.create_booking(trip_type='Round', is_return=False)
        return_trip = self.create_booking(trip_type='Round', is_return=True, linked=outbound)
        outbound.linked_booking = return_trip
        outbound.save()
        
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        
        bookings_list = response.context['bookings']
        # Should only show outbound trip (return is in expandable section)
        self.assertEqual(len(bookings_list), 1)
        self.assertEqual(bookings_list[0].id, outbound.id)
        self.assertFalse(bookings_list[0].is_return_trip)
    
    def test_orphaned_return_trip(self):
        """Test that an orphaned return trip shows as standalone"""
        # Create outbound and return
        outbound = self.create_booking(trip_type='Round', is_return=False, status='Confirmed')
        return_trip = self.create_booking(trip_type='Round', is_return=True, linked=outbound)
        outbound.linked_booking = return_trip
        outbound.save()
        
        # Cancel the outbound
        outbound.status = 'Cancelled'
        outbound.save()
        
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        
        bookings_list = response.context['bookings']
        # Should only show the orphaned return trip (outbound is cancelled)
        self.assertEqual(len(bookings_list), 1)
        self.assertEqual(bookings_list[0].id, return_trip.id)
        self.assertTrue(bookings_list[0].is_return_trip)
    
    def test_multiple_round_trips(self):
        """Test multiple round trips show correctly"""
        # First round trip
        outbound1 = self.create_booking(trip_type='Round', is_return=False)
        return1 = self.create_booking(trip_type='Round', is_return=True, linked=outbound1)
        outbound1.linked_booking = return1
        outbound1.save()
        
        # Second round trip
        outbound2 = self.create_booking(trip_type='Round', is_return=False)
        return2 = self.create_booking(trip_type='Round', is_return=True, linked=outbound2)
        outbound2.linked_booking = return2
        outbound2.save()
        
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        
        bookings_list = response.context['bookings']
        # Should show 2 outbound trips (returns are in expandable sections)
        self.assertEqual(len(bookings_list), 2)
        displayed_ids = {b.id for b in bookings_list}
        self.assertIn(outbound1.id, displayed_ids)
        self.assertIn(outbound2.id, displayed_ids)
        self.assertNotIn(return1.id, displayed_ids)
        self.assertNotIn(return2.id, displayed_ids)
    
    def test_mixed_trip_types(self):
        """Test mix of one-way, round trips, and orphaned returns"""
        # One-way trip
        oneway = self.create_booking(trip_type='Point')
        
        # Normal round trip
        outbound = self.create_booking(trip_type='Round', is_return=False)
        return_trip = self.create_booking(trip_type='Round', is_return=True, linked=outbound)
        outbound.linked_booking = return_trip
        outbound.save()
        
        # Orphaned return (outbound cancelled)
        cancelled_outbound = self.create_booking(trip_type='Round', is_return=False, status='Cancelled')
        orphaned_return = self.create_booking(trip_type='Round', is_return=True, linked=cancelled_outbound)
        cancelled_outbound.linked_booking = orphaned_return
        cancelled_outbound.save()
        
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        
        bookings_list = response.context['bookings']
        # Should show: one-way + round outbound + orphaned return = 3
        self.assertEqual(len(bookings_list), 3)
        displayed_ids = {b.id for b in bookings_list}
        self.assertIn(oneway.id, displayed_ids)
        self.assertIn(outbound.id, displayed_ids)
        self.assertIn(orphaned_return.id, displayed_ids)
        self.assertNotIn(return_trip.id, displayed_ids)  # Hidden (outbound shows it)
        self.assertNotIn(cancelled_outbound.id, displayed_ids)  # Cancelled
    
    def test_confirmed_count(self):
        """Test that confirmed count matches visible confirmed bookings"""
        # Create 2 confirmed round trips (4 bookings total)
        outbound1 = self.create_booking(trip_type='Round', is_return=False, status='Confirmed')
        return1 = self.create_booking(trip_type='Round', is_return=True, linked=outbound1, status='Confirmed')
        outbound1.linked_booking = return1
        outbound1.save()
        
        outbound2 = self.create_booking(trip_type='Round', is_return=False, status='Confirmed')
        return2 = self.create_booking(trip_type='Round', is_return=True, linked=outbound2, status='Confirmed')
        outbound2.linked_booking = return2
        outbound2.save()
        
        # Create 1 pending booking
        self.create_booking(trip_type='Point', status='Pending')
        
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        
        stats = response.context['stats']
        bookings_list = response.context['bookings']
        
        # Database has 4 confirmed bookings, but display shows 2 (outbounds only)
        self.assertEqual(stats['confirmed_count'], 4)  # Raw database count
        # But visible bookings should be filtered
        confirmed_visible = [b for b in bookings_list if b.status == 'Confirmed']
        self.assertEqual(len(confirmed_visible), 2)  # Only outbounds visible
    
    def test_hourly_booking_display(self):
        """Test that hourly bookings show correctly"""
        hourly = Booking.objects.create(
            user=self.user,
            passenger_name='Test Passenger',
            contact_number='1234567890',
            pickup_address='123 Main St',
            drop_off_address=None,  # Hourly has no drop-off
            pickup_date=self.pickup_date,
            pickup_time=self.pickup_time,
            trip_type='Hourly',
            vehicle_type='SUV',
            number_of_passengers=4,
            duration_hours=4,
            status='Confirmed'
        )
        
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        
        bookings_list = response.context['bookings']
        self.assertEqual(len(bookings_list), 1)
        self.assertEqual(bookings_list[0].id, hourly.id)
        self.assertEqual(bookings_list[0].trip_type, 'Hourly')
        self.assertIsNone(bookings_list[0].drop_off_address)


class BookingCountLogicTest(TestCase):
    """Test booking count calculations for stats"""
    
    @patch('signals.create_user_profile')
    def setUp(self, mock_signal):
        """Set up test user"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.pickup_date = (datetime.now() + timedelta(days=1)).date()
        self.pickup_time = datetime.now().replace(hour=10, minute=0).time()
    
    def create_booking(self, status='Confirmed', trip_type='Point', is_return=False):
        """Helper to create a booking"""
        return Booking.objects.create(
            user=self.user,
            passenger_name='Test Passenger',
            contact_number='1234567890',
            pickup_address='123 Main St',
            drop_off_address='456 Oak Ave' if trip_type != 'Hourly' else None,
            pickup_date=self.pickup_date,
            pickup_time=self.pickup_time,
            trip_type=trip_type,
            vehicle_type='Sedan',
            number_of_passengers=1,
            status=status,
            is_return_trip=is_return
        )
    
    def test_count_includes_both_legs_of_round_trip(self):
        """Test that confirmed count includes both outbound and return"""
        outbound = self.create_booking(status='Confirmed', trip_type='Round', is_return=False)
        return_trip = self.create_booking(status='Confirmed', trip_type='Round', is_return=True)
        
        confirmed_count = Booking.objects.filter(status='Confirmed').count()
        # Should count both legs
        self.assertEqual(confirmed_count, 2)
    
    def test_count_excludes_cancelled(self):
        """Test that counts exclude cancelled bookings"""
        self.create_booking(status='Confirmed')
        self.create_booking(status='Cancelled')
        self.create_booking(status='Pending')
        
        confirmed_count = Booking.objects.filter(status='Confirmed').count()
        self.assertEqual(confirmed_count, 1)
        
        pending_count = Booking.objects.filter(status='Pending').count()
        self.assertEqual(pending_count, 1)
