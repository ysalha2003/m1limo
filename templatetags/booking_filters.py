from django import template
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
