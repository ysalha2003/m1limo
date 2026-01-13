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
