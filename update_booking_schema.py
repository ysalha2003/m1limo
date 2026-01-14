#!/usr/bin/env python
"""
Script to update database schema for required phone_number and passenger_email fields.
This updates existing NULL values and changes the schema to NOT NULL.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from django.db import connection

def update_schema():
    """Update database schema to make phone_number and passenger_email required"""
    
    with connection.cursor() as cursor:
        # Check for NULL values first
        cursor.execute("SELECT COUNT(*) FROM bookings_booking WHERE phone_number IS NULL")
        null_phones = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM bookings_booking WHERE passenger_email IS NULL")
        null_emails = cursor.fetchone()[0]
        
        print(f"Found {null_phones} bookings with NULL phone_number")
        print(f"Found {null_emails} bookings with NULL passenger_email")
        
        # Update NULL values with defaults
        if null_phones > 0:
            cursor.execute("UPDATE bookings_booking SET phone_number = 'N/A' WHERE phone_number IS NULL")
            print(f"Updated {null_phones} bookings with default phone number 'N/A'")
        
        if null_emails > 0:
            cursor.execute("UPDATE bookings_booking SET passenger_email = 'noreply@m1limo.com' WHERE passenger_email IS NULL")
            print(f"Updated {null_emails} bookings with default email 'noreply@m1limo.com'")
        
        # For SQLite, we need to recreate the table to change NOT NULL constraint
        # This is SQLite-specific behavior
        print("\nUpdating schema to make fields NOT NULL...")
        
        # Create a temporary table with the new schema
        cursor.execute("""
            CREATE TABLE bookings_booking_new AS 
            SELECT * FROM bookings_booking
        """)
        
        # Drop old table
        cursor.execute("DROP TABLE bookings_booking")
        
        # Recreate with NOT NULL constraints
        cursor.execute("""
            CREATE TABLE bookings_booking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                booking_reference VARCHAR(20) UNIQUE,
                passenger_name VARCHAR(255) NOT NULL,
                phone_number VARCHAR(20) NOT NULL,
                passenger_email VARCHAR(254) NOT NULL,
                pick_up_address VARCHAR(255) NOT NULL,
                drop_off_address VARCHAR(255),
                pick_up_date DATE NOT NULL,
                pick_up_time TIME NOT NULL,
                return_date DATE,
                return_time TIME,
                return_pickup_address VARCHAR(255),
                trip_type VARCHAR(10) NOT NULL,
                hours_booked INTEGER,
                vehicle_type VARCHAR(50),
                number_of_passengers INTEGER NOT NULL,
                flight_number VARCHAR(20),
                notes TEXT,
                status VARCHAR(20) NOT NULL,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                driver_id INTEGER REFERENCES bookings_driver(id),
                user_id INTEGER NOT NULL REFERENCES auth_user(id),
                linked_booking_id INTEGER REFERENCES bookings_booking(id),
                booking_for_user_id INTEGER REFERENCES bookings_customer(id)
            )
        """)
        
        # Copy data back
        cursor.execute("""
            INSERT INTO bookings_booking 
            SELECT * FROM bookings_booking_new
        """)
        
        # Drop temporary table
        cursor.execute("DROP TABLE bookings_booking_new")
        
        print("Schema updated successfully!")
        print("\nNOTE: This is a simplified schema update.")
        print("Some indexes and constraints may need to be recreated.")

if __name__ == '__main__':
    update_schema()
