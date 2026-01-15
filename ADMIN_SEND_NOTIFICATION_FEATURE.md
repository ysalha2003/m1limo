# Admin Quick Action: Send Email Notification

## Overview
Added a "Send Email Notification" button to the Quick Actions section in the admin view of reservation details. This allows admins to manually trigger email notifications based on the current booking status.

## Implementation Details

### File Modified
- `templates/bookings/booking_detail.html` (lines 612-622)

### Button Location
- **Section**: Quick Actions (admin-only)
- **Position**: After "Edit Reservation" button
- **Visibility**: Admin users only (`{% if is_admin %}`)

### Functionality
- **Action**: Sends email notification for the current booking status
- **Method**: POST form submission to `/reservation/<booking_id>/resend-notification/`
- **View**: Uses existing `resend_notification` view in `views.py`
- **Recipients**: Sends to both user and passenger (if `send_passenger_notifications` is enabled)

### Status to Notification Mapping
The system automatically determines which notification type to send based on current status:

| Booking Status | Notification Type | Description |
|----------------|-------------------|-------------|
| Pending | `new` | New booking notification |
| Confirmed | `confirmed` | Booking confirmed |
| Cancelled | `cancelled` | Cancellation notification |
| Cancelled_Full_Charge | `cancelled` | Cancellation notification |
| Customer_No_Show | `cancelled` | Cancellation notification |
| Trip_Not_Covered | `cancelled` | Cancellation notification |
| Trip_Completed | `status_change` | Status update notification |

## Use Cases
1. **Initial notification not received**: User reports they didn't receive the booking confirmation
2. **Email address corrected**: After updating passenger email, resend the notification
3. **Status manually updated**: After manually changing booking status, trigger appropriate notification
4. **General communication**: Remind customer of their confirmed booking before pickup

## Button Design
```html
<form method="post" action="{% url 'resend_notification' booking.id %}" style="margin: 0;">
    {% csrf_token %}
    <button type="submit" class="btn btn-secondary" style="width: 100%; justify-content: center; display: flex; align-items: center; gap: 6px;">
        <svg style="width: 16px; height: 16px; flex-shrink: 0;" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path>
        </svg>
        <span>Send Email Notification</span>
    </button>
</form>
```

## Testing
✅ Tested with different booking statuses (Confirmed, Cancelled)
✅ Verified email delivery to both user and passenger
✅ Confirmed notification type mapping works correctly
✅ Verified notification history is recorded in database

## Success Messages
After sending, admin sees:
> "Notification for '[Status]' status resent successfully to all recipients."

Examples:
- "Notification for 'Confirmed' status resent successfully to all recipients."
- "Notification for 'Cancelled' status resent successfully to all recipients."

## Permissions
- **Admin only**: Button only visible when `is_admin` is True
- **Owner or Admin**: The `resend_notification` view checks `can_user_edit_booking()` permission
- **Error handling**: Displays error message if user lacks permission

## Notes
- This uses the existing `resend_notification` view, no new backend code required
- The button respects the `send_passenger_notifications` setting per booking
- Notification history is automatically logged in the `NotificationLog` model
- The notification appears in the "Recent Notifications" section below Quick Actions
