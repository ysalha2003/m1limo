# File-Based Email Templates - Complete Inventory

**Date:** January 16, 2026  
**Issue:** Templates disabled in admin but emails still sent via file-based fallback

---

## Summary

When all database templates are marked as **inactive**, the system falls back to **4 file-based templates** located in `templates/emails/`. This is why you still received the 'Trip Confirmed' notification even with all admin templates disabled.

---

## File-Based Templates Found (4 files)

### 1. **booking_notification.html**
**Location:** `templates/emails/booking_notification.html` (182 lines)  
**Used For:**
- New booking requests (notification_type='new')
- Booking confirmations (notification_type='confirmed')
- Booking cancellations (notification_type='cancelled')
- Status changes (notification_type='status_change')

**When Used:** When database templates for `booking_new`, `booking_confirmed`, `booking_cancelled`, or `booking_status_change` are inactive or missing.

**Features:**
- Professional gradient header (dark blue)
- Status-based color coding
- Booking details display
- Mobile-responsive design

---

### 2. **booking_reminder.html**
**Location:** `templates/emails/booking_reminder.html` (170 lines)  
**Used For:**
- Pickup reminders (notification_type='reminder')
- Sent before scheduled pickup time

**When Used:** When database template for `booking_reminder` is inactive or missing.

**Features:**
- Blue gradient header
- Prominent reminder badge
- Trip countdown display
- Mobile-responsive design

---

### 3. **driver_notification.html**
**Location:** `templates/emails/driver_notification.html` (146 lines)  
**Used For:**
- Driver trip assignment notifications
- Sent when a driver is assigned to a booking

**When Used:** When database template for `driver_notification` is inactive or missing.

**Features:**
- Gold/black theme for driver branding
- Trip details card
- Passenger contact information
- Action buttons for driver portal
- Accept/Reject trip links

---

### 4. **round_trip_notification.html**
**Location:** `templates/emails/round_trip_notification.html` (114 lines)  
**Used For:**
- Round trip booking requests (notification_type='new')
- Round trip confirmations (notification_type='confirmed')
- Round trip cancellations (notification_type='cancelled')
- Round trip status changes (notification_type='status_change')

**When Used:** When database templates for `round_trip_new`, `round_trip_confirmed`, `round_trip_cancelled`, or `round_trip_status_change` are inactive or missing.

**Features:**
- Purple gradient header for round trips
- Dual trip display (outbound + return)
- Status-based messaging
- Mobile-responsive design

---

## Fallback Logic in Code

### Location: `email_service.py`

The fallback mechanism exists in **3 main methods**:

#### 1. `send_booking_notification()` (Lines 100-116)
```python
# Fallback to file templates if database template not available or failed
if not db_template:
    subject = cls._get_email_subject(booking, notification_type, old_status, is_return)
    template_name = cls._get_template_name(notification_type)  # Returns file path

    try:
        html_message = render_to_string(template_name, context)  # ← USES FILE TEMPLATE
        plain_message = strip_tags(html_message)
    except Exception as e:
        logger.error(f"Template rendering error: {e}")
        html_message = cls._get_fallback_message(booking, notification_type)  # ← HARDCODED HTML
        plain_message = strip_tags(html_message)
```

#### 2. `send_round_trip_notification()` (Lines 458-470)
```python
# Fallback to file templates if database template not available or failed
if not db_template:
    subject = cls._get_round_trip_subject(first_trip, return_trip, notification_type)
    template_name = 'emails/round_trip_notification.html'  # ← FILE PATH

    try:
        html_message = render_to_string(template_name, context)  # ← USES FILE TEMPLATE
        plain_message = strip_tags(html_message)
    except Exception as e:
        logger.error(f"Round trip template rendering error: {e}")
        html_message = cls._get_fallback_round_trip_message(first_trip, return_trip, notification_type)  # ← HARDCODED HTML
```

#### 3. `send_driver_notification()` (Lines 744-763)
```python
# Fallback to file template if database template not available or failed
if not db_template:
    # Build context for file template with _build_driver_template_context
    template_context = cls._build_driver_template_context(booking, driver)
    
    # For file template, we need objects for Django template filters
    context = {
        'driver': driver,
        'booking': booking,
        # ... other context
    }
    
    html_message = render_to_string('emails/driver_notification.html', context)  # ← USES FILE TEMPLATE
    subject = f"New Trip Assignment - {booking.pick_up_date.strftime('%b %d, %Y')}"
    logger.info(f"Using file template fallback for driver notification")
```

---

## Helper Methods That Support Fallback

### `_get_template_name()` (Lines 564-570)
```python
@staticmethod
def _get_template_name(notification_type: str) -> str:
    """Get template file name for notification type."""
    if notification_type == 'reminder':
        return 'emails/booking_reminder.html'  # ← FILE PATH
    else:
        return 'emails/booking_notification.html'  # ← FILE PATH
```

### `_get_fallback_message()` (Lines 572-592)
Returns hardcoded HTML if file templates also fail.

### `_get_fallback_round_trip_message()` (Lines 533-562)
Returns hardcoded HTML for round trips if file templates fail.

---

## Fallback Chain

When a notification is triggered, the system follows this chain:

```
1. Try Database Template (EmailTemplate model)
   ↓ (if inactive or not found)
2. Try File-Based Template (templates/emails/*.html)
   ↓ (if file missing or rendering error)
3. Use Hardcoded HTML (_get_fallback_message)
```

**This is why you received emails even with all admin templates disabled** - the system fell back to Step 2 (file-based templates).

---

## Current Behavior

| Template Type | Database Status | What Happens |
|--------------|----------------|--------------|
| booking_new | INACTIVE | Uses `booking_notification.html` |
| booking_confirmed | INACTIVE | Uses `booking_notification.html` |
| booking_cancelled | INACTIVE | Uses `booking_notification.html` |
| booking_status_change | INACTIVE | Uses `booking_notification.html` |
| booking_reminder | INACTIVE | Uses `booking_reminder.html` |
| driver_notification | INACTIVE | Uses `driver_notification.html` |
| round_trip_new | INACTIVE | Uses `round_trip_notification.html` |
| round_trip_confirmed | INACTIVE | Uses `round_trip_notification.html` |
| round_trip_cancelled | INACTIVE | Uses `round_trip_notification.html` |
| round_trip_status_change | INACTIVE | Uses `round_trip_notification.html` |
| driver_rejection | INACTIVE | Uses hardcoded HTML (no file template) |
| driver_completion | INACTIVE | Uses hardcoded HTML (no file template) |

---

## What You Requested

You want to **disable file-based templates entirely** so that when admin templates are inactive, **NO emails are sent** (or emails are only sent if admin templates are active).

This requires removing the fallback logic from the 3 methods in `email_service.py`.

---

## Recommendations

### Option 1: Remove File-Based Fallback (Strict Mode)
- Modify `send_booking_notification()`, `send_round_trip_notification()`, and `send_driver_notification()`
- Remove the `if not db_template:` fallback blocks
- Result: **No email sent if database template is inactive**

### Option 2: Log Warning Instead of Sending
- Keep fallback logic but add a check for `is_active=True`
- Log warning: "Template inactive, email not sent"
- Result: **Emails only sent when database templates are active**

### Option 3: Admin Setting to Control Fallback
- Add a SystemSettings option: `allow_file_template_fallback`
- Make fallback conditional on this setting
- Result: **Admin control over fallback behavior**

---

## Files That Need Modification

If you want to remove file-based fallback:

1. **email_service.py** - Remove fallback logic in 3 methods
2. **Optional:** Delete or move the 4 file templates to a backup folder

---

## Impact Assessment

**If file-based fallback is removed:**

✅ **Pros:**
- Complete admin control via Django admin panel
- No surprise emails when templates are disabled
- Forces proper template management
- Clear system behavior

⚠️ **Considerations:**
- If admin template is inactive/missing, NO email will be sent
- Notifications will be silently skipped (or need error handling)
- Could cause missed notifications if templates not properly maintained

---

**Next Step:** Would you like me to remove the file-based fallback logic so that emails are ONLY sent when database templates are active?
