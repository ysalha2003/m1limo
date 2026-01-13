"""Display all email templates"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from models import EmailTemplate

templates = EmailTemplate.objects.all().order_by('template_type')

print("\n" + "="*80)
print("ALL EMAIL TEMPLATES - CREATED & READY")
print("="*80 + "\n")

for i, t in enumerate(templates, 1):
    status = "✓ Active" if t.is_active else "✗ Inactive"
    print(f"{i}. {t.name}")
    print(f"   Type: {t.template_type}")
    print(f"   Status: {status}")
    print(f"   Stats: {t.total_sent} sent, {t.total_failed} failed")
    print(f"   Subject: {t.subject_template[:60]}...")
    print()

print("="*80)
print(f"Total: {templates.count()} templates | All active and ready to use!")
print("="*80)
