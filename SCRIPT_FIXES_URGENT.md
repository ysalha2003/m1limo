# URGENT: Script Fixes Applied

## Issues Fixed

### 1. Vehicle Capacity Mismatch
**Problem**: Script used incorrect capacity limits
- ❌ Old: Sedan=3, Sprinter Van=14
- ✅ Fixed: Sedan=2, Sprinter Van=12

### 2. Hours Field Name Error
**Problem**: Script used `hours` but model uses `hours_booked`
- ❌ Old: `hours=hours`
- ✅ Fixed: `hours_booked=hours_boked`

## VPS Update Commands

### Quick Update (Copy-Paste)
```bash
# Upload fixed script
scp c:\m1\m1limo\reset_and_generate_test_data.py root@62.169.19.39:/opt/m1limo/

# Run on VPS
ssh root@62.169.19.39
cd /opt/m1limo && source venv/bin/activate
python reset_and_generate_test_data.py 30
```

## Expected Results

After fix, you should see:
- ✅ **0 errors** (was getting 11 errors before)
- ✅ **30 bookings created** (was only 24)
- ✅ Hourly bookings working
- ✅ All sedan bookings with ≤2 passengers

## What Changed

### Vehicle Capacity (Line 110)
```python
# Before
VEHICLE_CAPACITY = {'Sedan': 3, 'SUV': 6, 'Sprinter Van': 14}

# After
VEHICLE_CAPACITY = {'Sedan': 2, 'SUV': 6, 'Sprinter Van': 12}
```

### Hourly Booking Field (Line 279)
```python
# Before
hours=hours,

# After
hours_booked=hours_booked,
```

### Print Statement (Line 434)
```python
# Before
print(f"  📍 ... ({booking.hours} hours)")

# After  
print(f"  📍 ... ({booking.hours_booked} hours)")
```

## Re-Run Instructions

1. **Upload the fixed script** (from Windows):
   ```bash
   scp c:\m1\m1limo\reset_and_generate_test_data.py root@62.169.19.39:/opt/m1limo/
   ```

2. **Run on VPS**:
   ```bash
   ssh root@62.169.19.39
   cd /opt/m1limo
   source venv/bin/activate
   python reset_and_generate_test_data.py 30
   sudo systemctl restart m1limo
   ```

3. **Verify Results**:
   ```bash
   python show_summary.py
   ```

## Success Indicators

After running the fixed script:
- Total bookings: ~30 (depending on randomization)
- Point-to-Point: ~50%
- Round Trips: ~25% 
- Hourly: ~25%
- No error messages
- All bookings valid

## Test Immediately

The script is now ready for re-deployment. Upload and run to generate clean test data without errors.
