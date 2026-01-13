# Generated migration for EmailTemplate model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0004_viewedactivity'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='EmailTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('template_type', models.CharField(choices=[
                    ('booking_new', 'Booking - New Request'),
                    ('booking_confirmed', 'Booking - Confirmed'),
                    ('booking_cancelled', 'Booking - Cancelled'),
                    ('booking_status_change', 'Booking - Status Changed'),
                    ('booking_reminder', 'Booking - Pickup Reminder'),
                    ('driver_assignment', 'Driver - Trip Assignment'),
                    ('round_trip_new', 'Round Trip - New Request'),
                    ('round_trip_confirmed', 'Round Trip - Confirmed'),
                    ('round_trip_cancelled', 'Round Trip - Cancelled'),
                    ('round_trip_status_change', 'Round Trip - Status Changed'),
                ], max_length=50, unique=True, verbose_name='Template Type')),
                ('name', models.CharField(help_text='Friendly name for this template', max_length=200, verbose_name='Template Name')),
                ('description', models.TextField(blank=True, help_text='What this template is used for', verbose_name='Description')),
                ('subject_template', models.CharField(help_text='Email subject line. Use {variable_name} for dynamic content', max_length=200, verbose_name='Subject Template')),
                ('html_template', models.TextField(help_text='HTML email body. Use {variable_name} for dynamic content', verbose_name='HTML Template')),
                ('is_active', models.BooleanField(default=True, help_text='Only active templates will be used', verbose_name='Active')),
                ('send_to_user', models.BooleanField(default=True, help_text='Send to the booking user/customer', verbose_name='Send to User')),
                ('send_to_admin', models.BooleanField(default=True, help_text='Send to admin/notification recipients', verbose_name='Send to Admin')),
                ('send_to_passenger', models.BooleanField(default=False, help_text='Send to passenger if different from user', verbose_name='Send to Passenger')),
                ('total_sent', models.PositiveIntegerField(default=0, help_text='Total number of emails sent using this template', verbose_name='Total Sent')),
                ('total_failed', models.PositiveIntegerField(default=0, help_text='Total number of failed email attempts', verbose_name='Total Failed')),
                ('last_sent_at', models.DateTimeField(blank=True, help_text='Last time this template was used', null=True, verbose_name='Last Sent')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_email_templates', to=settings.AUTH_USER_MODEL, verbose_name='Created By')),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_email_templates', to=settings.AUTH_USER_MODEL, verbose_name='Updated By')),
            ],
            options={
                'verbose_name': 'Email Template',
                'verbose_name_plural': 'Email Templates',
                'db_table': 'bookings_emailtemplate',
                'ordering': ['template_type'],
            },
        ),
        migrations.AddIndex(
            model_name='emailtemplate',
            index=models.Index(fields=['template_type', 'is_active'], name='bookings_em_templat_2780bb_idx'),
        ),
    ]
