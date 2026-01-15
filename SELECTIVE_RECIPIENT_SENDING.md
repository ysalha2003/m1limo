# Selective Recipient Sending - Feature Documentation

## Overview
The Selective Recipient Sending feature allows administrators to choose specific recipients when manually sending booking notifications. This provides flexibility to override default notification behavior based on user preferences.

## Feature Details

### User Interface (Admin View)
When viewing a booking detail page as admin, the "Send Email Notification" section in Quick Actions displays:

1. **Recipient Selection Checkboxes:**
   - **Admin**: Always checked (required recipient)
   - **User**: Pre-checked if user has notifications enabled for this type
   - **Passenger**: Pre-checked if booking has passenger notifications enabled

2. **Visual Indicators:**
   - Enabled recipients: Checkbox is active and can be toggled
   - Disabled recipients: Checkbox is grayed out and disabled, with note "notifications disabled"
   - Each checkbox shows the recipient's email address

3. **Smart Defaults:**
   - Checkboxes are pre-selected based on current preferences
   - Admin can override by unchecking enabled recipients
   - Disabled checkboxes indicate the recipient has turned off notifications

### Backend Logic

#### Views (views.py)
**resend_notification view (lines 871-910):**
- Checks admin permission
- Reads checkbox values from POST data: `send_to_admin`, `send_to_user`, `send_to_passenger`
- Passes selected recipients to NotificationService as array: `['admin', 'user', 'passenger']`
- Builds success message listing who received the notification

#### NotificationService (notification_service.py)
**send_notification method:**
- New parameter: `selected_recipients` (optional list)
- If provided, uses `_get_selected_recipients()` instead of `get_recipients()`
- Logs admin selection for audit trail

**_get_selected_recipients method:**
- Takes booking, notification_type, and selected_recipients array
- Builds recipient list based only on selection (ignores preferences)
- Prevents duplicates (e.g., when passenger email == user email)
- Returns list of email addresses to send to

### User Preference Logic vs Admin Override

#### Default Behavior (without selection)
When admin doesn't select specific recipients, system uses **preference-based logic**:

1. **User notifications controlled by UserProfile:**
   - `receive_booking_confirmations`: For 'confirmed' notifications
   - `receive_status_updates`: For 'cancelled', 'status_change'
   - `receive_pickup_reminders`: For 'reminder'

2. **Passenger notifications controlled by booking:**
   - `send_passenger_notifications`: Boolean flag per booking
   - Only sent if passenger email exists

3. **Admin always receives all notification types**

#### Admin Override (with selection)
When admin selects specific recipients:

1. **Ignores user preferences**: Sends even if user disabled notifications
2. **Ignores booking settings**: Sends to passenger even if flag is False
3. **Provides full control**: Admin decides based on current situation

### Use Cases

#### Emergency Notifications
User disabled status updates, but trip is cancelled due to emergency:
- Admin can check "User" box to send notification anyway
- Override respects urgent need to communicate

#### Selective Communication
Only passenger needs pickup reminder, not admin:
- Admin unchecks "Admin" box
- Only passenger receives the reminder

#### Testing and Verification
Admin wants to test notification delivery:
- Can send to just one recipient at a time
- Verify each email address individually

#### Privacy-Conscious Updates
Sensitive status change that shouldn't go to passenger:
- Admin unchecks "Passenger" box
- Only user and admin receive notification

## Implementation Files

### Modified Files
1. **booking_detail.html** (lines 617-650)
   - Added recipient selection checkboxes
   - Conditional styling for disabled recipients
   - Form submits selections to resend_notification URL

2. **views.py** (lines 871-910)
   - Enhanced resend_notification view
   - Reads POST checkbox values
   - Passes selections to NotificationService
   - Builds detailed success message

3. **notification_service.py**
   - Updated send_notification signature (added selected_recipients parameter)
   - Added _get_selected_recipients helper method
   - Logs admin overrides for audit trail

### Template Structure
```html
<form method="post" action="{% url 'resend_notification' booking.id %}">
    {% csrf_token %}
    
    <!-- Recipient Selection -->
    <div>
        <p>Select Recipients:</p>
        
        <!-- Admin (always checked) -->
        <label>
            <input type="checkbox" name="send_to_admin" value="1" checked>
            Admin
        </label>
        
        <!-- User (conditional) -->
        <label style="{% if not will_notify_user %}opacity: 0.6;{% endif %}">
            <input type="checkbox" name="send_to_user" value="1" 
                   {% if will_notify_user %}checked{% endif %}
                   {% if not will_notify_user %}disabled{% endif %}>
            User ({{ booking.user.email }})
            {% if not will_notify_user %} - notifications disabled{% endif %}
        </label>
        
        <!-- Passenger (conditional) -->
        <label style="{% if not will_notify_passenger %}opacity: 0.6;{% endif %}">
            <input type="checkbox" name="send_to_passenger" value="1"
                   {% if will_notify_passenger %}checked{% endif %}
                   {% if not will_notify_passenger %}disabled{% endif %}>
            Passenger ({{ booking.passenger_email }})
            {% if not will_notify_passenger %} - notifications disabled{% endif %}
        </label>
    </div>
    
    <button type="submit">Send Email Notification</button>
</form>
```

### Backend Flow
```python
# 1. View receives POST
if request.POST.get('send_to_admin'):
    selected_recipients.append('admin')
if request.POST.get('send_to_user'):
    selected_recipients.append('user')
if request.POST.get('send_to_passenger'):
    selected_recipients.append('passenger')

# 2. Pass to service
NotificationService.send_notification(
    booking,
    notification_type,
    selected_recipients=selected_recipients
)

# 3. Service resolves recipients
if selected_recipients:
    # Admin override - ignore preferences
    recipients = _get_selected_recipients(booking, type, selected_recipients)
else:
    # Default - respect preferences
    recipients = get_recipients(booking, type)
```

## Testing

### Test Script
Run `test_selective_sending.py` to verify:
- All recipient combinations (admin, user, passenger)
- Empty selection handling
- Duplicate prevention
- Default vs selective comparison

### Test Results
All 8 tests pass successfully:
1. ✓ Send to all three recipients
2. ✓ Send to admin only
3. ✓ Send to user only
4. ✓ Send to passenger only
5. ✓ Send to user + passenger (exclude admin)
6. ✓ No recipients selected
7. ✓ Compare selective vs default
8. ✓ Duplicate prevention

## Benefits

1. **Flexibility**: Admin can handle edge cases requiring notification overrides
2. **Transparency**: Clear indication of who will receive vs who can receive
3. **Control**: Fine-grained selection for targeted communication
4. **Smart Defaults**: Pre-selected based on preferences, reducing clicks
5. **Safety**: Disabled recipients clearly marked to prevent confusion
6. **Audit Trail**: All selections logged for compliance

## Future Enhancements

Potential improvements:
- Add "Additional Recipients" checkbox for custom emails
- Include delivery status (sent, failed) in success message
- Add preview button to see notification content before sending
- Support bulk selection/deselection toggle
- Add reason field for admin overrides (audit documentation)

## Related Features

- **User Notification Preferences**: Controls default behavior (edit_profile.html)
- **Booking Passenger Notifications**: Per-booking flag for passenger emails
- **Quick Actions**: Admin section for manual operations
- **Notification History**: Tracks all sent notifications

## Version History

- **v1.0** (Current): Initial implementation with checkbox selection
  - Admin, User, Passenger selection
  - Smart defaults based on preferences
  - Disabled state for recipients with notifications off
