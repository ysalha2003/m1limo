# Test Data Script Update - Use 'co' User

**Date:** January 15, 2026  
**Change:** Modified reset_and_generate_test_data.py to assign all bookings to user 'co'

---

## What Changed

Modified `reset_and_generate_test_data.py` to use the existing 'co' user for all test bookings instead of creating random test users.

### Before
- Created users: `testuser`, `testuser2`, `testuser3`, `testuser4`
- Randomly assigned bookings to different test users
- Used emails: `yaser.salha.se+1@gmail.com` through `yaser.salha.se+4@gmail.com`

### After
- Uses existing 'co' user for ALL bookings
- All test reservations belong to the 'co' user
- Passenger emails still use: `yaser.salha.se+1@gmail.com` through `yaser.salha.se+20@gmail.com`
- Exits with error if 'co' user doesn't exist

---

## VPS Deployment

### Step 1: Upload Updated Script
```bash
# From local machine
scp c:\m1\m1limo\reset_and_generate_test_data.py root@62.169.19.39:/opt/m1limo/
```

### Step 2: Verify 'co' User Exists
```bash
# SSH to VPS
ssh root@62.169.19.39
cd /opt/m1limo
source venv/bin/activate

# Check if 'co' user exists
python check_co_user.py
```

**Expected Output:**
```
✓ User 'co' found!
  Username: co
  Email: co@example.com
```

### Step 3: Generate Test Data
```bash
# Generate 30 test bookings (all assigned to 'co' user)
python reset_and_generate_test_data.py 30

# Restart service
sudo systemctl restart m1limo
```

### Step 4: Verify
```bash
# Check that all bookings belong to 'co'
python manage.py shell

# In Django shell:
from models import Booking
from django.contrib.auth.models import User

co_user = User.objects.get(username='co')
booking_count = Booking.objects.filter(user=co_user).count()
total_bookings = Booking.objects.count()

print(f"Total bookings: {total_bookings}")
print(f"Bookings for 'co': {booking_count}")
print(f"All bookings belong to 'co': {booking_count == total_bookings}")
```

**Expected Output:**
```
Total bookings: 30
Bookings for 'co': 30
All bookings belong to 'co': True
```

---

## Code Changes

### Function: `create_test_users()` (Lines 172-182)

**Before:**
```python
def create_test_users():
    """Create or get test users"""
    users = []
    
    # Main test user
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={...}
    )
    # ... creates 4 test users
    return users
```

**After:**
```python
def create_test_users():
    """Get the existing 'co' user for all bookings"""
    try:
        user = User.objects.get(username='co')
        print(f"✓ Using existing user: {user.username} ({user.email})")
        return [user]  # Return as list for compatibility
    except User.DoesNotExist:
        print("❌ ERROR: User 'co' not found in database")
        print("   Please create the 'co' user first or modify the script.")
        sys.exit(1)
```

### Function: `generate_test_data()` (Lines 388-402)

**Before:**
```python
# Create users
users = create_test_users()
base_date = datetime.now().date() + timedelta(days=1)

# ... setup counters ...

for i in range(num_bookings):
    user = random.choice(users)  # Random user selection
    trip_type = random.choice(TRIP_TYPES)
```

**After:**
```python
# Get the 'co' user for all bookings
users = create_test_users()
user = users[0]  # Use the 'co' user for all bookings
base_date = datetime.now().date() + timedelta(days=1)

# ... setup counters ...

for i in range(num_bookings):
    trip_type = random.choice(TRIP_TYPES)  # No random user selection
```

---

## Testing

Created helper script: `check_co_user.py` to verify 'co' user exists before running the data generation script.

---

## Benefits

1. **Centralized Data:** All test bookings under one user account
2. **Easy Testing:** Login as 'co' to see all test data
3. **Simpler Management:** No need to track multiple test users
4. **Production-Like:** Mimics real-world scenario where users have multiple bookings

---

## Rollback

If you need to revert to the old behavior (multiple test users):

```bash
# Get the old version from git
cd /opt/m1limo
git checkout HEAD~1 reset_and_generate_test_data.py
```

Or manually edit the script to use `random.choice(users)` again.

---

## Notes

- Passenger names and contact info are still randomized
- Passenger emails still use test email addresses (yaser.salha.se+1@gmail.com, etc.)
- Only the booking **owner** (user field) is set to 'co'
- All other booking generation logic remains unchanged
