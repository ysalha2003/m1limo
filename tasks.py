"""
Background tasks for asynchronous operations.

This module contains all background tasks that should run asynchronously
to avoid blocking HTTP requests.
"""

import logging
from background_task import background
from django.core.exceptions import ObjectDoesNotExist

logger = logging.getLogger(__name__)


@background(schedule=0)  # Run immediately
def send_booking_notification_async(booking_id, notification_type, old_status=None):
    """
    Send booking notification asynchronously.

    Args:
        booking_id: ID of the booking
        notification_type: Type of notification ('new', 'confirmed', 'cancelled', etc.)
        old_status: Previous status (for status change notifications)
    """
    try:
        from models import Booking
        from notification_service import NotificationService

        logger.info(f"[ASYNC] Starting notification task for booking {booking_id}, type: {notification_type}")

        booking = Booking.objects.get(id=booking_id)
        result = NotificationService.send_notification(booking, notification_type, old_status)

        if result['sent']:
            logger.info(f"[ASYNC] Successfully sent {notification_type} notification for booking {booking_id}")
        else:
            logger.warning(f"[ASYNC] Failed to send notification for booking {booking_id}: {result['errors']}")

        return result

    except ObjectDoesNotExist:
        logger.error(f"[ASYNC] Booking {booking_id} not found for notification")
        return {'sent': False, 'errors': ['Booking not found']}
    except Exception as e:
        logger.error(f"[ASYNC] Error sending notification for booking {booking_id}: {e}", exc_info=True)
        return {'sent': False, 'errors': [str(e)]}


@background(schedule=0)
def send_round_trip_notification_async(outbound_id, return_id, notification_type):
    """
    Send unified round-trip notification asynchronously.

    Args:
        outbound_id: ID of the outbound booking
        return_id: ID of the return booking
        notification_type: Type of notification
    """
    try:
        from models import Booking
        from notification_service import NotificationService

        logger.info(f"[ASYNC] Starting round-trip notification task for bookings {outbound_id}/{return_id}")

        outbound = Booking.objects.get(id=outbound_id)
        return_booking = Booking.objects.get(id=return_id)

        result = NotificationService.send_round_trip_notification(
            outbound,
            return_booking,
            notification_type
        )

        if result['sent']:
            logger.info(f"[ASYNC] Successfully sent round-trip {notification_type} notification")
        else:
            logger.warning(f"[ASYNC] Failed to send round-trip notification: {result['errors']}")

        return result

    except ObjectDoesNotExist as e:
        logger.error(f"[ASYNC] Booking not found for round-trip notification: {e}")
        return {'sent': False, 'errors': ['Booking not found']}
    except Exception as e:
        logger.error(f"[ASYNC] Error sending round-trip notification: {e}", exc_info=True)
        return {'sent': False, 'errors': [str(e)]}


@background(schedule=60)  # Run after 1 minute
def cleanup_old_notifications(days=90):
    """
    Clean up old notification records to prevent database bloat.

    Args:
        days: Number of days to keep notifications (default: 90)
    """
    try:
        from models import Notification
        from django.utils import timezone
        from datetime import timedelta

        cutoff_date = timezone.now() - timedelta(days=days)
        deleted_count = Notification.objects.filter(sent_at__lt=cutoff_date).delete()[0]

        logger.info(f"[ASYNC] Cleaned up {deleted_count} old notification records")
        return deleted_count

    except Exception as e:
        logger.error(f"[ASYNC] Error cleaning up notifications: {e}", exc_info=True)
        return 0
