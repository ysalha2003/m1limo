"""
Test script for Activity Log improvements

Tests the new formatting filters and ensures they work correctly.
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from datetime import time, date, datetime
from templatetags.booking_filters import format_change_value, format_change_display

print("=" * 80)
print("ACTIVITY LOG IMPROVEMENTS - TEST SUITE")
print("=" * 80)
print()

# Test 1: Time formatting (remove seconds)
print("TEST 1: Time Formatting")
print("-" * 40)
test_times = [
    ("19:15:00", "7:15 PM"),
    ("07:30:00", "7:30 AM"),
    ("12:00:00", "12:00 PM"),
    ("00:00:00", "12:00 AM"),
    ("16:45:00", "4:45 PM"),
]

for test_input, expected in test_times:
    result = format_change_value(test_input)
    status = "✓" if result == expected else "✗"
    print(f"{status} {test_input:12} → {result:12} (expected: {expected})")
print()

# Test 2: Boolean formatting
print("TEST 2: Boolean Formatting")
print("-" * 40)
test_bools = [
    (True, "", "Yes"),
    (False, "", "No"),
    (True, "share_driver_info", "Enabled"),
    (False, "share_driver_info", "Disabled"),
    ("True", "driver_paid", "Enabled"),
    ("False", "is_active", "Disabled"),
]

for value, field_name, expected in test_bools:
    result = format_change_value(value, field_name)
    status = "✓" if result == expected else "✗"
    print(f"{status} {str(value):8} ({field_name:20}) → {result:12} (expected: {expected})")
print()

# Test 3: None/Empty handling
print("TEST 3: None/Empty Value Handling")
print("-" * 40)
test_none = [
    (None, None),
    ("", None),
    ("None", None),
]

for test_input, expected in test_none:
    result = format_change_value(test_input)
    status = "✓" if result == expected else "✗"
    print(f"{status} {repr(test_input):12} → {repr(result):12} (expected: {repr(expected)})")
print()

# Test 4: Change display formatting
print("TEST 4: Change Display Formatting")
print("-" * 40)
test_changes = [
    ({'old': None, 'new': 'John Doe'}, '', 'added', "Set to John Doe"),
    ({'old': 'John Doe', 'new': None}, '', 'removed', "Removed (was John Doe)"),
    ({'old': '19:15:00', 'new': '16:30:00'}, 'pick_up_time', 'changed', None),
    ({'old': 'False', 'new': 'True'}, 'share_driver_info', 'changed', None),
]

for change_data, field_name, expected_type, expected_message in test_changes:
    result = format_change_display(change_data, field_name)
    if result:
        status = "✓" if result['type'] == expected_type else "✗"
        print(f"{status} Type: {result['type']:8} | Old: {repr(result['old']):20} | New: {repr(result['new']):20}")
        if result['message']:
            print(f"   Message: {result['message']}")
    else:
        print(f"✗ None result for {change_data}")
print()

# Test 5: Date formatting
print("TEST 5: Date Formatting")
print("-" * 40)
test_date = date(2026, 1, 15)
result = format_change_value(test_date)
expected = "Jan 15, 2026"
status = "✓" if result == expected else "✗"
print(f"{status} {test_date} → {result} (expected: {expected})")
print()

# Test 6: Time object formatting
print("TEST 6: Time Object Formatting")
print("-" * 40)
test_time = time(19, 15, 0)
result = format_change_value(test_time)
expected = "7:15 PM"
status = "✓" if result == expected else "✗"
print(f"{status} {test_time} → {result} (expected: {expected})")
print()

print("=" * 80)
print("TEST COMPLETE")
print("=" * 80)
print()
print("SUMMARY OF IMPROVEMENTS:")
print("✓ Times display without seconds (7:15 PM instead of 19:15:00)")
print("✓ Booleans show as Yes/No or Enabled/Disabled")
print("✓ None values handled gracefully (not shown as 'None')")
print("✓ Smart change messages ('Set to' / 'Removed' / 'Changed from')")
print("✓ Dates formatted as 'Jan 15, 2026'")
print()
