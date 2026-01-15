# Test Data Generation - Commands & Documentation

## Overview
The new `reset_and_generate_test_data.py` script replaces all previous test data generation scripts with a single comprehensive solution that includes all new features:

- ✅ `send_passenger_notifications` field
- ✅ `additional_recipients` field  
- ✅ Round trip bookings with proper linking
- ✅ Multiple statuses and vehicle types
- ✅ Chicago area locations
- ✅ Test emails: `yaser.salha.se+1@gmail.com` through `yaser.salha.se+20@gmail.com`

---

## Features Implemented

### New Booking Fields
1. **send_passenger_notifications** (Boolean)
   - 75% of bookings have this enabled
   - Controls whether passenger receives email notifications

2. **additional_recipients** (TextField)
   - 20-30% of bookings have additional recipients
   - Contains comma-separated email addresses
   - Example: `yaser.salha.se+5@gmail.com, yaser.salha.se+10@gmail.com`

### Booking Distribution
- **Point-to-Point**: ~50% of bookings
- **Round Trips**: ~25% of bookings (creates 2 linked bookings per trip)
- **Hourly**: ~25% of bookings

### Status Distribution
- **Confirmed**: ~75% of bookings
- **Pending**: ~25% of bookings

---

## Local Development Usage

### Basic Usage (20 bookings)
```bash
cd c:\m1\m1limo
python reset_and_generate_test_data.py
```

### Custom Number of Bookings
```bash
python reset_and_generate_test_data.py 50
```

### What It Does
1. Asks for confirmation before proceeding
2. Deletes ALL existing bookings
3. Creates test users (testuser, testuser2, testuser3, testuser4)
4. Generates specified number of bookings with:
   - Random Chicago locations
   - Various trip types
   - Different statuses
   - Email notification settings
   - Additional recipients (some bookings)

---

## VPS Production Usage

### Step 1: Connect to VPS
```bash
ssh root@62.169.19.39
```

### Step 2: Navigate to Project Directory
```bash
cd /opt/m1limo
```

### Step 3: Activate Virtual Environment
```bash
source venv/bin/activate
```

### Step 4: Upload Script (if not already uploaded)
```bash
# From local machine, upload the script:
scp c:\m1\m1limo\reset_and_generate_test_data.py root@62.169.19.39:/opt/m1limo/
```

### Step 5: Run Script
```bash
# Generate 20 test bookings
python reset_and_generate_test_data.py 20

# Or generate 50 test bookings
python reset_and_generate_test_data.py 50
```

### Step 6: Restart Application (if needed)
```bash
sudo systemctl restart m1limo
```

### Step 7: Verify Data
```bash
# Quick check
python show_summary.py

# Or use Django shell
python manage.py shell
>>> from models import Booking
>>> Booking.objects.count()
>>> Booking.objects.filter(send_passenger_notifications=True).count()
>>> Booking.objects.exclude(additional_recipients=None).count()
```

---

## Complete VPS Command Sequence

```bash
# Copy-paste this entire sequence for VPS deployment:

# 1. Connect to VPS
ssh root@62.169.19.39

# 2. Navigate to project
cd /opt/m1limo

# 3. Activate virtual environment
source venv/bin/activate

# 4. Run script (generates 30 test bookings)
python reset_and_generate_test_data.py 30

# 5. Verify results
python show_summary.py

# 6. Check application is running
sudo systemctl status m1limo

# 7. If needed, restart
sudo systemctl restart m1limo

# 8. Exit
exit
```

---

## Test Email Addresses

The script uses the following email pattern for testing:
- `yaser.salha.se+1@gmail.com`
- `yaser.salha.se+2@gmail.com`
- `yaser.salha.se+3@gmail.com`
- ... up to ...
- `yaser.salha.se+20@gmail.com`

**Gmail Plus Addressing:** All emails go to `yaser.salha.se@gmail.com` but can be filtered/tracked individually.

---

## Sample Output

```
======================================================================
M1 LIMO - TEST DATA RESET & GENERATION
======================================================================

This will DELETE all existing bookings and create 30 new test bookings.
Test emails will use: yaser.salha.se+1@gmail.com through yaser.salha.se+20@gmail.com

Press Ctrl+C to cancel...

Press ENTER to continue or Ctrl+C to cancel: 

⚠️  Deleting 45 existing bookings...
✅ Deleted 45 bookings

✓ Using existing user: testuser (yaser.salha.se+1@gmail.com)

======================================================================
GENERATING 30 TEST BOOKINGS
======================================================================

✓ Point-to-Point #501: John Anderson
  📍 Willis Tower, 233 S Wacker Dr, Chicago, IL 60606... → Navy Pier, 600 E Grand Ave, Chicago, IL 60611...
  📅 2026-01-20 @ 14:30:00 | SUV | Confirmed
  📧 Passenger Email: yaser.salha.se+1@gmail.com (notifications: ✅)
  📧 Additional: yaser.salha.se+5@gmail.com, yaser.salha.se+12@gmail.com

✓ Round Trip #502 (Outbound): Sarah Martinez
  📍 O'Hare International Airport (ORD), Chicago, IL 606... → Palmer House Hilton, 17 E Monroe St, Chicag...
  📅 2026-01-25 @ 10:00:00
✓ Round Trip #503 (Return): Sarah Martinez
  📍 Palmer House Hilton, 17 E Monroe St, Chicag... → O'Hare International Airport (ORD), Chicago, IL 606...
  📅 2026-01-28 @ 15:30:00
  📧 Passenger Email: yaser.salha.se+2@gmail.com (notifications: ✅)

[... more bookings ...]

======================================================================
✅ TEST DATA GENERATION COMPLETE
======================================================================
Total bookings created: 42
  Point-to-Point: 15
  Round Trips: 8 pairs (16 bookings)
  Hourly: 11

Database Statistics:
  Total in DB: 42
  Confirmed: 32
  Pending: 10
  With Additional Recipients: 13
  Passenger Notifications Enabled: 31
======================================================================

✨ Ready to test! Visit http://localhost:8000/dashboard
```

---

## Verification Checklist

After running the script, verify:

### ✅ Basic Data
- [ ] Bookings exist in dashboard
- [ ] Multiple trip types (Point, Round, Hourly)
- [ ] Various statuses (Confirmed, Pending)
- [ ] Chicago area locations are realistic

### ✅ New Features
- [ ] Some bookings have `send_passenger_notifications=False`
- [ ] Some bookings have `additional_recipients` populated
- [ ] Round trips are properly linked (check booking detail page)
- [ ] Email notifications section shows correct status

### ✅ Email Notifications
- [ ] Can toggle passenger notifications in Edit mode
- [ ] Additional recipients field shows emails (not "None")
- [ ] Send button works and sends to correct recipients
- [ ] Status-based notifications work (Pending→new, Confirmed→confirmed, etc.)

---

## Troubleshooting

### Issue: Script fails with "No module named 'models'"
**Solution:**
```bash
# Ensure you're in the correct directory
cd /opt/m1limo

# Ensure virtual environment is activated
source venv/bin/activate
```

### Issue: Permission denied
**Solution:**
```bash
# Make script executable
chmod +x reset_and_generate_test_data.py
```

### Issue: Database locked
**Solution:**
```bash
# Stop the application first
sudo systemctl stop m1limo

# Run the script
python reset_and_generate_test_data.py 20

# Start the application
sudo systemctl start m1limo
```

### Issue: Bookings created but not showing in dashboard
**Solution:**
```bash
# Clear cache and restart
sudo systemctl restart m1limo

# Check logs
sudo journalctl -u m1limo -f
```

---

## Legacy Scripts (Deprecated)

The following scripts are now **replaced** by `reset_and_generate_test_data.py`:

- ❌ `create_round_trips.py` - Round trip creation now integrated
- ❌ `multiply_bookings.py` - Multiplication logic now built-in
- ❌ `create_initial_bookings.py` - Initialization now comprehensive

**Note:** You can delete these old scripts or keep them for reference.

---

## Next Steps

1. Run script on local development to verify
2. Review generated data in dashboard
3. Test email notification features
4. Deploy to VPS with commands above
5. Verify all features work on production

---

## Support

If you encounter issues:
1. Check Django logs: `sudo journalctl -u m1limo -f`
2. Verify database: `python manage.py dbshell`
3. Check script output for specific error messages
4. Ensure all migrations are applied: `python manage.py migrate`
