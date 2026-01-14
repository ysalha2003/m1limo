# Generated migration to make phone_number and passenger_email required

from django.db import migrations, models


def set_default_values(apps, schema_editor):
    """Set default values for existing NULL records before making fields required"""
    Booking = apps.get_model('bookings', 'Booking')
    # Set default phone number for records with NULL phone_number
    Booking.objects.filter(phone_number__isnull=True).update(phone_number='N/A')
    # Set default email for records with NULL passenger_email
    Booking.objects.filter(passenger_email__isnull=True).update(passenger_email='noreply@m1limo.com')


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0005_emailtemplate'),
    ]

    operations = [
        # First, set default values for existing NULL records
        migrations.RunPython(set_default_values, reverse_code=migrations.RunPython.noop),
        
        # Then alter the fields to be NOT NULL
        migrations.AlterField(
            model_name='booking',
            name='phone_number',
            field=models.CharField(blank=False, help_text='Passenger phone number for contact', max_length=20, null=False),
        ),
        migrations.AlterField(
            model_name='booking',
            name='passenger_email',
            field=models.EmailField(blank=False, help_text='Passenger email for communication and notifications', max_length=254, null=False),
        ),
    ]
