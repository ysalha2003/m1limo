# 📧 Email Template Types - Quick Reference

## 🎯 Priority Order (Create These First)

### ⭐ MUST HAVE (Create these immediately)

#### 1. **Booking Confirmed** 
- **When sent:** Customer completes a new booking
- **Sent to:** Passenger
- **Purpose:** Confirm booking details, provide booking ID
- **Key variables:** `{passenger_name}` `{booking_id}` `{pick_up_date}` `{pick_up_time}` `{pick_up_location}` `{drop_off_location}`

#### 2. **Pickup Reminder**
- **When sent:** 24 hours before pickup (automated task)
- **Sent to:** Passenger  
- **Purpose:** Remind passenger about upcoming trip
- **Key variables:** All booking variables + `{driver_name}` `{driver_phone}`

#### 3. **Driver Assignment**
- **When sent:** Admin assigns driver to booking
- **Sent to:** Passenger
- **Purpose:** Tell passenger who their driver is
- **Key variables:** `{driver_name}` `{driver_phone}` + booking details

---

### 🔄 ROUND TRIP TEMPLATES (If you offer round trips)

#### 4. **Round Trip - Confirmed**
- **When sent:** Customer books a round trip (both legs created)
- **Sent to:** Passenger
- **Purpose:** Confirm both outbound AND return trips
- **Key variables:** All booking variables + `{return_pick_up_date}` `{return_pick_up_time}` `{return_pick_up_location}` `{return_drop_off_location}`

#### 5. **Round Trip - New**
- **When sent:** Admin is notified of new round trip booking
- **Sent to:** Admin
- **Purpose:** Alert admin to assign drivers
- **Key variables:** All round trip details

---

### ⚠️ IMPORTANT UPDATES

#### 6. **Booking Cancelled**
- **When sent:** Booking is cancelled by passenger or admin
- **Sent to:** Passenger
- **Purpose:** Confirm cancellation, explain refund policy
- **Key variables:** `{booking_id}` `{cancellation_reason}` `{pick_up_date}`

#### 7. **Status Change**
- **When sent:** Booking status changes (e.g., pending → confirmed → completed)
- **Sent to:** Passenger
- **Purpose:** Keep passenger informed of booking progress
- **Key variables:** `{old_status}` `{new_status}` `{booking_id}`

---

### 📋 ADMIN NOTIFICATIONS (Nice to have)

#### 8. **New Booking**
- **When sent:** New booking created
- **Sent to:** Admin/Dispatcher
- **Purpose:** Alert admin to new booking requiring attention
- **Key variables:** All booking details + `{passenger_phone}` `{passenger_email}`

#### 9. **Round Trip - Cancelled**
- **When sent:** Round trip cancelled
- **Sent to:** Passenger
- **Purpose:** Confirm both trips cancelled
- **Key variables:** Round trip details + `{cancellation_reason}`

#### 10. **Round Trip - Status Change**
- **When sent:** Round trip status changes
- **Sent to:** Passenger
- **Purpose:** Update on round trip progress
- **Key variables:** Round trip details + `{old_status}` `{new_status}`

---

## 🚀 Quick Start Guide

### Step 1: Create Top 3 Templates First
1. **Booking Confirmed** - Most important!
2. **Pickup Reminder** - Reduces no-shows
3. **Driver Assignment** - Builds trust

### Step 2: Test Each Template
```bash
# Create template in admin
# Click "Preview Template"
# Click "Send Test Email"
# Check your inbox
```

### Step 3: Activate Templates
- Check the **"Active"** checkbox
- Only 1 template per type can be active
- System will use your template instead of old HTML files

### Step 4: Monitor Results
- Check admin list for **Success Rate**
- View **Total Sent** statistics
- Check **Last Used** timestamp

---

## 📝 Template Creation Checklist

For each template you create:

- [ ] Choose correct **Template Type**
- [ ] Give it a clear **Name** (e.g., "Booking Confirmation - Jan 2026")
- [ ] Write **Subject** with variables (e.g., "Booking #{booking_id} Confirmed")
- [ ] Copy HTML example from EMAIL_TEMPLATE_GUIDE.md
- [ ] Replace variables for your use case
- [ ] Check **Active** checkbox
- [ ] Click **Save**
- [ ] Click **Preview Template** to test
- [ ] Click **Send Test Email** to your inbox
- [ ] Verify email looks good
- [ ] Test with real booking if needed

---

## 🎨 Where to Find HTML Examples

Open [EMAIL_TEMPLATE_GUIDE.md](EMAIL_TEMPLATE_GUIDE.md) and find:

- **Section: "Real World Examples"**
  - Example 1: Simple Booking Confirmation
  - Example 2: Pickup Reminder (24 Hours Before)  
  - Example 3: Driver Assignment Notification

- **Section: "Available Variables - Copy & Paste"**
  - All variables with explanations
  - Organized by category (passenger, booking, trip, driver)

---

## 🔄 Workflow Examples

### Scenario 1: Customer Books One-Way Trip
```
1. Customer fills booking form → "Booking Confirmed" email sent
2. Admin assigns driver → "Driver Assignment" email sent
3. 24h before pickup → "Pickup Reminder" email sent
4. Trip completed → Status changes to "completed"
```

### Scenario 2: Customer Books Round Trip
```
1. Customer books round trip → "Round Trip - Confirmed" email sent
   (Contains both outbound AND return details)
2. Admin assigns driver to outbound → "Driver Assignment" email sent
3. 24h before outbound → "Pickup Reminder" sent
4. 24h before return → Another "Pickup Reminder" sent for return leg
```

### Scenario 3: Customer Cancels
```
1. Customer requests cancellation → "Booking Cancelled" email sent
2. Email explains cancellation policy
3. Booking marked as cancelled in system
```

---

## 🎯 Template Type Database Values

When creating templates, select these from the dropdown:

| Display Name | Database Value | Code Reference |
|-------------|----------------|----------------|
| New Booking | `booking_new` | For admin notifications |
| Booking Confirmed | `booking_confirmed` | Most important! |
| Booking Cancelled | `booking_cancelled` | Cancellation confirmations |
| Status Change | `status_changed` | When status updates |
| Pickup Reminder | `booking_reminder` | 24h before pickup |
| Driver Assignment | `driver_assigned` | When driver assigned |
| Round Trip - New | `round_trip_new` | Admin: new round trip |
| Round Trip - Confirmed | `round_trip_confirmed` | Customer: round trip booked |
| Round Trip - Cancelled | `round_trip_cancelled` | Round trip cancelled |
| Round Trip - Status Change | `round_trip_status_changed` | Round trip status update |

---

## 💡 Pro Tips

### Tip 1: Start Simple
Don't create all 10 at once. Start with top 3:
1. Booking Confirmed
2. Pickup Reminder  
3. Driver Assignment

### Tip 2: Use Duplicate Feature
1. Create one template
2. Click "Duplicate Template"
3. Modify for different type
4. Saves time!

### Tip 3: Test Before Activating
1. Create template (leave Active unchecked)
2. Use "Preview" and "Send Test Email"
3. When perfect, check "Active"
4. Old template becomes inactive automatically (only 1 active per type)

### Tip 4: Keep Old as Backup
Don't delete old templates - just uncheck "Active"
They're saved as backup if you need to revert

### Tip 5: Track What Works
- Check **Success Rate** in admin list
- Templates with 100% = working great
- Templates with <100% = check "Last Error" field

---

## 🆘 Common Questions

**Q: What if I don't create a template for a type?**  
A: System uses the old HTML files from `templates/emails/` folder

**Q: Can I have multiple templates active for one type?**  
A: No - only 1 active template per type. System uses the most recently activated one.

**Q: What happens to old HTML files?**  
A: They stay as fallback. If no active DB template, old files are used.

**Q: How do I know which template was sent?**  
A: Check admin list view - see "Total Sent" and "Last Used" timestamp

**Q: Can I test without sending real email?**  
A: Yes! Use "Preview Template" button to see HTML without sending

**Q: What if customer doesn't get email?**  
A: Check template's "Last Error" field in admin for error message

---

## 📊 Expected Usage Statistics

After 1 month, you should see:

| Template | Expected Sends | Success Rate |
|----------|---------------|--------------|
| Booking Confirmed | Highest | 95-100% |
| Pickup Reminder | High | 90-100% |
| Driver Assignment | Medium-High | 95-100% |
| Booking Cancelled | Low | 95-100% |
| Status Change | Medium | 95-100% |
| New Booking (admin) | Same as Booking Confirmed | 100% |

Low success rate? Check "Last Error" field!

---

## ✅ Ready to Create?

1. Go to: http://your-domain.com/admin/bookings/emailtemplate/add/
2. Start with **"Booking Confirmed"**
3. Use HTML example from EMAIL_TEMPLATE_GUIDE.md
4. Preview, test, activate!
5. Move to next template

You've got this! 🚀
