# services/email_service.py
import logging
import smtplib
from typing import Optional
from django.conf import settings
from django.core.mail import EmailMessage, send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone
from models import Booking

logger = logging.getLogger('services')


class EmailService:
    """
    Unified Email Service for M1 Limo notifications.
    
    Uses role-based templates that adapt based on context:
    - customer_booking: All customer notifications (new/confirmed/cancelled/status changes)
    - customer_reminder: Pickup reminders
    - driver_assignment: Driver trip assignments
    - admin_booking: Admin booking alerts
    - admin_driver: Admin driver event alerts
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
        booking: Booking,
        notification_type: str,
        recipient_email: str,
        old_status: Optional[str] = None,
        is_return: bool = False
    ) -> bool:
        """
        Send booking notification email with user preference checking.
        Returns True if email sent or skipped by preference.
        """
        try:
            if recipient_email == booking.user.email:
                try:
                    from models import UserProfile
                    profile = booking.user.profile

                    if notification_type == 'confirmed' and not profile.receive_booking_confirmations:
                        logger.info(f"Skipping confirmation email to {recipient_email} (user preference)")
                        return True

                    elif notification_type in ['status_change', 'cancelled'] and not profile.receive_status_updates:
                        logger.info(f"Skipping status update email to {recipient_email} (user preference)")
                        return True

                    elif notification_type == 'reminder' and not profile.receive_pickup_reminders:
                        logger.info(f"Skipping reminder email to {recipient_email} (user preference)")
                        return True

                except Exception as e:
                    logger.warning(f"Could not check user preferences for {recipient_email}: {e}")
                    pass

            context = cls._build_email_context(
                booking=booking,
                notification_type=notification_type,
                old_status=old_status,
                is_return=is_return
            )

            # Map notification type to template type
            template_type_map = {
                'new': 'booking_new',
                'confirmed': 'booking_confirmed',
                'cancelled': 'booking_cancelled',
                'status_change': 'booking_status_change',
                'reminder': 'booking_reminder'
            }
            db_template_type = template_type_map.get(notification_type)
            
            # Load active database template (NO FALLBACK)
            db_template = cls._load_email_template(db_template_type) if db_template_type else None
            
            if not db_template:
                logger.warning(f"No active database template found for {notification_type}, email NOT sent to {recipient_email}")
                return False
            
            try:
                # Build context for database template
                template_context = cls._build_template_context(booking, notification_type, old_status, is_return)
                subject = db_template.render_subject(template_context)
                html_message = db_template.render_html(template_context)
                plain_message = strip_tags(html_message)
                
                logger.info(f"Using database template for {notification_type}")
                db_template.increment_sent()
            except Exception as e:
                logger.error(f"Database template rendering error: {e}")
                db_template.increment_failed()
                return False

            logger.info(f"Sending {notification_type} email to {recipient_email}")

            # Skip Direct SMTP (timeout waste), use Django's email backend directly
            success = (
                cls._try_email_message(recipient_email, subject, html_message) or
                cls._try_send_mail(recipient_email, subject, plain_message, html_message)
            )

            if success:
                logger.info(f"Email sent successfully to {recipient_email}")
            else:
                logger.error(f"All email sending methods failed for {recipient_email}")

            return success
            
        except Exception as e:
            logger.error(f"Error sending email to {recipient_email}: {e}", exc_info=True)
            return False
    
    @staticmethod
    def _build_email_context(
        booking: Booking,
        notification_type: str,
        old_status: Optional[str] = None,
        is_return: bool = False
    ) -> dict:
        """Build context dictionary for email templates."""
        context = {
            'booking': booking,
            'notification_type': notification_type,
            'company_info': settings.COMPANY_INFO,
            'is_return': is_return,
        }
        
        if old_status:
            context['old_status'] = old_status
            context['new_status'] = booking.status
        
        return context

    @staticmethod
    def _build_template_context(
        booking: Booking,
        notification_type: str,
        old_status: Optional[str] = None,
        is_return: bool = False
    ) -> dict:
        """Build context dictionary for database email templates (variable format)."""
        context = {
            'booking_reference': booking.booking_reference,
            'passenger_name': booking.passenger_name,
            'phone_number': booking.phone_number,
            'passenger_email': booking.passenger_email or '',
            'pick_up_date': booking.pick_up_date.strftime('%B %d, %Y') if booking.pick_up_date else '',
            'pick_up_time': booking.pick_up_time.strftime('%I:%M %p') if booking.pick_up_time else '',
            'pick_up_address': booking.pick_up_address,
            'drop_off_address': booking.drop_off_address,
            'vehicle_type': booking.vehicle_type or '',
            'trip_type': booking.get_trip_type_display() if hasattr(booking, 'get_trip_type_display') else booking.trip_type,
            'number_of_passengers': str(booking.number_of_passengers) if booking.number_of_passengers else '',
            'flight_number': booking.flight_number or '',
            'notes': booking.notes or '',
            'status': booking.get_status_display() if hasattr(booking, 'get_status_display') else booking.status,
            'old_status': old_status or '',
            'new_status': booking.get_status_display() if hasattr(booking, 'get_status_display') else booking.status,
            'user_email': booking.user.email if booking.user else '',
            'user_username': booking.user.username if booking.user else '',
            'company_name': settings.COMPANY_INFO.get('name', 'M1 Limousine Service'),
            'support_email': settings.COMPANY_INFO.get('email', 'support@m1limo.com'),
            'dashboard_url': f"{settings.BASE_URL}/dashboard",
        }
        
        # Add driver information if available
        if booking.assigned_driver:
            context['driver_name'] = booking.assigned_driver.get_full_name() if hasattr(booking.assigned_driver, 'get_full_name') else str(booking.assigned_driver)
            context['driver_phone'] = booking.assigned_driver.phone if hasattr(booking.assigned_driver, 'phone') else ''
            context['driver_vehicle'] = f"{booking.assigned_driver.vehicle_make} {booking.assigned_driver.vehicle_model}" if hasattr(booking.assigned_driver, 'vehicle_make') else ''
        else:
            context['driver_name'] = ''
            context['driver_phone'] = ''
            context['driver_vehicle'] = ''
            
        # Add return trip information if it's the return leg of a round trip
        if booking.trip_type == 'Round' and booking.is_return_trip:
            context['return_pick_up_date'] = booking.return_date.strftime('%B %d, %Y') if booking.return_date else ''
            context['return_pick_up_time'] = booking.return_time.strftime('%I:%M %p') if booking.return_time else ''
            context['return_pick_up_address'] = booking.drop_off_address  # Return starts from drop-off
            context['return_drop_off_address'] = booking.pick_up_address  # Return ends at pick-up
        
        return context
    
    @staticmethod
    def _build_round_trip_template_context(
        first_trip: Booking,
        return_trip: Booking,
        notification_type: str
    ) -> dict:
        """Build context dictionary for database round-trip email templates."""
        context = {
            'booking_reference': first_trip.booking_reference,
            'passenger_name': first_trip.passenger_name,
            'phone_number': first_trip.phone_number,
            'passenger_email': first_trip.passenger_email or '',
            # First trip details
            'pick_up_date': first_trip.pick_up_date.strftime('%B %d, %Y') if first_trip.pick_up_date else '',
            'pick_up_time': first_trip.pick_up_time.strftime('%I:%M %p') if first_trip.pick_up_time else '',
            'pick_up_address': first_trip.pick_up_address,
            'drop_off_address': first_trip.drop_off_address,
            # Return trip details
            'return_pick_up_date': return_trip.pick_up_date.strftime('%B %d, %Y') if return_trip.pick_up_date else '',
            'return_pick_up_time': return_trip.pick_up_time.strftime('%I:%M %p') if return_trip.pick_up_time else '',
            'return_pick_up_address': return_trip.pick_up_address,
            'return_drop_off_address': return_trip.drop_off_address,
            # Shared details
            'vehicle_type': first_trip.vehicle_type or '',
            'trip_type': 'Round Trip',
            'number_of_passengers': str(first_trip.number_of_passengers) if first_trip.number_of_passengers else '',
            'flight_number': first_trip.flight_number or '',
            'notes': first_trip.notes or '',
            'status': first_trip.get_status_display() if hasattr(first_trip, 'get_status_display') else first_trip.status,
            'user_email': first_trip.user.email if first_trip.user else '',
            'user_username': first_trip.user.username if first_trip.user else '',
            'company_name': settings.COMPANY_INFO.get('name', 'M1 Limousine Service'),
            'support_email': settings.COMPANY_INFO.get('email', 'support@m1limo.com'),
            'dashboard_url': f"{settings.BASE_URL}/dashboard",
        }
        
        return context
    
    @staticmethod
    def _build_driver_rejection_template_context(booking: Booking) -> dict:
        """Build context dictionary for driver rejection notification templates."""
        from django.conf import settings
        
        context = {
            # Driver information
            'driver_full_name': booking.assigned_driver.get_full_name() if hasattr(booking.assigned_driver, 'get_full_name') else str(booking.assigned_driver),
            'driver_email': booking.assigned_driver.email if hasattr(booking.assigned_driver, 'email') else '',
            
            # Booking reference
            'booking_reference': booking.booking_reference or f"#{booking.id}",
            'booking_id': str(booking.id),
            
            # Trip details
            'passenger_name': booking.passenger_name,
            'pickup_date': booking.pick_up_date.strftime('%A, %B %d, %Y') if booking.pick_up_date else '',
            'pickup_time': booking.pick_up_time.strftime('%I:%M %p') if booking.pick_up_time else '',
            'pick_up_address': booking.pick_up_address,
            'drop_off_address': booking.drop_off_address or '',
            
            # Rejection details
            'rejection_reason': booking.driver_rejection_reason or 'No reason provided',
            'rejected_at': booking.driver_rejected_at.strftime('%B %d, %Y at %I:%M %p') if hasattr(booking, 'driver_rejected_at') and booking.driver_rejected_at else timezone.now().strftime('%B %d, %Y at %I:%M %p'),
            
            # URLs
            'dashboard_url': f"{settings.BASE_URL}/dashboard",
            'booking_url': f"{settings.BASE_URL}/reservation/{booking.id}/",
            
            # Company information
            'company_name': settings.COMPANY_INFO.get('name', 'M1 Limousine Service'),
            'support_email': settings.COMPANY_INFO.get('email', 'support@m1limo.com'),
        }
        
        return context
    
    @staticmethod
    def _build_driver_completion_template_context(booking: Booking) -> dict:
        """Build context dictionary for driver completion notification templates."""
        from django.conf import settings
        
        context = {
            # Driver information
            'driver_full_name': booking.assigned_driver.get_full_name() if hasattr(booking.assigned_driver, 'get_full_name') else str(booking.assigned_driver),
            'driver_email': booking.assigned_driver.email if hasattr(booking.assigned_driver, 'email') else '',
            
            # Booking reference
            'booking_reference': booking.booking_reference or f"#{booking.id}",
            'booking_id': str(booking.id),
            
            # Trip details
            'passenger_name': booking.passenger_name,
            'pickup_date': booking.pick_up_date.strftime('%A, %B %d, %Y') if booking.pick_up_date else '',
            'pickup_time': booking.pick_up_time.strftime('%I:%M %p') if booking.pick_up_time else '',
            'pick_up_address': booking.pick_up_address,
            'drop_off_address': booking.drop_off_address or '',
            
            # Completion details
            'completed_at': booking.driver_completed_at.strftime('%B %d, %Y at %I:%M %p') if hasattr(booking, 'driver_completed_at') and booking.driver_completed_at else timezone.now().strftime('%B %d, %Y at %I:%M %p'),
            'trip_notes': getattr(booking, 'driver_completion_notes', '') or '',
            
            # URLs
            'dashboard_url': f"{settings.BASE_URL}/dashboard",
            'booking_url': f"{settings.BASE_URL}/reservation/{booking.id}/",
            
            # Company information
            'company_name': settings.COMPANY_INFO.get('name', 'M1 Limousine Service'),
            'support_email': settings.COMPANY_INFO.get('email', 'support@m1limo.com'),
        }
        
        return context
    
    @staticmethod
    def _build_driver_template_context(booking: Booking, driver) -> dict:
        """Build context dictionary for driver email templates (variable format)."""
        import hashlib
        from django.conf import settings
        
        # Generate secure tokens for driver portal access
        token = hashlib.md5(f"{booking.id}-{driver.email}".encode()).hexdigest()[:16]
        base_url = settings.BASE_URL
        driver_portal_url = f"{base_url}/driver/trip/{booking.id}/{token}/"
        
        all_trips_token = hashlib.md5(driver.email.encode()).hexdigest()[:16]
        all_trips_url = f"{base_url}/driver/trips/{driver.email}/{all_trips_token}/"
        
        context = {
            # Driver information
            'driver_full_name': driver.get_full_name() if hasattr(driver, 'get_full_name') else str(driver),
            'driver_email': driver.email,
            
            # Booking reference
            'booking_reference': booking.booking_reference or f"#{booking.id}",
            
            # Trip details (formatted strings for database templates)
            'pickup_location': booking.pick_up_address,
            'pickup_date': booking.pick_up_date.strftime('%A, %B %d, %Y') if booking.pick_up_date else '',
            'pickup_time': booking.pick_up_time.strftime('%I:%M %p') if booking.pick_up_time else '',
            'drop_off_location': booking.drop_off_address or '',
            
            # Passenger information
            'passenger_name': booking.passenger_name,
            'passenger_phone': booking.phone_number,
            'passenger_email': booking.passenger_email or '',
            
            # Vehicle and trip details
            'vehicle_type': booking.vehicle_type or '',
            'trip_type': booking.get_trip_type_display() if hasattr(booking, 'get_trip_type_display') else booking.trip_type,
            'number_of_passengers': str(booking.number_of_passengers) if booking.number_of_passengers else '',
            
            # Payment information
            'payment_amount': str(booking.driver_payment_amount) if hasattr(booking, 'driver_payment_amount') and booking.driver_payment_amount else '',
            
            # Portal URLs
            'driver_portal_url': driver_portal_url,
            'all_trips_url': all_trips_url,
            
            # Company information
            'company_name': settings.COMPANY_INFO.get('name', 'M1 Limousine Service'),
            'support_email': settings.COMPANY_INFO.get('email', 'support@m1limo.com'),
            'support_phone': settings.COMPANY_INFO.get('phone', ''),
        }
        
        return context
    
    @classmethod
    def send_round_trip_notification(
        cls,
        first_trip: Booking,
        return_trip: Booking,
        notification_type: str,
        recipient_email: str
    ) -> bool:
        """
        Send unified round-trip notification with both trips in one email.
        Respects user notification preferences.
        """
        try:
            if recipient_email == first_trip.user.email:
                try:
                    from models import UserProfile
                    profile = first_trip.user.profile

                    if notification_type == 'confirmed' and not profile.receive_booking_confirmations:
                        logger.info(f"Skipping round-trip confirmation email to {recipient_email} (user preference)")
                        return True

                    elif notification_type in ['status_change', 'cancelled'] and not profile.receive_status_updates:
                        logger.info(f"Skipping round-trip status update email to {recipient_email} (user preference)")
                        return True

                except Exception as e:
                    logger.warning(f"Could not check user preferences for {recipient_email}: {e}")
                    pass

            # Build company info with dashboard URL
            company_info = settings.COMPANY_INFO.copy()
            company_info['dashboard_url'] = f"{settings.BASE_URL}/dashboard"
            
            # Build booking URL for the view details button
            booking_url = f"{settings.BASE_URL}/reservation/{first_trip.id}/"
            
            context = {
                'is_round_trip': True,
                'booking': first_trip,  # Main booking for template
                'first_trip': first_trip,
                'return_trip': return_trip,
                'notification_type': notification_type,
                'company_info': company_info,
                'booking_url': booking_url,
                # Add flat variables for backwards compatibility with old template syntax
                'booking_id': first_trip.id,
                'booking_reference': first_trip.booking_reference,
                'passenger_name': first_trip.passenger_name,
                'phone_number': first_trip.phone_number,
                'passenger_email': first_trip.passenger_email or '',
                'pick_up_date': first_trip.pick_up_date.strftime('%B %d, %Y') if first_trip.pick_up_date else '',
                'pick_up_time': first_trip.pick_up_time.strftime('%I:%M %p') if first_trip.pick_up_time else '',
                'pick_up_address': first_trip.pick_up_address,
                'drop_off_address': first_trip.drop_off_address,
                'vehicle_type': first_trip.vehicle_type or '',
                'trip_type': 'Round Trip',
            }

            # Map notification type to template type
            template_type_map = {
                'new': 'round_trip_new',
                'confirmed': 'round_trip_confirmed',
                'cancelled': 'round_trip_cancelled',
                'status_change': 'round_trip_status_change'
            }
            db_template_type = template_type_map.get(notification_type)
            
            # Load active database template (NO FALLBACK)
            db_template = cls._load_email_template(db_template_type) if db_template_type else None
            
            if not db_template:
                logger.warning(f"No active database template found for round-trip {notification_type}, email NOT sent to {recipient_email}")
                return False
            
            try:
                # Use the same context as file templates (booking objects, not strings)
                # Database templates now use Django template syntax and expect booking objects
                subject = db_template.render_subject(context)
                html_message = db_template.render_html(context)
                plain_message = strip_tags(html_message)
                
                logger.info(f"Using database template for round-trip {notification_type}")
                db_template.increment_sent()
            except Exception as e:
                logger.error(f"Database template rendering error for round-trip: {e}")
                db_template.increment_failed()
                return False

            logger.info(f"Sending round-trip {notification_type} email to {recipient_email}")

            # Skip Direct SMTP (timeout waste), use Django's email backend directly
            success = (
                cls._try_email_message(recipient_email, subject, html_message) or
                cls._try_send_mail(recipient_email, subject, plain_message, html_message)
            )

            if success:
                logger.info(f"Round-trip email sent successfully to {recipient_email}")
            else:
                logger.error(f"All email sending methods failed for round-trip to {recipient_email}")

            return success

        except Exception as e:
            logger.error(f"Error sending round-trip email to {recipient_email}: {e}", exc_info=True)
            return False

    @staticmethod
    def _get_email_subject(
        booking: Booking,
        notification_type: str,
        old_status: Optional[str] = None,
        is_return: bool = False
    ) -> str:
        """Generate email subject line for single trips."""
        if notification_type == 'new':
            return f"Trip Request: {booking.passenger_name} - {booking.pick_up_date}"
        elif notification_type == 'confirmed':
            return f"Trip Confirmed: {booking.passenger_name} - {booking.pick_up_date}"
        elif notification_type == 'cancelled':
            return f"Trip Cancelled: {booking.passenger_name} - {booking.pick_up_date}"
        elif notification_type == 'status_change':
            return f"Trip Update: {old_status} -> {booking.status} - {booking.passenger_name}"
        elif notification_type == 'reminder':
            trip_type = "Return Trip" if is_return else "Pickup"
            time = booking.return_time if is_return else booking.pick_up_time
            return f"REMINDER: {trip_type} in 2 Hours - {booking.passenger_name} at {time}"
        else:
            return f"Trip Update: {booking.passenger_name} - {booking.pick_up_date}"

    @staticmethod
    def _get_round_trip_subject(
        first_trip: Booking,
        return_trip: Booking,
        notification_type: str
    ) -> str:
        """Generate subject line for round-trip emails."""
        if notification_type == 'new':
            return f"Round Trip Request: {first_trip.passenger_name} - {first_trip.pick_up_date} & {return_trip.pick_up_date}"
        elif notification_type == 'confirmed':
            return f"Round Trip Confirmed: {first_trip.passenger_name} - {first_trip.pick_up_date} & {return_trip.pick_up_date}"
        elif notification_type == 'cancelled':
            return f"Round Trip Cancelled: {first_trip.passenger_name} - {first_trip.pick_up_date} & {return_trip.pick_up_date}"
        elif notification_type == 'status_change':
            return f"Round Trip Update: {first_trip.passenger_name}"
        else:
            return f"Round Trip Update: {first_trip.passenger_name}"

    @staticmethod
    def _get_fallback_round_trip_message(
        first_trip: Booking,
        return_trip: Booking,
        notification_type: str
    ) -> str:
        """Generate fallback HTML message for round trips when template fails."""
        status_text = {
            'new': 'Round Trip Requested - Status: Pending',
            'confirmed': 'Round Trip Confirmed',
            'cancelled': 'Round Trip Cancelled',
        }.get(notification_type, 'Round Trip Updated')

        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px; text-align: center;">
            <h2 style="color: #0f172a;">{status_text}</h2>
            <div style="margin: 20px 0;">
                <p style="color: #64748b; font-size: 12px; font-weight: bold;">FIRST TRIP</p>
                <p style="font-size: 16px; font-weight: bold; color: #0f172a;">{first_trip.pick_up_date} at {first_trip.pick_up_time}</p>
            </div>
            <div style="margin: 20px 0;">
                <p style="color: #64748b; font-size: 12px; font-weight: bold;">RETURN TRIP</p>
                <p style="font-size: 16px; font-weight: bold; color: #0f172a;">{return_trip.pick_up_date} at {return_trip.pick_up_time}</p>
            </div>
            <p style="color: #64748b;">Please log in to your dashboard to view full details.</p>
            <p style="color: #94a3b8; font-size: 12px; margin-top: 30px;">M1 Limousine Service</p>
        </body>
        </html>
        """
    
    @staticmethod
    def _get_template_name(notification_type: str) -> str:
        """Get template file name for notification type."""
        if notification_type == 'reminder':
            return 'emails/booking_reminder.html'
        else:
            return 'emails/booking_notification.html'
    
    @staticmethod
    def _get_fallback_message(booking: Booking, notification_type: str) -> str:
        """Generate fallback HTML message when template fails."""
        status_text = {
            'new': 'Booking Requested - Status: Pending',
            'confirmed': 'Booking Confirmed',
            'cancelled': 'Booking Cancelled',
        }.get(notification_type, 'Booking Updated')

        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px; text-align: center;">
            <h2 style="color: #0f172a;">{status_text}</h2>
            <p style="color: #475569;">Booking #{booking.id}</p>
            <p style="font-size: 18px; font-weight: bold; color: #0f172a;">{booking.pick_up_date} at {booking.pick_up_time}</p>
            <p style="color: #64748b;">Please log in to your dashboard to view full details.</p>
            <p style="color: #94a3b8; font-size: 12px; margin-top: 30px;">M1 Limousine Service</p>
        </body>
        </html>
        """
    
    @staticmethod
    def _try_direct_smtp(recipient: str, subject: str, html_message: str) -> bool:
        """Try sending via direct SMTP connection."""
        try:
            # Set 5 second timeout to prevent hanging
            server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT, timeout=5)
            server.set_debuglevel(0)

            if settings.EMAIL_USE_TLS:
                server.starttls()

            server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
            
            from_email = settings.EMAIL_HOST_USER
            email_message = f"""From: {from_email}
To: {recipient}
MIME-Version: 1.0
Content-type: text/html
Subject: {subject}

{html_message}
"""
            server.sendmail(from_email, [recipient], email_message.encode('utf-8'))
            server.quit()
            
            logger.info("Email sent via direct SMTP")
            return True
            
        except Exception as e:
            logger.error(f"Direct SMTP failed: {e}")
            return False
    
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
    
    @classmethod
    def send_test_email(cls, recipient_email: str) -> dict:
        """Send test email to verify email configuration."""
        import datetime
        
        try:
            subject = "M1 Limo Email System Test"
            html_message = f"""
            <html>
                <body>
                    <h1>Email System Test</h1>
                    <p>This is a test email from the M1 Limo booking system.</p>
                    <p>If you received this, the email system is working correctly.</p>
                    <p>Time: {datetime.datetime.now()}</p>
                </body>
            </html>
            """
            
            success = (
                cls._try_direct_smtp(recipient_email, subject, html_message) or
                cls._try_email_message(recipient_email, subject, html_message) or
                cls._try_send_mail(recipient_email, subject, strip_tags(html_message), html_message)
            )
            
            if success:
                return {
                    'success': True,
                    'message': f'Test email sent successfully to {recipient_email}'
                }
            else:
                return {
                    'success': False,
                    'message': 'All email sending methods failed'
                }
                
        except Exception as e:
            logger.error(f"Test email failed: {e}", exc_info=True)
            return {
                'success': False,
                'message': str(e)
            }

    @classmethod
    def send_driver_notification(cls, booking, driver) -> bool:
        """
        Send driver assignment notification with programmable template support.
        Tries database template first, falls back to file template if unavailable.
        """
        from django.template.loader import render_to_string

        logger.info(f"Sending driver notification to {driver.email} for booking {booking.id}")

        try:
            # Load active database template (NO FALLBACK)
            db_template = cls._load_email_template('driver_notification')
            
            if not db_template:
                logger.warning(f"No active database template found for driver_notification, email NOT sent to {driver.email}")
                return False
            
            try:
                # Build context for database template (string-based variables)
                template_context = cls._build_driver_template_context(booking, driver)
                subject = db_template.render_subject(template_context)
                html_message = db_template.render_html(template_context)
                
                logger.info(f"Using database template for driver notification")
                db_template.increment_sent()
            except Exception as e:
                logger.error(f"Database template rendering error: {e}")
                db_template.increment_failed()
                return False

            # Try all email sending methods
            success = (
                cls._try_direct_smtp(driver.email, subject, html_message) or
                cls._try_email_message(driver.email, subject, html_message) or
                cls._try_send_mail(driver.email, subject, strip_tags(html_message), html_message)
            )

            if success:
                logger.info(f"Driver notification sent successfully to {driver.email}")
            else:
                logger.error(f"Failed to send driver notification to {driver.email}")

            return success

        except Exception as e:
            logger.error(f"Error sending driver notification: {e}", exc_info=True)
            return False

    # ============================================================================
    # UNIFIED TEMPLATE SYSTEM (New)
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
