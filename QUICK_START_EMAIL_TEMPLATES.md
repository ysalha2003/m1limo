# Quick Start Guide: Managing Email Templates

## Accessing Email Templates

1. Log in to Django Admin: http://62.169.19.39:8081/admin
2. Look for "Email Templates" in the sidebar
3. Click to view all templates

## Editing a Template

1. Click on the template name (e.g., "Booking Confirmation Email")
2. Modify the **Subject Template** or **HTML Template**
3. Use `{variable_name}` for dynamic content (see Available Variables below)
4. Click "Save" at the bottom

## Using Variables

Variables are placeholders that get replaced with real data. Use curly braces:

### Example Subject:
```
Trip Confirmed: {passenger_name} - {pick_up_date}
```

### Example HTML:
```html
<p>Dear {passenger_name},</p>
<p>Your trip on {pick_up_date} at {pick_up_time} is confirmed!</p>
<p>Pickup: {pick_up_address}</p>
<p>Destination: {drop_off_address}</p>
```

## Common Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{booking_reference}` | Booking ID | M1-260113-A5 |
| `{passenger_name}` | Passenger name | John Smith |
| `{pick_up_date}` | Pickup date | January 20, 2026 |
| `{pick_up_time}` | Pickup time | 2:00 PM |
| `{pick_up_address}` | Pickup location | 111 S Michigan Ave |
| `{drop_off_address}` | Drop-off location | O'Hare Airport |
| `{vehicle_type}` | Vehicle | Sedan |
| `{status}` | Booking status | Confirmed |
| `{company_name}` | Company name | M1 Limousine Service |
| `{support_email}` | Support email | support@m1limo.com |

**See full list in admin**: Open any template → Expand "Available Variables" section

## Previewing Templates

1. Select a template (checkbox on left)
2. Choose "Preview template with sample data" from Actions dropdown
3. Click "Go"
4. View rendered email with sample data

## Testing Templates

1. Select a template (checkbox on left)
2. Choose "Send test email to yourself" from Actions dropdown
3. Click "Go"
4. Check your email inbox (uses your admin user email)
5. Test emails have [TEST] prefix

## Creating Template Variations

1. Select a template (checkbox on left)
2. Choose "Duplicate selected template" from Actions dropdown
3. Click "Go"
4. Edit the duplicate:
   - Change **Template Type** (required - must be unique)
   - Modify subject and content
   - Save

## Template Status

### Active (✓)
- Template is being used for emails
- Shows in green in list

### Inactive (✗)
- Template exists but not used
- System falls back to file templates
- Good for testing new versions

## Understanding Statistics

Each template shows:
- **Total Sent**: How many emails sent successfully
- **Success Rate**: Percentage successful (color-coded)
  - 🟢 Green: ≥ 95% - Excellent
  - 🟠 Orange: ≥ 80% - Good
  - 🔴 Red: < 80% - Needs attention
- **Last Sent**: When last used

## Tips & Best Practices

### ✅ DO:
- Preview templates before activating
- Test with real email addresses
- Keep subjects under 60 characters for mobile
- Use semantic HTML (p, h1, h2, etc.)
- Check Available Variables for each template type
- Save drafts as inactive until ready

### ❌ DON'T:
- Don't use `{{ variable }}` (Django syntax) - use `{variable}`
- Don't use variables not in the Available Variables list
- Don't forget to activate templates after testing
- Don't delete the original file templates (they're fallbacks)

## HTML Email Basics

### Inline Styles
Email clients don't support CSS files. Use inline styles:
```html
<p style="color: #333; font-size: 16px;">Text here</p>
```

### Colors
- Use hex codes: `#333` for dark gray, `#fff` for white
- Brand colors already in templates

### Layout
```html
<div style="max-width: 600px; margin: 0 auto;">
  <!-- Content here -->
</div>
```

### Buttons
```html
<a href="URL" style="background: #0f172a; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; display: inline-block;">
  Click Here
</a>
```

## Troubleshooting

### Template not showing in emails?
1. Check "Active" is checked
2. Verify template type matches notification type
3. Check statistics - any failures?

### Variables not replaced?
1. Verify variable name exactly matches Available Variables
2. Use `{variable}` not `{{ variable }}`
3. Check for typos in variable names

### Email looks broken?
1. Preview in admin first
2. Test different email clients
3. Use inline styles only
4. Avoid complex CSS

### Changes not appearing?
1. Clear browser cache
2. Check you saved the template
3. Verify template is active
4. Check logs for errors

## Getting Help

- **Documentation**: See EMAIL_TEMPLATE_SYSTEM_SUMMARY.md
- **Available Variables**: In admin, expand "Available Variables" section
- **Test Safely**: Always use Preview and Test actions first
- **Rollback**: Duplicate original before major changes

## Quick Reference: Template Types

| Type | When Sent | Key Variables |
|------|-----------|---------------|
| booking_confirmed | Trip confirmed | booking_reference, passenger_name, pick_up_date |
| booking_cancelled | Trip cancelled | booking_reference, passenger_name |
| booking_status_change | Status changes | old_status, new_status |
| booking_reminder | 2 hours before pickup | pick_up_time, pick_up_address |
| driver_assignment | Driver assigned | driver_name, driver_phone |
| round_trip_confirmed | Round trip confirmed | pick_up_date, return_pick_up_date |

## Example: Customizing Confirmation Email

**Before**:
```
Subject: Trip Confirmed: {passenger_name} - {pick_up_date}
```

**After** (more friendly):
```
Subject: ✓ All set! Your {vehicle_type} is booked for {pick_up_date}
```

**Before**:
```html
<p>Your trip is confirmed.</p>
```

**After** (more details):
```html
<p>Great news, {passenger_name}! Your {vehicle_type} is confirmed.</p>
<p>We'll pick you up on {pick_up_date} at {pick_up_time}.</p>
<p style="color: #666;">Questions? Call us or reply to this email.</p>
```

---

**Remember**: Always Preview → Test → Activate!
