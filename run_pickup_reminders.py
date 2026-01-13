#!/usr/bin/env python
"""
Wrapper script to run send_pickup_reminders command.
Works around flat Django project structure limitations.
"""
import os
import sys
import django

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

# Import and run the command directly
from management.commands.send_pickup_reminders import Command

if __name__ == '__main__':
    command = Command()
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--hours', type=float, default=24)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    
    # Run command
    command.handle(hours=args.hours, dry_run=args.dry_run)
