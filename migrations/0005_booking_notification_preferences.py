# Generated migration for notification preferences
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0004_viewedactivity'),
    ]

    operations = [
        migrations.AddField(
            model_name='booking',
            name='send_passenger_notifications',
            field=models.BooleanField(
                default=True,
                help_text='Send booking confirmations and updates to passenger email'
            ),
        ),
        migrations.AddField(
            model_name='booking',
            name='additional_recipients',
            field=models.TextField(
                blank=True,
                null=True,
                help_text='Additional email addresses (comma-separated) to receive notifications'
            ),
        ),
    ]
