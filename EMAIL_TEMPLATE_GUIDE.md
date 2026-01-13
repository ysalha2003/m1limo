# 📧 Email Template System - Easy Guide

## 🎯 What is This?

Instead of editing HTML files in the code, you can now create and edit email templates **directly in Django Admin**. Change the text, subject, design - all from your browser!

---

## 🚀 Quick Start - Create Your First Template

### Step 1: Access Admin
1. Go to: `http://your-server.com/admin/`
2. Login with your admin account
3. Look for "**Email templates**" in the sidebar
4. Click "**+ Add Email template**"

### Step 2: Fill in the Template

#### Basic Fields:
```
Template Type: Choose from dropdown (e.g., "Booking Confirmed")
Name: Give it a friendly name (e.g., "Booking Confirmation Email v2")
Active: ✓ Check this box (unchecked = disabled)
```

#### Email Subject:
```
Your Booking is Confirmed - {pick_up_date}
```
- Use **{variable_name}** for dynamic content
- Example: `{passenger_name}` will be replaced with the actual passenger name

#### Email HTML Body:
```html
<html>
<body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f5f5f5;">
    <div style="max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px;">
        
        <h1 style="color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px;">
            Booking Confirmed! ✓
        </h1>
        
        <p style="font-size: 16px; color: #333;">
            Dear <strong>{passenger_name}</strong>,
        </p>
        
        <p>Great news! Your booking has been confirmed.</p>
        
        <div style="background: #e8f4f8; padding: 20px; border-radius: 5px; margin: 20px 0;">
            <h3 style="margin-top: 0; color: #2980b9;">📅 Trip Details</h3>
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="padding: 8px; font-weight: bold;">Booking ID:</td>
                    <td style="padding: 8px;">#{booking_id}</td>
                </tr>
                <tr style="background: #d4e9f3;">
                    <td style="padding: 8px; font-weight: bold;">Pickup Date:</td>
                    <td style="padding: 8px;">{pick_up_date}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; font-weight: bold;">Pickup Time:</td>
                    <td style="padding: 8px;">{pick_up_time}</td>
                </tr>
                <tr style="background: #d4e9f3;">
                    <td style="padding: 8px; font-weight: bold;">From:</td>
                    <td style="padding: 8px;">{pick_up_location}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; font-weight: bold;">To:</td>
                    <td style="padding: 8px;">{drop_off_location}</td>
                </tr>
            </table>
        </div>
        
        <p style="font-size: 14px; color: #555;">
            A driver will be assigned to your trip soon. You'll receive another notification once assigned.
        </p>
        
        <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd;">
            <p style="font-size: 12px; color: #888;">
                Questions? Reply to this email or contact us at support@m1limo.com
            </p>
        </div>
        
    </div>
</body>
</html>
```

#### Notes Section (optional):
```
Updated design with better formatting. Created Jan 2026.
```

### Step 3: Save
Click **"Save and continue editing"** at the bottom

---

## 🎨 Available Variables - Copy & Paste

When creating templates, you can use these variables. Just copy and paste them into your subject or HTML body:

### 👤 Passenger Information
```
{passenger_name}     → "John Smith"
{passenger_email}    → "john@example.com"
{passenger_phone}    → "+1234567890"
```

### 📅 Booking Details
```
{booking_id}         → "42"
{booking_status}     → "confirmed"
{trip_type}          → "one_way" or "round_trip"
```

### 🚗 Trip Information
```
{pick_up_location}   → "123 Main St, New York"
{drop_off_location}  → "Airport Terminal 5"
{pick_up_date}       → "2026-01-20"
{pick_up_time}       → "14:30"
{passengers}         → "3"
```

### 🔙 Return Trip (Round Trip Only)
```
{return_pick_up_date}     → "2026-01-25"
{return_pick_up_time}     → "09:00"
{return_pick_up_location} → "Airport Terminal 5"
{return_drop_off_location}→ "123 Main St, New York"
```

### 👨‍✈️ Driver Information
```
{driver_name}        → "Mike Johnson"
{driver_phone}       → "+1987654321"
```

### 🌐 System Links
```
{booking_url}        → Full URL to view booking
{cancellation_url}   → Link to cancel booking
```

---

## 🧪 Test Your Template (3 Ways)

### Method 1: Preview in Admin (Recommended)
1. Open your template in admin
2. Click **"Preview Template"** button (top right)
3. See exactly how it will look with sample data
4. Make adjustments and preview again

### Method 2: Send Test Email
1. Open your template in admin
2. Click **"Send Test Email"** button
3. Check your admin email inbox
4. See the real email with sample data

### Method 3: Django Shell
```bash
python manage.py shell
```
```python
from models import EmailTemplate

# Get your template
template = EmailTemplate.objects.get(template_type='booking_confirmed')

# Test with sample data
context = {
    'passenger_name': 'John Doe',
    'booking_id': '123',
    'pick_up_date': 'January 20, 2026',
    'pick_up_time': '2:30 PM',
    'pick_up_location': 'Downtown Hotel',
    'drop_off_location': 'Airport'
}

# Test subject
print(template.render_subject(context))

# Test HTML (view in browser)
html = template.render_html(context)
with open('test_email.html', 'w') as f:
    f.write(html)
print("✓ Open test_email.html in browser")
```

---

## 📋 Real World Examples

### Example 1: Simple Booking Confirmation

**Template Type:** `booking_confirmed`

**Subject:**
```
Booking #{booking_id} Confirmed - {pick_up_date}
```

**HTML Body:**
```html
<html>
<body style="font-family: Arial; padding: 20px;">
    <h2>Hi {passenger_name}!</h2>
    <p>Your booking is confirmed for <strong>{pick_up_date}</strong> at <strong>{pick_up_time}</strong>.</p>
    <p><strong>From:</strong> {pick_up_location}<br>
       <strong>To:</strong> {drop_off_location}</p>
    <p>We'll send another email when your driver is assigned.</p>
    <p>Thanks,<br>M1 Limo Team</p>
</body>
</html>
```

---

### Example 2: Pickup Reminder (24 Hours Before)

**Template Type:** `booking_reminder`

**Subject:**
```
🚗 Tomorrow: Your Pickup at {pick_up_time}
```

**HTML Body:**
```html
<html>
<body style="font-family: Arial; padding: 20px; background: #fff3cd;">
    <div style="max-width: 600px; margin: 0 auto; background: white; padding: 20px; border: 2px solid #ffc107;">
        <h2 style="color: #856404;">⏰ Reminder: Pickup Tomorrow!</h2>
        
        <p>Hi <strong>{passenger_name}</strong>,</p>
        
        <p style="font-size: 18px; color: #333;">
            Your pickup is scheduled for <strong>{pick_up_date}</strong> at <strong>{pick_up_time}</strong>
        </p>
        
        <div style="background: #f8f9fa; padding: 15px; margin: 20px 0; border-left: 4px solid #ffc107;">
            <p style="margin: 5px 0;"><strong>📍 Pickup Location:</strong> {pick_up_location}</p>
            <p style="margin: 5px 0;"><strong>🎯 Destination:</strong> {drop_off_location}</p>
            <p style="margin: 5px 0;"><strong>👤 Driver:</strong> {driver_name}</p>
            <p style="margin: 5px 0;"><strong>📞 Driver Phone:</strong> {driver_phone}</p>
        </div>
        
        <p>Please be ready 5 minutes before pickup time.</p>
        
        <p style="font-size: 12px; color: #666; margin-top: 30px;">
            Need to cancel? <a href="{cancellation_url}">Click here</a>
        </p>
    </div>
</body>
</html>
```

---

### Example 3: Driver Assignment Notification

**Template Type:** `driver_assigned`

**Subject:**
```
Driver Assigned: {driver_name} - Booking #{booking_id}
```

**HTML Body:**
```html
<html>
<body style="font-family: Arial; padding: 20px;">
    <h2 style="color: #27ae60;">✓ Driver Assigned to Your Trip</h2>
    
    <p>Good news, <strong>{passenger_name}</strong>!</p>
    
    <div style="background: #d4edda; padding: 20px; border-radius: 5px; border-left: 5px solid #28a745;">
        <h3 style="margin-top: 0;">👨‍✈️ Your Driver</h3>
        <p style="font-size: 18px; margin: 10px 0;">
            <strong>{driver_name}</strong>
        </p>
        <p style="margin: 5px 0;">📞 Phone: <strong>{driver_phone}</strong></p>
    </div>
    
    <div style="margin-top: 20px; padding: 20px; background: #f8f9fa; border-radius: 5px;">
        <h3 style="margin-top: 0;">📋 Trip Summary</h3>
        <p><strong>Date:</strong> {pick_up_date} at {pick_up_time}</p>
        <p><strong>Pickup:</strong> {pick_up_location}</p>
        <p><strong>Destination:</strong> {drop_off_location}</p>
    </div>
    
    <p style="margin-top: 20px;">
        Your driver will contact you if needed. Have a great trip!
    </p>
    
    <p style="font-size: 12px; color: #888; margin-top: 30px;">
        Booking ID: #{booking_id}
    </p>
</body>
</html>
```

---

## 🎯 Tips for Creating Templates

### ✅ DO:
- **Keep it simple** - Clean design is better than fancy
- **Use inline styles** - Email clients don't support external CSS
- **Test on mobile** - Use max-width: 600px for main container
- **Use variables** - Makes emails personal and dynamic
- **Add clear CTAs** - Buttons or links for actions
- **Include booking ID** - For customer service reference

### ❌ DON'T:
- **Don't use external CSS files** - Won't work in emails
- **Don't use JavaScript** - Emails can't run scripts
- **Don't use background images** - Many email clients block them
- **Don't make it too wide** - Keep under 600px
- **Don't forget mobile** - Test how it looks on phones

---

## 🔄 How It Works Behind the Scenes

```
1. User books a trip
   ↓
2. System triggers email notification
   ↓
3. System checks: Is there an ACTIVE template in database?
   ↓
   YES → Use database template (your custom one!)
   NO  → Use old HTML file (fallback)
   ↓
4. Replace all {variables} with real data
   ↓
5. Send email to passenger
   ↓
6. Update statistics (total sent, success rate)
```

---

## 📊 Check Template Statistics

In the admin list view, you can see:
- **Total Sent** - How many times used
- **Success Rate** - % of successful emails
- **Last Used** - When was it last sent

This helps you track which templates work best!

---

## 🔧 Common Tasks

### Duplicate a Template (Create Variation)
1. Open existing template
2. Click **"Duplicate Template"** button
3. Edit the copy
4. Change name to "v2" or "Test Version"
5. Uncheck "Active" on old one
6. Check "Active" on new one

### Disable a Template (Revert to Old HTML)
1. Open template
2. Uncheck **"Active"** checkbox
3. Save
4. System will use old HTML files until you activate a template again

### Test Changes Without Affecting Live
1. Duplicate your live template
2. Make changes to the copy
3. Leave both inactive
4. Use "Preview" and "Send Test Email" to test
5. When ready: Activate new, deactivate old

---

## 🆘 Troubleshooting

### Problem: Variables show as {passenger_name} in email
**Solution:** The variable name is wrong. Check the "Available Variables" list above.

### Problem: Template not being used (old HTML still sent)
**Solution:** 
1. Check "Active" checkbox is ✓
2. Only ONE template per type should be active
3. Check template type matches the email being sent

### Problem: HTML looks broken
**Solution:**
1. Use inline styles only (style="..." in each tag)
2. Test with "Preview Template" button
3. Keep design simple - complex CSS doesn't work in emails

### Problem: Email not sent
**Solution:**
1. Check admin > Email templates > Statistics
2. Look at "Last Error" field
3. Check server logs: `logs/django.log`

---

## 📚 Template Types Available

| Type | When It's Sent | Key Variables |
|------|----------------|---------------|
| `booking_confirmed` | When booking created | passenger_name, pick_up_date, booking_id |
| `booking_reminder` | 24h before pickup | All booking + driver details |
| `driver_assigned` | When driver assigned | driver_name, driver_phone |
| `booking_cancelled` | When booking cancelled | cancellation reason |
| `booking_new` | Admin notification of new booking | All booking details |
| `round_trip_return` | Return trip created | return dates, locations |
| `driver_notification` | Driver gets trip assignment | All trip + passenger details |
| `status_changed` | Booking status changes | old_status, new_status |

---

## 🎓 Learning by Example - Step by Step

### Create a "Booking Confirmed" Email - Complete Walkthrough

#### Step 1: Go to Admin
```
URL: http://your-server.com/admin/bookings/emailtemplate/add/
```

#### Step 2: Choose Type
```
Template Type: [Booking Confirmed] ← select from dropdown
```

#### Step 3: Basic Info
```
Name: Booking Confirmation - January 2026
Active: ✓
Description: Sent when customer completes booking
```

#### Step 4: Write Subject (Simple)
```
Your M1 Limo Booking is Confirmed
```

#### Step 5: Write HTML (Start Simple, Add Style Later)
```html
<html>
<body>
    <p>Hi {passenger_name},</p>
    <p>Your booking is confirmed!</p>
    <p>Pickup: {pick_up_date} at {pick_up_time}</p>
    <p>From: {pick_up_location}</p>
    <p>To: {drop_off_location}</p>
    <p>Booking ID: #{booking_id}</p>
    <p>Thanks, M1 Limo</p>
</body>
</html>
```

#### Step 6: Save
Click **"Save and continue editing"**

#### Step 7: Preview
Click **"Preview Template"** button - You'll see sample email!

#### Step 8: Test
Click **"Send Test Email"** - Check your inbox!

#### Step 9: Improve (Now add styling)
```html
<html>
<body style="font-family: Arial, sans-serif; padding: 20px; background: #f0f0f0;">
    <div style="max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
        
        <h1 style="color: #2c3e50; margin-top: 0;">Booking Confirmed! ✓</h1>
        
        <p style="font-size: 16px;">Hi <strong>{passenger_name}</strong>,</p>
        
        <p>Great news! Your booking has been confirmed.</p>
        
        <div style="background: #e8f4f8; padding: 20px; border-radius: 5px; margin: 20px 0;">
            <p style="margin: 5px 0;"><strong>📅 Date:</strong> {pick_up_date}</p>
            <p style="margin: 5px 0;"><strong>🕐 Time:</strong> {pick_up_time}</p>
            <p style="margin: 5px 0;"><strong>📍 From:</strong> {pick_up_location}</p>
            <p style="margin: 5px 0;"><strong>🎯 To:</strong> {drop_off_location}</p>
        </div>
        
        <p style="font-size: 14px; color: #666;">
            Your booking ID is <strong>#{booking_id}</strong>
        </p>
        
        <p style="margin-top: 30px; font-size: 12px; color: #888; border-top: 1px solid #ddd; padding-top: 20px;">
            Questions? Email support@m1limo.com
        </p>
        
    </div>
</body>
</html>
```

#### Step 10: Preview Again & Send Test
Much better! 🎨

---

## 🎉 You're Ready!

Now you can:
1. ✅ Create email templates in admin
2. ✅ Use variables for dynamic content
3. ✅ Preview and test before going live
4. ✅ Update emails without touching code
5. ✅ Track email statistics

**Next:** Create templates for all 10 notification types and customize them for your brand!

---

## 💡 Quick Reference Card

```
Access: /admin/bookings/emailtemplate/
Actions: Add | Edit | Preview | Send Test | Duplicate
Variables: {passenger_name} {booking_id} {pick_up_date} etc.
Styling: Use inline style="..." attributes only
Testing: Preview button or Send Test Email button
Activate: Check "Active" checkbox and Save
Disable: Uncheck "Active" (system uses old HTML files)
Statistics: View in list page (total sent, success rate)
```

Need help? Check the "Variable documentation" section in each template - it shows all available variables for that type!
