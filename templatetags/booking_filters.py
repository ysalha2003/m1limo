from django import template
from django.utils import timezone
from datetime import datetime, timedelta
from models import BookingStop

register = template.Library()


@register.filter
def get_stops(booking):
    """Get outbound stops for a booking"""
    return BookingStop.objects.filter(
        booking=booking,
        is_return_stop=False
    ).order_by('stop_number')


@register.filter
def get_return_stops(booking):
    """Get return stops for a booking"""
    return BookingStop.objects.filter(
        booking=booking,
        is_return_stop=True
    ).order_by('stop_number')


@register.filter
def has_stops(booking):
    """Check if booking has outbound stops"""
    return BookingStop.objects.filter(
        booking=booking,
        is_return_stop=False
    ).exists()


@register.filter
def has_return_stops(booking):
    """Check if booking has return stops"""
    return BookingStop.objects.filter(
        booking=booking,
        is_return_stop=True
    ).exists()


@register.filter(name='replace')
def replace(value, arg):
    """
    Replace substring in string
    Usage: {{ value|replace:"old,new" }}
    """
    if not isinstance(value, str):
        return value

    if ',' not in arg:
        return value

    old, new = arg.split(',', 1)
    return value.replace(old, new)


@register.filter
def clean_special_requests(value):
    """
    Clean special requests field for backward compatibility
    Handles both notes and return_special_requests fields
    """
    if not value:
        return ''
    return str(value).strip()


@register.filter
def format_field_name(field_name):
    """
    Convert field_name to human-readable format (e.g., pick_up_time → Pick-up Time)
    """
    from models import BookingHistory
    return BookingHistory.format_field_name(field_name)


@register.filter
def get_field_change(history, field_name):
    """
    Get the old and new values for a specific field from history
    Usage: {% with change=history|get_field_change:field %}
    """
    return history.get_field_change(field_name)


@register.filter
def get_changed_fields(history):
    """
    Get list of changed fields from history
    Usage: {% for field in history.get_changed_fields %}
    """
    return history.get_changed_fields()


@register.filter
def format_change_value(value, field_name=''):
    """
    Format change values for clean display in activity logs.
    Handles dates, times, booleans, None values, etc.
    
    Usage: {{ value|format_change_value:field_name }}
    """
    from datetime import datetime, date, time
    
    # Handle None/empty - return special marker
    if value is None or value == '' or value == 'None':
        return None  # Will be displayed as "(not set)" in template
    
    # Handle datetime objects
    if isinstance(value, datetime):
        return value.strftime('%b %d, %Y at %I:%M %p')
    
    # Handle date objects
    if isinstance(value, date):
        return value.strftime('%b %d, %Y')
    
    # Handle time objects or time strings with seconds
    if isinstance(value, time):
        return value.strftime('%I:%M %p').lstrip('0')  # Remove leading zero
    
    # Handle time strings like "19:15:00"
    if isinstance(value, str) and ':' in value:
        try:
            # Try to parse as time
            parts = value.split(':')
            if len(parts) >= 2:
                hour = int(parts[0])
                minute = int(parts[1])
                # Convert to 12-hour format
                period = 'AM' if hour < 12 else 'PM'
                if hour == 0:
                    hour = 12
                elif hour > 12:
                    hour -= 12
                return f"{hour}:{minute:02d} {period}"
        except (ValueError, IndexError):
            pass  # Not a time string, continue
    
    # Handle booleans
    if isinstance(value, bool):
        # Context-aware boolean formatting
        if field_name in ['share_driver_info', 'is_active', 'driver_paid']:
            return 'Enabled' if value else 'Disabled'
        return 'Yes' if value else 'No'
    
    # Handle "True"/"False" strings
    if value == 'True':
        if field_name in ['share_driver_info', 'is_active', 'driver_paid']:
            return 'Enabled'
        return 'Yes'
    if value == 'False':
        if field_name in ['share_driver_info', 'is_active', 'driver_paid']:
            return 'Disabled'
        return 'No'
    
    # Return as-is for everything else
    return str(value)


@register.filter
def format_change_display(change_data, field_name):
    """
    Format the entire change display (old → new) with smart messaging.
    
    Usage: {{ change_data|format_change_display:field_name }}
    Returns: dict with 'old', 'new', 'type' keys
    """
    if not change_data:
        return None
    
    old_value = change_data.get('old')
    new_value = change_data.get('new')
    
    # Format both values
    old_formatted = format_change_value(old_value, field_name)
    new_formatted = format_change_value(new_value, field_name)
    
    # Determine change type for smarter display
    if old_formatted is None and new_formatted is None:
        return None  # No meaningful change
    elif old_formatted is None:
        return {
            'type': 'added',
            'old': None,
            'new': new_formatted,
            'message': f"Set to {new_formatted}"
        }
    elif new_formatted is None:
        return {
            'type': 'removed',
            'old': old_formatted,
            'new': None,
            'message': f"Removed (was {old_formatted})"
        }
    else:
        return {
            'type': 'changed',
            'old': old_formatted,
            'new': new_formatted,
            'message': None
        }


@register.filter
def format_action_name(action):
    """
    Format action names for display
    """
    action_map = {
        'created': 'Created',
        'updated': 'Updated',
        'status_changed': 'Status Changed',
        'cancelled': 'Cancelled',
        'driver_assigned': 'Driver Assigned',
        'driver_reassigned': 'Driver Reassigned',
        'driver_rejected': 'Driver Rejected',
        'driver_completed': 'Trip Completed',
    }
    return action_map.get(action, action.replace('_', ' ').title())


@register.filter
def hours_until_pickup(booking):
    """
    Calculate hours remaining until pickup time
    Returns rounded hours, or None if pickup time has passed
    """
    if not booking or not booking.pick_up_date or not booking.pick_up_time:
        return None
    
    try:
        # Combine date and time into a datetime object
        pickup_datetime = datetime.combine(booking.pick_up_date, booking.pick_up_time)
        
        # Make it timezone aware if needed
        if timezone.is_naive(pickup_datetime):
            pickup_datetime = timezone.make_aware(pickup_datetime)
        
        # Get current time
        now = timezone.now()
        
        # Calculate difference
        time_diff = pickup_datetime - now
        
        # Only return positive hours (future pickups)
        if time_diff.total_seconds() > 0:
            hours = round(time_diff.total_seconds() / 3600)
            return hours
        
        return None
    except Exception:
        return None


@register.filter
def format_action_name(value):
    """
    Format action names to be human-readable
    Converts 'Driver_Assigned' to 'Driver Assigned'
    """
    if not value:
        return value
    return value.replace('_', ' ').title()

@register.filter
def format_time_until_pickup(booking):
    """
    Format time until pickup as weeks, days, hours
    Returns dict with weeks, days, hours, and total_hours
    """
    if not booking or not booking.pick_up_date or not booking.pick_up_time:
        return None
    
    try:
        # Combine date and time into a datetime object
        pickup_datetime = datetime.combine(booking.pick_up_date, booking.pick_up_time)
        
        # Make it timezone aware if needed
        if timezone.is_naive(pickup_datetime):
            pickup_datetime = timezone.make_aware(pickup_datetime)
        
        # Get current time
        now = timezone.now()
        
        # Calculate difference
        time_diff = pickup_datetime - now
        
        # Only return positive values (future pickups)
        if time_diff.total_seconds() > 0:
            total_hours = int(time_diff.total_seconds() / 3600)
            
            weeks = total_hours // 168  # 168 hours in a week
            remaining_hours = total_hours % 168
            days = remaining_hours // 24
            hours = remaining_hours % 24
            
            return {
                'weeks': weeks,
                'days': days,
                'hours': hours,
                'total_hours': total_hours
            }
        
        return None
    except Exception:
        return None
