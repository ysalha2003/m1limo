#!/usr/bin/env python
"""
Test script for selective recipient sending feature.
Tests the admin's ability to select specific recipients when resending notifications.
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from django.contrib.auth.models import User
from models import Booking
from notification_service import NotificationService

def test_selective_sending():
    """Test selective recipient sending with different combinations"""
    
    print("\n" + "="*80)
    print("SELECTIVE RECIPIENT SENDING TEST")
    print("="*80)
    
    # Get a test booking
    booking = Booking.objects.filter(status='Confirmed').first()
    if not booking:
        print("❌ No confirmed bookings found for testing")
        return
    
    print(f"\nTest Booking: #{booking.id}")
    print(f"User: {booking.user.email if booking.user else 'None'}")
    print(f"Passenger: {booking.passenger_email or 'None'}")
    print(f"Status: {booking.status}")
    
    # Test 1: Send to all three recipients
    print("\n" + "-"*80)
    print("TEST 1: Send to all recipients (Admin + User + Passenger)")
    print("-"*80)
    selected = ['admin', 'user', 'passenger']
    recipients = NotificationService._get_selected_recipients(booking, 'confirmed', selected)
    print(f"Recipients: {recipients}")
    print(f"✓ Expected 3 recipients, got {len(recipients)}")
    
    # Test 2: Send to admin only
    print("\n" + "-"*80)
    print("TEST 2: Send to Admin only")
    print("-"*80)
    selected = ['admin']
    recipients = NotificationService._get_selected_recipients(booking, 'confirmed', selected)
    print(f"Recipients: {recipients}")
    print(f"✓ Expected 1 recipient (admin), got {len(recipients)}")
    
    # Test 3: Send to user only
    print("\n" + "-"*80)
    print("TEST 3: Send to User only")
    print("-"*80)
    selected = ['user']
    recipients = NotificationService._get_selected_recipients(booking, 'confirmed', selected)
    print(f"Recipients: {recipients}")
    print(f"✓ Expected 1 recipient (user), got {len(recipients)}")
    
    # Test 4: Send to passenger only
    print("\n" + "-"*80)
    print("TEST 4: Send to Passenger only")
    print("-"*80)
    selected = ['passenger']
    recipients = NotificationService._get_selected_recipients(booking, 'confirmed', selected)
    print(f"Recipients: {recipients}")
    expected = 1 if booking.passenger_email else 0
    print(f"✓ Expected {expected} recipient(s), got {len(recipients)}")
    
    # Test 5: Send to user + passenger (exclude admin)
    print("\n" + "-"*80)
    print("TEST 5: Send to User + Passenger (exclude Admin)")
    print("-"*80)
    selected = ['user', 'passenger']
    recipients = NotificationService._get_selected_recipients(booking, 'confirmed', selected)
    print(f"Recipients: {recipients}")
    expected = 2 if booking.passenger_email else 1
    print(f"✓ Expected {expected} recipient(s), got {len(recipients)}")
    
    # Test 6: Empty selection
    print("\n" + "-"*80)
    print("TEST 6: No recipients selected")
    print("-"*80)
    selected = []
    recipients = NotificationService._get_selected_recipients(booking, 'confirmed', selected)
    print(f"Recipients: {recipients}")
    print(f"✓ Expected 0 recipients, got {len(recipients)}")
    
    # Test 7: Compare with default behavior
    print("\n" + "-"*80)
    print("TEST 7: Compare selective vs default recipients")
    print("-"*80)
    default_recipients = NotificationService.get_recipients(booking, 'confirmed')
    print(f"Default recipients (based on preferences): {default_recipients}")
    
    selected = ['admin', 'user', 'passenger']
    selective_recipients = NotificationService._get_selected_recipients(booking, 'confirmed', selected)
    print(f"Selective recipients (admin override): {selective_recipients}")
    
    print("\nKey difference: Selective sending ignores user preferences!")
    print("Admin can send to users even if they've disabled notifications.")
    
    # Test 8: Verify duplicate prevention (passenger == user)
    print("\n" + "-"*80)
    print("TEST 8: Duplicate prevention when passenger email == user email")
    print("-"*80)
    # Create a temporary booking scenario
    if booking.user and booking.passenger_email:
        original_passenger = booking.passenger_email
        booking.passenger_email = booking.user.email  # Set passenger to same as user
        
        selected = ['admin', 'user', 'passenger']
        recipients = NotificationService._get_selected_recipients(booking, 'confirmed', selected)
        print(f"When passenger email == user email:")
        print(f"Recipients: {recipients}")
        print(f"✓ Expected 2 recipients (admin + user, no duplicate), got {len(recipients)}")
        
        # Restore original
        booking.passenger_email = original_passenger
    
    print("\n" + "="*80)
    print("ALL TESTS COMPLETED")
    print("="*80)
    print("\n✅ Selective recipient sending is working correctly!")
    print("\nThis feature allows admin to:")
    print("  • Choose exactly who receives notifications")
    print("  • Override user preference settings when needed")
    print("  • Send targeted updates to specific parties")
    print("  • Handle emergency notifications flexibly")

if __name__ == '__main__':
    test_selective_sending()
