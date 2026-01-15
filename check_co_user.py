"""Quick test to check if 'co' user exists"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from django.contrib.auth.models import User

try:
    user = User.objects.get(username='co')
    print(f"✓ User 'co' found!")
    print(f"  Username: {user.username}")
    print(f"  Email: {user.email}")
    print(f"  First Name: {user.first_name}")
    print(f"  Last Name: {user.last_name}")
except User.DoesNotExist:
    print("✗ User 'co' NOT found in database")
    print("\nYou can create it with:")
    print("python manage.py createsuperuser --username co --email co@example.com")
