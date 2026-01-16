"""Test that the driver attribute fix works"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from models import Booking
from email_service import EmailService

print("\n" + "="*80)
print("TESTING DRIVER ATTRIBUTE FIX")
print("="*80 + "\n")

# Test with booking 209
try:
    booking = Booking.objects.get(id=209)
    print(f"Booking ID: {booking.id}")
    print(f"Passenger: {booking.passenger_name}")
    print(f"Has assigned_driver: {hasattr(booking, 'assigned_driver')}")
    print(f"Assigned driver: {booking.assigned_driver if booking.assigned_driver else 'None'}")
    
    print("\nBuilding template context...")
    context = EmailService._build_template_context(booking, 'confirmed')
    
    print("✅ Context built successfully!")
    print(f"\nDriver Information in Context:")
    print(f"  driver_name: {context.get('driver_name', 'N/A')}")
    print(f"  driver_phone: {context.get('driver_phone', 'N/A')}")
    print(f"  driver_vehicle: {context.get('driver_vehicle', 'N/A')}")
    
    print("\n" + "="*80)
    print("✅ FIX VERIFIED - No 'driver' attribute error!")
    print("="*80 + "\n")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    print("\n" + "="*80)
    import traceback
    traceback.print_exc()
