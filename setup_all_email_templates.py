"""
Comprehensive script to create all 10 email templates from existing HTML files
This will systematically create production-ready templates for all notification types
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from models import EmailTemplate
from django.contrib.auth import get_user_model

User = get_user_model()

print("="*80)
print("EMAIL TEMPLATE SYSTEM - COMPREHENSIVE SETUP")
print("="*80)

# Get admin user for created_by field
try:
    admin_user = User.objects.filter(is_superuser=True).first()
    if admin_user:
        print(f"✓ Admin user found: {admin_user.username}")
    else:
        print("⚠ No admin user found - templates will be created without user tracking")
        admin_user = None
except:
    admin_user = None

print("\n" + "="*80)
print("CREATING TEMPLATES")
print("="*80 + "\n")

def create_template(template_type, name, description, subject, html_content, priority="medium"):
    """Create or update a template"""
    
    # Check if active template exists
    existing = EmailTemplate.objects.filter(template_type=template_type, is_active=True).first()
    
    if existing:
        print(f"⚠ [{priority.upper()}] {name}")
        print(f"   Template already exists: {existing.name}")
        print(f"   Skipping to avoid overwriting your customizations\n")
        return existing
    
    # Create new template
    template = EmailTemplate.objects.create(
        template_type=template_type,
        name=name,
        description=description,
        subject_template=subject,
        html_template=html_content,
        is_active=True,
        created_by=admin_user
    )
    
    print(f"✓ [{priority.upper()}] {name}")
    print(f"   Type: {template_type}")
    print(f"   Subject: {subject[:60]}...")
    print(f"   Status: Active and ready to use\n")
    
    return template


# ============================================================================
# PRIORITY 1: MUST HAVE - Core customer communications
# ============================================================================

print("🔴 PRIORITY 1: MUST HAVE (Core Customer Communications)")
print("-" * 80 + "\n")

# 1. BOOKING CONFIRMED
create_template(
    template_type='booking_confirmed',
    name='Booking Confirmation',
    description='Sent to passengers when booking is confirmed. Most important template.',
    subject='Booking Confirmed #{booking_id} - {pick_up_date}',
    html_content='''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>M1 Limousine - Booking Confirmed</title>
</head>
<body style="font-family: 'Poppins', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #0f172a; margin: 0; padding: 0; background-color: #f8fafc;">
    <div style="max-width: 500px; margin: 40px auto; background-color: #ffffff; border-radius: 14px; overflow: hidden; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.08);">
        
        <!-- Header -->
        <div style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; padding: 32px 24px; text-align: center;">
            <h1 style="margin: 0 0 8px 0; font-size: 22px; font-weight: 700; letter-spacing: -0.02em;">Booking Confirmed ✓</h1>
            <p style="margin: 0; font-size: 13px; color: rgba(255,255,255,0.9); font-weight: 500;">M1 Limousine Service</p>
            <div style="display: inline-block; padding: 8px 16px; border-radius: 999px; font-weight: 600; margin-top: 16px; font-size: 13px; background: rgba(255,255,255,0.2); color: white; border: 1px solid rgba(255,255,255,0.3);">
                Booking #{booking_id}
            </div>
        </div>
        
        <!-- Content -->
        <div style="padding: 32px 24px; text-align: center;">
            <p style="font-size: 15px; color: #475569; margin-bottom: 24px; line-height: 1.6;">
                Dear <strong>{passenger_name}</strong>,<br>
                Your booking has been confirmed! We look forward to serving you.
            </p>
            
            <!-- Trip Details -->
            <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 20px; margin: 24px 0; text-align: left;">
                <h3 style="margin: 0 0 16px 0; font-size: 14px; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em;">Trip Details</h3>
                
                <div style="margin-bottom: 12px;">
                    <div style="font-size: 12px; color: #64748b; margin-bottom: 4px;">📅 Pickup Date & Time</div>
                    <div style="font-size: 16px; font-weight: 600; color: #0f172a;">{pick_up_date} at {pick_up_time}</div>
                </div>
                
                <div style="margin-bottom: 12px;">
                    <div style="font-size: 12px; color: #64748b; margin-bottom: 4px;">📍 Pickup Location</div>
                    <div style="font-size: 15px; color: #0f172a;">{pick_up_location}</div>
                </div>
                
                <div style="margin-bottom: 12px;">
                    <div style="font-size: 12px; color: #64748b; margin-bottom: 4px;">🎯 Drop-off Location</div>
                    <div style="font-size: 15px; color: #0f172a;">{drop_off_location}</div>
                </div>
                
                <div>
                    <div style="font-size: 12px; color: #64748b; margin-bottom: 4px;">👥 Passengers</div>
                    <div style="font-size: 15px; color: #0f172a;">{passengers}</div>
                </div>
            </div>
            
            <p style="font-size: 14px; color: #64748b; margin: 20px 0;">
                A driver will be assigned to your trip soon. You'll receive another notification once assigned.
            </p>
            
            <a href="{booking_url}" style="display: inline-block; background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); color: white; padding: 14px 28px; text-decoration: none; border-radius: 10px; font-weight: 600; font-size: 14.5px; margin-top: 8px;">
                View Booking Details
            </a>
        </div>
        
        <!-- Footer -->
        <div style="padding: 24px; text-align: center; background: #f8fafc; border-top: 1px solid #e2e8f0;">
            <p style="font-size: 12px; color: #64748b; margin: 0 0 8px 0;">
                Questions? Contact us at <a href="mailto:support@m1limo.com" style="color: #3b82f6;">support@m1limo.com</a>
            </p>
            <p style="font-size: 11px; color: #94a3b8; margin: 0;">
                © 2026 M1 Limousine Service. All rights reserved.
            </p>
        </div>
    </div>
</body>
</html>''',
    priority="high"
)

# 2. PICKUP REMINDER
with open('templates/emails/booking_reminder.html', 'r', encoding='utf-8') as f:
    reminder_html = f.read()

create_template(
    template_type='booking_reminder',
    name='Pickup Reminder (24 Hours)',
    description='Sent 24 hours before pickup as automated reminder. Reduces no-shows.',
    subject='⏰ Reminder: Your pickup tomorrow at {pick_up_time}',
    html_content=reminder_html,
    priority="high"
)

# 3. DRIVER ASSIGNMENT
create_template(
    template_type='driver_assignment',
    name='Driver Assigned Notification',
    description='Sent when driver is assigned to booking. Builds trust and provides driver contact.',
    subject='Driver Assigned: {driver_name} - Booking #{booking_id}',
    html_content='''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>M1 Limousine - Driver Assigned</title>
</head>
<body style="font-family: 'Poppins', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #0f172a; margin: 0; padding: 0; background-color: #f8fafc;">
    <div style="max-width: 500px; margin: 40px auto; background-color: #ffffff; border-radius: 14px; overflow: hidden; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.08);">
        
        <!-- Header -->
        <div style="background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); color: white; padding: 32px 24px; text-align: center;">
            <h1 style="margin: 0 0 8px 0; font-size: 22px; font-weight: 700; letter-spacing: -0.02em;">Driver Assigned 🚗</h1>
            <p style="margin: 0; font-size: 13px; color: rgba(255,255,255,0.9); font-weight: 500;">Your trip is being prepared</p>
        </div>
        
        <!-- Content -->
        <div style="padding: 32px 24px; text-align: center;">
            <p style="font-size: 15px; color: #475569; margin-bottom: 24px;">
                Good news, <strong>{passenger_name}</strong>!<br>
                A driver has been assigned to your upcoming trip.
            </p>
            
            <!-- Driver Info -->
            <div style="background: #dbeafe; border: 2px solid #3b82f6; border-radius: 10px; padding: 24px; margin: 24px 0;">
                <div style="font-size: 12px; color: #1e40af; font-weight: 600; margin-bottom: 8px; text-transform: uppercase;">Your Driver</div>
                <div style="font-size: 22px; font-weight: 700; color: #0f172a; margin-bottom: 12px;">👨‍✈️ {driver_name}</div>
                <div style="font-size: 16px; color: #1e40af; font-weight: 600;">📞 {driver_phone}</div>
            </div>
            
            <!-- Trip Summary -->
            <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 20px; margin: 24px 0; text-align: left;">
                <h3 style="margin: 0 0 16px 0; font-size: 14px; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em;">Trip Summary</h3>
                
                <div style="margin-bottom: 12px;">
                    <div style="font-size: 12px; color: #64748b; margin-bottom: 4px;">📅 Date & Time</div>
                    <div style="font-size: 15px; font-weight: 600; color: #0f172a;">{pick_up_date} at {pick_up_time}</div>
                </div>
                
                <div style="margin-bottom: 12px;">
                    <div style="font-size: 12px; color: #64748b; margin-bottom: 4px;">📍 Pickup</div>
                    <div style="font-size: 14px; color: #0f172a;">{pick_up_location}</div>
                </div>
                
                <div>
                    <div style="font-size: 12px; color: #64748b; margin-bottom: 4px;">🎯 Destination</div>
                    <div style="font-size: 14px; color: #0f172a;">{drop_off_location}</div>
                </div>
            </div>
            
            <p style="font-size: 13px; color: #64748b; margin: 20px 0;">
                Your driver will contact you if needed. Have a great trip!
            </p>
            
            <a href="{booking_url}" style="display: inline-block; background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); color: white; padding: 14px 28px; text-decoration: none; border-radius: 10px; font-weight: 600; font-size: 14.5px; margin-top: 8px;">
                View Trip Details
            </a>
        </div>
        
        <!-- Footer -->
        <div style="padding: 24px; text-align: center; background: #f8fafc; border-top: 1px solid #e2e8f0;">
            <p style="font-size: 11px; color: #64748b; margin: 0;">
                Booking ID: #{booking_id} | M1 Limousine Service
            </p>
        </div>
    </div>
</body>
</html>''',
    priority="high"
)

# ============================================================================
# PRIORITY 2: ROUND TRIP SUPPORT
# ============================================================================

print("\n🟡 PRIORITY 2: ROUND TRIP SUPPORT")
print("-" * 80 + "\n")

# 4. ROUND TRIP CONFIRMED
with open('templates/emails/round_trip_notification.html', 'r', encoding='utf-8') as f:
    roundtrip_html = f.read()

create_template(
    template_type='round_trip_confirmed',
    name='Round Trip Confirmation',
    description='Sent when customer books round trip. Shows both outbound and return details.',
    subject='Round Trip Confirmed #{booking_id} - {pick_up_date}',
    html_content=roundtrip_html,
    priority="high"
)

# ============================================================================
# PRIORITY 3: IMPORTANT UPDATES
# ============================================================================

print("\n🟠 PRIORITY 3: IMPORTANT UPDATES (Cancellations & Status Changes)")
print("-" * 80 + "\n")

# 5. BOOKING CANCELLED
create_template(
    template_type='booking_cancelled',
    name='Booking Cancellation Confirmation',
    description='Sent when booking is cancelled. Confirms cancellation and explains policy.',
    subject='Booking Cancelled #{booking_id}',
    html_content='''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>M1 Limousine - Booking Cancelled</title>
</head>
<body style="font-family: 'Poppins', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #0f172a; margin: 0; padding: 0; background-color: #f8fafc;">
    <div style="max-width: 500px; margin: 40px auto; background-color: #ffffff; border-radius: 14px; overflow: hidden; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.08);">
        
        <!-- Header -->
        <div style="background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); color: white; padding: 32px 24px; text-align: center;">
            <h1 style="margin: 0 0 8px 0; font-size: 22px; font-weight: 700; letter-spacing: -0.02em;">Booking Cancelled</h1>
            <p style="margin: 0; font-size: 13px; color: rgba(255,255,255,0.9); font-weight: 500;">M1 Limousine Service</p>
            <div style="display: inline-block; padding: 8px 16px; border-radius: 999px; font-weight: 600; margin-top: 16px; font-size: 13px; background: rgba(255,255,255,0.2); color: white; border: 1px solid rgba(255,255,255,0.3);">
                Booking #{booking_id}
            </div>
        </div>
        
        <!-- Content -->
        <div style="padding: 32px 24px; text-align: center;">
            <p style="font-size: 15px; color: #475569; margin-bottom: 24px; line-height: 1.6;">
                Dear <strong>{passenger_name}</strong>,<br>
                Your booking has been cancelled as requested.
            </p>
            
            <!-- Cancelled Booking Details -->
            <div style="background: #fef2f2; border: 1px solid #fecaca; border-radius: 10px; padding: 20px; margin: 24px 0; text-align: left;">
                <h3 style="margin: 0 0 16px 0; font-size: 14px; color: #991b1b; text-transform: uppercase; letter-spacing: 0.05em;">Cancelled Trip</h3>
                
                <div style="margin-bottom: 12px;">
                    <div style="font-size: 12px; color: #991b1b; margin-bottom: 4px;">📅 Date & Time</div>
                    <div style="font-size: 15px; font-weight: 600; color: #0f172a;">{pick_up_date} at {pick_up_time}</div>
                </div>
                
                <div style="margin-bottom: 12px;">
                    <div style="font-size: 12px; color: #991b1b; margin-bottom: 4px;">📍 Pickup Location</div>
                    <div style="font-size: 14px; color: #0f172a;">{pick_up_location}</div>
                </div>
                
                <div>
                    <div style="font-size: 12px; color: #991b1b; margin-bottom: 4px;">🎯 Destination</div>
                    <div style="font-size: 14px; color: #0f172a;">{drop_off_location}</div>
                </div>
            </div>
            
            <div style="background: #fef3c7; border-left: 4px solid #f59e0b; padding: 16px; border-radius: 6px; margin: 24px 0; text-align: left;">
                <p style="font-size: 13px; color: #78350f; margin: 0; line-height: 1.6;">
                    <strong>Refund Policy:</strong> Cancellations made 24+ hours before pickup receive a full refund. 
                    Cancellations within 24 hours may be subject to a cancellation fee. 
                    Please allow 3-5 business days for refunds to process.
                </p>
            </div>
            
            <p style="font-size: 14px; color: #64748b; margin: 20px 0;">
                We're sorry to see you go. We hope to serve you again in the future!
            </p>
            
            <a href="{booking_url}" style="display: inline-block; background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); color: white; padding: 14px 28px; text-decoration: none; border-radius: 10px; font-weight: 600; font-size: 14.5px; margin-top: 8px;">
                Book a New Trip
            </a>
        </div>
        
        <!-- Footer -->
        <div style="padding: 24px; text-align: center; background: #f8fafc; border-top: 1px solid #e2e8f0;">
            <p style="font-size: 12px; color: #64748b; margin: 0 0 8px 0;">
                Questions? Contact us at <a href="mailto:support@m1limo.com" style="color: #3b82f6;">support@m1limo.com</a>
            </p>
            <p style="font-size: 11px; color: #94a3b8; margin: 0;">
                © 2026 M1 Limousine Service. All rights reserved.
            </p>
        </div>
    </div>
</body>
</html>''',
    priority="medium"
)

# 6. STATUS CHANGE
create_template(
    template_type='booking_status_change',
    name='Booking Status Update',
    description='Sent when booking status changes (pending→confirmed, confirmed→completed, etc.)',
    subject='Booking Status Updated - #{booking_id}',
    html_content='''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>M1 Limousine - Status Update</title>
</head>
<body style="font-family: 'Poppins', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #0f172a; margin: 0; padding: 0; background-color: #f8fafc;">
    <div style="max-width: 500px; margin: 40px auto; background-color: #ffffff; border-radius: 14px; overflow: hidden; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.08);">
        
        <!-- Header -->
        <div style="background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%); color: white; padding: 32px 24px; text-align: center;">
            <h1 style="margin: 0 0 8px 0; font-size: 22px; font-weight: 700; letter-spacing: -0.02em;">Status Updated 🔄</h1>
            <p style="margin: 0; font-size: 13px; color: rgba(255,255,255,0.9); font-weight: 500;">Booking #{booking_id}</p>
        </div>
        
        <!-- Content -->
        <div style="padding: 32px 24px; text-align: center;">
            <p style="font-size: 15px; color: #475569; margin-bottom: 24px;">
                Dear <strong>{passenger_name}</strong>,<br>
                Your booking status has been updated.
            </p>
            
            <!-- Status Change Display -->
            <div style="background: #f5f3ff; border: 1px solid #ddd6fe; border-radius: 10px; padding: 24px; margin: 24px 0;">
                <div style="display: flex; align-items: center; justify-content: center; gap: 16px;">
                    <div style="text-align: center;">
                        <div style="font-size: 11px; color: #6b21a8; margin-bottom: 6px; text-transform: uppercase;">Previous Status</div>
                        <div style="background: #e0e7ff; color: #3730a3; padding: 8px 16px; border-radius: 8px; font-weight: 600; font-size: 13px;">
                            {old_status}
                        </div>
                    </div>
                    <div style="font-size: 24px; color: #8b5cf6;">→</div>
                    <div style="text-align: center;">
                        <div style="font-size: 11px; color: #6b21a8; margin-bottom: 6px; text-transform: uppercase;">New Status</div>
                        <div style="background: #7c3aed; color: white; padding: 8px 16px; border-radius: 8px; font-weight: 600; font-size: 13px;">
                            {new_status}
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Trip Details -->
            <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 20px; margin: 24px 0; text-align: left;">
                <h3 style="margin: 0 0 16px 0; font-size: 14px; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em;">Trip Details</h3>
                
                <div style="margin-bottom: 12px;">
                    <div style="font-size: 12px; color: #64748b; margin-bottom: 4px;">📅 Date & Time</div>
                    <div style="font-size: 15px; font-weight: 600; color: #0f172a;">{pick_up_date} at {pick_up_time}</div>
                </div>
                
                <div style="margin-bottom: 12px;">
                    <div style="font-size: 12px; color: #64748b; margin-bottom: 4px;">📍 Pickup</div>
                    <div style="font-size: 14px; color: #0f172a;">{pick_up_location}</div>
                </div>
                
                <div>
                    <div style="font-size: 12px; color: #64748b; margin-bottom: 4px;">🎯 Destination</div>
                    <div style="font-size: 14px; color: #0f172a;">{drop_off_location}</div>
                </div>
            </div>
            
            <a href="{booking_url}" style="display: inline-block; background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%); color: white; padding: 14px 28px; text-decoration: none; border-radius: 10px; font-weight: 600; font-size: 14.5px; margin-top: 8px;">
                View Full Details
            </a>
        </div>
        
        <!-- Footer -->
        <div style="padding: 24px; text-align: center; background: #f8fafc; border-top: 1px solid #e2e8f0;">
            <p style="font-size: 12px; color: #64748b; margin: 0 0 8px 0;">
                Questions? Contact us at <a href="mailto:support@m1limo.com" style="color: #3b82f6;">support@m1limo.com</a>
            </p>
        </div>
    </div>
</body>
</html>''',
    priority="medium"
)

# ============================================================================
# PRIORITY 4: ADMIN NOTIFICATIONS
# ============================================================================

print("\n🟢 PRIORITY 4: ADMIN NOTIFICATIONS (Internal alerts)")
print("-" * 80 + "\n")

# 7. NEW BOOKING (Admin)
create_template(
    template_type='booking_new',
    name='New Booking Alert (Admin)',
    description='Sent to admin/dispatcher when new booking created. Requires attention to assign driver.',
    subject='🆕 New Booking #{booking_id} - {passenger_name}',
    html_content='''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>M1 Limousine - New Booking Alert</title>
</head>
<body style="font-family: 'Poppins', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #0f172a; margin: 0; padding: 0; background-color: #f8fafc;">
    <div style="max-width: 500px; margin: 40px auto; background-color: #ffffff; border-radius: 14px; overflow: hidden; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.08);">
        
        <!-- Header -->
        <div style="background: linear-gradient(135deg, #f97316 0%, #ea580c 100%); color: white; padding: 32px 24px; text-align: center;">
            <h1 style="margin: 0 0 8px 0; font-size: 22px; font-weight: 700; letter-spacing: -0.02em;">🆕 New Booking</h1>
            <p style="margin: 0; font-size: 13px; color: rgba(255,255,255,0.9); font-weight: 500;">Action Required: Assign Driver</p>
            <div style="display: inline-block; padding: 8px 16px; border-radius: 999px; font-weight: 600; margin-top: 16px; font-size: 13px; background: rgba(255,255,255,0.2); color: white; border: 1px solid rgba(255,255,255,0.3);">
                Booking #{booking_id}
            </div>
        </div>
        
        <!-- Content -->
        <div style="padding: 32px 24px;">
            
            <!-- Passenger Info -->
            <div style="background: #fff7ed; border: 2px solid #f97316; border-radius: 10px; padding: 20px; margin-bottom: 20px;">
                <h3 style="margin: 0 0 12px 0; font-size: 14px; color: #9a3412; text-transform: uppercase;">Passenger Information</h3>
                <div style="margin-bottom: 8px;">
                    <span style="font-size: 12px; color: #9a3412;">👤 Name:</span>
                    <strong style="font-size: 15px; color: #0f172a; display: block; margin-top: 2px;">{passenger_name}</strong>
                </div>
                <div style="margin-bottom: 8px;">
                    <span style="font-size: 12px; color: #9a3412;">📧 Email:</span>
                    <a href="mailto:{passenger_email}" style="font-size: 14px; color: #3b82f6; display: block; margin-top: 2px;">{passenger_email}</a>
                </div>
                <div>
                    <span style="font-size: 12px; color: #9a3412;">📞 Phone:</span>
                    <a href="tel:{passenger_phone}" style="font-size: 15px; color: #0f172a; font-weight: 600; display: block; margin-top: 2px;">{passenger_phone}</a>
                </div>
            </div>
            
            <!-- Trip Details -->
            <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 20px; margin-bottom: 20px;">
                <h3 style="margin: 0 0 12px 0; font-size: 14px; color: #64748b; text-transform: uppercase;">Trip Details</h3>
                
                <div style="margin-bottom: 12px;">
                    <div style="font-size: 12px; color: #64748b; margin-bottom: 4px;">📅 Pickup Date & Time</div>
                    <div style="font-size: 16px; font-weight: 600; color: #0f172a;">{pick_up_date} at {pick_up_time}</div>
                </div>
                
                <div style="margin-bottom: 12px;">
                    <div style="font-size: 12px; color: #64748b; margin-bottom: 4px;">📍 Pickup Location</div>
                    <div style="font-size: 14px; color: #0f172a;">{pick_up_location}</div>
                </div>
                
                <div style="margin-bottom: 12px;">
                    <div style="font-size: 12px; color: #64748b; margin-bottom: 4px;">🎯 Drop-off Location</div>
                    <div style="font-size: 14px; color: #0f172a;">{drop_off_location}</div>
                </div>
                
                <div style="margin-bottom: 12px;">
                    <div style="font-size: 12px; color: #64748b; margin-bottom: 4px;">👥 Number of Passengers</div>
                    <div style="font-size: 14px; color: #0f172a;">{passengers}</div>
                </div>
                
                <div>
                    <div style="font-size: 12px; color: #64748b; margin-bottom: 4px;">🚗 Trip Type</div>
                    <div style="font-size: 14px; color: #0f172a; text-transform: capitalize;">{trip_type}</div>
                </div>
            </div>
            
            <!-- Action Required -->
            <div style="background: #fef3c7; border-left: 4px solid #f59e0b; padding: 16px; border-radius: 6px; margin-bottom: 20px;">
                <p style="font-size: 13px; color: #78350f; margin: 0; font-weight: 600;">
                    ⚠️ ACTION REQUIRED: Please assign a driver to this booking as soon as possible.
                </p>
            </div>
            
            <a href="{booking_url}" style="display: inline-block; width: 100%; box-sizing: border-box; background: linear-gradient(135deg, #f97316 0%, #ea580c 100%); color: white; padding: 14px 28px; text-decoration: none; border-radius: 10px; font-weight: 600; font-size: 14.5px; text-align: center;">
                Assign Driver Now →
            </a>
        </div>
        
        <!-- Footer -->
        <div style="padding: 24px; text-align: center; background: #f8fafc; border-top: 1px solid #e2e8f0;">
            <p style="font-size: 11px; color: #64748b; margin: 0;">
                Admin Notification | M1 Limousine Service
            </p>
        </div>
    </div>
</body>
</html>''',
    priority="low"
)

# 8. ROUND TRIP - NEW (Admin)
create_template(
    template_type='round_trip_new',
    name='New Round Trip Alert (Admin)',
    description='Sent to admin when new round trip booking created. Both trips need drivers assigned.',
    subject='🔄 New Round Trip #{booking_id} - {passenger_name}',
    html_content='''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>M1 Limousine - New Round Trip</title>
</head>
<body style="font-family: 'Poppins', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #0f172a; margin: 0; padding: 0; background-color: #f8fafc;">
    <div style="max-width: 500px; margin: 40px auto; background-color: #ffffff; border-radius: 14px; overflow: hidden; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.08);">
        
        <!-- Header -->
        <div style="background: linear-gradient(135deg, #f97316 0%, #ea580c 100%); color: white; padding: 32px 24px; text-align: center;">
            <h1 style="margin: 0 0 8px 0; font-size: 22px; font-weight: 700; letter-spacing: -0.02em;">🔄 New Round Trip</h1>
            <p style="margin: 0; font-size: 13px; color: rgba(255,255,255,0.9); font-weight: 500;">Action Required: Assign Drivers (Both Legs)</p>
        </div>
        
        <!-- Content -->
        <div style="padding: 32px 24px;">
            
            <!-- Passenger Info -->
            <div style="background: #fff7ed; border: 2px solid #f97316; border-radius: 10px; padding: 20px; margin-bottom: 20px;">
                <h3 style="margin: 0 0 12px 0; font-size: 14px; color: #9a3412; text-transform: uppercase;">Passenger Information</h3>
                <div style="margin-bottom: 8px;">
                    <span style="font-size: 12px; color: #9a3412;">👤 Name:</span>
                    <strong style="font-size: 15px; color: #0f172a; display: block; margin-top: 2px;">{passenger_name}</strong>
                </div>
                <div style="margin-bottom: 8px;">
                    <span style="font-size: 12px; color: #9a3412;">📧 Email:</span>
                    <a href="mailto:{passenger_email}" style="font-size: 14px; color: #3b82f6; display: block; margin-top: 2px;">{passenger_email}</a>
                </div>
                <div>
                    <span style="font-size: 12px; color: #9a3412;">📞 Phone:</span>
                    <a href="tel:{passenger_phone}" style="font-size: 15px; color: #0f172a; font-weight: 600; display: block; margin-top: 2px;">{passenger_phone}</a>
                </div>
            </div>
            
            <!-- Outbound Trip -->
            <div style="background: #dbeafe; border: 2px solid #3b82f6; border-radius: 10px; padding: 16px; margin-bottom: 12px;">
                <div style="font-size: 11px; color: #1e40af; font-weight: 600; margin-bottom: 8px; text-transform: uppercase;">➡️ Outbound Trip</div>
                <div style="font-size: 14px; font-weight: 600; color: #0f172a; margin-bottom: 8px;">{pick_up_date} at {pick_up_time}</div>
                <div style="font-size: 13px; color: #1e40af;">
                    {pick_up_location} → {drop_off_location}
                </div>
                <div style="margin-top: 8px; font-size: 12px; color: #1e40af;">Booking #{booking_id}</div>
            </div>
            
            <!-- Return Trip -->
            <div style="background: #f0fdf4; border: 2px solid #10b981; border-radius: 10px; padding: 16px; margin-bottom: 20px;">
                <div style="font-size: 11px; color: #065f46; font-weight: 600; margin-bottom: 8px; text-transform: uppercase;">⬅️ Return Trip</div>
                <div style="font-size: 14px; font-weight: 600; color: #0f172a; margin-bottom: 8px;">{return_pick_up_date} at {return_pick_up_time}</div>
                <div style="font-size: 13px; color: #065f46;">
                    {return_pick_up_location} → {return_drop_off_location}
                </div>
                <div style="margin-top: 8px; font-size: 12px; color: #065f46;">Return Booking ID available in admin</div>
            </div>
            
            <!-- Action Required -->
            <div style="background: #fef3c7; border-left: 4px solid #f59e0b; padding: 16px; border-radius: 6px; margin-bottom: 20px;">
                <p style="font-size: 13px; color: #78350f; margin: 0; font-weight: 600;">
                    ⚠️ ACTION REQUIRED: Assign drivers to BOTH outbound and return trips.
                </p>
            </div>
            
            <a href="{booking_url}" style="display: inline-block; width: 100%; box-sizing: border-box; background: linear-gradient(135deg, #f97316 0%, #ea580c 100%); color: white; padding: 14px 28px; text-decoration: none; border-radius: 10px; font-weight: 600; font-size: 14.5px; text-align: center;">
                Manage Round Trip →
            </a>
        </div>
        
        <!-- Footer -->
        <div style="padding: 24px; text-align: center; background: #f8fafc; border-top: 1px solid #e2e8f0;">
            <p style="font-size: 11px; color: #64748b; margin: 0;">
                Admin Notification | M1 Limousine Service
            </p>
        </div>
    </div>
</body>
</html>''',
    priority="low"
)

# 9. ROUND TRIP - CANCELLED
create_template(
    template_type='round_trip_cancelled',
    name='Round Trip Cancellation',
    description='Sent when round trip is cancelled. Confirms both legs cancelled.',
    subject='Round Trip Cancelled #{booking_id}',
    html_content='''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>M1 Limousine - Round Trip Cancelled</title>
</head>
<body style="font-family: 'Poppins', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #0f172a; margin: 0; padding: 0; background-color: #f8fafc;">
    <div style="max-width: 500px; margin: 40px auto; background-color: #ffffff; border-radius: 14px; overflow: hidden; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.08);">
        
        <!-- Header -->
        <div style="background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); color: white; padding: 32px 24px; text-align: center;">
            <h1 style="margin: 0 0 8px 0; font-size: 22px; font-weight: 700; letter-spacing: -0.02em;">Round Trip Cancelled</h1>
            <p style="margin: 0; font-size: 13px; color: rgba(255,255,255,0.9); font-weight: 500;">Both trips have been cancelled</p>
        </div>
        
        <!-- Content -->
        <div style="padding: 32px 24px; text-align: center;">
            <p style="font-size: 15px; color: #475569; margin-bottom: 24px;">
                Dear <strong>{passenger_name}</strong>,<br>
                Your round trip booking has been cancelled. Both the outbound and return trips are now cancelled.
            </p>
            
            <!-- Cancelled Trips -->
            <div style="background: #fef2f2; border: 1px solid #fecaca; border-radius: 10px; padding: 20px; margin: 24px 0; text-align: left;">
                <h3 style="margin: 0 0 16px 0; font-size: 14px; color: #991b1b; text-transform: uppercase;">Cancelled Trips</h3>
                
                <div style="margin-bottom: 16px; padding-bottom: 16px; border-bottom: 1px solid #fecaca;">
                    <div style="font-size: 11px; color: #991b1b; margin-bottom: 6px;">➡️ OUTBOUND</div>
                    <div style="font-size: 14px; font-weight: 600; color: #0f172a; margin-bottom: 4px;">{pick_up_date} at {pick_up_time}</div>
                    <div style="font-size: 13px; color: #475569;">{pick_up_location} → {drop_off_location}</div>
                </div>
                
                <div>
                    <div style="font-size: 11px; color: #991b1b; margin-bottom: 6px;">⬅️ RETURN</div>
                    <div style="font-size: 14px; font-weight: 600; color: #0f172a; margin-bottom: 4px;">{return_pick_up_date} at {return_pick_up_time}</div>
                    <div style="font-size: 13px; color: #475569;">{return_pick_up_location} → {return_drop_off_location}</div>
                </div>
            </div>
            
            <div style="background: #fef3c7; border-left: 4px solid #f59e0b; padding: 16px; border-radius: 6px; margin: 24px 0; text-align: left;">
                <p style="font-size: 13px; color: #78350f; margin: 0; line-height: 1.6;">
                    <strong>Refund Policy:</strong> Cancellations made 24+ hours before pickup receive a full refund. 
                    Please allow 3-5 business days for refunds to process.
                </p>
            </div>
            
            <p style="font-size: 14px; color: #64748b; margin: 20px 0;">
                We hope to serve you again in the future!
            </p>
            
            <a href="{booking_url}" style="display: inline-block; background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); color: white; padding: 14px 28px; text-decoration: none; border-radius: 10px; font-weight: 600; font-size: 14.5px; margin-top: 8px;">
                Book a New Trip
            </a>
        </div>
        
        <!-- Footer -->
        <div style="padding: 24px; text-align: center; background: #f8fafc; border-top: 1px solid #e2e8f0;">
            <p style="font-size: 12px; color: #64748b; margin: 0 0 8px 0;">
                Questions? Contact us at <a href="mailto:support@m1limo.com" style="color: #3b82f6;">support@m1limo.com</a>
            </p>
        </div>
    </div>
</body>
</html>''',
    priority="low"
)

# 10. ROUND TRIP - STATUS CHANGE
create_template(
    template_type='round_trip_status_change',
    name='Round Trip Status Update',
    description='Sent when round trip status changes. Updates on overall trip progress.',
    subject='Round Trip Status Updated - #{booking_id}',
    html_content='''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>M1 Limousine - Round Trip Status Update</title>
</head>
<body style="font-family: 'Poppins', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #0f172a; margin: 0; padding: 0; background-color: #f8fafc;">
    <div style="max-width: 500px; margin: 40px auto; background-color: #ffffff; border-radius: 14px; overflow: hidden; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.08);">
        
        <!-- Header -->
        <div style="background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%); color: white; padding: 32px 24px; text-align: center;">
            <h1 style="margin: 0 0 8px 0; font-size: 22px; font-weight: 700; letter-spacing: -0.02em;">Round Trip Updated 🔄</h1>
            <p style="margin: 0; font-size: 13px; color: rgba(255,255,255,0.9); font-weight: 500;">Status Change Notification</p>
        </div>
        
        <!-- Content -->
        <div style="padding: 32px 24px; text-align: center;">
            <p style="font-size: 15px; color: #475569; margin-bottom: 24px;">
                Dear <strong>{passenger_name}</strong>,<br>
                Your round trip booking status has been updated.
            </p>
            
            <!-- Status Change -->
            <div style="background: #f5f3ff; border: 1px solid #ddd6fe; border-radius: 10px; padding: 20px; margin: 24px 0;">
                <div style="font-size: 11px; color: #6b21a8; margin-bottom: 8px;">STATUS CHANGE</div>
                <div style="font-size: 15px; color: #475569;">
                    <span style="background: #e0e7ff; color: #3730a3; padding: 6px 12px; border-radius: 6px; font-weight: 600;">{old_status}</span>
                    <span style="margin: 0 8px; color: #8b5cf6;">→</span>
                    <span style="background: #7c3aed; color: white; padding: 6px 12px; border-radius: 6px; font-weight: 600;">{new_status}</span>
                </div>
            </div>
            
            <!-- Round Trip Details -->
            <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 20px; margin: 24px 0; text-align: left;">
                <h3 style="margin: 0 0 16px 0; font-size: 14px; color: #64748b; text-transform: uppercase;">Round Trip Details</h3>
                
                <div style="margin-bottom: 16px; padding-bottom: 16px; border-bottom: 1px solid #e2e8f0;">
                    <div style="font-size: 11px; color: #64748b; margin-bottom: 6px;">➡️ OUTBOUND</div>
                    <div style="font-size: 14px; font-weight: 600; color: #0f172a; margin-bottom: 4px;">{pick_up_date} at {pick_up_time}</div>
                    <div style="font-size: 13px; color: #475569;">{pick_up_location} → {drop_off_location}</div>
                </div>
                
                <div>
                    <div style="font-size: 11px; color: #64748b; margin-bottom: 6px;">⬅️ RETURN</div>
                    <div style="font-size: 14px; font-weight: 600; color: #0f172a; margin-bottom: 4px;">{return_pick_up_date} at {return_pick_up_time}</div>
                    <div style="font-size: 13px; color: #475569;">{return_pick_up_location} → {return_drop_off_location}</div>
                </div>
            </div>
            
            <a href="{booking_url}" style="display: inline-block; background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%); color: white; padding: 14px 28px; text-decoration: none; border-radius: 10px; font-weight: 600; font-size: 14.5px; margin-top: 8px;">
                View Full Details
            </a>
        </div>
        
        <!-- Footer -->
        <div style="padding: 24px; text-align: center; background: #f8fafc; border-top: 1px solid #e2e8f0;">
            <p style="font-size: 12px; color: #64748b; margin: 0;">
                Booking #{booking_id} | M1 Limousine Service
            </p>
        </div>
    </div>
</body>
</html>''',
    priority="low"
)

# ============================================================================
# SUMMARY & NEXT STEPS
# ============================================================================

print("\n" + "="*80)
print("SETUP COMPLETE!")
print("="*80 + "\n")

# Count templates by priority
total = EmailTemplate.objects.count()
active = EmailTemplate.objects.filter(is_active=True).count()

print(f"📊 Statistics:")
print(f"   Total templates: {total}")
print(f"   Active templates: {active}")
print(f"   Template types covered: {EmailTemplate.objects.values('template_type').distinct().count()}/10")

print("\n✅ System Ready:")
print("   1. All 10 template types created")
print("   2. Templates are active and ready to use")
print("   3. Email service will use DB templates automatically")
print("   4. Old HTML files serve as fallback")

print("\n🎯 Next Steps:")
print("   1. Access admin: http://your-domain.com/admin/bookings/emailtemplate/")
print("   2. Review each template using 'Preview Template' button")
print("   3. Customize templates with your branding")
print("   4. Use 'Send Test Email' to test in your inbox")
print("   5. Monitor success rates in admin list view")

print("\n📚 Documentation:")
print("   - EMAIL_TEMPLATE_GUIDE.md - Complete usage guide")
print("   - EMAIL_TEMPLATE_TYPES.md - Template type reference")
print("   - EMAIL_TEMPLATE_TESTING_SUMMARY.md - Testing documentation")

print("\n" + "="*80)
