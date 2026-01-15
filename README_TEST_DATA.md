# M1 Limo Test Data Generation

## Quick Start

### Local Development
```bash
python reset_and_generate_test_data.py 30
```

### VPS Production
```bash
# Upload script
scp c:\m1\m1limo\reset_and_generate_test_data.py root@62.169.19.39:/opt/m1limo/

# Run on VPS
ssh root@62.169.19.39
cd /opt/m1limo && source venv/bin/activate
python reset_and_generate_test_data.py 30
sudo systemctl restart m1limo
```

## What This Script Does

1. **Deletes** all existing bookings (asks for confirmation)
2. **Creates** test users with emails: `yaser.salha.se+1@gmail.com` through `+20`
3. **Generates** bookings with:
   - ✅ Point-to-Point trips (~50%)
   - ✅ Round trips with proper linking (~25%)
   - ✅ Hourly bookings (~25%)
   - ✅ `send_passenger_notifications` field (75% enabled)
   - ✅ `additional_recipients` field (20-30% populated)
   - ✅ Chicago area locations
   - ✅ Multiple statuses (Confirmed, Pending)
   - ✅ Various vehicle types (Sedan, SUV, Sprinter Van)

## Test Email Addresses

All test emails use Gmail's plus addressing:
- `yaser.salha.se+1@gmail.com`
- `yaser.salha.se+2@gmail.com`
- ...
- `yaser.salha.se+20@gmail.com`

All emails go to `yaser.salha.se@gmail.com` but can be filtered individually.

## Features to Test

### Email Notifications
1. Go to Reservation Details page
2. Click **Edit** in Email Notifications section
3. Toggle "Send booking notifications to passenger"
4. Add additional recipients (comma-separated)
5. Click **Save**
6. Click **Send** button to resend notification

### Notification Behavior
- **Send button** now sends notification based on current booking status:
  - Pending → sends 'new' notification
  - Confirmed → sends 'confirmed' notification
  - Cancelled → sends 'cancelled' notification
  - Trip Completed → sends 'status_change' notification

### Additional Recipients
- Field now shows empty instead of "None"
- Can add multiple emails separated by commas
- All recipients receive notifications

## Files Included

1. **reset_and_generate_test_data.py** - Main script
2. **TEST_DATA_COMMANDS.md** - Complete documentation
3. **VPS_COMMANDS_QUICK_REF.py** - Quick reference commands
4. **README_TEST_DATA.md** - This file

## Verification

After running the script, check:
```bash
python show_summary.py
```

Or in Django shell:
```python
from models import Booking
print(f"Total: {Booking.objects.count()}")
print(f"Notifications enabled: {Booking.objects.filter(send_passenger_notifications=True).count()}")
print(f"With additional recipients: {Booking.objects.exclude(additional_recipients=None).exclude(additional_recipients='').count()}")
```

## Troubleshooting

**Issue**: Script fails with import error  
**Solution**: Ensure you're in `/opt/m1limo` and virtual environment is activated

**Issue**: Database locked  
**Solution**: Stop application first: `sudo systemctl stop m1limo`

**Issue**: Changes not visible in dashboard  
**Solution**: Restart application: `sudo systemctl restart m1limo`

## Support

For detailed instructions, see:
- **TEST_DATA_COMMANDS.md** - Complete guide
- **VPS_COMMANDS_QUICK_REF.py** - Copy-paste commands
