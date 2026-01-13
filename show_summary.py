import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from models import Booking

print('\n' + '='*70)
print('📊 DATABASE SUMMARY')
print('='*70)
print(f'Total Bookings: {Booking.objects.count()}')
print(f'Confirmed: {Booking.objects.filter(status="Confirmed").count()}')
print(f'Pending: {Booking.objects.filter(status="Pending").count()}')
print(f'\nBy Trip Type:')
print(f'  Point-to-Point: {Booking.objects.filter(trip_type="Point").count()}')
print(f'  Round Trip: {Booking.objects.filter(trip_type="Round").count()}')
print(f'  Hourly: {Booking.objects.filter(trip_type="Hourly").count()}')

round_trips = Booking.objects.filter(trip_type='Round', is_return_trip=False).count()
print(f'\n  Round Trip Pairs: {round_trips} (outbound + return = {round_trips * 2} bookings)')

print(f'\n📍 Sample Chicago Locations (Recent Bookings):')
for b in Booking.objects.order_by('-id')[:8]:
    trip_label = f"{b.trip_type}"
    if b.trip_type == 'Round':
        trip_label = f"Round ({'Return' if b.is_return_trip else 'Outbound'})"
    print(f'  #{b.id}: {b.passenger_name} | {trip_label}')
    print(f'       {b.pick_up_address[:60]}')

print('='*70 + '\n')
