# services/notification_service.py
import logging
from typing import Optional, Dict, Any, List
from django.conf import settings
from django.utils import timezone
from email_service import EmailService
from models import Booking, Notification, NotificationRecipient, BookingNotification

logger = logging.getLogger('services')


class NotificationService:
    """
    Unified Notification Service for M1 Limo.
    
    Orchestrates notification sending via unified email templates:
    - send_unified_booking_notification(): Customer & admin alerts for booking events
    - send_unified_driver_notification(): Driver trip assignments
    - send_unified_admin_driver_alert(): Admin alerts for driver events (rejection/completion)
    
    All notifications are recorded in the database for auditing.
    """

    # ============================================================================
    # UNIFIED NOTIFICATION METHODS
    # ============================================================================

    @classmethod
    def send_unified_booking_notification(
        cls,
        booking: Booking,
        event: str,
        old_status: Optional[str] = None,
        selected_recipients: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Send unified booking notification (replaces send_notification for booking events).
        Uses customer_booking template for customers and admin_booking template for admins.
        
        Args:
            booking: Booking instance
            event: 'new' | 'confirmed' | 'cancelled' | 'status_change'
            old_status: Previous status (for status_change events)
            selected_recipients: Optional list of recipient types ['user', 'passenger', 'admin']
                               If None, sends to all (default behavior)
        
        Returns:
            dict: Status with sent, successful_recipients, failed_recipients, errors
        """
        logger.info(f"[UNIFIED NOTIFICATION] Booking: {booking.id}, Event: {event}, Selected: {selected_recipients}")
        
        successful_recipients = []
        failed_recipients = []
        errors = []
        
        # Build context for notifications
        extra_context = {
            'event': event,
            'old_status': old_status
        }
        
        # Send to customers (User + Passenger) - only if selected or no selection specified
        should_send_to_customers = selected_recipients is None or 'user' in selected_recipients or 'passenger' in selected_recipients
        
        if should_send_to_customers:
            customer_recipients = cls._get_customer_recipients(booking, selected_recipients)
            for recipient_email in customer_recipients:
                try:
                    success = EmailService.send_unified_notification(
                        template_type='customer_booking',
                        booking=booking,
                        recipient_email=recipient_email,
                        extra_context=extra_context
                    )
                    
                    cls._record_notification(
                        booking=booking,
                        notification_type=f'customer_{event}',
                        channel='email',
                        recipient=recipient_email,
                        success=success
                    )
                    
                    if success:
                        successful_recipients.append(recipient_email)
                        logger.info(f"[UNIFIED] Customer notification sent to {recipient_email}")
                    else:
                        failed_recipients.append(recipient_email)
                        errors.append(f"Customer notification failed: {recipient_email}")
                
                except Exception as e:
                    logger.error(f"[UNIFIED] Error sending to customer {recipient_email}: {e}")
                    failed_recipients.append(recipient_email)
                    errors.append(f"{recipient_email}: {str(e)}")
        
        # Send to admins - only if selected or no selection specified
        should_send_to_admin = selected_recipients is None or 'admin' in selected_recipients
        
        if should_send_to_admin:
            admin_recipients = cls._get_admin_recipients(booking, event)
            for recipient_email in admin_recipients:
                try:
                    success = EmailService.send_unified_notification(
                        template_type='admin_booking',
                        booking=booking,
                        recipient_email=recipient_email,
                        extra_context=extra_context
                    )
                    
                    cls._record_notification(
                        booking=booking,
                        notification_type=f'admin_{event}',
                        channel='email',
                        recipient=recipient_email,
                        success=success
                    )
                    
                    if success:
                        successful_recipients.append(recipient_email)
                        logger.info(f"[UNIFIED] Admin notification sent to {recipient_email}")
                    else:
                        failed_recipients.append(recipient_email)
                        errors.append(f"Admin notification failed: {recipient_email}")
                
                except Exception as e:
                    logger.error(f"[UNIFIED] Error sending to admin {recipient_email}: {e}")
                    failed_recipients.append(recipient_email)
                    errors.append(f"{recipient_email}: {str(e)}")
        
        # Calculate total recipients actually attempted
        total_attempted = len(successful_recipients) + len(failed_recipients)
        notification_sent = len(successful_recipients) > 0
        
        logger.info(f"[UNIFIED NOTIFICATION END] Booking: {booking.id}, Sent: {notification_sent}, Success: {len(successful_recipients)}/{total_attempted}")
        
        return {
            'sent': notification_sent,
            'total_recipients': total_attempted,
            'successful_recipients': successful_recipients,
            'failed_recipients': failed_recipients,
            'errors': errors
        }

    @classmethod
    def send_unified_driver_notification(
        cls,
        booking: Booking,
        driver: 'Driver',
        accept_url: str = '#',
        reject_url: str = '#'
    ) -> bool:
        """
        Send unified driver assignment notification.
        Uses driver_assignment template.
        
        Args:
            booking: Booking instance
            driver: Driver instance
            accept_url: URL for driver to accept trip
            reject_url: URL for driver to reject trip
        
        Returns:
            bool: True if sent successfully
        """
        logger.info(f"[UNIFIED DRIVER] Booking: {booking.id}, Driver: {driver.full_name}")
        
        if not driver.email:
            logger.warning(f"[UNIFIED DRIVER] Driver {driver.full_name} has no email")
            return False
        
        try:
            extra_context = {
                'accept_url': accept_url,
                'reject_url': reject_url
            }
            
            success = EmailService.send_unified_notification(
                template_type='driver_assignment',
                booking=booking,
                recipient_email=driver.email,
                extra_context=extra_context
            )
            
            cls._record_notification(
                booking=booking,
                notification_type='driver_assignment',
                channel='email',
                recipient=driver.email,
                success=success
            )
            
            if success:
                logger.info(f"[UNIFIED DRIVER] Notification sent to {driver.email}")
            else:
                logger.error(f"[UNIFIED DRIVER] Failed to send to {driver.email}")
            
            return success
        
        except Exception as e:
            logger.error(f"[UNIFIED DRIVER] Error: {e}", exc_info=True)
            return False

    @classmethod
    def send_unified_admin_driver_alert(
        cls,
        booking: Booking,
        driver: 'Driver',
        event_type: str,
        reason: str = '',
        notes: str = ''
    ) -> bool:
        """
        Send unified admin driver alert (rejection/completion).
        Uses admin_driver template.
        
        Args:
            booking: Booking instance
            driver: Driver instance
            event_type: 'rejection' | 'completion'
            reason: Reason for rejection/completion
            notes: Additional notes
        
        Returns:
            bool: True if sent to at least one admin
        """
        logger.info(f"[UNIFIED ADMIN DRIVER] Booking: {booking.id}, Event: {event_type}")
        
        # Get all admin recipients
        admin_recipients = cls._get_all_admin_recipients()
        
        if not admin_recipients:
            logger.warning(f"[UNIFIED ADMIN DRIVER] No admin recipients configured")
            return False
        
        extra_context = {
            'event_type': event_type,
            'driver_name': driver.full_name,
            'driver_phone': driver.phone_number,
            'reason': reason,
            'notes': notes,
            'timestamp': timezone.now()
        }
        
        success_count = 0
        for admin_email in admin_recipients:
            try:
                success = EmailService.send_unified_notification(
                    template_type='admin_driver',
                    booking=booking,
                    recipient_email=admin_email,
                    extra_context=extra_context
                )
                
                cls._record_notification(
                    booking=booking,
                    notification_type=f'admin_driver_{event_type}',
                    channel='email',
                    recipient=admin_email,
                    success=success
                )
                
                if success:
                    success_count += 1
                    logger.info(f"[UNIFIED ADMIN DRIVER] Sent to {admin_email}")
                else:
                    logger.error(f"[UNIFIED ADMIN DRIVER] Failed to send to {admin_email}")
            
            except Exception as e:
                logger.error(f"[UNIFIED ADMIN DRIVER] Error sending to {admin_email}: {e}")
        
        logger.info(f"[UNIFIED ADMIN DRIVER END] Sent to {success_count}/{len(admin_recipients)} admins")
        return success_count > 0

    # ============================================================================
    # HELPER METHODS
    # ============================================================================

    @classmethod
    def _get_customer_recipients(cls, booking: Booking, selected_recipients: Optional[list] = None) -> List[str]:
        """
        Get customer recipients (User + Passenger if different).
        
        Args:
            booking: Booking instance
            selected_recipients: Optional list to filter recipients ['user', 'passenger']
        
        Returns:
            list: List of customer email addresses
        """
        recipients = []
        
        # User who created booking (only if selected or no selection)
        if (selected_recipients is None or 'user' in selected_recipients):
            if booking.user and booking.user.email:
                recipients.append(booking.user.email)
        
        # Passenger if different email (only if selected or no selection)
        if (selected_recipients is None or 'passenger' in selected_recipients):
            if booking.send_passenger_notifications and booking.passenger_email:
                if booking.passenger_email.lower() != booking.user.email.lower():
                    recipients.append(booking.passenger_email)
        
        return recipients

    @classmethod
    def _get_admin_recipients(cls, booking: Booking, event: str) -> List[str]:
        """
        Get admin recipients dynamically from staff/superuser accounts.
        Uses current email from User profile, respects changes in admin panel.
        
        Args:
            booking: Booking instance
            event: 'new' | 'confirmed' | 'cancelled' | 'status_change'
        
        Returns:
            list: List of admin email addresses (from User.email field)
        """
        recipients = set()
        
        try:
            from django.contrib.auth.models import User
            
            # Get all active staff/superuser accounts with email
            admin_users = User.objects.filter(
                is_active=True,
                is_staff=True
            ).exclude(email='')
            
            # Admin/staff users receive all booking notifications by default
            # This ensures business operations are not missed
            for admin in admin_users:
                if admin.email:
                    recipients.add(admin.email)
            
            logger.info(f"[ADMIN RECIPIENTS] Found {len(recipients)} admin(s) for event '{event}'")
        
        except Exception as e:
            logger.error(f"Error getting admin recipients: {e}")
        
        return list(recipients)

    @classmethod
    def _get_all_admin_recipients(cls) -> List[str]:
        """
        Get all active admin recipients dynamically from staff/superuser accounts.
        Driver events are critical and sent to all admins.
        Uses current email from User.email field.
        
        Returns:
            list: List of all admin email addresses
        """
        recipients = []
        
        try:
            from django.contrib.auth.models import User
            
            # Get all active staff/superuser accounts with email
            admin_users = User.objects.filter(
                is_active=True,
                is_staff=True
            ).exclude(email='').values_list('email', flat=True)
            
            recipients = list(admin_users)
            logger.info(f"[ADMIN RECIPIENTS] Found {len(recipients)} admin(s) for driver alerts")
        
        except Exception as e:
            logger.error(f"Error getting all admin recipients: {e}")
        
        return recipients

    @classmethod
    def _record_notification(
        cls,
        booking: Booking,
        notification_type: str,
        channel: str,
        recipient: str,
        success: bool
    ) -> None:
        """
        Record notification in database for auditing.
        
        Args:
            booking: Booking instance
            notification_type: Type of notification (e.g., 'customer_confirmed')
            channel: 'email' | 'sms'
            recipient: Recipient address
            success: Whether notification was sent successfully
        """
        try:
            Notification.objects.create(
                booking=booking,
                notification_type=notification_type,
                channel=channel,
                recipient=recipient,
                success=success,
                error_message=None if success else 'Failed to send'
            )
        except Exception as e:
            logger.error(f"Error recording notification: {e}")
