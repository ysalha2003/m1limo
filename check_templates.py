"""
Check available email templates.
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from models import EmailTemplate

print("\nAvailable Email Templates:")
print("=" * 100)

templates = EmailTemplate.objects.all().order_by('template_type')

for template in templates:
    status = "✅ ACTIVE" if template.is_active else "❌ INACTIVE"
    print(f"{status:12} | Type: {template.template_type:20} | Name: {template.name}")

print("=" * 100)
print(f"Total templates: {templates.count()}")
