"""
Quick Reference: VPS Deployment Commands
=========================================

Copy and paste these commands directly into your VPS terminal.
"""

# =============================================================================
# OPTION 1: Upload and Run Script (From Windows Local Machine)
# =============================================================================

# Step 1: Upload script to VPS (run from Windows PowerShell/CMD)
scp c:\m1\m1limo\reset_and_generate_test_data.py root@62.169.19.39:/opt/m1limo/

# Step 2: Connect to VPS
ssh root@62.169.19.39

# Step 3: Run commands on VPS
cd /opt/m1limo
source venv/bin/activate
python reset_and_generate_test_data.py 30
python show_summary.py
sudo systemctl restart m1limo


# =============================================================================
# OPTION 2: All Commands in One Block (Run on VPS after connecting)
# =============================================================================

# Connect to VPS first: ssh root@62.169.19.39
# Then paste this entire block:

cd /opt/m1limo && \
source venv/bin/activate && \
python reset_and_generate_test_data.py 30 && \
python show_summary.py && \
sudo systemctl restart m1limo && \
echo "✅ Test data generation complete!"


# =============================================================================
# OPTION 3: Manual Step-by-Step (Most Control)
# =============================================================================

# 1. Connect
ssh root@62.169.19.39

# 2. Navigate
cd /opt/m1limo

# 3. Activate environment
source venv/bin/activate

# 4. (Optional) Check current data
python show_summary.py

# 5. Run generation script (30 bookings)
python reset_and_generate_test_data.py 30

# 6. Verify new data
python show_summary.py

# 7. Check specific features
python manage.py shell
from models import Booking
print(f"Total: {Booking.objects.count()}")
print(f"With notifications enabled: {Booking.objects.filter(send_passenger_notifications=True).count()}")
print(f"With additional recipients: {Booking.objects.exclude(additional_recipients=None).exclude(additional_recipients='').count()}")
exit()

# 8. Restart application
sudo systemctl restart m1limo

# 9. Check status
sudo systemctl status m1limo

# 10. View logs (Ctrl+C to exit)
sudo journalctl -u m1limo -f

# 11. Disconnect
exit


# =============================================================================
# Quick Verification Commands
# =============================================================================

# Check booking counts
python -c "import os, django; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings'); django.setup(); from models import Booking; print(f'Total: {Booking.objects.count()}, Confirmed: {Booking.objects.filter(status=\"Confirmed\").count()}, Pending: {Booking.objects.filter(status=\"Pending\").count()}')"

# Check notification features
python -c "import os, django; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings'); django.setup(); from models import Booking; print(f'Notifications enabled: {Booking.objects.filter(send_passenger_notifications=True).count()}, With additional recipients: {Booking.objects.exclude(additional_recipients=None).exclude(additional_recipients=\"\").count()}')"


# =============================================================================
# Troubleshooting Commands
# =============================================================================

# If application won't start
sudo systemctl stop m1limo
sudo systemctl start m1limo
sudo systemctl status m1limo

# Check logs for errors
sudo journalctl -u m1limo -n 50 --no-pager

# Test Django shell
python manage.py shell

# Run migrations if needed
python manage.py migrate

# Collect static files if needed
python manage.py collectstatic --noinput


# =============================================================================
# Test Email Addresses Used
# =============================================================================

# The script uses these test emails (all go to yaser.salha.se@gmail.com):
# yaser.salha.se+1@gmail.com
# yaser.salha.se+2@gmail.com
# yaser.salha.se+3@gmail.com
# ... through ...
# yaser.salha.se+20@gmail.com


# =============================================================================
# Expected Output
# =============================================================================

"""
After running reset_and_generate_test_data.py 30, you should see:

======================================================================
M1 LIMO - TEST DATA RESET & GENERATION
======================================================================

This will DELETE all existing bookings and create 30 new test bookings.
Test emails will use: yaser.salha.se+1@gmail.com through yaser.salha.se+20@gmail.com

Press Ctrl+C to cancel...

Press ENTER to continue or Ctrl+C to cancel: 

⚠️  Deleting 150 existing bookings...
✅ Deleted 150 bookings

✓ Using existing user: testuser (yaser.salha.se+1@gmail.com)

======================================================================
GENERATING 30 TEST BOOKINGS
======================================================================

✓ Point-to-Point #1: John Anderson
  📍 Willis Tower, 233 S Wacker Dr, Chicago, IL 60606... → Navy Pier...
  📅 2026-01-20 @ 14:30:00 | SUV | Confirmed
  📧 Passenger Email: yaser.salha.se+1@gmail.com (notifications: ✅)
  📧 Additional: yaser.salha.se+5@gmail.com, yaser.salha.se+12@gmail.com

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
"""
