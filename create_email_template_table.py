"""
Script to create EmailTemplate table manually
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from django.db import connection
from models import EmailTemplate

# Create the table using schema editor
with connection.schema_editor() as schema_editor:
    schema_editor.create_model(EmailTemplate)

print("✓ EmailTemplate table created successfully")

# Create the index
from django.db.models import Index
index = Index(fields=['template_type', 'is_active'], name='bookings_em_templat_2780bb_idx')
with connection.schema_editor() as schema_editor:
    schema_editor.add_index(EmailTemplate, index)

print("✓ EmailTemplate index created successfully")
