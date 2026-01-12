# services/notification_service.py
import logging
from typing import Optional, Dict, Any
from django.conf import settings
from email_service import EmailService
from models import Booking, Notification, NotificationRecipient, BookingNotification

logger = logging.getLogger('services')


class NotificationService:
    """Orchestrates sending notifications via email."""
    
    NOTIFICATION_MAP = {
        'new': {'email_template': 'booking_notification'},
        'confirmed': {'email_template': 'booking_notification'},
        'cancelled': {'email_template': 'booking_notification'},
        'status_change': {'email_template': 'booking_notification'},
        'reminder': {'email_template': 'booking_reminder'},
    }
    
    @classmethod
    def send_notification(
        cls,
        booking: Booking,
        notification_type: str,
        old_status: Optional[str] = None,
        is_return: bool = False
    ) -> Dict[str, Any]:
        """
        Send notification to all configured recipients.
        Returns detailed status for error handling.
        """
        logger.info(f"[NOTIFICATION START] Booking: {booking.id}, Type: {notification_type}")

        # Get recipients
        recipients = cls.get_recipients(booking, notification_type)

        if not recipients:
            logger.warning(f"[NOTIFICATION] No recipients for booking {booking.id}")
            return {
                'sent': False,
                'total_recipients': 0,
                'successful_recipients': [],
                'failed_recipients': [],
                'errors': ['No recipients configured']
            }

        logger.info(f"[NOTIFICATION] Sending to {len(recipients)} recipients")

        notification_sent = False
        successful_recipients = []
        failed_recipients = []
        errors = []

        for recipient_email in recipients:
            try:
                logger.info(f"[EMAIL] Sending {notification_type} to {recipient_email}")

                success = EmailService.send_booking_notification(
                    booking=booking,
                    notification_type=notification_type,
                    recipient_email=recipient_email,
                    old_status=old_status,
                    is_return=is_return
                )

                cls._record_notification(
                    booking=booking,
                    notification_type=notification_type,
                    channel='email',
                    recipient=recipient_email,
                    success=success
                )

                if success:
                    logger.info(f"[EMAIL] OK Sent to {recipient_email}")
                    notification_sent = True
                    successful_recipients.append(recipient_email)
                else:
                    logger.error(f"[EMAIL] FAIL Failed to send to {recipient_email}")
                    failed_recipients.append(recipient_email)
                    errors.append(f"Failed to send to {recipient_email}")

            except Exception as e:
                error_msg = str(e)
                logger.error(f"[EMAIL] Exception sending to {recipient_email}: {e}", exc_info=True)
                cls._record_notification(
                    booking=booking,
                    notification_type=notification_type,
                    channel='email',
                    recipient=recipient_email,
                    success=False,
                    error_message=error_msg
                )
                failed_recipients.append(recipient_email)
                errors.append(f"{recipient_email}: {error_msg}")

        logger.info(f"[NOTIFICATION END] Booking: {booking.id}, Sent: {notification_sent}")

        return {
            'sent': notification_sent,
            'total_recipients': len(recipients),
            'successful_recipients': successful_recipients,
            'failed_recipients': failed_recipients,
            'errors': errors
        }
    
    @classmethod
    def get_recipients(
        cls,
        booking: Booking,
        notification_type: str
    ) -> list:
        """Get all email recipients based on notification preferences."""
        recipients = set()

        admin_email = getattr(settings, 'ADMIN_EMAIL', None)
        if admin_email:
            recipients.add(admin_email)

        # Always send to account holder's email for all notification types
        if booking.user.email:
            recipients.add(booking.user.email)

        # Only send reminders to passenger email (if different from user email)
        if notification_type == 'reminder' and booking.passenger_email:
            if booking.passenger_email != booking.user.email:
                recipients.add(booking.passenger_email)

        try:
            booking_ids = [booking.id]
            if booking.linked_booking:
                booking_ids.append(booking.linked_booking.id)
                logger.info(f"Including recipients from linked booking {booking.linked_booking.id}")

            booking_notifications = BookingNotification.objects.filter(
                booking__id__in=booking_ids,
                recipient__is_active=True
            ).select_related('recipient')

            for bn in booking_notifications:
                recipient = bn.recipient

                if notification_type == 'new' and recipient.notify_new:
                    recipients.add(recipient.email)
                elif notification_type == 'confirmed' and recipient.notify_confirmed:
                    recipients.add(recipient.email)
                elif notification_type == 'cancelled' and recipient.notify_cancelled:
                    recipients.add(recipient.email)
                elif notification_type == 'status_change' and getattr(recipient, 'notify_status_changes', True):
                    recipients.add(recipient.email)
                elif notification_type == 'reminder' and getattr(recipient, 'notify_reminders', True):
                    recipients.add(recipient.email)

        except Exception as e:
            logger.error(f"Error getting booking-specific recipients: {e}")

        try:
            global_recipients = NotificationRecipient.objects.filter(is_active=True)

            for recipient in global_recipients:
                if notification_type == 'new' and recipient.notify_new:
                    recipients.add(recipient.email)
                elif notification_type == 'confirmed' and recipient.notify_confirmed:
                    recipients.add(recipient.email)
                elif notification_type == 'cancelled' and recipient.notify_cancelled:
                    recipients.add(recipient.email)
                elif notification_type == 'status_change' and getattr(recipient, 'notify_status_changes', True):
                    recipients.add(recipient.email)
                elif notification_type == 'reminder' and getattr(recipient, 'notify_reminders', True):
                    recipients.add(recipient.email)

        except Exception as e:
            logger.error(f"Error getting global recipients: {e}")

        return list(recipients)
    
    @staticmethod
    def _record_notification(
        booking: Booking,
        notification_type: str,
        channel: str,
        recipient: str,
        success: bool,
        error_message: Optional[str] = None
    ) -> None:
        """Record notification attempt in database for tracking."""
        try:
            notification = Notification.objects.create(
                booking=booking,
                notification_type=notification_type,
                channel=channel,
                recipient=recipient,
                success=success,
                error_message=error_message
            )
            
            status_text = "OK" if success else "FAIL"
            logger.info(
                f"[DB] {status_text} Recorded {channel} {notification_type} "
                f"to {recipient} for booking {booking.id}, success: {success}"
            )
            
        except Exception as e:
            logger.error(f"[DB] Failed to record notification: {e}", exc_info=True)
    
    @classmethod
    def send_reminder(
        cls,
        booking: Booking,
        is_return: bool = False
    ) -> bool:
        """Send pickup reminder notification."""
        return cls.send_notification(
            booking=booking,
            notification_type='reminder',
            is_return=is_return
        )
    
    @classmethod
    def send_round_trip_notification(
        cls,
        first_trip: Booking,
        return_trip: Booking,
        notification_type: str
    ) -> Dict[str, Any]:
        """
        Send unified email for round-trip bookings.
        Prevents duplicate emails by combining both trips in one message.
        """
        logger.info(f"[ROUND TRIP NOTIFICATION] First: {first_trip.id}, Return: {return_trip.id}, Type: {notification_type}")

        recipients = cls.get_recipients(first_trip, notification_type)

        if not recipients:
            logger.warning(f"[NOTIFICATION] No recipients for booking {first_trip.id}")
            return {
                'sent': False,
                'total_recipients': 0,
                'successful_recipients': [],
                'failed_recipients': [],
                'errors': ['No recipients configured']
            }

        logger.info(f"[NOTIFICATION] Sending unified round-trip email to {len(recipients)} recipients")

        notification_sent = False
        successful_recipients = []
        failed_recipients = []
        errors = []

        for recipient_email in recipients:
            try:
                logger.info(f"[EMAIL] Sending round-trip {notification_type} to {recipient_email}")

                success = EmailService.send_round_trip_notification(
                    first_trip=first_trip,
                    return_trip=return_trip,
                    notification_type=notification_type,
                    recipient_email=recipient_email
                )

                cls._record_notification(
                    booking=first_trip,
                    notification_type=notification_type,
                    channel='email',
                    recipient=recipient_email,
                    success=success
                )
                cls._record_notification(
                    booking=return_trip,
                    notification_type=notification_type,
                    channel='email',
                    recipient=recipient_email,
                    success=success
                )

                if success:
                    logger.info(f"[EMAIL] OK Sent unified round-trip email to {recipient_email}")
                    notification_sent = True
                    successful_recipients.append(recipient_email)
                else:
                    logger.error(f"[EMAIL] FAIL Failed to send to {recipient_email}")
                    failed_recipients.append(recipient_email)
                    errors.append(f"Failed to send to {recipient_email}")

            except Exception as e:
                error_msg = str(e)
                logger.error(f"[EMAIL] Exception sending to {recipient_email}: {e}", exc_info=True)
                cls._record_notification(
                    booking=first_trip,
                    notification_type=notification_type,
                    channel='email',
                    recipient=recipient_email,
                    success=False,
                    error_message=error_msg
                )
                failed_recipients.append(recipient_email)
                errors.append(f"{recipient_email}: {error_msg}")

        logger.info(f"[ROUND TRIP NOTIFICATION END] First: {first_trip.id}, Return: {return_trip.id}")

        return {
            'sent': notification_sent,
            'total_recipients': len(recipients),
            'successful_recipients': successful_recipients,
            'failed_recipients': failed_recipients,
            'errors': errors
        }

    @classmethod
    def resend_notification(
        cls,
        booking: Booking,
        notification_type: str
    ) -> bool:
        """Manually resend a notification."""
        logger.info(f"Manually resending {notification_type} for booking {booking.id}")
        return cls.send_notification(booking, notification_type)
    
    @classmethod
    def get_notification_history(cls, booking: Booking) -> Dict[str, Any]:
        """Get notification history and statistics for a booking."""
        notifications = booking.notification_log.all().order_by('-sent_at')
        
        return {
            'total_sent': notifications.count(),
            'email_sent': notifications.filter(channel='email', success=True).count(),
            'email_failed': notifications.filter(channel='email', success=False).count(),
            'latest_notifications': list(notifications[:10]),
            'all_notifications': notifications,
        }
    
    @classmethod
    def test_notification(
        cls,
        booking: Booking,
        test_email: str,
        notification_type: str = 'new'
    ) -> bool:
        """Send test notification to specific email address."""
        logger.info(f"[TEST] Sending test {notification_type} notification to {test_email}")

        try:
            success = EmailService.send_booking_notification(
                booking=booking,
                notification_type=notification_type,
                recipient_email=test_email
            )

            if success:
                logger.info(f"[TEST] OK Test email sent to {test_email}")
            else:
                logger.error(f"[TEST] FAIL Test email failed")

            return success

        except Exception as e:
            logger.error(f"[TEST] Exception: {e}", exc_info=True)
            return False

    @classmethod
    def send_driver_notification(cls, booking: Booking, driver) -> bool:
        """
        Send driver assignment notification email with essential trip details only.

        Args:
            booking: The Booking instance
            driver: The Driver instance

        Returns:
            bool: True if email sent successfully, False otherwise
        """
        logger.info(f"[DRIVER NOTIFICATION] Booking {booking.id} assigned to driver {driver.full_name}")

        try:
            success = EmailService.send_driver_notification(
                booking=booking,
                driver=driver
            )

            # Record notification
            cls._record_notification(
                booking=booking,
                notification_type='driver_assignment',
                channel='email',
                recipient=driver.email,
                success=success
            )

            if success:
                logger.info(f"[DRIVER NOTIFICATION] OK Sent to {driver.email}")
            else:
                logger.error(f"[DRIVER NOTIFICATION] FAIL Failed to send to {driver.email}")

            return success

        except Exception as e:
            logger.error(f"[DRIVER NOTIFICATION] Exception: {e}", exc_info=True)
            cls._record_notification(
                booking=booking,
                notification_type='driver_assignment',
                channel='email',
                recipient=driver.email,
                success=False,
                error_message=str(e)
            )
            return False

    @classmethod
    def send_driver_rejection_notification(cls, booking: Booking) -> bool:
        """
        Notify admin when a driver rejects a previously accepted trip.

        Args:
            booking: The Booking instance with driver rejection details

        Returns:
            bool: True if email sent successfully, False otherwise
        """
        logger.info(f"[DRIVER REJECTION] Booking {booking.id} rejected by driver {booking.assigned_driver.full_name}")

        try:
            from django.conf import settings
            admin_email = getattr(settings, 'ADMIN_EMAIL', None)

            if not admin_email:
                logger.warning(f"[DRIVER REJECTION] No admin email configured")
                return False

            subject = f"DRIVER REJECTION - Trip {booking.id} - {booking.pick_up_date.strftime('%b %d, %Y')}"

            html_message = f"""
            <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <h2 style="color: #dc3545;">Driver Trip Rejection</h2>

                <p><strong>{booking.assigned_driver.full_name}</strong> has rejected a previously accepted trip assignment.</p>

                <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid #dc3545; margin: 20px 0;">
                    <h3 style="margin-top: 0;">Trip Details:</h3>
                    <p><strong>Booking ID:</strong> {booking.id}</p>
                    <p><strong>Passenger:</strong> {booking.passenger_name}</p>
                    <p><strong>Pickup Date:</strong> {booking.pick_up_date.strftime('%B %d, %Y')}</p>
                    <p><strong>Pickup Time:</strong> {booking.pick_up_time.strftime('%I:%M %p')}</p>
                    <p><strong>Pickup Location:</strong> {booking.pick_up_address}</p>
                    {f'<p><strong>Drop-off Location:</strong> {booking.drop_off_address}</p>' if booking.drop_off_address else ''}
                </div>

                <div style="background: #fff3cd; padding: 15px; border-radius: 6px; border: 1px solid #ffc107; margin: 20px 0;">
                    <h4 style="margin-top: 0; color: #856404;">Rejection Reason:</h4>
                    <p style="color: #856404; margin: 0;">{booking.driver_rejection_reason}</p>
                </div>

                <p style="color: #666; font-size: 13px; margin-top: 30px;">
                    <strong>Action Required:</strong> Please assign a different driver to this trip.
                </p>
            </body>
            </html>
            """

            from django.utils.html import strip_tags

            success = (
                EmailService._try_email_message(admin_email, subject, html_message) or
                EmailService._try_send_mail(admin_email, subject, strip_tags(html_message), html_message)
            )

            cls._record_notification(
                booking=booking,
                notification_type='driver_rejection',
                channel='email',
                recipient=admin_email,
                success=success
            )

            if success:
                logger.info(f"[DRIVER REJECTION] OK Notification sent to admin")
            else:
                logger.error(f"[DRIVER REJECTION] FAIL Failed to send notification to admin")

            return success

        except Exception as e:
            logger.error(f"[DRIVER REJECTION] Exception: {e}", exc_info=True)
            return False

    @classmethod
    def send_driver_completion_notification(cls, booking: Booking) -> bool:
        """
        Notify admin when a driver marks a trip as completed.
        This data will be used for billing purposes in the future.

        Args:
            booking: The Booking instance with driver completion details

        Returns:
            bool: True if email sent successfully, False otherwise
        """
        logger.info(f"[DRIVER COMPLETION] Booking {booking.id} completed by driver {booking.assigned_driver.full_name}")

        try:
            from django.conf import settings
            admin_email = getattr(settings, 'ADMIN_EMAIL', None)

            if not admin_email:
                logger.warning(f"[DRIVER COMPLETION] No admin email configured")
                return False

            subject = f"Trip Completed - {booking.passenger_name} - {booking.pick_up_date.strftime('%b %d, %Y')}"

            html_message = f"""
            <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <h2 style="color: #28a745;">Trip Completed</h2>

                <p><strong>{booking.assigned_driver.full_name}</strong> has marked the trip as completed.</p>

                <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid #28a745; margin: 20px 0;">
                    <h3 style="margin-top: 0;">Trip Details:</h3>
                    <p><strong>Booking ID:</strong> {booking.id}</p>
                    <p><strong>Driver:</strong> {booking.assigned_driver.full_name}</p>
                    <p><strong>Passenger:</strong> {booking.passenger_name}</p>
                    <p><strong>Pickup Date:</strong> {booking.pick_up_date.strftime('%B %d, %Y')}</p>
                    <p><strong>Pickup Time:</strong> {booking.pick_up_time.strftime('%I:%M %p')}</p>
                    <p><strong>Pickup Location:</strong> {booking.pick_up_address}</p>
                    {f'<p><strong>Drop-off Location:</strong> {booking.drop_off_address}</p>' if booking.drop_off_address else ''}
                    <p><strong>Completed At:</strong> {booking.driver_completed_at.strftime('%B %d, %Y at %I:%M %p')}</p>
                </div>

                <p style="color: #666; font-size: 13px; margin-top: 30px;">
                    <em>Note: This completion data will be used for billing purposes.</em>
                </p>
            </body>
            </html>
            """

            from django.utils.html import strip_tags

            success = (
                EmailService._try_email_message(admin_email, subject, html_message) or
                EmailService._try_send_mail(admin_email, subject, strip_tags(html_message), html_message)
            )

            cls._record_notification(
                booking=booking,
                notification_type='driver_completion',
                channel='email',
                recipient=admin_email,
                success=success
            )

            if success:
                logger.info(f"[DRIVER COMPLETION] OK Notification sent to admin")
            else:
                logger.error(f"[DRIVER COMPLETION] FAIL Failed to send notification to admin")

            return success

        except Exception as e:
            logger.error(f"[DRIVER COMPLETION] Exception: {e}", exc_info=True)
            return False
