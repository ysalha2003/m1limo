# bookings/signals.py
import logging
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from models import Booking, UserProfile, BookingPermission

User = get_user_model()
logger = logging.getLogger('bookings')


@receiver(pre_save, sender=Booking)
def booking_pre_save(sender, instance, **kwargs):
    """Capture previous status before save for change detection."""
    if instance.pk:
        try:
            previous = Booking.objects.get(pk=instance.pk)
            instance._previous_status = previous.status

            if previous.status != instance.status:
                logger.info(
                    f"Pre-save: Booking {instance.pk} status changing "
                    f"from {previous.status} to {instance.status}"
                )
        except Booking.DoesNotExist:
            instance._previous_status = None
            logger.warning(f"Pre-save: Booking {instance.pk} not found")
    else:
        instance._previous_status = None
        logger.info("Pre-save: New booking being created")


@receiver(post_save, sender=Booking)
def booking_post_save(sender, instance, created, **kwargs):
    """
    Log booking changes and invalidate cache.
    Notifications handled by BookingService to prevent duplicates and ensure proper context.
    """
    from django.core.cache import cache
    cache.delete('dashboard_stats')

    if hasattr(instance, '_skip_signal_notification') and instance._skip_signal_notification:
        logger.debug(f"Signal: Skipping notification for booking {instance.id} - handled by service")
        return

    if created:
        logger.info(f"Signal: New booking {instance.id} created with status {instance.status}")

    elif hasattr(instance, '_previous_status') and instance._previous_status != instance.status:
        logger.info(
            f"Signal: Status changed from {instance._previous_status} "
            f"to {instance.status} for booking {instance.id}"
        )


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Auto-create UserProfile and BookingPermission when a new User is created.
    This ensures all users have notification preferences and booking permissions.
    """
    if created:
        UserProfile.objects.get_or_create(user=instance)
        BookingPermission.objects.get_or_create(user=instance)
        logger.info(f"Signal: Created UserProfile and BookingPermission for new user {instance.username}")
