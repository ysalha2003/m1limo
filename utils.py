"""Utility functions for the booking system."""
import logging
from typing import Optional
from models import Booking
from notification_service import NotificationService

logger = logging.getLogger(__name__)


def send_pickup_reminder_email(booking: Booking, is_return: bool = False) -> bool:
    """
    Send pickup reminder notification via NotificationService.
    Called by send_pickup_reminders management command.
    """
    try:
        logger.info(
            f"Sending {'return' if is_return else 'outbound'} pickup reminder "
            f"for booking {booking.id} - {booking.passenger_name}"
        )

        from email_service import EmailService
        
        # Send unified reminder
        success = EmailService.send_unified_notification(
            template_type='customer_reminder',
            booking=booking,
            recipient_email=booking.user.email,
            extra_context={}
        )

        if success:
            logger.info(
                f"Successfully sent {'return' if is_return else 'outbound'} reminder "
                f"for booking {booking.id}"
            )
        else:
            logger.warning(
                f"Failed to send {'return' if is_return else 'outbound'} reminder "
                f"for booking {booking.id}"
            )

        return success

    except Exception as e:
        logger.error(
            f"Error sending {'return' if is_return else 'outbound'} reminder "
            f"for booking {booking.id}: {str(e)}",
            exc_info=True
        )
        return False
