# Generated manually for driver response tracking

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0002_add_notification_preferences_and_index'),
    ]

    operations = [
        migrations.AddField(
            model_name='booking',
            name='driver_response_status',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('pending', 'Pending Response'),
                    ('accepted', 'Accepted'),
                    ('rejected', 'Rejected'),
                    ('completed', 'Trip Completed'),
                ],
                default='pending',
                help_text="Driver's response to the trip assignment"
            ),
        ),
        migrations.AddField(
            model_name='booking',
            name='driver_rejection_reason',
            field=models.TextField(
                blank=True,
                null=True,
                help_text="Reason provided by driver for rejecting the trip"
            ),
        ),
        migrations.AddField(
            model_name='booking',
            name='driver_response_at',
            field=models.DateTimeField(
                null=True,
                blank=True,
                help_text="When the driver responded to the assignment"
            ),
        ),
        migrations.AddField(
            model_name='booking',
            name='driver_completed_at',
            field=models.DateTimeField(
                null=True,
                blank=True,
                help_text="When the driver marked the trip as completed"
            ),
        ),
    ]
