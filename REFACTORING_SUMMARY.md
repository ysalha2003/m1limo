# Booking Form Refactoring: Require Both Phone and Email

## Summary
Refactored the booking form from a hybrid "phone OR email" single field (`passenger_contact`) to require BOTH phone number AND email as separate mandatory fields.

## Changes Made

### 1. Database Model ([models.py](models.py))
**Lines 260-261:**
- Made `phone_number` field required (removed `blank=True, null=True`)
- Made `passenger_email` field required (removed `blank=True, null=True`)
- Both fields now have `null=False, blank=False` explicitly set

**Line 522:**
- Removed validation logic that checked for "at least one contact method"
- Fields are now enforced at the field level

### 2. Booking Form ([booking_forms.py](booking_forms.py))
**Removed:**
- `passenger_contact` CharField (hybrid field)
- `clean_passenger_contact()` method
- Hybrid field routing logic in `clean()` method
- Passenger contact pre-population logic in `__init__`

**Added:**
- `phone_number` CharField with tel input type, required=True, max_length=20
- `passenger_email` EmailField with email input type, required=True
- `clean_phone_number()` method with regex validation: `r'^\+?\d{10,15}$'`

**Updated:**
- Simplified `clean()` method (removed routing logic)
- Updated Meta.fields to include both fields directly

### 3. New Booking Template ([templates/bookings/new_booking.html](templates/bookings/new_booking.html))
**Lines 640-650:** Form fields
- Replaced single `passenger_contact` field with two separate fields:
  - `phone_number` with label "Passenger Phone Number *"
  - `passenger_email` with label "Passenger Email *"

**Lines 1357-1378:** JavaScript instant validation
- Removed `contactField` blur validation
- Added `phoneField` validation with regex: `/^\+?\d{10,15}$/`
- Added `emailField` validation with regex: `/^[^\s@]+@[^\s@]+\.[^\s@]+$/`

**Lines 1495-1513:** Frequent passenger auto-fill
- Changed from single `contactField.value` to separate:
  - `phoneField.value = phone`
  - `emailField.value = email`

**Lines 1671-1677:** updateReviewData() function
- Changed `id_passenger_contact` → `id_phone_number`
- Added `review_email` population from `id_passenger_email`

**Lines 985-1025:** Review section HTML
- Added "Email" row in view mode with `id="review_email"`
- Edit mode now has separate inputs:
  - `edit_phone_number` for phone
  - `edit_passenger_email` for email

**Lines 1876-1886:** toggleEditMode() function
- Changed `edit_passenger_contact` → `edit_phone_number` and `edit_passenger_email`
- Both fields now populated separately when entering edit mode

### 4. Update Booking Template ([templates/bookings/update_booking.html](templates/bookings/update_booking.html))
**Lines 78-100:**
- Replaced single `passenger_contact` field with two separate fields:
  - `phone_number` field with label, errors, and help text
  - `passenger_email` field with label, errors, and help text

### 5. Views ([views.py](views.py))
**Lines 433-437:** new_booking view
- Updated comment: "phone_number and passenger_email are now required fields in the form"
- Existing code works correctly (checks for both in cleaned_data)

**Lines 502-509:** Frequent passenger pre-population
- Changed from single `passenger_contact` to:
  - `phone_number`: passenger.phone_number
  - `passenger_email`: passenger.email

**Lines 680-684:** edit_booking view
- Updated comment (same as new_booking)

**Lines 791-794:** create_round_trip view
- Removed `passenger_contact` from excluded fields list
- Updated comment

**Lines 867-870:** Round trip initial data
- Changed from single `passenger_contact` to both:
  - `phone_number`: original_booking.phone_number
  - `passenger_email`: original_booking.passenger_email

### 6. Data Migration
**Fixed Existing Records:**
- Created `run_fix_booking_contacts.py` wrapper script
- Created `management/commands/fix_booking_contacts.py` command
- Updated 7 bookings with NULL phone_number → 'N/A'
- Updated 17 bookings with NULL passenger_email → 'noreply@m1limo.com'
- Verified: 0 bookings now have NULL values

**Note:** Database schema still allows NULL at the database level because migrations were never properly applied. However, Django model validation now enforces both fields as required, and existing NULL values have been fixed.

### 7. Database Migration File
**Created:** `migrations/0006_require_phone_and_email.py`
- Sets default values for existing NULL records
- Alters fields to NOT NULL
- **Note:** This migration is not yet applied due to migration system issues

## Testing

### Form Validation Tests
Created `test_booking_form.py` to verify:
1. ✅ Form **requires phone_number** field
2. ✅ Form **requires passenger_email** field
3. ✅ Phone format validation works (10-15 digits)
4. ✅ Email format validation works (Django EmailField)

### Results
All validations working correctly:
- Missing phone → "This field is required"
- Missing email → "This field is required"
- Invalid phone → "Please enter a valid phone number with 10-15 digits"
- Invalid email → Django's built-in email validation

## Files Created
1. `migrations/0006_require_phone_and_email.py` - Database migration (not applied)
2. `management/commands/fix_booking_contacts.py` - Command to fix NULL values
3. `run_fix_booking_contacts.py` - Wrapper script for fix command
4. `update_booking_schema.py` - (Not used, too risky for production)
5. `test_booking_form.py` - Form validation tests

## Deployment Checklist
- [x] Update models.py (both fields required)
- [x] Update booking_forms.py (separate fields with validation)
- [x] Update new_booking.html (form fields, JavaScript, review section)
- [x] Update update_booking.html (form fields)
- [x] Update views.py (remove passenger_contact references)
- [x] Fix existing NULL values in database
- [x] Test form validation
- [ ] **Deploy to server:**
  ```bash
  cd /opt/m1limo
  git pull origin main
  source venv/bin/activate
  python run_fix_booking_contacts.py  # If needed on server
  sudo systemctl restart m1limo nginx
  ```
- [ ] **Test on server:**
  - Create new booking with both fields
  - Edit existing booking
  - Create round trip
  - Check email templates receive both variables

## Notes
- Email templates already use `{{ phone_number }}` and `{{ passenger_email }}` separately, so no changes needed
- Other display templates (booking_detail.html, dashboard.html) already show both fields
- Admin interface already has both fields configured
- Form now has 3 fields in step 1 instead of 2 (name, phone, email)
- Frequent passenger data already stores phone and email separately

## Compatibility
- **Backwards Compatible:** Old bookings with only one contact method now have defaults ('N/A' or 'noreply@m1limo.com')
- **Forward Compatible:** New bookings will always have both phone and email
- **Email Templates:** Already compatible (use both variables)
- **Display Templates:** Already compatible (show both fields)
