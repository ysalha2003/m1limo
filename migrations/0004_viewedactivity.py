# Generated manually on 2025-12-31

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('bookings', '0003_add_driver_response_tracking'),
    ]

    operations = [
        migrations.CreateModel(
            name='ViewedActivity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('viewed_at', models.DateTimeField(auto_now_add=True, help_text='When this activity was viewed')),
                ('activity', models.ForeignKey(help_text='The activity that was viewed', on_delete=django.db.models.deletion.CASCADE, related_name='viewed_by', to='bookings.bookinghistory')),
                ('user', models.ForeignKey(help_text='Admin user who viewed this activity', on_delete=django.db.models.deletion.CASCADE, related_name='viewed_activities', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Viewed Activity',
                'verbose_name_plural': 'Viewed Activities',
                'ordering': ['-viewed_at'],
            },
        ),
        migrations.AddIndex(
            model_name='viewedactivity',
            index=models.Index(fields=['user', 'activity'], name='bookings_vi_user_id_e60fcb_idx'),
        ),
        migrations.AddIndex(
            model_name='viewedactivity',
            index=models.Index(fields=['viewed_at'], name='bookings_vi_viewed__686797_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='viewedactivity',
            unique_together={('user', 'activity')},
        ),
    ]
