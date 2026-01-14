import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from django.urls import reverse

print("✓ Testing URL reversals after booking→reservation refactor:\n")

url_tests = [
    ('new_reservation', None),
    ('reservation_detail', [1]),
    ('reservation_confirmation', [1]),
    ('update_reservation', [1]),
    ('cancel_reservation', [1]),
    ('reservation_actions', [1, 'complete']),
    ('past_confirmed_reservations', None),
    ('past_pending_reservations', None),
    ('reservation_activity', None),
    ('confirm_reservation_action', [1, 'complete']),
]

passed = 0
failed = 0

for url_name, args in url_tests:
    try:
        if args:
            url = reverse(url_name, args=args)
        else:
            url = reverse(url_name)
        print(f"  ✓ {url_name:35} -> {url}")
        passed += 1
    except Exception as e:
        print(f"  ✗ {url_name:35} -> ERROR: {e}")
        failed += 1

print(f"\n{'='*60}")
print(f"Results: {passed} passed, {failed} failed")
if failed == 0:
    print("✓ All URL patterns working correctly!")
else:
    print(f"✗ {failed} URL pattern(s) need attention")
