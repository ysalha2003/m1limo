"""
COMPLETE Email Template Setup - All 13 Notification Scenarios
Creates templates for every email scenario in the system
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from models import EmailTemplate
from django.contrib.auth import get_user_model

User = get_user_model()

print("="*80)
print("COMPLETE EMAIL TEMPLATE SYSTEM SETUP")
print("All 13 Notification Scenarios")
print("="*80)

admin_user = User.objects.filter(is_superuser=True).first()
if admin_user:
    print(f"✓ Admin user: {admin_user.username}\n")
else:
    print("⚠ No admin user - templates created without user tracking\n")
    admin_user = None

def create_or_update_template(template_type, name, description, subject, html_content, send_to_user=True, send_to_admin=True, send_to_passenger=False):
    """Create or update a template"""
    
    existing = EmailTemplate.objects.filter(template_type=template_type).first()
    
    if existing:
        print(f"⚠ {name}")
        print(f"   Template exists - skipping\n")
        return existing
    
    template = EmailTemplate.objects.create(
        template_type=template_type,
        name=name,
        description=description,
        subject_template=subject,
        html_template=html_content,
        is_active=True,
        send_to_user=send_to_user,
        send_to_admin=send_to_admin,
        send_to_passenger=send_to_passenger,
        created_by=admin_user
    )
    
    print(f"✓ {name}")
    print(f"   Type: {template_type}")
    print(f"   Recipients: User={send_to_user}, Admin={send_to_admin}, Passenger={send_to_passenger}\n")
    
    return template

print("="*80)
print("CREATING ALL EMAIL TEMPLATES")
print("="*80 + "\n")

# Read existing HTML files
with open('templates/emails/booking_reminder.html', 'r', encoding='utf-8') as f:
    reminder_html = f.read()

with open('templates/emails/round_trip_notification.html', 'r', encoding='utf-8') as f:
    roundtrip_html = f.read()

with open('templates/emails/driver_notification.html', 'r', encoding='utf-8') as f:
    driver_notif_html = f.read()

# ============================================================================
# 1-6: CUSTOMER NOTIFICATIONS
# ============================================================================

print("📧 CUSTOMER NOTIFICATIONS (6 templates)")
print("-" * 80 + "\n")

# 1. NEW BOOKING (Admin)
create_or_update_template(
    template_type='booking_new',
    name='New Booking Alert (Admin)',
    description='Sent to admin when new booking created',
    subject='🆕 New Booking #{booking_id} - {passenger_name}',
    send_to_user=False,
    send_to_admin=True,
    send_to_passenger=False,
    html_content='''<!DOCTYPE html>
<html><body style="font-family: Arial; padding: 20px; background: #f5f5f5;">
<div style="max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px;">
    <h1 style="color: #f97316; border-bottom: 3px solid #f97316; padding-bottom: 10px;">🆕 New Booking</h1>
    <p style="font-size: 16px; margin: 20px 0;">A new booking requires driver assignment.</p>
    <div style="background: #fff7ed; padding: 20px; border-radius: 8px; border-left: 4px solid #f97316; margin: 20px 0;">
        <h3 style="margin-top: 0; color: #9a3412;">Passenger Information</h3>
        <p><strong>Name:</strong> {passenger_name}</p>
        <p><strong>Email:</strong> {passenger_email}</p>
        <p><strong>Phone:</strong> {passenger_phone}</p>
    </div>
    <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
        <h3 style="margin-top: 0;">Trip Details</h3>
        <p><strong>Booking ID:</strong> #{booking_id}</p>
        <p><strong>Date & Time:</strong> {pick_up_date} at {pick_up_time}</p>
        <p><strong>Pickup:</strong> {pick_up_location}</p>
        <p><strong>Destination:</strong> {drop_off_location}</p>
        <p><strong>Passengers:</strong> {passengers}</p>
        <p><strong>Trip Type:</strong> {trip_type}</p>
    </div>
    <div style="background: #fef3c7; padding: 15px; border-radius: 6px; border-left: 4px solid #f59e0b; margin: 20px 0;">
        <p style="margin: 0; font-weight: 600; color: #78350f;">⚠️ ACTION REQUIRED: Assign driver to this booking</p>
    </div>
    <a href="{booking_url}" style="display: block; text-align: center; background: #f97316; color: white; padding: 15px; text-decoration: none; border-radius: 8px; font-weight: 600; margin: 20px 0;">Assign Driver Now →</a>
</div>
</body></html>'''
)

# 2. BOOKING CONFIRMED
create_or_update_template(
    template_type='booking_confirmed',
    name='Booking Confirmation',
    description='Sent when booking is confirmed',
    subject='Booking Confirmed #{booking_id} - {pick_up_date}',
    send_to_user=True,
    send_to_admin=True,
    send_to_passenger=False,
    html_content='''<!DOCTYPE html>
<html><body style="font-family: Arial; padding: 20px; background: #f5f5f5;">
<div style="max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px;">
    <h1 style="color: #10b981; border-bottom: 3px solid #10b981; padding-bottom: 10px;">✓ Booking Confirmed</h1>
    <p style="font-size: 16px;">Dear <strong>{passenger_name}</strong>,</p>
    <p>Your booking has been confirmed! We look forward to serving you.</p>
    <div style="background: #f0fdf4; padding: 20px; border-radius: 8px; border-left: 4px solid #10b981; margin: 20px 0;">
        <h3 style="margin-top: 0; color: #065f46;">Trip Details</h3>
        <p><strong>Booking ID:</strong> #{booking_id}</p>
        <p><strong>Date & Time:</strong> {pick_up_date} at {pick_up_time}</p>
        <p><strong>Pickup:</strong> {pick_up_location}</p>
        <p><strong>Destination:</strong> {drop_off_location}</p>
        <p><strong>Passengers:</strong> {passengers}</p>
    </div>
    <p style="color: #666; font-size: 14px;">A driver will be assigned soon. You'll receive another notification once assigned.</p>
    <a href="{booking_url}" style="display: block; text-align: center; background: #10b981; color: white; padding: 15px; text-decoration: none; border-radius: 8px; font-weight: 600; margin: 20px 0;">View Booking Details</a>
</div>
</body></html>'''
)

# 3. BOOKING CANCELLED  
create_or_update_template(
    template_type='booking_cancelled',
    name='Booking Cancellation',
    description='Sent when booking is cancelled',
    subject='Booking Cancelled #{booking_id}',
    send_to_user=True,
    send_to_admin=True,
    send_to_passenger=False,
    html_content='''<!DOCTYPE html>
<html><body style="font-family: Arial; padding: 20px; background: #f5f5f5;">
<div style="max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px;">
    <h1 style="color: #ef4444; border-bottom: 3px solid #ef4444; padding-bottom: 10px;">Booking Cancelled</h1>
    <p style="font-size: 16px;">Dear <strong>{passenger_name}</strong>,</p>
    <p>Your booking has been cancelled as requested.</p>
    <div style="background: #fef2f2; padding: 20px; border-radius: 8px; border-left: 4px solid #ef4444; margin: 20px 0;">
        <h3 style="margin-top: 0; color: #991b1b;">Cancelled Trip</h3>
        <p><strong>Booking ID:</strong> #{booking_id}</p>
        <p><strong>Date & Time:</strong> {pick_up_date} at {pick_up_time}</p>
        <p><strong>Pickup:</strong> {pick_up_location}</p>
        <p><strong>Destination:</strong> {drop_off_location}</p>
    </div>
    <div style="background: #fef3c7; padding: 15px; border-radius: 6px; border-left: 4px solid #f59e0b; margin: 20px 0;">
        <p style="margin: 0; font-size: 13px; color: #78350f;"><strong>Refund Policy:</strong> Cancellations made 24+ hours before pickup receive a full refund. Please allow 3-5 business days for processing.</p>
    </div>
    <p style="color: #666;">We hope to serve you again in the future!</p>
</div>
</body></html>'''
)

# 4. STATUS CHANGE
create_or_update_template(
    template_type='booking_status_change',
    name='Booking Status Update',
    description='Sent when booking status changes',
    subject='Booking Status Updated - #{booking_id}',
    send_to_user=True,
    send_to_admin=True,
    send_to_passenger=False,
    html_content='''<!DOCTYPE html>
<html><body style="font-family: Arial; padding: 20px; background: #f5f5f5;">
<div style="max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px;">
    <h1 style="color: #8b5cf6; border-bottom: 3px solid #8b5cf6; padding-bottom: 10px;">🔄 Status Updated</h1>
    <p style="font-size: 16px;">Dear <strong>{passenger_name}</strong>,</p>
    <p>Your booking status has been updated.</p>
    <div style="background: #f5f3ff; padding: 20px; border-radius: 8px; border: 1px solid #ddd6fe; margin: 20px 0; text-align: center;">
        <div style="font-size: 12px; color: #6b21a8; margin-bottom: 10px;">STATUS CHANGE</div>
        <div><span style="background: #e0e7ff; color: #3730a3; padding: 8px 16px; border-radius: 6px; font-weight: 600;">{old_status}</span> <span style="margin: 0 10px; color: #8b5cf6;">→</span> <span style="background: #7c3aed; color: white; padding: 8px 16px; border-radius: 6px; font-weight: 600;">{new_status}</span></div>
    </div>
    <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
        <h3 style="margin-top: 0;">Trip Details</h3>
        <p><strong>Booking ID:</strong> #{booking_id}</p>
        <p><strong>Date & Time:</strong> {pick_up_date} at {pick_up_time}</p>
        <p><strong>Pickup:</strong> {pick_up_location}</p>
        <p><strong>Destination:</strong> {drop_off_location}</p>
    </div>
    <a href="{booking_url}" style="display: block; text-align: center; background: #8b5cf6; color: white; padding: 15px; text-decoration: none; border-radius: 8px; font-weight: 600; margin: 20px 0;">View Full Details</a>
</div>
</body></html>'''
)

# 5. PICKUP REMINDER
create_or_update_template(
    template_type='booking_reminder',
    name='Pickup Reminder (24h)',
    description='Sent 24 hours before pickup',
    subject='⏰ Reminder: Your pickup tomorrow at {pick_up_time}',
    send_to_user=True,
    send_to_admin=False,
    send_to_passenger=True,
    html_content=reminder_html
)

# 6. DRIVER ASSIGNMENT (to passenger)
create_or_update_template(
    template_type='driver_assignment',
    name='Driver Assigned Notification',
    description='Sent to passenger when driver is assigned',
    subject='Driver Assigned: {driver_name} - Booking #{booking_id}',
    send_to_user=True,
    send_to_admin=False,
    send_to_passenger=False,
    html_content='''<!DOCTYPE html>
<html><body style="font-family: Arial; padding: 20px; background: #f5f5f5;">
<div style="max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px;">
    <h1 style="color: #3b82f6; border-bottom: 3px solid #3b82f6; padding-bottom: 10px;">🚗 Driver Assigned</h1>
    <p style="font-size: 16px;">Good news, <strong>{passenger_name}</strong>!</p>
    <p>A driver has been assigned to your upcoming trip.</p>
    <div style="background: #dbeafe; padding: 24px; border-radius: 10px; border: 2px solid #3b82f6; margin: 20px 0; text-align: center;">
        <div style="font-size: 12px; color: #1e40af; font-weight: 600; margin-bottom: 8px;">YOUR DRIVER</div>
        <div style="font-size: 22px; font-weight: 700; color: #0f172a; margin-bottom: 12px;">👨‍✈️ {driver_name}</div>
        <div style="font-size: 16px; color: #1e40af; font-weight: 600;">📞 {driver_phone}</div>
    </div>
    <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
        <h3 style="margin-top: 0;">Trip Summary</h3>
        <p><strong>Date & Time:</strong> {pick_up_date} at {pick_up_time}</p>
        <p><strong>Pickup:</strong> {pick_up_location}</p>
        <p><strong>Destination:</strong> {drop_off_location}</p>
    </div>
    <p style="color: #666; font-size: 14px;">Your driver will contact you if needed. Have a great trip!</p>
    <a href="{booking_url}" style="display: block; text-align: center; background: #3b82f6; color: white; padding: 15px; text-decoration: none; border-radius: 8px; font-weight: 600; margin: 20px 0;">View Trip Details</a>
</div>
</body></html>'''
)

# ============================================================================
# 7-9: DRIVER NOTIFICATIONS
# ============================================================================

print("\n🚗 DRIVER NOTIFICATIONS (3 templates)")
print("-" * 80 + "\n")

# 7. DRIVER TRIP NOTIFICATION (to driver)
create_or_update_template(
    template_type='driver_notification',
    name='Driver Trip Assignment',
    description='Sent to driver when assigned to a trip',
    subject='New Trip Assignment - {pick_up_date} at {pick_up_time}',
    send_to_user=False,
    send_to_admin=False,
    send_to_passenger=False,
    html_content=driver_notif_html
)

# 8. DRIVER REJECTION (admin alert)
create_or_update_template(
    template_type='driver_rejection',
    name='Driver Rejection Alert (Admin)',
    description='Sent to admin when driver rejects a trip',
    subject='⚠️ DRIVER REJECTION - Trip #{booking_id} - {pick_up_date}',
    send_to_user=False,
    send_to_admin=True,
    send_to_passenger=False,
    html_content='''<!DOCTYPE html>
<html><body style="font-family: Arial; padding: 20px; background: #f5f5f5;">
<div style="max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px;">
    <h1 style="color: #dc3545; border-bottom: 3px solid #dc3545; padding-bottom: 10px;">⚠️ Driver Trip Rejection</h1>
    <p style="font-size: 16px;"><strong>{driver_name}</strong> has rejected a previously accepted trip assignment.</p>
    <div style="background: #fff5f5; padding: 20px; border-radius: 8px; border-left: 4px solid #dc3545; margin: 20px 0;">
        <h3 style="margin-top: 0; color: #991b1b;">Trip Details</h3>
        <p><strong>Booking ID:</strong> #{booking_id}</p>
        <p><strong>Passenger:</strong> {passenger_name}</p>
        <p><strong>Phone:</strong> {passenger_phone}</p>
        <p><strong>Date & Time:</strong> {pick_up_date} at {pick_up_time}</p>
        <p><strong>Pickup:</strong> {pick_up_location}</p>
        <p><strong>Destination:</strong> {drop_off_location}</p>
    </div>
    <div style="background: #fef3c7; padding: 15px; border-radius: 6px; border: 1px solid #ffc107; margin: 20px 0;">
        <h4 style="margin-top: 0; color: #856404;">Rejection Reason:</h4>
        <p style="color: #856404; margin: 0;">{driver_rejection_reason}</p>
    </div>
    <div style="background: #fef3c7; padding: 15px; border-radius: 6px; border-left: 4px solid #f59e0b; margin: 20px 0;">
        <p style="margin: 0; font-weight: 600; color: #78350f;">⚠️ ACTION REQUIRED: Assign a different driver to this trip</p>
    </div>
    <a href="{booking_url}" style="display: block; text-align: center; background: #dc3545; color: white; padding: 15px; text-decoration: none; border-radius: 8px; font-weight: 600; margin: 20px 0;">Assign New Driver →</a>
</div>
</body></html>'''
)

# 9. DRIVER COMPLETION (admin alert)
create_or_update_template(
    template_type='driver_completion',
    name='Driver Trip Completion Alert (Admin)',
    description='Sent to admin when driver completes a trip',
    subject='✓ Trip Completed - {passenger_name} - {pick_up_date}',
    send_to_user=False,
    send_to_admin=True,
    send_to_passenger=False,
    html_content='''<!DOCTYPE html>
<html><body style="font-family: Arial; padding: 20px; background: #f5f5f5;">
<div style="max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px;">
    <h1 style="color: #28a745; border-bottom: 3px solid #28a745; padding-bottom: 10px;">✓ Trip Completed</h1>
    <p style="font-size: 16px;"><strong>{driver_name}</strong> has marked the trip as completed.</p>
    <div style="background: #f0fdf4; padding: 20px; border-radius: 8px; border-left: 4px solid #28a745; margin: 20px 0;">
        <h3 style="margin-top: 0; color: #065f46;">Trip Details</h3>
        <p><strong>Booking ID:</strong> #{booking_id}</p>
        <p><strong>Driver:</strong> {driver_name}</p>
        <p><strong>Passenger:</strong> {passenger_name}</p>
        <p><strong>Date & Time:</strong> {pick_up_date} at {pick_up_time}</p>
        <p><strong>Pickup:</strong> {pick_up_location}</p>
        <p><strong>Destination:</strong> {drop_off_location}</p>
        <p><strong>Completed At:</strong> {driver_completed_at}</p>
    </div>
    <p style="color: #666; font-size: 13px; margin-top: 30px;"><em>Note: This completion data will be used for billing purposes.</em></p>
</div>
</body></html>'''
)

# ============================================================================
# 10-13: ROUND TRIP NOTIFICATIONS
# ============================================================================

print("\n🔄 ROUND TRIP NOTIFICATIONS (4 templates)")
print("-" * 80 + "\n")

# 10. ROUND TRIP NEW (admin)
create_or_update_template(
    template_type='round_trip_new',
    name='New Round Trip Alert (Admin)',
    description='Sent to admin when new round trip is created',
    subject='🔄 New Round Trip #{booking_id} - {passenger_name}',
    send_to_user=False,
    send_to_admin=True,
    send_to_passenger=False,
    html_content='''<!DOCTYPE html>
<html><body style="font-family: Arial; padding: 20px; background: #f5f5f5;">
<div style="max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px;">
    <h1 style="color: #f97316; border-bottom: 3px solid #f97316; padding-bottom: 10px;">🔄 New Round Trip</h1>
    <p style="font-size: 16px;">A new round trip booking requires driver assignment for both legs.</p>
    <div style="background: #fff7ed; padding: 20px; border-radius: 8px; border-left: 4px solid #f97316; margin: 20px 0;">
        <h3 style="margin-top: 0; color: #9a3412;">Passenger</h3>
        <p><strong>{passenger_name}</strong></p>
        <p>{passenger_email} | {passenger_phone}</p>
    </div>
    <div style="background: #dbeafe; padding: 16px; border-radius: 8px; border: 2px solid #3b82f6; margin: 12px 0;">
        <div style="font-size: 11px; color: #1e40af; font-weight: 600; margin-bottom: 8px;">➡️ OUTBOUND TRIP</div>
        <p style="margin: 5px 0;"><strong>{pick_up_date}</strong> at <strong>{pick_up_time}</strong></p>
        <p style="margin: 5px 0; color: #1e40af; font-size: 14px;">{pick_up_location} → {drop_off_location}</p>
        <p style="margin: 8px 0 0 0; font-size: 12px; color: #1e40af;">Booking #{booking_id}</p>
    </div>
    <div style="background: #f0fdf4; padding: 16px; border-radius: 8px; border: 2px solid #10b981; margin: 12px 0;">
        <div style="font-size: 11px; color: #065f46; font-weight: 600; margin-bottom: 8px;">⬅️ RETURN TRIP</div>
        <p style="margin: 5px 0;"><strong>{return_pick_up_date}</strong> at <strong>{return_pick_up_time}</strong></p>
        <p style="margin: 5px 0; color: #065f46; font-size: 14px;">{return_pick_up_location} → {return_drop_off_location}</p>
    </div>
    <div style="background: #fef3c7; padding: 15px; border-radius: 6px; border-left: 4px solid #f59e0b; margin: 20px 0;">
        <p style="margin: 0; font-weight: 600; color: #78350f;">⚠️ ACTION REQUIRED: Assign drivers to BOTH outbound and return trips</p>
    </div>
    <a href="{booking_url}" style="display: block; text-align: center; background: #f97316; color: white; padding: 15px; text-decoration: none; border-radius: 8px; font-weight: 600; margin: 20px 0;">Manage Round Trip →</a>
</div>
</body></html>'''
)

# 11. ROUND TRIP CONFIRMED
create_or_update_template(
    template_type='round_trip_confirmed',
    name='Round Trip Confirmation',
    description='Sent to passenger when round trip is confirmed',
    subject='Round Trip Confirmed #{booking_id} - {pick_up_date}',
    send_to_user=True,
    send_to_admin=True,
    send_to_passenger=False,
    html_content=roundtrip_html
)

# 12. ROUND TRIP CANCELLED
create_or_update_template(
    template_type='round_trip_cancelled',
    name='Round Trip Cancellation',
    description='Sent when round trip is cancelled',
    subject='Round Trip Cancelled #{booking_id}',
    send_to_user=True,
    send_to_admin=True,
    send_to_passenger=False,
    html_content='''<!DOCTYPE html>
<html><body style="font-family: Arial; padding: 20px; background: #f5f5f5;">
<div style="max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px;">
    <h1 style="color: #ef4444; border-bottom: 3px solid #ef4444; padding-bottom: 10px;">Round Trip Cancelled</h1>
    <p style="font-size: 16px;">Dear <strong>{passenger_name}</strong>,</p>
    <p>Your round trip booking has been cancelled. Both outbound and return trips are now cancelled.</p>
    <div style="background: #fef2f2; padding: 20px; border-radius: 8px; border-left: 4px solid #ef4444; margin: 20px 0;">
        <h3 style="margin-top: 0; color: #991b1b;">Cancelled Trips</h3>
        <div style="margin-bottom: 16px; padding-bottom: 16px; border-bottom: 1px solid #fecaca;">
            <div style="font-size: 11px; color: #991b1b; margin-bottom: 6px;">➡️ OUTBOUND</div>
            <p style="margin: 5px 0;"><strong>{pick_up_date}</strong> at <strong>{pick_up_time}</strong></p>
            <p style="margin: 5px 0; font-size: 14px;">{pick_up_location} → {drop_off_location}</p>
        </div>
        <div>
            <div style="font-size: 11px; color: #991b1b; margin-bottom: 6px;">⬅️ RETURN</div>
            <p style="margin: 5px 0;"><strong>{return_pick_up_date}</strong> at <strong>{return_pick_up_time}</strong></p>
            <p style="margin: 5px 0; font-size: 14px;">{return_pick_up_location} → {return_drop_off_location}</p>
        </div>
    </div>
    <div style="background: #fef3c7; padding: 15px; border-radius: 6px; border-left: 4px solid #f59e0b; margin: 20px 0;">
        <p style="margin: 0; font-size: 13px; color: #78350f;"><strong>Refund Policy:</strong> Cancellations made 24+ hours before pickup receive a full refund. Please allow 3-5 business days for processing.</p>
    </div>
    <p style="color: #666;">We hope to serve you again in the future!</p>
</div>
</body></html>'''
)

# 13. ROUND TRIP STATUS CHANGE
create_or_update_template(
    template_type='round_trip_status_change',
    name='Round Trip Status Update',
    description='Sent when round trip status changes',
    subject='Round Trip Status Updated - #{booking_id}',
    send_to_user=True,
    send_to_admin=True,
    send_to_passenger=False,
    html_content='''<!DOCTYPE html>
<html><body style="font-family: Arial; padding: 20px; background: #f5f5f5;">
<div style="max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px;">
    <h1 style="color: #8b5cf6; border-bottom: 3px solid #8b5cf6; padding-bottom: 10px;">🔄 Round Trip Updated</h1>
    <p style="font-size: 16px;">Dear <strong>{passenger_name}</strong>,</p>
    <p>Your round trip booking status has been updated.</p>
    <div style="background: #f5f3ff; padding: 20px; border-radius: 8px; border: 1px solid #ddd6fe; margin: 20px 0; text-align: center;">
        <div style="font-size: 11px; color: #6b21a8; margin-bottom: 10px;">STATUS CHANGE</div>
        <div><span style="background: #e0e7ff; color: #3730a3; padding: 6px 12px; border-radius: 6px; font-weight: 600;">{old_status}</span> <span style="margin: 0 8px; color: #8b5cf6;">→</span> <span style="background: #7c3aed; color: white; padding: 6px 12px; border-radius: 6px; font-weight: 600;">{new_status}</span></div>
    </div>
    <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
        <h3 style="margin-top: 0;">Round Trip Details</h3>
        <div style="margin-bottom: 16px; padding-bottom: 16px; border-bottom: 1px solid #e2e8f0;">
            <div style="font-size: 11px; color: #64748b; margin-bottom: 6px;">➡️ OUTBOUND</div>
            <p style="margin: 5px 0;"><strong>{pick_up_date}</strong> at <strong>{pick_up_time}</strong></p>
            <p style="margin: 5px 0; font-size: 14px;">{pick_up_location} → {drop_off_location}</p>
        </div>
        <div>
            <div style="font-size: 11px; color: #64748b; margin-bottom: 6px;">⬅️ RETURN</div>
            <p style="margin: 5px 0;"><strong>{return_pick_up_date}</strong> at <strong>{return_pick_up_time}</strong></p>
            <p style="margin: 5px 0; font-size: 14px;">{return_pick_up_location} → {return_drop_off_location}</p>
        </div>
    </div>
    <a href="{booking_url}" style="display: block; text-align: center; background: #8b5cf6; color: white; padding: 15px; text-decoration: none; border-radius: 8px; font-weight: 600; margin: 20px 0;">View Full Details</a>
</div>
</body></html>'''
)

# ============================================================================
# SUMMARY
# ============================================================================

print("\n" + "="*80)
print("SETUP COMPLETE!")
print("="*80 + "\n")

total = EmailTemplate.objects.count()
active = EmailTemplate.objects.filter(is_active=True).count()

print(f"📊 Statistics:")
print(f"   Total templates: {total}")
print(f"   Active templates: {active}")
print(f"   Template types: {EmailTemplate.objects.values('template_type').distinct().count()}/13")

print("\n✅ All Notification Scenarios Covered:")
print("   Customer: 6 templates (new, confirmed, cancelled, status, reminder, driver assigned)")
print("   Driver: 3 templates (trip notification, rejection alert, completion alert)")
print("   Round Trip: 4 templates (new, confirmed, cancelled, status)")

print("\n🎯 Admin Control:")
print("   Each template has enable/disable toggle (is_active field)")
print("   Configure recipients per template (send_to_user, send_to_admin, send_to_passenger)")
print("   Preview and test email functions available")
print("   Statistics tracking (sent count, success rate)")

print("\n📚 Access:")
print("   Admin: http://your-domain.com/admin/bookings/emailtemplate/")
print("   Edit any template to customize content")
print("   Uncheck 'Active' to disable specific notifications")

print("\n" + "="*80)
