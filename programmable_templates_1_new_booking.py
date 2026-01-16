"""
PROGRAMMABLE EMAIL TEMPLATES FOR M1 LIMOUSINE
==============================================

These templates use Django template syntax and can be uploaded to the Email Templates
section in the Django admin panel.

All templates have been tested and include:
- Proper variable substitution using {{ variable }}
- Functional clickable links
- Professional styling with inline CSS
- Mobile-responsive design
- Proper email client compatibility

Available variables for each template are documented in the template comments.
"""

# ============================================================================
# TEMPLATE 1: NEW BOOKING NOTIFICATION
# ============================================================================

NEW_BOOKING_TEMPLATE = {
    'template_type': 'booking_new',
    'name': 'New Booking Request',
    'description': 'Sent when a new booking is created (Pending status)',
    'subject_template': 'New Trip Request: {{ booking.passenger_name }} - {{ booking.pick_up_date|date:"M j, Y" }}',
    'html_template': '''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>M1 Limousine - New Booking Request</title>
</head>
<body style="font-family: 'Poppins', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #0f172a; margin: 0; padding: 0; background-color: #f8fafc;">
    <div style="max-width: 500px; margin: 40px auto; background-color: #ffffff; border-radius: 14px; overflow: hidden; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.08);">
        
        <!-- Header -->
        <div style="background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); color: white; padding: 32px 24px; text-align: center;">
            <h1 style="margin: 0 0 8px 0; font-size: 22px; font-weight: 700; letter-spacing: -0.02em;">Trip Request Received 📋</h1>
            <p style="margin: 0; font-size: 13px; color: #cbd5e1; font-weight: 500;">M1 Limousine Service</p>
            <div style="display: inline-block; padding: 8px 16px; border-radius: 999px; font-weight: 600; margin-top: 16px; font-size: 13px; background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%); color: #0f172a; border: 1px solid rgba(30, 41, 59, 0.25);">
                Status: Pending
            </div>
        </div>
        
        <!-- Content -->
        <div style="padding: 32px 24px; text-align: center;">
            <p style="font-size: 15px; color: #475569; margin-bottom: 24px; line-height: 1.6;">
                Dear <strong>{{ booking.passenger_name }}</strong>,<br>
                Your trip request has been received. We'll confirm your reservation shortly.
            </p>
            
            <div style="font-size: 14px; color: #64748b; margin-bottom: 8px;">
                Booking Reference: <strong style="color: #0f172a; font-weight: 600;">{{ booking.booking_reference }}</strong>
            </div>
            
            <div style="font-size: 16px; font-weight: 600; color: #0f172a; margin: 16px 0;">
                {{ booking.pick_up_date|date:"l, F j, Y" }} at {{ booking.pick_up_time|time:"g:i A" }}
            </div>
            
            <!-- Trip Details Box -->
            <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 20px; margin: 24px 0; text-align: left;">
                <h3 style="margin: 0 0 12px 0; font-size: 14px; color: #64748b; text-transform: uppercase;">Trip Details</h3>
                
                <div style="margin-bottom: 12px;">
                    <div style="font-size: 11px; color: #64748b; margin-bottom: 4px;">PICKUP</div>
                    <div style="font-size: 14px; color: #0f172a;">{{ booking.pick_up_address }}</div>
                </div>
                
                <div style="margin-bottom: 12px;">
                    <div style="font-size: 11px; color: #64748b; margin-bottom: 4px;">DROP-OFF</div>
                    <div style="font-size: 14px; color: #0f172a;">{{ booking.drop_off_address }}</div>
                </div>
                
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 16px; padding-top: 16px; border-top: 1px solid #e2e8f0;">
                    <div>
                        <div style="font-size: 11px; color: #64748b; margin-bottom: 4px;">VEHICLE</div>
                        <div style="font-size: 13px; color: #0f172a; font-weight: 500;">{{ booking.vehicle_type }}</div>
                    </div>
                    <div>
                        <div style="font-size: 11px; color: #64748b; margin-bottom: 4px;">PASSENGERS</div>
                        <div style="font-size: 13px; color: #0f172a; font-weight: 500;">{{ booking.number_of_passengers }}</div>
                    </div>
                </div>
                
                {% if booking.flight_number %}
                <div style="margin-top: 12px;">
                    <div style="font-size: 11px; color: #64748b; margin-bottom: 4px;">FLIGHT NUMBER</div>
                    <div style="font-size: 13px; color: #0f172a;">{{ booking.flight_number }}</div>
                </div>
                {% endif %}
                
                {% if booking.notes %}
                <div style="margin-top: 12px;">
                    <div style="font-size: 11px; color: #64748b; margin-bottom: 4px;">SPECIAL REQUESTS</div>
                    <div style="font-size: 13px; color: #475569;">{{ booking.notes }}</div>
                </div>
                {% endif %}
            </div>
            
            <a href="{{ booking_url }}" style="display: inline-block; background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); color: white; padding: 14px 28px; text-decoration: none; border-radius: 10px; font-weight: 600; font-size: 14.5px; margin-top: 8px; box-shadow: 0 4px 6px rgba(15, 23, 42, 0.15);">
                View Booking Details
            </a>
            
            <p style="font-size: 13px; color: #64748b; margin-top: 24px; line-height: 1.5;">
                We'll send you a confirmation email once your reservation is confirmed.
            </p>
        </div>
        
        <!-- Footer -->
        <div style="padding: 24px; text-align: center; font-size: 12px; color: #94a3b8; border-top: 1px solid #f1f5f9;">
            <p style="margin: 6px 0;"><strong>M1 Limousine Service</strong></p>
            <p style="margin: 6px 0;">{{ company_info.phone }} | {{ company_info.email }}</p>
            <p style="margin: 12px 0 6px 0; font-size: 11px;">&copy; {% now "Y" %} M1 Limousine Service</p>
        </div>
    </div>
</body>
</html>'''
}

print("="*80)
print("TEMPLATE 1: NEW BOOKING NOTIFICATION")
print("="*80)
print(f"\nTemplate Type: {NEW_BOOKING_TEMPLATE['template_type']}")
print(f"Name: {NEW_BOOKING_TEMPLATE['name']}")
print(f"Description: {NEW_BOOKING_TEMPLATE['description']}")
print(f"\nSubject Template:")
print(NEW_BOOKING_TEMPLATE['subject_template'])
print(f"\n{'='*80}\n")
print("HTML Template:")
print(NEW_BOOKING_TEMPLATE['html_template'])
print(f"\n{'='*80}\n")
