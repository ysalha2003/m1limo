#!/usr/bin/env python
"""Convert email templates from Python format strings to Django template syntax"""

import os
import django
import re

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from models import EmailTemplate

def convert_format_strings_to_django(text):
    """Convert {variable} to {{ variable }} for Django templates"""
    # Replace {variable} with {{ variable }}
    # But don't touch {% %} or {{ }} that are already there
    def replace_single_braces(match):
        var_name = match.group(1)
        return f'{{{{ {var_name} }}}}'
    
    # Match {word} but not {% or {{
    pattern = r'(?<!\{)\{([a-zA-Z_][a-zA-Z0-9_]*)\}(?!\})'
    result = re.sub(pattern, replace_single_braces, text)
    return result

print("=" * 60)
print("Converting Email Templates to Django Template Syntax")
print("=" * 60)
print()

templates = EmailTemplate.objects.all()
total_count = templates.count()
updated_count = 0

for template in templates:
    print(f"📧 {template.name} ({template.template_type})")
    
    # Convert subject
    old_subject = template.subject_template
    new_subject = convert_format_strings_to_django(old_subject)
    
    if old_subject != new_subject:
        print(f"   Subject changed:")
        print(f"   OLD: {old_subject}")
        print(f"   NEW: {new_subject}")
        template.subject_template = new_subject
        template.save(update_fields=['subject_template'])
        updated_count += 1
    else:
        print(f"   Subject: No changes needed")
    
    print()

print("=" * 60)
print(f"✅ Conversion complete!")
print(f"   Total templates: {total_count}")
print(f"   Updated: {updated_count}")
print(f"   No changes: {total_count - updated_count}")
print("=" * 60)
