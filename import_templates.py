"""
Script to import existing email templates directly
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from models import EmailTemplate
from django.contrib.auth import get_user_model
from django.conf import settings

User = get_user_model()

# Get a system user
try:
    system_user = User.objects.filter(is_superuser=True).first()
    if not system_user:
        system_user = User.objects.filter(is_staff=True).first()
    if not system_user:
        system_user = User.objects.first()
except Exception:
    system_user = None

templates_dir = os.path.join(os.path.dirname(__file__), 'templates', 'emails')

# Define templates to import  
templates_to_import = [
    {
        'type': 'booking_confirmed',
        'name': 'Booking Confirmation Email',
        'description': 'Sent when a booking is confirmed',
        'subject': 'Trip Confirmed: {passenger_name} - {pick_up_date}',
        'html': '''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Trip Confirmed</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #0f172a; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; background: #fff; }}
        .status {{ background: #22c55e; color: white; padding: 10px; border-radius: 5px; display: inline-block; }}
        .details {{ margin: 20px 0; }}
        .detail-row {{ margin: 10px 0; }}
        .label {{ font-weight: bold; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{company_name}</h1>
            <p>Transportation Services</p>
        </div>
        <div class="content">
            <div class="status">✓ CONFIRMED</div>
            <h2>Your Trip is Confirmed</h2>
            <div class="details">
                <div class="detail-row">
                    <span class="label">Booking Reference:</span> {booking_reference}
                </div>
                <div class="detail-row">
                    <span class="label">Passenger:</span> {passenger_name}
                </div>
                <div class="detail-row">
                    <span class="label">Date:</span> {pick_up_date}
                </div>
                <div class="detail-row">
                    <span class="label">Time:</span> {pick_up_time}
                </div>
                <div class="detail-row">
                    <span class="label">Pickup:</span> {pick_up_address}
                </div>
                <div class="detail-row">
                    <span class="label">Drop-off:</span> {drop_off_address}
                </div>
                <div class="detail-row">
                    <span class="label">Vehicle:</span> {vehicle_type}
                </div>
                <div class="detail-row">
                    <span class="label">Passengers:</span> {number_of_passengers}
                </div>
            </div>
            <p>For any questions, contact us at {support_email}</p>
        </div>
    </div>
</body>
</html>''',
        'send_to_user': True,
        'send_to_admin': True,
    },
    {
        'type': 'booking_reminder',
        'name': 'Pickup Reminder Email',
        'description': 'Sent 2 hours before pickup time',
        'subject': 'REMINDER: Pickup in 2 Hours - {passenger_name} at {pick_up_time}',
        'html': '''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Pickup Reminder</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #f59e0b; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; background: #fff; }}
        .reminder {{ background: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px; margin: 20px 0; }}
        .details {{ margin: 20px 0; }}
        .detail-row {{ margin: 10px 0; }}
        .label {{ font-weight: bold; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⏰ Pickup Reminder</h1>
        </div>
        <div class="content">
            <div class="reminder">
                <strong>Your pickup is in 2 hours!</strong>
            </div>
            <div class="details">
                <div class="detail-row">
                    <span class="label">Reference:</span> {booking_reference}
                </div>
                <div class="detail-row">
                    <span class="label">Passenger:</span> {passenger_name}
                </div>
                <div class="detail-row">
                    <span class="label">Pickup Time:</span> {pick_up_time}
                </div>
                <div class="detail-row">
                    <span class="label">Pickup Location:</span> {pick_up_address}
                </div>
                <div class="detail-row">
                    <span class="label">Destination:</span> {drop_off_address}
                </div>
            </div>
            <p>Please be ready at the pickup location. Contact: {support_email}</p>
        </div>
    </div>
</body>
</html>''',
        'send_to_user': True,
        'send_to_admin': False,
    },
]

imported_count = 0
for template_data in templates_to_import:
    template_type = template_data['type']
    
    # Check if exists
    existing = EmailTemplate.objects.filter(template_type=template_type).first()
    if existing:
        print(f"⚠ Skipping {template_type} - already exists")
        continue
    
    try:
        EmailTemplate.objects.create(
            template_type=template_type,
            name=template_data['name'],
            description=template_data['description'],
            subject_template=template_data['subject'],
            html_template=template_data['html'],
            send_to_user=template_data['send_to_user'],
            send_to_admin=template_data['send_to_admin'],
            is_active=True,
            created_by=system_user,
            updated_by=system_user,
        )
        print(f"✓ Created template: {template_type}")
        imported_count += 1
    except Exception as e:
        print(f"✗ Error importing {template_type}: {str(e)}")

print(f"\n=== Import Summary ===")
print(f"Imported: {imported_count} templates")
print("\nTemplates are now available in Django admin!")
print("You can customize them at: Admin > Email Templates")
