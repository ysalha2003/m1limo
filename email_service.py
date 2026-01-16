# services/email_service.py
import logging
import smtplib
from typing import Optional
from django.conf import settings
from django.core.mail import EmailMessage, send_mail
from django.utils.html import strip_tags
from django.utils import timezone
from models import Booking

logger = logging.getLogger('services')


class EmailService:
    """
    Unified Email Service for M1 Limo notifications.
    
    Uses 5 role-based templates that adapt based on context:
    - customer_booking: All customer notifications (new/confirmed/cancelled/status changes)
    - customer_reminder: Pickup reminders
    - driver_assignment: Driver trip assignments
    - admin_booking: Admin booking alerts
    - admin_driver: Admin driver event alerts
    
    All templates are database-driven and manageable via Django admin.
    No file-based fallbacks - inactive templates will not send emails.
    """

    # ============================================================================
    # CORE METHODS
    # ============================================================================

    @classmethod
    def _load_email_template(cls, template_type: str) -> Optional['EmailTemplate']:
        """
        Load email template from database.
        Returns None if template not found or not active.
        """
        try:
            from models import EmailTemplate
            template = EmailTemplate.objects.filter(
                template_type=template_type,
                is_active=True
            ).first()
            return template
        except Exception as e:
            logger.warning(f"Could not load email template {template_type} from database: {e}")
            return None

    @staticmethod
    def _try_email_message(recipient: str, subject: str, html_message: str) -> bool:
        """Try sending via Django EmailMessage."""
        try:
            email = EmailMessage(
                subject=subject,
                body=html_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[recipient],
            )
            email.content_subtype = "html"
            
            result = email.send(fail_silently=False)
            
            if result == 1:
                logger.info("Email sent via EmailMessage")
                return True
            else:
                logger.error(f"EmailMessage returned {result}")
                return False
                
        except Exception as e:
            logger.error(f"EmailMessage failed: {e}")
            return False
    
    @staticmethod
    def _try_send_mail(
        recipient: str,
        subject: str,
        plain_message: str,
        html_message: str
    ) -> bool:
        """Try sending via Django send_mail."""
        try:
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient],
                html_message=html_message,
                fail_silently=False,
            )
            
            logger.info("Email sent via send_mail")
            return True
            
        except Exception as e:
            logger.error(f"send_mail failed: {e}")
            return False

    # ============================================================================
    # UNIFIED TEMPLATE SYSTEM
    # ============================================================================

    @classmethod
    def send_unified_notification(
        cls,
        template_type: str,
        booking: Booking,
        recipient_email: str,
        extra_context: Optional[dict] = None
    ) -> bool:
        """
        Send notification using unified template system.
        
        Args:
            template_type: 'customer_booking' | 'customer_reminder' | 'driver_assignment' | 'admin_booking' | 'admin_driver'
            booking: Booking instance
            recipient_email: Recipient email address
            extra_context: Additional context variables (optional)
        
        Returns:
            bool: True if email sent successfully
        """
        try:
            # Load unified template
            template = cls._load_email_template(template_type)
            if not template:
                logger.warning(f"No active unified template found for {template_type}, email NOT sent to {recipient_email}")
                return False
            
            # Build unified context
            context = cls._build_unified_context(
                template_type=template_type,
                booking=booking,
                extra_context=extra_context
            )
            
            # Render and send
            try:
                subject = template.render_subject(context)
                html_message = template.render_html(context)
                plain_message = strip_tags(html_message)
                
                logger.info(f"Sending unified {template_type} notification to {recipient_email}")
                
                success = (
                    cls._try_email_message(recipient_email, subject, html_message) or
                    cls._try_send_mail(recipient_email, subject, plain_message, html_message)
                )
                
                if success:
                    template.increment_sent()
                    logger.info(f"Unified {template_type} email sent successfully to {recipient_email}")
                else:
                    template.increment_failed()
                    logger.error(f"Failed to send unified {template_type} email to {recipient_email}")
                
                return success
                
            except Exception as e:
                logger.error(f"Unified template rendering error for {template_type}: {e}")
                template.increment_failed()
                return False
        
        except Exception as e:
            logger.error(f"Error sending unified notification to {recipient_email}: {e}", exc_info=True)
            return False

    @staticmethod
    def _build_unified_context(
        template_type: str,
        booking: Booking,
        extra_context: Optional[dict] = None
    ) -> dict:
        """
        Build context for unified templates.
        Provides all variables needed for any template to render correctly.
        """
        # Base context (common to all templates)
        context = {
            # Core booking info
            'booking_reference': booking.booking_reference,
            'passenger_name': booking.passenger_name,
            'phone_number': booking.phone_number,
            'passenger_email': booking.passenger_email or '',
            'pick_up_address': booking.pick_up_address,
            'drop_off_address': booking.drop_off_address,
            'pick_up_date': booking.pick_up_date,
            'pick_up_time': booking.pick_up_time,
            'status': booking.status,
            'status_display': booking.get_status_display(),
            'trip_type': booking.trip_type,
            'notes': booking.notes or '',
            
            # Trip type flags
            'is_round_trip': booking.trip_type == 'Round',
            'has_return': booking.trip_type == 'Round' and booking.is_return_trip,
            
            # Round trip details
            'return_date': booking.return_date if booking.trip_type == 'Round' else None,
            'return_time': booking.return_time if booking.trip_type == 'Round' else None,
            'return_pickup_address': booking.return_pickup_address if booking.trip_type == 'Round' else '',
            'return_dropoff_address': booking.return_dropoff_address if booking.trip_type == 'Round' else '',
            
            # Hourly details
            'hours_booked': booking.hours_booked if booking.trip_type == 'Hourly' else 0,
            
            # Driver info
            'has_driver': bool(booking.assigned_driver),
            'driver_name': '',
            'driver_phone': '',
            'driver_email': '',
            'driver_car_type': '',
            'driver_car_number': '',
            
            # Status flags for conditional sections
            'is_new': booking.status == 'Pending',
            'is_confirmed': booking.status == 'Confirmed',
            'is_cancelled': booking.status == 'Cancelled',
            'is_completed': booking.status == 'Completed',
            
            # Defaults
            'old_status': None,
            'event': 'status_change',
            'action_needed': False,
            'user_email': booking.user.email if booking.user else '',
        }
        
        # Add driver details if assigned
        if booking.assigned_driver:
            context.update({
                'driver_name': booking.assigned_driver.full_name,
                'driver_phone': booking.assigned_driver.phone_number,
                'driver_email': booking.assigned_driver.email or '',
                'driver_car_type': booking.assigned_driver.car_type,
                'driver_car_number': booking.assigned_driver.car_number,
            })
        
        # Template-specific additions
        if template_type == 'customer_booking':
            # Extract event from extra_context if provided
            if extra_context:
                context['event'] = extra_context.get('event', 'status_change')
                if 'old_status' in extra_context:
                    context['old_status'] = extra_context['old_status']
        
        elif template_type == 'customer_reminder':
            # Calculate hours until pickup
            from datetime import datetime, timedelta
            try:
                pickup_datetime = datetime.combine(booking.pick_up_date, booking.pick_up_time)
                hours_until = int((pickup_datetime - datetime.now()).total_seconds() / 3600)
                context['hours_until_pickup'] = max(0, hours_until)
            except:
                context['hours_until_pickup'] = 24
        
        elif template_type == 'driver_assignment':
            # Driver-specific context
            context['special_requests'] = booking.notes or ''
            context['accept_url'] = extra_context.get('accept_url', '#') if extra_context else '#'
            context['reject_url'] = extra_context.get('reject_url', '#') if extra_context else '#'
        
        elif template_type == 'admin_booking':
            # Admin booking alert context
            if extra_context:
                context['event'] = extra_context.get('event', 'status_change')
                if 'old_status' in extra_context:
                    context['old_status'] = extra_context['old_status']
            context['action_needed'] = not booking.assigned_driver
            context['admin_url'] = f"/admin/bookings/booking/{booking.id}/change/"
        
        elif template_type == 'admin_driver':
            # Admin driver alert context
            if extra_context:
                context['event_type'] = extra_context.get('event_type', 'unknown')
                context['reason'] = extra_context.get('reason', '')
                context['notes'] = extra_context.get('notes', '')
                context['timestamp'] = extra_context.get('timestamp', timezone.now())
            context['admin_url'] = f"/admin/bookings/booking/{booking.id}/change/"
        
        # Merge extra context (override defaults)
        if extra_context:
            context.update(extra_context)
        
        return context
