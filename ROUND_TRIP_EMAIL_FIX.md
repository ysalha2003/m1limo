# Round Trip Email Template Fix

## Problem

Round trip email templates were showing raw variable placeholders like `{passenger_name}` instead of actual values, and the "View Full Details" button was not clickable.

**Root Cause:** Context mismatch between database templates and the context being passed to them.

## Issues Identified

### Issue 1: Variable Rendering
- **Symptom**: Email showed `{passenger_name}`, `{old_status}`, etc. instead of actual values
- **Cause**: Database templates use Django template syntax (`{{ variable }}`) but were receiving string context from `_build_round_trip_template_context()`
- **Example**: Template expects `{{ first_trip.pick_up_date }}` but received `{'pick_up_date': 'May 15, 2024'}`

### Issue 2: Non-Clickable Button  
- **Symptom**: "View Full Details" button had no href link (defaulted to `#`)
- **Cause**: `company_info.dashboard_url` was not included in the context
- **Template line 377**: `<a href="{{ company_info.dashboard_url|default:'#' }}" class="btn">View Dashboard</a>`

## Solutions Implemented

### Fix 1: Unified Context for All Templates

**Location:** `email_service.py`, lines 274-295

**What Changed:**
- Added `dashboard_url` to `company_info` dictionary
- Added flat variables (`booking_id`, `passenger_name`, etc.) to context for backwards compatibility
- Both file templates and database templates now receive the same context with:
  - Booking objects (`first_trip`, `return_trip`) for Django syntax
  - Flat variables for simple template variables

**Before:**
```python
context = {
    'first_trip': first_trip,
    'return_trip': return_trip,
    'company_info': settings.COMPANY_INFO,  # No dashboard_url
}
# Then called _build_round_trip_template_context() for database templates
```

**After:**
```python
company_info = settings.COMPANY_INFO.copy()
company_info['dashboard_url'] = f"{settings.BASE_URL}/dashboard"

context = {
    'first_trip': first_trip,
    'return_trip': return_trip,
    'company_info': company_info,
    # Flat variables for compatibility
    'booking_id': first_trip.id,
    'booking_reference': first_trip.booking_reference,
    'passenger_name': first_trip.passenger_name,
    'pick_up_date': first_trip.pick_up_date.strftime('%B %d, %Y'),
    # ... etc
}
```

### Fix 2: Use Object Context for Database Templates

**Location:** `email_service.py`, lines 299-306

**What Changed:**
- Database templates now receive the same booking object context as file templates
- Removed call to `_build_round_trip_template_context()` which created string-only context

**Before:**
```python
template_context = cls._build_round_trip_template_context(first_trip, return_trip, notification_type)
subject = db_template.render_subject(template_context)
html_message = db_template.render_html(template_context)
```

**After:**
```python
# Use the same context as file templates (booking objects, not strings)
subject = db_template.render_subject(context)
html_message = db_template.render_html(context)
```

## Database Template Structure

The system has 4 active database templates for round trips:
- `round_trip_new`: New Round Trip Alert (Admin)
- `round_trip_confirmed`: Round Trip Confirmation
- `round_trip_cancelled`: Round Trip Cancellation  
- `round_trip_status_change`: Round Trip Status Update

**Template Syntax:** All database templates use Django template syntax with:
- Conditionals: `{% if notification_type == 'new' %}`
- Object access: `{{ first_trip.pick_up_date|date:"M j, Y" }}`
- Filters: `{{ company_info.dashboard_url|default:'#' }}`

## Testing Recommendations

### Test Case 1: Round Trip Confirmation Email
1. Create a round trip booking (outbound + return)
2. Confirm both trips
3. Check email for:
   - ✅ Passenger name displays correctly (not `{passenger_name}`)
   - ✅ Dates display correctly (not `{pick_up_date}`)
   - ✅ "View Dashboard" button is clickable with correct URL

### Test Case 2: Round Trip Status Change
1. Update a round trip booking status
2. Check email for:
   - ✅ Old and new status display correctly
   - ✅ Status transition displays as "Pending -> Confirmed" (not `{old_status} -> {new_status}`)

### Test Case 3: Dashboard Link
1. Click "View Dashboard" button in any round trip email
2. Should navigate to: `http://62.169.19.39:8081/dashboard`
3. Should not navigate to `#` (broken link)

## Backwards Compatibility

The context now includes:
1. **Booking objects** for Django template syntax:
   - `{{ first_trip.pick_up_date }}` ✅
   - `{{ return_trip.pick_up_time }}` ✅
   - `{{ first_trip.passenger_name }}` ✅

2. **Flat variables** for simple syntax:
   - `{{ booking_id }}` ✅
   - `{{ passenger_name }}` ✅
   - `{{ pick_up_date }}` ✅ (pre-formatted string)

This ensures both old and new template formats work correctly.

## Related Files

- `email_service.py` - Email sending logic (lines 246-335)
- `models.py` - EmailTemplate model with Django template rendering (lines 1115-1315)
- `templates/emails/round_trip_notification.html` - File-based fallback template
- Database: `EmailTemplate` records for round trip notifications

## Notes

- The `_build_round_trip_template_context()` function is now unused for database templates but kept for potential future use
- File templates use `render_to_string()` which automatically handles Django template syntax
- Database templates use `Template().render(Context())` which also supports Django syntax
- Both approaches now receive the same context dictionary

## Production Impact

- ✅ **No breaking changes** - backwards compatible with existing templates
- ✅ **No database migration required** - only code changes
- ✅ **Immediate effect** - applies to all new emails sent after deployment
- ✅ **Fallback intact** - file templates still work if database template fails
