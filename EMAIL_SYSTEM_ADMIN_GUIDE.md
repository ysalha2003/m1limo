# 📧 Complete Email Template System - Admin Guide

## ✅ COMPLETE SYSTEM - 13 Templates for ALL Scenarios

Your email notification system now covers **every** notification scenario with admin-programmable templates.

---

## 📊 All 13 Notification Scenarios

### 👥 CUSTOMER NOTIFICATIONS (6 templates)

| # | Template Name | When Sent | Sent To | Enable/Disable |
|---|--------------|-----------|---------|----------------|
| 1 | **New Booking Alert** | New booking created | Admin only | ✓ is_active checkbox |
| 2 | **Booking Confirmation** | Booking confirmed | Customer + Admin | ✓ is_active checkbox |
| 3 | **Booking Cancellation** | Booking cancelled | Customer + Admin | ✓ is_active checkbox |
| 4 | **Status Update** | Status changes | Customer + Admin | ✓ is_active checkbox |
| 5 | **Pickup Reminder** | 24h before pickup | Customer + Passenger | ✓ is_active checkbox |
| 6 | **Driver Assigned** | Driver assigned to trip | Customer only | ✓ is_active checkbox |

### 🚗 DRIVER NOTIFICATIONS (3 templates)

| # | Template Name | When Sent | Sent To | Enable/Disable |
|---|--------------|-----------|---------|----------------|
| 7 | **Driver Trip Assignment** | Driver assigned to trip | Driver only | ✓ is_active checkbox |
| 8 | **Driver Rejection Alert** | Driver rejects trip | Admin only | ✓ is_active checkbox |
| 9 | **Driver Completion Alert** | Driver completes trip | Admin only | ✓ is_active checkbox |

### 🔄 ROUND TRIP NOTIFICATIONS (4 templates)

| # | Template Name | When Sent | Sent To | Enable/Disable |
|---|--------------|-----------|---------|----------------|
| 10 | **New Round Trip Alert** | Round trip created | Admin only | ✓ is_active checkbox |
| 11 | **Round Trip Confirmation** | Round trip confirmed | Customer + Admin | ✓ is_active checkbox |
| 12 | **Round Trip Cancellation** | Round trip cancelled | Customer + Admin | ✓ is_active checkbox |
| 13 | **Round Trip Status Update** | Round trip status changes | Customer + Admin | ✓ is_active checkbox |

---

## 🎛️ Admin Control Panel

### Access Templates:
```
http://your-domain.com/admin/bookings/emailtemplate/
```

### For Each Template You Can:

1. **Enable/Disable** - Uncheck `is_active` to disable
2. **Configure Recipients** - Toggle who receives:
   - `send_to_user` - Booking user's email
   - `send_to_admin` - Admin email(s)
   - `send_to_passenger` - Passenger email (if different)
3. **Edit Content** - Customize subject and HTML body
4. **Preview** - See rendered email with sample data
5. **Test** - Send test email to your inbox
6. **Track Statistics** - View sent count and success rate

---

## 📝 How to Disable Specific Notifications

### Example: Disable Driver Rejection Alerts

1. Go to `/admin/bookings/emailtemplate/`
2. Click **"Driver Rejection Alert (Admin)"**
3. **Uncheck** the `Active` checkbox
4. Click **Save**
5. ✓ No more driver rejection emails sent

### Example: Enable Only Critical Notifications

Keep these **ACTIVE** (✓):
- Booking Confirmation
- Booking Cancellation  
- Driver Assigned
- Pickup Reminder

Disable these by **UNCHECKING** (✗):
- New Booking Alert (you get enough emails already)
- Status Update (too frequent)
- Driver Rejection Alert (handle in admin panel)
- Driver Completion Alert (check dashboard instead)

---

## 🎯 Common Admin Scenarios

### Scenario 1: Stop Sending Admin Alerts for Every New Booking

**Problem:** Getting too many "New Booking Alert" emails

**Solution:**
1. Go to template: **"New Booking Alert (Admin)"**
2. Uncheck `Active`
3. Save
4. ✓ Admins stop receiving new booking emails
5. Bookings still work normally

---

### Scenario 2: Change Who Receives Driver Rejection Alerts

**Problem:** Want multiple admins to get driver rejection alerts

**Solution:**
1. Go to template: **"Driver Rejection Alert (Admin)"**
2. Template already set to `send_to_admin = True`
3. Add more admin emails in Django settings:
   ```python
   ADMIN_EMAIL = 'admin@m1limo.com'  # Primary
   # For multiple, use NotificationRecipient model in admin
   ```
4. Or create **NotificationRecipient** entries for each admin

---

### Scenario 3: Customize Email Branding

**Problem:** Want to add company logo and colors

**Solution:**
1. Open any template
2. Edit `Html template` field
3. Add logo at top:
   ```html
   <img src="https://your-domain.com/static/images/logo.png" style="width: 150px;">
   ```
4. Change colors in style attributes:
   ```html
   style="background: #YOUR_BRAND_COLOR;"
   ```
5. Preview → Save → Apply to other templates

---

### Scenario 4: A/B Test Email Templates

**Problem:** Want to test which email gets better response

**Solution:**
1. Open template (e.g., "Booking Confirmation")
2. Click **"Duplicate Template"** button (if available in list actions)
3. Edit copy with new design
4. **Deactivate** old template (uncheck Active)
5. **Activate** new template (check Active)
6. Monitor statistics (sent count, success rate)
7. Compare performance

---

## 🔍 Monitoring & Statistics

### View Template Performance:

**Admin List View** shows:
- **Total Sent** - How many times template used
- **Success Rate** - % of successful deliveries
- **Last Sent** - When last used
- **Status** - Active or Inactive

### Check Individual Template:
1. Open template
2. Scroll to **"Statistics"** section
3. See:
   - Total sent
   - Total failed
   - Success rate %
   - Last sent timestamp
   - Last error (if any)

---

## ⚡ Quick Actions

### Disable ALL Admin Notifications:
1. Go to template list
2. Filter by: `send to admin = Yes`
3. For each result, uncheck `Active`
4. ✓ Admins get no emails (customers still do)

### Disable ALL Notifications Temporarily:
1. Go to template list
2. Select all templates (checkbox at top)
3. Choose action: "Deactivate selected templates"
4. ✓ System falls back to old HTML files OR sends no emails

### Enable Notifications After Testing:
1. Go to template list  
2. Select templates to enable
3. Choose action: "Activate selected templates"
4. ✓ Database templates used again

---

## 🛠️ Troubleshooting

### Problem: Emails Not Sending

**Check:**
1. Is template `Active`? (✓ checkbox)
2. Are recipients configured? (`send_to_user`, `send_to_admin`)
3. Check template **"Last Error"** field
4. Check Django logs: `logs/django.log`
5. Test with **"Send Test Email"** button

### Problem: Wrong Variables in Email

**Solution:**
1. Open template
2. Scroll to **"Available Variables"** section
3. See table of all valid variables
4. Copy variable names exactly: `{passenger_name}`
5. Subject and HTML must use same format

### Problem: Template Not Being Used

**Check:**
1. Only ONE template per type can be active
2. Most recently activated template is used
3. If multiple active, system uses first found
4. **Solution:** Deactivate duplicates

---

## 📚 Template Variables Reference

### Common Variables (All Templates):
```
{booking_id}          - Booking ID number
{passenger_name}      - Passenger full name  
{passenger_email}     - Passenger email
{passenger_phone}     - Passenger phone
{pick_up_date}        - Pickup date
{pick_up_time}        - Pickup time
{pick_up_location}    - Pickup address
{drop_off_location}   - Destination address
{passengers}          - Number of passengers
{trip_type}           - Trip type (one_way/round_trip)
{booking_status}      - Current status
{booking_url}         - Link to booking details
```

### Driver Variables:
```
{driver_name}         - Driver full name
{driver_phone}        - Driver phone number
{driver_rejection_reason} - Why driver rejected
{driver_completed_at} - When trip completed
```

### Status Change Variables:
```
{old_status}          - Previous status
{new_status}          - New status
```

### Round Trip Variables:
```
{return_pick_up_date}     - Return trip date
{return_pick_up_time}     - Return trip time
{return_pick_up_location} - Return pickup address
{return_drop_off_location}- Return destination
```

**View full list:** Open any template → Scroll to **"Available Variables"** section

---

## 🚀 Server Deployment Commands

### On Remote Server:

```bash
# 1. Navigate to project
cd /opt/m1limo
source venv/bin/activate

# 2. Create all 13 templates
python setup_complete_email_system.py

# 3. Verify templates created
python show_templates.py

# 4. Restart services
sudo systemctl restart nginx
sudo systemctl restart m1limo

# 5. Access admin
# http://your-domain.com/admin/bookings/emailtemplate/
```

---

## ✅ System Benefits

### Before (Hard-Coded):
- ✗ Edit HTML files in code
- ✗ Deploy to server every change
- ✗ Restart server for email changes
- ✗ No preview before sending
- ✗ No statistics tracking
- ✗ Can't disable specific notifications

### After (Database Templates):
- ✅ Edit in admin interface
- ✅ No code deployment needed
- ✅ Changes apply immediately
- ✅ Preview with sample data
- ✅ Track sent count and success rate
- ✅ Enable/disable any notification
- ✅ Control recipients per template
- ✅ Test before going live

---

## 📞 Support

### Common Questions:

**Q: What if I break a template?**
A: System falls back to old HTML files. Or duplicate working template and try again.

**Q: Can I have multiple templates active?**
A: No - only 1 active template per type. System uses most recently activated.

**Q: How do I revert to old emails?**
A: Uncheck `Active` on template. System uses HTML files in `templates/emails/`.

**Q: Can I export templates?**
A: Not built-in yet. Copy HTML from template to save locally.

**Q: Where are statistics stored?**
A: In `EmailTemplate` model fields: `total_sent`, `total_failed`, `last_sent_at`

---

## 🎉 You're Ready!

Your email system is now:
- ✅ **Complete** - All 13 scenarios covered
- ✅ **Programmable** - Edit in admin
- ✅ **Controllable** - Enable/disable per template
- ✅ **Trackable** - Statistics for each template
- ✅ **Testable** - Preview and send test emails
- ✅ **Production-ready** - Used by live bookings

**Access now:** http://your-domain.com/admin/bookings/emailtemplate/
