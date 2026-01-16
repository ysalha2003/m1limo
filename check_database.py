"""
Check database contents to understand available test data.
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from django.contrib.auth import get_user_model
from models import Booking, Driver, EmailTemplate, BookingNotification, Notification

User = get_user_model()

print("=" * 80)
print("DATABASE CONTENTS SUMMARY")
print("=" * 80)

# Users
users = User.objects.all()
print(f"\n1. USERS ({users.count()} total):")
for user in users[:5]:
    print(f"   - {user.username} ({user.email}) - Staff: {user.is_staff}, Superuser: {user.is_superuser}")
if users.count() > 5:
    print(f"   ... and {users.count() - 5} more")

# Drivers
drivers = Driver.objects.all()
print(f"\n2. DRIVERS ({drivers.count()} total):")
for driver in drivers[:5]:
    print(f"   - {driver.full_name} ({driver.car_type} - {driver.car_number}) - Active: {driver.is_active}")
if drivers.count() > 5:
    print(f"   ... and {drivers.count() - 5} more")

# Bookings
bookings = Booking.objects.all()
print(f"\n3. BOOKINGS ({bookings.count()} total):")
status_breakdown = {}
for booking in bookings:
    status_breakdown[booking.status] = status_breakdown.get(booking.status, 0) + 1

for status, count in status_breakdown.items():
    print(f"   - {status}: {count}")

print(f"\n   Recent bookings:")
for booking in bookings.order_by('-id')[:5]:
    driver_name = booking.assigned_driver.get_full_name() if booking.assigned_driver else "Unassigned"
    print(f"   - ID {booking.id}: {booking.passenger_name} | {booking.status} | {booking.trip_type} | Driver: {driver_name}")

# Trip types breakdown
trip_types = {}
for booking in bookings:
    trip_types[booking.trip_type] = trip_types.get(booking.trip_type, 0) + 1
print(f"\n   Trip Types:")
for trip_type, count in trip_types.items():
    print(f"   - {trip_type}: {count}")

# Round trips
round_trips = bookings.filter(trip_type='Round')
print(f"\n   Round Trips: {round_trips.count()}")
for booking in round_trips[:3]:
    linked = "Linked" if booking.linked_booking else "Not linked"
    is_return = "Return leg" if booking.is_return_trip else "Outbound leg"
    print(f"   - ID {booking.id}: {is_return} | {linked}")

# Email Templates
templates = EmailTemplate.objects.all()
print(f"\n4. EMAIL TEMPLATES ({templates.count()} total):")
active = templates.filter(is_active=True).count()
inactive = templates.filter(is_active=False).count()
print(f"   - Active: {active}")
print(f"   - Inactive: {inactive}")

# Notifications (audit log)
notifications = Notification.objects.all()
print(f"\n5. NOTIFICATIONS (AUDIT LOG) ({notifications.count()} total):")
if notifications.count() > 0:
    recent_notifications = notifications.order_by('-sent_at')[:5]
    for notif in recent_notifications:
        status = "✅" if notif.success else "❌"
        print(f"   {status} {notif.notification_type} to {notif.recipient[:30]}... | Booking {notif.booking_id}")
else:
    print("   (No notifications logged yet)")

# Booking-Recipient links
booking_notifications = BookingNotification.objects.all()
print(f"\n6. BOOKING NOTIFICATIONS (LINKS) ({booking_notifications.count()} total)")

print("\n" + "=" * 80)
print("DATA AVAILABILITY FOR TESTING")
print("=" * 80)
print(f"✅ Users available: {users.count() > 0}")
print(f"✅ Drivers available: {drivers.count() > 0}")
print(f"✅ Bookings available: {bookings.count() > 0}")
print(f"✅ Templates available: {templates.count() > 0}")
print(f"✅ Notifications logged: {notifications.count() > 0}")
print("=" * 80)
