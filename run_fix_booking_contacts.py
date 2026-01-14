#!/usr/bin/env python
"""
Wrapper script to run fix_booking_contacts management command.
Handles Django setup for flat project structure.
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

# Import the command
from management.commands.fix_booking_contacts import Command

if __name__ == '__main__':
    # Parse command line arguments
    dry_run = '--dry-run' in sys.argv
    
    # Execute the command
    command = Command()
    command.handle(dry_run=dry_run)
