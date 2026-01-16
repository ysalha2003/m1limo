# Reservation Activity Log - Improvement Plan

## Current Issues Identified

### 1. Details Column Problems
- Shows seconds in time fields (19:15:00 instead of 7:15 PM)
- Shows "changed from None to (empty)" messages
- Shows raw database values instead of human-readable values
- No formatting for dates (shows YYYY-MM-DD format)

### 2. Missing Functionality
- No column sorting (Timestamp, Reservation, Action, Changed By)
- No way to quickly find specific changes

### 3. Logging Best Practices Issues
- Times stored with seconds unnecessarily
- Status values show database codes instead of display names
- Boolean values show "True/False" instead of "Yes/No" or "Enabled/Disabled"
- Empty/None values displayed inconsistently

## Proposed Solutions

### 1. Enhanced Value Formatting (Template Filter)
Create a new `format_change_value` filter that:
- Formats dates: `2026-01-15` → `Jan 15, 2026`
- Formats times: `19:15:00` → `7:15 PM` (no seconds)
- Formats booleans: `True` → `Yes`, `False` → `No`
- Formats None/empty: `None` or `""` → `(not set)`
- Formats status: Uses `get_status_display()` for human-readable names
- Preserves other values as-is

### 2. Improved Change Detection
Create `format_change_display` filter that:
- Hides redundant "changed from (not set) to (not set)" entries
- Shows "Set to {value}" when old value was None/empty
- Shows "Removed" when new value is None/empty
- Shows "Changed from {old} to {new}" for normal changes

### 3. Sortable Columns
Add JavaScript-based sorting:
- Click column headers to sort ascending/descending
- Visual indicator (arrows) for sort direction
- Maintains filter parameters during sort
- Works with pagination (sorts current page)

### 4. Better Logging Practices in views.py

#### When creating BookingHistory entries:
```python
# BEFORE (Current):
changes = {
    'pick_up_time': {
        'old': '19:15:00',  # Raw database value
        'new': '16:15:00'
    }
}

# AFTER (Improved):
changes = {
    'pick_up_time': {
        'old': booking_old.pick_up_time.strftime('%I:%M %p') if booking_old.pick_up_time else None,
        'new': booking.pick_up_time.strftime('%I:%M %p') if booking.pick_up_time else None
    }
}
```

#### Format values before storing:
- **Dates**: Use `strftime('%b %d, %Y')` → "Jan 15, 2026"
- **Times**: Use `strftime('%I:%M %p')` → "7:15 PM"
- **Status**: Use `get_status_display()` → "Confirmed" not "confirmed"
- **Booleans**: Convert to "Yes"/"No" or "Enabled"/"Disabled"
- **None**: Store as `None` (filter will handle display)

### 5. Standardized Helper Function

Create a utility function in models.py or utils.py:

```python
def format_field_for_history(field_name, field_value, booking_instance=None):
    """
    Format field values for clean display in activity logs.
    
    Args:
        field_name: Name of the field (e.g., 'pick_up_time')
        field_value: Raw value from database
        booking_instance: Optional booking instance for related lookups
    
    Returns:
        Formatted string suitable for history display
    """
    from datetime import datetime, date, time
    
    # Handle None/empty
    if field_value is None or field_value == '':
        return None
    
    # Handle datetimes
    if isinstance(field_value, datetime):
        return field_value.strftime('%b %d, %Y at %I:%M %p')
    
    # Handle dates
    if isinstance(field_value, date):
        return field_value.strftime('%b %d, %Y')
    
    # Handle times - remove seconds
    if isinstance(field_value, time):
        return field_value.strftime('%I:%M %p')
    
    # Handle booleans
    if isinstance(field_value, bool):
        if field_name in ['share_driver_info', 'is_active']:
            return 'Enabled' if field_value else 'Disabled'
        return 'Yes' if field_value else 'No'
    
    # Handle status field
    if field_name == 'status' and booking_instance:
        return booking_instance.get_status_display()
    
    # Handle choice fields with get_FOO_display()
    if booking_instance and hasattr(booking_instance, f'get_{field_name}_display'):
        return getattr(booking_instance, f'get_{field_name}_display')()
    
    # Return as-is for strings, numbers, etc.
    return str(field_value)
```

### 6. Column Sorting Implementation

Add to booking_activity.html:
```html
<th class="sortable" data-sort="timestamp">
    Timestamp
    <span class="sort-icon">⇅</span>
</th>
```

JavaScript for client-side sorting:
```javascript
<script>
document.querySelectorAll('.sortable').forEach(header => {
    header.addEventListener('click', function() {
        const sortField = this.dataset.sort;
        const currentOrder = this.classList.contains('sort-asc') ? 'desc' : 'asc';
        
        // Update URL with sort parameter
        const url = new URL(window.location);
        url.searchParams.set('sort', sortField);
        url.searchParams.set('order', currentOrder);
        window.location = url.toString();
    });
});
</script>
```

Update view to handle sorting:
```python
# In booking_activity view
sort_field = request.GET.get('sort', 'changed_at')
sort_order = request.GET.get('order', 'desc')

sort_mapping = {
    'timestamp': 'changed_at',
    'reservation': 'booking__id',
    'action': 'action',
    'changed_by': 'changed_by__username'
}

actual_field = sort_mapping.get(sort_field, 'changed_at')
if sort_order == 'desc':
    actual_field = f'-{actual_field}'

history_qs = history_qs.order_by(actual_field)
```

## Implementation Priority

1. **HIGH PRIORITY** - Value formatting filters (immediate visual improvement)
2. **HIGH PRIORITY** - Update logging to use formatted values
3. **MEDIUM PRIORITY** - Column sorting functionality
4. **LOW PRIORITY** - Additional UI enhancements (search, export)

## Example Before/After

### BEFORE:
```
Pick-up Time changed from 19:15:00 to 16:15:00
Additional Recipients changed from None to (empty)
Status changed from pending to confirmed
Share Driver Info changed from False to True
```

### AFTER:
```
Pick-up Time changed from 7:15 PM to 4:15 PM
Additional Recipients removed
Status changed from Pending to Confirmed
Driver Info Sharing enabled
```

## Files to Modify

1. **templatetags/booking_filters.py** - Add formatting filters
2. **models.py or utils.py** - Add `format_field_for_history()` helper
3. **views.py** - Update all `BookingHistory.objects.create()` calls
4. **templates/bookings/booking_activity.html** - Add sorting and use new filters
5. **views.py (booking_activity function)** - Add sorting logic
