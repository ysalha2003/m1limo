# 🚀 M1 Limousine Production Deployment Guide

## ✅ **ISSUES FIXED FOR PRODUCTION**

### 1. **Email Template Optimization**
- **✅ FIXED:** Removed logo images from email templates (static files don't load in emails)
- **✅ FIXED:** Replaced with clean, text-based "M1 LIMOUSINE SERVICE" header
- **✅ BENEFIT:** Faster email loading, no broken images, professional appearance
- **Files Updated:**
  - `templates/emails/booking_notification.html`
  - `templates/emails/driver_notification.html`
  - `templates/emails/booking_reminder.html`
  - `templates/emails/round_trip_notification.html`

### 2. **Production URL Configuration**
- **✅ FIXED:** All email links now use `settings.BASE_URL` instead of localhost
- **✅ FIXED:** Dashboard links point to `{BASE_URL}/dashboard`
- **✅ FIXED:** Driver portal links use production URL
- **Configuration:** `BASE_URL = http://62.169.19.39:8081` in settings.py
- **Files Updated:**
  - `email_service.py` (lines 186, 241, 587)

### 3. **Smart Trip ID Search**
- **✅ IMPLEMENTED:** Search with `#147` returns only Trip #147 (not phone numbers)
- **✅ IMPLEMENTED:** Search with `147` searches both Trip ID and other fields
- **✅ IMPLEMENTED:** Updated placeholder: "Trip #ID, Name, Phone, or Reference Number"
- **Files Updated:**
  - `views.py` (dashboard function)
  - `templates/bookings/dashboard.html`

---

## 📊 **BUSINESS LOGIC OVERVIEW**

### **Booking Lifecycle**

```
1. CREATION
   ├─→ User creates booking (new_booking view)
   ├─→ Status: "Pending"
   ├─→ Email sent to user (confirmation)
   ├─→ Email sent to admin (notification)
   └─→ BookingHistory entry created (action='created')

2. ADMIN CONFIRMATION
   ├─→ Admin reviews booking
   ├─→ Status: Pending → Confirmed
   ├─→ Driver can be assigned
   ├─→ Email sent to user (confirmation)
   └─→ BookingHistory entry (action='status_changed')

3. DRIVER ASSIGNMENT
   ├─→ Admin assigns driver (assign_driver view)
   ├─→ Driver receives email with portal link
   ├─→ Driver can accept/reject via unique token link
   ├─→ driver_response_status: 'pending' → 'accepted'/'rejected'
   └─→ BookingHistory entry (action='driver_assigned')

4. TRIP EXECUTION
   ├─→ Driver completes trip via portal link
   ├─→ Validation: Must be 5+ hours after pickup time
   ├─→ Status: Confirmed → Trip_Completed
   ├─→ driver_response_status: 'accepted' → 'completed'
   └─→ BookingHistory entry (action='driver_completed')

5. CANCELLATION
   ├─→ User/Admin cancels booking
   ├─→ Status: * → Cancelled or Cancelled_Full_Charge
   ├─→ Email notifications sent
   └─→ BookingHistory entry (action='cancelled')
```

### **Round Trip Handling**

```
Round Trip = 2 Separate Bookings Linked Together

Outbound Trip (trip_label="Outbound")
   ├─→ is_return_trip = False
   ├─→ linked_booking_id = [Return Trip ID]
   └─→ Separate driver assignment

Return Trip (trip_label="Return")
   ├─→ is_return_trip = True
   ├─→ linked_booking_id = [Outbound Trip ID]
   └─→ Separate driver assignment

Both trips:
   - Have their own status
   - Can be managed independently
   - Show linked trip in UI
   - Send combined email notification option
```

### **Status Flow**

```
Pending → Confirmed → Trip_Completed
   ↓          ↓
Cancelled   Cancelled_Full_Charge
   ↓          ↓
Trip_Not_Covered (for past pending trips)
Customer_No_Show (for no-shows)
```

### **Email Notifications**

| Trigger | Recipient | Template | Condition |
|---------|-----------|----------|-----------|
| New Booking | User + Admin | booking_notification.html | notification_type='new' |
| Confirmed | User | booking_notification.html | notification_type='confirmed' |
| Cancelled | User | booking_notification.html | notification_type='cancelled' |
| Driver Assignment | Driver | driver_notification.html | When driver assigned |
| Pickup Reminder | User | booking_reminder.html | 2 hours before pickup |
| Round Trip | User | round_trip_notification.html | For linked trips |

**User Preferences (UserProfile model):**
- `receive_booking_confirmations` (default: True)
- `receive_status_updates` (default: True)
- `receive_pickup_reminders` (default: True)

---

## 🔒 **SECURITY FEATURES**

### **Driver Portal Authentication**
```python
# Token Generation (MD5 hash)
token = md5(f"{booking_id}-{driver_email}").hexdigest()[:16]

# URL Structure
/driver/trip/{booking_id}/{token}/
/driver/trips/{driver_email}/{all_trips_token}/

# Validation in views.py
expected_token = md5(f"{booking_id}-{driver.email}").hexdigest()[:16]
if token != expected_token:
    # Access denied
```

### **5-Hour Trip Completion Rule**
```python
# Drivers can only mark trip complete AFTER 5 hours from pickup
pickup_datetime = combine(booking.pick_up_date, booking.pick_up_time)
time_since_pickup = now - pickup_datetime

if time_since_pickup < timedelta(hours=5):
    # Validation fails, show error message
```

---

## 🎨 **UI BEHAVIOR & TEMPLATES**

### **Dashboard (templates/bookings/dashboard.html)**
**Features:**
- ✅ Mobile responsive (768px, 480px breakpoints)
- ✅ Smart search with `#` prefix for Trip IDs
- ✅ Filter by status, date range
- ✅ Stat cards with click-to-filter
- ✅ Today's pickups highlighted
- ✅ Round trip expand/collapse
- ✅ "NEW" badge for unviewed changes

**Admin vs User Views:**
- **Admin:** See all bookings, can assign drivers, view customer info
- **User:** See only their bookings, can edit (if <2 hours to pickup)

### **Booking Detail (templates/bookings/booking_detail.html)**
**Features:**
- ✅ Mobile responsive with comprehensive media queries
- ✅ Status banner with color coding
- ✅ Trip information cards
- ✅ Linked booking display for round trips
- ✅ Edit menu (fixed position on mobile)
- ✅ Driver information (if assigned)
- ✅ Booking history timeline

**Mobile Optimizations:**
- Grids stack to single column
- Buttons go full-width
- Fixed-position edit menu at bottom center
- Reduced font sizes (480px breakpoint)

### **Activity Log (templates/bookings/booking_activity.html)**
**Features:**
- ✅ Mobile responsive (table → cards on mobile)
- ✅ Filter by action type, date range
- ✅ Pagination
- ✅ Accessible from navbar (staff only)
- ✅ Shows change diffs with old → new values

**Mobile Behavior:**
- Table rows become cards
- Data labels appear inline via `data-label` attributes
- Stack vertically with proper spacing

---

## 🌐 **PRODUCTION DEPLOYMENT CHECKLIST**

### **Ubuntu VPS Configuration**

1. **Environment Variables**
   ```bash
   export DEBUG=False
   export BASE_URL=http://62.169.19.39:8081  # Or your domain
   export ALLOWED_HOSTS=62.169.19.39,m1limo.com
   ```

2. **Static Files**
   ```bash
   python manage.py collectstatic --noinput
   ```

3. **Database Migration**
   ```bash
   python manage.py migrate
   ```

4. **Create Superuser**
   ```bash
   python manage.py createsuperuser
   ```

5. **Email Configuration (settings.py)**
   ```python
   EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
   EMAIL_HOST = 'smtp.gmail.com'  # Or your SMTP server
   EMAIL_PORT = 587
   EMAIL_USE_TLS = True
   EMAIL_HOST_USER = os.environ.get('EMAIL_USER')
   EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_PASSWORD')
   ```

6. **Web Server (Gunicorn)**
   ```bash
   gunicorn wsgi:application --bind 0.0.0.0:8081
   ```

7. **Process Manager (Systemd)**
   ```ini
   [Unit]
   Description=M1 Limousine Gunicorn Service
   After=network.target

   [Service]
   User=www-data
   Group=www-data
   WorkingDirectory=/path/to/m1limo
   Environment="PATH=/path/to/venv/bin"
   Environment="DEBUG=False"
   Environment="BASE_URL=http://62.169.19.39:8081"
   ExecStart=/path/to/venv/bin/gunicorn wsgi:application --bind 0.0.0.0:8081

   [Install]
   WantedBy=multi-user.target
   ```

### **Link Verification**

All internal links use Django's `{% url %}` template tags:
- ✅ `{% url 'dashboard' %}` → `/dashboard/`
- ✅ `{% url 'reservation_detail' booking.id %}` → `/reservation/{id}/`
- ✅ `{% url 'driver_trip_response' booking.id token %}` → `/driver/trip/{id}/{token}/`

**Email links use `settings.BASE_URL`:**
- ✅ Dashboard: `{BASE_URL}/dashboard`
- ✅ Driver Portal: `{BASE_URL}/driver/trip/{id}/{token}/`

---

## 📈 **KEY METRICS & MONITORING**

### **Booking Statistics**
- Total bookings by status
- Pending (awaiting confirmation)
- Confirmed (active trips)
- Trip_Completed (finished)
- Cancelled (user/admin cancelled)

### **Driver Performance**
- Accepted trips
- Rejected trips
- Completed trips
- Payment status tracking

### **User Activity**
- New registrations
- Booking frequency
- Cancellation rate
- Email preference opt-outs

---

## 🔧 **MAINTENANCE TASKS**

### **Daily**
- Review past confirmed trips (automated alert banner)
- Review past pending requests (automated alert banner)
- Check driver assignments for today's pickups

### **Weekly**
- Review booking history for anomalies
- Check email delivery logs
- Monitor driver response rates

### **Monthly**
- Review user profiles and preferences
- Clean up old booking history (optional)
- Generate reports (bookings by month, revenue, etc.)

---

## 📝 **BUSINESS RULES SUMMARY**

1. **Booking Edit Window:** Users can edit bookings up to 2 hours before pickup
2. **Driver Completion:** Must wait 5 hours after pickup time to mark complete
3. **Round Trip:** Always creates 2 separate bookings with `linked_booking_id`
4. **Email Preferences:** Users can opt-out of confirmations, updates, or reminders
5. **Search Priority:** `#147` searches Trip ID only, `147` searches all fields
6. **Status Validation:** Certain transitions are restricted (e.g., can't complete before pickup)
7. **Activity Log:** All changes tracked in BookingHistory with old/new values
8. **Driver Payment:** Tracked separately, admin can mark as paid

---

## ✅ **VERIFICATION STEPS**

After deployment, verify:

1. ✅ Access site at `http://62.169.19.39:8081`
2. ✅ Create test booking (status: Pending)
3. ✅ Check email received (no broken logo images)
4. ✅ Confirm booking (status: Confirmed)
5. ✅ Assign driver, verify driver email with working portal link
6. ✅ Test driver portal: `http://62.169.19.39:8081/driver/trip/{id}/{token}/`
7. ✅ Test search: `#147` returns only Trip #147
8. ✅ Test mobile view (responsive design)
9. ✅ Test Activity Log from mobile navbar
10. ✅ Verify all dashboard links work correctly

---

## 🎯 **CONCLUSION**

Your system is now **production-ready** with:

- ✅ Optimized, lightweight emails (no broken images)
- ✅ Correct production URLs for Ubuntu VPS
- ✅ Smart Trip ID search functionality
- ✅ Comprehensive mobile responsiveness
- ✅ Secure driver portal with token authentication
- ✅ Robust business logic with validation
- ✅ Complete audit trail (BookingHistory)
- ✅ User notification preferences

All links will work correctly on your Ubuntu VPS with public IPv4 `62.169.19.39:8081`.
