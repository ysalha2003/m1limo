#!/bin/bash
# VPS Update Script - Use 'co' user for test data
# Run this on VPS after uploading the updated reset_and_generate_test_data.py

echo "==========================================="
echo "Updating Test Data Script - Use 'co' User"
echo "==========================================="
echo ""

# Check if 'co' user exists
echo "1. Checking if 'co' user exists..."
python manage.py shell -c "from django.contrib.auth.models import User; u=User.objects.filter(username='co').first(); print(f'✓ User co exists: {u.username} ({u.email})' if u else '❌ User co NOT FOUND')"

echo ""
echo "2. Generating 30 test bookings for user 'co'..."
python reset_and_generate_test_data.py 30

echo ""
echo "3. Restarting service..."
sudo systemctl restart m1limo

echo ""
echo "==========================================="
echo "✓ Update Complete!"
echo "==========================================="
echo ""
echo "All 30 bookings now belong to user 'co'"
echo "Login at: http://62.169.19.39:8081/login"
echo ""
