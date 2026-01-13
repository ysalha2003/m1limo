# services/booking_service.py
from typing import Dict, Any, Optional, List
from django.db import transaction
from django.core.paginator import Paginator
from django.conf import settings
from django.db.models import QuerySet
from django.utils import timezone
from django.core.cache import cache
from django.contrib.auth.models import User
from models import (
    Booking, BookingStop, BookingNotification,
    NotificationRecipient, FrequentPassenger, SystemSettings, BookingHistory
)
import logging

logger = logging.getLogger('services')


class BookingService:
    """Service layer for booking operations."""

    @staticmethod
    def _create_history_entry(
        booking: Booking,
        action: str,
        changed_by: User,
        changes: Optional[Dict] = None,
        change_reason: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> 'BookingHistory':
        """Create a history entry for booking changes"""
        import json
        from django.core.serializers.json import DjangoJSONEncoder

        # Create booking snapshot
        snapshot = {
            'id': booking.id,
            'passenger_name': booking.passenger_name,
            'phone_number': booking.phone_number,
            'passenger_email': booking.passenger_email,
            'pick_up_address': booking.pick_up_address,
            'drop_off_address': booking.drop_off_address,
            'pick_up_date': str(booking.pick_up_date),
            'pick_up_time': str(booking.pick_up_time),
            'vehicle_type': booking.vehicle_type,
            'trip_type': booking.trip_type,
            'number_of_passengers': booking.number_of_passengers,
            'status': booking.status,
            'hours_booked': booking.hours_booked,
            'flight_number': booking.flight_number,
            'notes': booking.notes,
            'booking_reference': booking.booking_reference,
        }

        history = BookingHistory.objects.create(
            booking=booking,
            action=action,
            changed_by=changed_by,
            booking_snapshot=snapshot,
            changes=changes,
            change_reason=change_reason,
            ip_address=ip_address
        )

        logger.info(f"Created history entry: {action} for booking {booking.id} by {changed_by.username}")
        return history

    @staticmethod
    @transaction.atomic
    def create_booking(
        user: User,
        booking_data: Dict[str, Any],
        stops_data: Optional[List[Dict]] = None,
        return_stops_data: Optional[List[Dict]] = None,
        notification_recipients: Optional[List[NotificationRecipient]] = None,
        created_by: Optional[User] = None
    ) -> Booking:
        """
        Create booking with related stops and notifications.
        Round trips create two linked booking records.

        Args:
            user: The user who owns the booking
            created_by: The user who actually created the booking (for audit trail)
        """
        from notification_service import NotificationService

        # If created_by not specified, assume the booking owner created it
        if created_by is None:
            created_by = user

        logger.info(f"Creating new booking for user: {user.username}")

        booking_data['user'] = user
        # Auto-confirm if created by admin, otherwise set to Pending
        if created_by.is_staff:
            booking_data['status'] = 'Confirmed'
        else:
            booking_data['status'] = 'Pending'

        if booking_data.get('trip_type') == 'Hourly':
            booking_data['drop_off_address'] = None

        is_round_trip = booking_data.get('trip_type') == 'Round'

        return_booking_data = None
        if is_round_trip:
            return_booking_data = {
                'passenger_name': booking_data.get('passenger_name'),
                'phone_number': booking_data.get('phone_number'),
                'passenger_email': booking_data.get('passenger_email'),
                'pick_up_address': booking_data.get('return_pickup_address'),
                'drop_off_address': booking_data.get('return_dropoff_address'),
                'pick_up_date': booking_data.get('return_date'),
                'pick_up_time': booking_data.get('return_time'),
                'vehicle_type': booking_data.get('vehicle_type'),
                'trip_type': 'Round',
                'number_of_passengers': booking_data.get('number_of_passengers'),
                'flight_number': booking_data.get('return_flight_number'),
                'notes': booking_data.get('return_special_requests'),
                'user': user,
                'status': 'Confirmed' if created_by.is_staff else 'Pending',
                'is_return_trip': True,
            }

        booking = Booking.objects.create(**booking_data)
        booking._skip_signal_notification = True
        logger.info(f"Created outbound booking ID: {booking.id} with status: {booking.status}")

        # Create history entry for booking creation
        BookingService._create_history_entry(
            booking=booking,
            action='created',
            changed_by=created_by,
            change_reason=f"Booking created by {created_by.username}" + (f" for {user.username}" if created_by != user else "")
        )

        if stops_data:
            for stop_info in stops_data:
                BookingStop.objects.create(
                    booking=booking,
                    address=stop_info['address'],
                    stop_number=stop_info['stop_number'],
                    is_return_stop=False
                )
            logger.info(f"Created {len(stops_data)} outbound stops")

        return_booking = None
        if is_round_trip and return_booking_data:
            return_booking = Booking.objects.create(**return_booking_data, linked_booking=booking)
            return_booking._skip_signal_notification = True
            logger.info(f"Created return booking ID: {return_booking.id} linked to outbound {booking.id}")

            booking.linked_booking = return_booking
            booking.save(update_fields=['linked_booking'])

            if return_stops_data:
                for stop_info in return_stops_data:
                    BookingStop.objects.create(
                        booking=return_booking,
                        address=stop_info['address'],
                        stop_number=stop_info['stop_number'],
                        is_return_stop=False
                    )
                logger.info(f"Created {len(return_stops_data)} return stops")

            if notification_recipients:
                for recipient in notification_recipients:
                    BookingNotification.objects.create(
                        booking=return_booking,
                        recipient=recipient
                    )

        if notification_recipients:
            for recipient in notification_recipients:
                BookingNotification.objects.create(
                    booking=booking,
                    recipient=recipient
                )
            logger.info(f"Linked {len(notification_recipients)} notification recipients")

        cache.delete('dashboard_stats')

        # Send notifications immediately (synchronous for low-traffic systems)
        # For 30 bookings/day, immediate sending is more reliable than background tasks
        notification_type = 'confirmed' if booking.status == 'Confirmed' else 'new'

        if return_booking:
            logger.info(f"Sending unified round-trip {notification_type} notification (First: {booking.id}, Return: {return_booking.id})")
            NotificationService.send_round_trip_notification(booking, return_booking, notification_type)
        else:
            logger.info(f"Sending {notification_type} notification for booking {booking.id}")
            NotificationService.send_notification(booking, notification_type)

        return booking
    
    @staticmethod
    @transaction.atomic
    def update_booking(
        booking: Booking,
        booking_data: Dict[str, Any],
        stops_data: Optional[List[Dict]] = None,
        return_stops_data: Optional[List[Dict]] = None,
        notification_recipients: Optional[List[NotificationRecipient]] = None,
        changed_by: Optional[User] = None
    ) -> Booking:
        """
        Update booking and linked return trip if applicable.
        Reverts status to Pending if critical fields changed by non-admin.
        """
        from notification_service import NotificationService

        logger.info(f"Updating booking ID: {booking.id}")

        original_status = booking.status

        is_outbound_with_return = booking.linked_booking and not booking.is_return_trip

        # Determine who is making the edit
        editor_is_admin = changed_by.is_staff if changed_by else booking.user.is_staff

        # CRITICAL: Fetch original booking from database to detect actual changes
        # The booking object may have form-bound values, so we need DB original
        old_booking = Booking.objects.get(pk=booking.pk)

        # Auto-status logic based on requirements:
        # - Admin edits (for themselves or others) → stay/become Confirmed
        # - User edits on Confirmed booking → revert to Pending
        if editor_is_admin:
            # Admin edits always stay Confirmed (or become Confirmed if was Pending)
            if original_status in ['Pending', 'Confirmed']:
                booking_data['status'] = 'Confirmed'
                logger.info(f"Admin edit: Booking {booking.id} status set to Confirmed")
        else:
            # User editing their own booking
            if original_status == 'Confirmed':
                # Check if any fields were actually changed (compare against DB original)
                any_field_changed = False
                for field in booking_data:
                    if field != 'status':
                        old_value = getattr(old_booking, field, None)
                        new_value = booking_data[field]
                        if old_value != new_value:
                            any_field_changed = True
                            logger.info(f"User edit: Field '{field}' changed from '{old_value}' to '{new_value}'")
                            break

                if any_field_changed:
                    booking_data['status'] = 'Pending'
                    logger.info(f"User edit: Booking {booking.id} reverted to Pending after edit by user {booking.user.username}")

        return_booking_updates = None
        if is_outbound_with_return:
            return_booking_updates = {}
            if 'return_date' in booking_data:
                return_booking_updates['pick_up_date'] = booking_data['return_date']
            if 'return_time' in booking_data:
                return_booking_updates['pick_up_time'] = booking_data['return_time']
            if 'return_pickup_address' in booking_data:
                return_booking_updates['pick_up_address'] = booking_data['return_pickup_address']
            if 'return_dropoff_address' in booking_data:
                return_booking_updates['drop_off_address'] = booking_data['return_dropoff_address']
            if 'return_flight_number' in booking_data:
                return_booking_updates['flight_number'] = booking_data['return_flight_number']
            if 'return_special_requests' in booking_data:
                return_booking_updates['notes'] = booking_data['return_special_requests']

            if 'passenger_name' in booking_data:
                return_booking_updates['passenger_name'] = booking_data['passenger_name']
            if 'phone_number' in booking_data:
                return_booking_updates['phone_number'] = booking_data['phone_number']
            if 'passenger_email' in booking_data:
                return_booking_updates['passenger_email'] = booking_data['passenger_email']
            if 'number_of_passengers' in booking_data:
                return_booking_updates['number_of_passengers'] = booking_data['number_of_passengers']
            if 'vehicle_type' in booking_data:
                return_booking_updates['vehicle_type'] = booking_data['vehicle_type']

            # FIX: Only update linked booking status if it's not cancelled
            # After partial cancellation, the remaining trip should be editable independently
            if 'status' in booking_data:
                linked_booking_obj = booking.linked_booking
                if linked_booking_obj and linked_booking_obj.status not in ['Cancelled', 'Cancelled_Full_Charge']:
                    return_booking_updates['status'] = booking_data['status']
                else:
                    logger.info(f"Skipping status update for linked booking {linked_booking_obj.id if linked_booking_obj else 'None'} - it's cancelled")

        # CRITICAL FIX #3: Validate status transition BEFORE setting field
        if 'status' in booking_data and booking_data['status'] != original_status:
            # Validate the transition is allowed
            booking.validate_status_transition(original_status, booking_data['status'])
            logger.info(f"Validated status transition: {original_status} → {booking_data['status']}")

        # Track field changes for history - old_booking already fetched above
        changes = {}
        logger.info(f"Tracking changes for booking {booking.id}. Fields to check: {list(booking_data.keys())}")

        for field, new_value in booking_data.items():
            old_value = getattr(old_booking, field, None)  # Use old_booking from database
            if old_value != new_value:
                changes[field] = {'old': str(old_value), 'new': str(new_value)}
                logger.debug(f"Change detected - {field}: {old_value} → {new_value}")

        logger.info(f"Detected {len(changes)} changed fields: {list(changes.keys())}")

        # Update booking fields
        for field, value in booking_data.items():
            setattr(booking, field, value)

        booking.save()
        logger.info(f"Updated booking {booking.id}")

        # Create history entry for update
        if changes:
            action = 'status_changed' if 'status' in changes else 'updated'
            user_who_changed = changed_by if changed_by else booking.user
            logger.info(f"Creating history entry with action='{action}' for {len(changes)} changes by {user_who_changed.username}")
            BookingService._create_history_entry(
                booking=booking,
                action=action,
                changed_by=user_who_changed,
                changes=changes,
                change_reason=f"Booking updated by {user_who_changed.username}"
            )
        else:
            logger.warning(f"No changes detected for booking {booking.id} update - no history entry created")

        if stops_data is not None:
            booking.stops.filter(is_return_stop=False).delete()
            for stop_info in stops_data:
                BookingStop.objects.create(
                    booking=booking,
                    address=stop_info['address'],
                    stop_number=stop_info['stop_number'],
                    is_return_stop=False
                )

        if is_outbound_with_return and return_booking_updates:
            linked_booking = booking.linked_booking

            # FIX: Skip updating cancelled linked bookings (partial cancellation independence)
            if linked_booking.status in ['Cancelled', 'Cancelled_Full_Charge']:
                logger.info(f"Skipping update for linked booking {linked_booking.id} - it's cancelled")
            else:
                logger.info(f"Updating linked return booking {linked_booking.id}")

                if 'status' in return_booking_updates:
                    linked_original_status = linked_booking.status
                    if return_booking_updates['status'] != linked_original_status:
                        linked_booking.validate_status_transition(linked_original_status, return_booking_updates['status'])
                        logger.info(f"Validated linked booking status transition: {linked_original_status} → {return_booking_updates['status']}")

                for field, value in return_booking_updates.items():
                    setattr(linked_booking, field, value)

                linked_booking.save()
                logger.info(f"Updated linked return booking {linked_booking.id}")

                if return_stops_data is not None:
                    linked_booking.stops.all().delete()
                    for stop_info in return_stops_data:
                        BookingStop.objects.create(
                            booking=linked_booking,
                            address=stop_info['address'],
                            stop_number=stop_info['stop_number'],
                            is_return_stop=False
                        )

                if notification_recipients is not None:
                    BookingNotification.objects.filter(booking=linked_booking).delete()
                    for recipient in notification_recipients:
                        BookingNotification.objects.create(
                            booking=linked_booking,
                            recipient=recipient
                        )

        if notification_recipients is not None:
            BookingNotification.objects.filter(booking=booking).delete()
            for recipient in notification_recipients:
                BookingNotification.objects.create(
                    booking=booking,
                    recipient=recipient
                )

        cache.delete('dashboard_stats')

        if original_status != booking.status:
            logger.info(f"Status changed from {original_status} to {booking.status}")
            if is_outbound_with_return:
                NotificationService.send_round_trip_notification(
                    booking,
                    booking.linked_booking,
                    'status_change'
                )
            else:
                NotificationService.send_notification(booking, 'status_change', old_status=original_status)

        return booking
    
    @staticmethod
    @transaction.atomic
    def update_booking_status(
        booking: Booking,
        new_status: str,
        admin_comment: Optional[str] = None,
        changed_by: Optional[User] = None,
        reason: Optional[str] = None
    ) -> Booking:
        """
        Update booking status with automatic linked trip updates and 4-hour cancellation policy.
        Uses row locking to prevent race conditions.

        CRITICAL FIX #4: Added reason parameter and 4-hour cancellation policy
        """
        from notification_service import NotificationService

        booking = Booking.objects.select_for_update().get(pk=booking.pk)

        original_status = booking.status

        if original_status == new_status:
            logger.info(f"Booking {booking.id} status already '{new_status}'")
            return booking

        try:
            booking.validate_status_transition(original_status, new_status)
        except Exception as e:
            logger.error(f"Invalid status transition for booking {booking.id}: {e}")
            raise

        logger.info(f"Updating booking {booking.id} status: {original_status} → {new_status}")

        # CRITICAL FIX #4: Apply 4-hour cancellation policy
        if new_status in ['Cancelled', 'Cancelled_Full_Charge']:
            if not reason:
                raise ValueError("Cancellation reason is required")

            # Calculate hours until pickup
            hours_until = booking.hours_until_pickup()

            # Apply policy based on booking status
            # Confirmed bookings: 2-hour policy
            # Pending bookings: 4-hour policy
            if booking.status == 'Confirmed':
                threshold = 2
            else:
                threshold = 4
                
            if hours_until < threshold:
                # Within threshold → Full charge
                booking.status = 'Cancelled_Full_Charge'
                logger.info(f'Cancellation within {threshold} hours ({hours_until:.1f}h) → Full charge')
            else:
                # More than threshold → Free cancellation
                booking.status = 'Cancelled'
                logger.info(f'Cancellation > {threshold} hours ({hours_until:.1f}h) → Free')

            booking.cancellation_reason = reason
        else:
            booking.status = new_status

        if admin_comment:
            booking.admin_comment = admin_comment

        # Mark as admin_reviewed when confirming (PART 1: Cancellation permissions)
        if new_status == 'Confirmed' and changed_by and changed_by.is_staff:
            booking.admin_reviewed = True
            logger.info(f"Booking {booking.id} marked as admin_reviewed")

        booking.save()

        # Create history entry for status change
        BookingService._create_history_entry(
            booking=booking,
            action='status_changed',
            changed_by=changed_by if changed_by else booking.user,
            changes={'status': {'old': original_status, 'new': new_status}},
            change_reason=f"Status changed from {original_status} to {new_status}" + (f" - {admin_comment}" if admin_comment else "")
        )

        send_unified_notification = False
        linked_booking = None

        if booking.linked_booking and not booking.is_return_trip:
            linked_booking = Booking.objects.select_for_update().get(pk=booking.linked_booking.pk)

            if new_status == 'Confirmed' and linked_booking.status == 'Pending':
                logger.info(f"Auto-confirming linked return booking {linked_booking.id}")
                linked_original_status = linked_booking.status
                linked_booking.status = 'Confirmed'
                linked_booking.admin_reviewed = True  # Also mark linked booking as reviewed
                if admin_comment:
                    linked_booking.admin_comment = f"Auto-confirmed with outbound trip. {admin_comment}"
                else:
                    linked_booking.admin_comment = "Auto-confirmed with outbound trip."
                linked_booking.save()
                logger.info(f"Linked return booking {linked_booking.id} confirmed")

                # Create history entry for linked booking
                BookingService._create_history_entry(
                    booking=linked_booking,
                    action='status_changed',
                    changed_by=changed_by if changed_by else booking.user,
                    changes={'status': {'old': linked_original_status, 'new': 'Confirmed'}},
                    change_reason=f"Auto-confirmed with outbound trip #{booking.id}"
                )

                send_unified_notification = True

            elif new_status in ['Cancelled', 'Rejected', 'Cancelled_Full_Charge']:
                logger.info(f"Auto-updating linked return booking {linked_booking.id} to {new_status}")
                linked_original_status = linked_booking.status
                linked_booking.status = new_status
                if not linked_booking.cancellation_reason:
                    linked_booking.cancellation_reason = f"Auto-cancelled: Outbound trip was {new_status.lower()}"
                linked_booking.save()
                logger.info(f"Linked return booking {linked_booking.id} updated to {new_status}")

                # Create history entry for linked booking
                BookingService._create_history_entry(
                    booking=linked_booking,
                    action='status_changed',
                    changed_by=changed_by if changed_by else booking.user,
                    changes={'status': {'old': linked_original_status, 'new': new_status}},
                    change_reason=f"Auto-cancelled: Outbound trip #{booking.id} was {new_status.lower()}"
                )

                send_unified_notification = True

        cache.delete('dashboard_stats')

        notification_map = {
            'Confirmed': 'confirmed',
            'Rejected': 'status_change',
            'Cancelled': 'cancelled',
            'Cancelled_Full_Charge': 'cancelled',
            'Trip_Completed': 'status_change',
        }

        notification_type = notification_map.get(new_status)
        if notification_type:
            if send_unified_notification and linked_booking:
                logger.info(f"Sending unified round-trip {notification_type} notification")
                NotificationService.send_round_trip_notification(
                    booking,
                    linked_booking,
                    notification_type
                )
            else:
                NotificationService.send_notification(booking, notification_type, old_status=original_status)

        return booking
    
    @staticmethod
    def get_dashboard_stats() -> Dict[str, int]:
        """Get dashboard statistics with 5-minute cache.

        Note: Counts include ALL trips. Round trips consist of 2 separate bookings
        (outbound + return), and each is counted individually.
        """
        cache_key = 'dashboard_stats'
        stats = cache.get(cache_key)

        if stats is None:
            today = timezone.now().date()
            # Count ALL bookings - each trip is counted individually
            stats = {
                'total_bookings': Booking.objects.count(),
                'active_bookings': Booking.objects.active().count(),
                'pending_count': Booking.objects.pending().count(),
                'confirmed_count': Booking.objects.confirmed().count(),
                'today_trips': Booking.objects.today().count(),
                'upcoming_trips': Booking.objects.upcoming().count(),
                'completed_trips': Booking.objects.completed().count(),
            }
            cache.set(cache_key, stats, 300)
            logger.debug(f"Dashboard stats cached: {stats}")

        return stats
    
    @staticmethod
    def get_paginated_bookings(
        request,
        queryset: Optional[QuerySet] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Return paginated and filtered bookings with optimized queries."""
        bookings = queryset if queryset is not None else Booking.objects.all()

        if filters:
            status_filter = filters.get('status')
            date_range = filters.get('date_range')
            vehicle_type = filters.get('vehicle_type')
            trip_type = filters.get('trip_type')
            user_filter = filters.get('user')
            search_query = filters.get('search')
            
            if status_filter:
                bookings = bookings.filter(status=status_filter)
            
            if date_range:
                today = timezone.now().date()
                if date_range == 'today':
                    bookings = bookings.filter(pick_up_date=today)
                elif date_range == 'tomorrow':
                    tomorrow = today + timezone.timedelta(days=1)
                    bookings = bookings.filter(pick_up_date=tomorrow)
                elif date_range == 'week':
                    week_later = today + timezone.timedelta(days=7)
                    bookings = bookings.filter(
                        pick_up_date__gte=today,
                        pick_up_date__lte=week_later
                    )
                elif date_range == 'month':
                    month_later = today + timezone.timedelta(days=30)
                    bookings = bookings.filter(
                        pick_up_date__gte=today,
                        pick_up_date__lte=month_later
                    )
                elif date_range == 'upcoming':
                    bookings = bookings.filter(pick_up_date__gte=today)
                elif date_range == 'past':
                    bookings = bookings.filter(pick_up_date__lt=today)
            
            if vehicle_type:
                bookings = bookings.filter(vehicle_type=vehicle_type)
            
            if trip_type:
                bookings = bookings.filter(trip_type=trip_type)
            
            if user_filter:
                bookings = bookings.filter(user_id=user_filter)
            
            if search_query:
                bookings = bookings.search(search_query)

        optimized_bookings = bookings.select_related('user').prefetch_related('stops', 'notifications')

        paginator = Paginator(optimized_bookings, settings.ITEMS_PER_PAGE)
        page_obj = paginator.get_page(request.GET.get('page'))
        
        return {
            'page_obj': page_obj,
            'bookings': page_obj.object_list,
            'paginator': paginator,
            'filters': filters or {},
        }
    
    @staticmethod
    def get_next_pickup(user: Optional[User] = None) -> Optional[Booking]:
        """Get next upcoming confirmed pickup for user or system-wide."""
        now = timezone.now()
        query = Booking.objects.confirmed()
        
        if user and not user.is_staff:
            query = query.filter(user=user)

        next_booking = query.filter(
            pick_up_date__gte=now.date()
        ).order_by('pick_up_date', 'pick_up_time').first()
        
        return next_booking
    
    @staticmethod
    @transaction.atomic
    def request_cancellation(
        booking: Booking,
        cancellation_reason: str
    ) -> Booking:
        """
        Cancel booking with 4-hour policy enforcement.
        Automatically cancels linked return trip for round trips.
        """
        from notification_service import NotificationService
        from django.core.exceptions import ValidationError

        logger.info(f"Cancellation requested for booking {booking.id}")

        can_cancel, will_charge, hours_until = booking.can_cancel()

        if not can_cancel:
            raise ValidationError("Cannot cancel past bookings")

        booking.cancellation_reason = cancellation_reason

        if will_charge:
            booking.status = 'Cancelled_Full_Charge'
            logger.info(f"Booking {booking.id} cancelled with full charge ({hours_until:.1f} hours notice)")
        else:
            booking.status = 'Cancelled'
            logger.info(f"Booking {booking.id} cancelled free of charge ({hours_until:.1f} hours notice)")

        booking.save()

        if booking.linked_booking and not booking.is_return_trip:
            linked_booking = booking.linked_booking
            logger.info(f"Auto-cancelling linked return booking {linked_booking.id}")

            _, linked_will_charge, linked_hours = linked_booking.can_cancel()

            linked_booking.status = 'Cancelled_Full_Charge' if linked_will_charge else 'Cancelled'
            linked_booking.cancellation_reason = f"Auto-cancelled: Outbound trip was cancelled. Original reason: {cancellation_reason}"
            linked_booking.save()
            logger.info(f"Linked return booking {linked_booking.id} cancelled (charge: {linked_will_charge})")

            NotificationService.send_notification(linked_booking, 'cancelled')

        cache.delete('dashboard_stats')

        NotificationService.send_notification(booking, 'cancelled')

        return booking

    @staticmethod
    @transaction.atomic
    def cancel_entire_booking(
        booking: Booking,
        cancellation_reason: str = ""
    ) -> tuple:
        """
        Cancel entire round trip or single trip.
        For round trips, if either trip is within 4 hours, both are charged.
        """
        from notification_service import NotificationService
        from django.core.exceptions import ValidationError

        logger.info(f"[CANCEL ENTIRE BOOKING] Starting for booking {booking.id}")

        if booking.is_return_trip:
            return_trip = booking
            first_trip = booking.linked_booking
        else:
            first_trip = booking
            return_trip = booking.linked_booking

        can_cancel, will_charge, hours_until = first_trip.can_cancel()

        if not can_cancel:
            raise ValidationError("Cannot cancel past trips")

        if return_trip:
            can_cancel_return, will_charge_return, hours_return = return_trip.can_cancel()

            should_charge_both = will_charge or will_charge_return

            if not can_cancel_return:
                return_trip.status = 'Cancelled'
            else:
                return_trip.status = 'Cancelled_Full_Charge' if should_charge_both else 'Cancelled'

            first_trip.status = 'Cancelled_Full_Charge' if should_charge_both else 'Cancelled'

            return_trip.cancellation_reason = cancellation_reason
            return_trip.save()
            logger.info(f"Return trip {return_trip.id} cancelled (charge: {should_charge_both}, first: {hours_until:.1f}hrs, return: {hours_return:.1f}hrs)")
        else:
            first_trip.status = 'Cancelled_Full_Charge' if will_charge else 'Cancelled'

        first_trip.cancellation_reason = cancellation_reason
        first_trip.save()
        logger.info(f"First trip {first_trip.id} cancelled (charge: {first_trip.status == 'Cancelled_Full_Charge'})")

        # Create history entry for first trip cancellation
        from models import BookingHistory
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        # Try to get the user who initiated cancellation (will be set by caller)
        changed_by = getattr(first_trip, '_cancelled_by', None)
        
        changes = {
            'status': {
                'old': 'Pending' if not hasattr(first_trip, '_old_status') else first_trip._old_status,
                'new': first_trip.status
            },
            'cancellation_reason': {
                'old': None,
                'new': cancellation_reason if cancellation_reason else '(No reason provided)'
            },
            'charge_applied': {
                'old': None,
                'new': 'Full charge' if first_trip.status == 'Cancelled_Full_Charge' else 'No charge'
            },
            'hours_until_pickup': {
                'old': None,
                'new': f'{hours_until:.1f} hours'
            }
        }
        
        BookingHistory.objects.create(
            booking=first_trip,
            action='cancelled',
            changed_by=changed_by if changed_by else first_trip.user,
            booking_snapshot={},
            changes=changes,
            change_reason=f"Trip cancelled by {changed_by.username if changed_by else first_trip.user.username}. Reason: {cancellation_reason if cancellation_reason else 'Not provided'}. {'Full charge applied' if first_trip.status == 'Cancelled_Full_Charge' else 'No charge'} ({hours_until:.1f}h notice)."
        )
        
        # Create history entry for return trip if exists
        if return_trip:
            return_changes = {
                'status': {
                    'old': 'Pending' if not hasattr(return_trip, '_old_status') else return_trip._old_status,
                    'new': return_trip.status
                },
                'cancellation_reason': {
                    'old': None,
                    'new': cancellation_reason if cancellation_reason else '(No reason provided)'
                },
                'charge_applied': {
                    'old': None,
                    'new': 'Full charge' if return_trip.status == 'Cancelled_Full_Charge' else 'No charge'
                },
                'hours_until_pickup': {
                    'old': None,
                    'new': f'{hours_return:.1f} hours'
                }
            }
            
            BookingHistory.objects.create(
                booking=return_trip,
                action='cancelled',
                changed_by=changed_by if changed_by else return_trip.user,
                booking_snapshot={},
                changes=return_changes,
                change_reason=f"Return trip cancelled as part of round trip cancellation by {changed_by.username if changed_by else return_trip.user.username}. Reason: {cancellation_reason if cancellation_reason else 'Not provided'}. {'Full charge applied' if return_trip.status == 'Cancelled_Full_Charge' else 'No charge'} ({hours_return:.1f}h notice)."
            )

        cache.delete('dashboard_stats')

        if return_trip:
            logger.info(f"Sending unified round-trip cancellation notification")
            NotificationService.send_round_trip_notification(first_trip, return_trip, 'cancelled')
        else:
            logger.info(f"Sending single-trip cancellation notification")
            NotificationService.send_notification(first_trip, 'cancelled')

        return (first_trip, return_trip)

    @staticmethod
    @transaction.atomic
    def cancel_single_trip(
        booking: Booking,
        cancellation_reason: str = ""
    ) -> Booking:
        """
        Cancel single trip while keeping linked trip active.
        Charges for both trips if either is within 4 hours.
        """
        from notification_service import NotificationService
        from django.core.exceptions import ValidationError

        logger.info(f"[CANCEL SINGLE TRIP] Cancelling booking {booking.id} only")

        can_cancel, will_charge, hours_until = booking.can_cancel()

        if not can_cancel:
            raise ValidationError("Cannot cancel past trips")

        if booking.linked_booking:
            _, linked_will_charge, linked_hours = booking.linked_booking.can_cancel()

            if will_charge or linked_will_charge:
                booking.status = 'Cancelled_Full_Charge'
                logger.info(
                    f"Booking {booking.id} charged (this trip: {hours_until:.1f}hrs, "
                    f"linked trip: {linked_hours:.1f}hrs - at least one within 4hrs)"
                )
            else:
                booking.status = 'Cancelled'
                logger.info(f"Booking {booking.id} cancelled free (both trips >4hrs away)")
        else:
            booking.status = 'Cancelled_Full_Charge' if will_charge else 'Cancelled'

        booking.cancellation_reason = cancellation_reason
        booking.save()

        logger.info(f"Booking {booking.id} cancelled individually (charge: {booking.status == 'Cancelled_Full_Charge'})")

        # Create history entry for single trip cancellation
        from models import BookingHistory
        
        # Try to get the user who initiated cancellation (will be set by caller)
        changed_by = getattr(booking, '_cancelled_by', None)
        
        linked_hours_str = f'{linked_hours:.1f} hours' if booking.linked_booking else 'N/A'
        
        changes = {
            'status': {
                'old': 'Pending' if not hasattr(booking, '_old_status') else booking._old_status,
                'new': booking.status
            },
            'cancellation_reason': {
                'old': None,
                'new': cancellation_reason if cancellation_reason else '(No reason provided)'
            },
            'charge_applied': {
                'old': None,
                'new': 'Full charge' if booking.status == 'Cancelled_Full_Charge' else 'No charge'
            },
            'hours_until_pickup': {
                'old': None,
                'new': f'{hours_until:.1f} hours (Linked trip: {linked_hours_str})' if booking.linked_booking else f'{hours_until:.1f} hours'
            }
        }
        
        BookingHistory.objects.create(
            booking=booking,
            action='cancelled',
            changed_by=changed_by if changed_by else booking.user,
            booking_snapshot={},
            changes=changes,
            change_reason=f"Single trip cancelled by {changed_by.username if changed_by else booking.user.username}. Reason: {cancellation_reason if cancellation_reason else 'Not provided'}. {'Full charge applied' if booking.status == 'Cancelled_Full_Charge' else 'No charge'} ({hours_until:.1f}h notice). Linked trip remains active." if booking.linked_booking else f"Trip cancelled by {changed_by.username if changed_by else booking.user.username}. Reason: {cancellation_reason if cancellation_reason else 'Not provided'}. {'Full charge applied' if booking.status == 'Cancelled_Full_Charge' else 'No charge'} ({hours_until:.1f}h notice)."
        )

        cache.delete('dashboard_stats')

        NotificationService.send_notification(booking, 'cancelled')

        return booking

    @staticmethod
    @transaction.atomic
    def delete_booking(booking: Booking) -> None:
        """
        Soft delete booking by setting status to Cancelled.
        Auto-cancels linked return trip.
        """
        logger.info(f"Deleting booking {booking.id}")

        booking.status = 'Cancelled'
        booking.save()

        if booking.linked_booking and not booking.is_return_trip:
            linked_booking = booking.linked_booking
            logger.info(f"Auto-cancelling linked return booking {linked_booking.id}")
            linked_booking.status = 'Cancelled'
            linked_booking.cancellation_reason = f"Auto-cancelled: Outbound trip (Booking #{booking.id}) was cancelled"
            linked_booking.save()
            logger.info(f"Linked return booking {linked_booking.id} cancelled")

        cache.delete('dashboard_stats')
    
    @staticmethod
    def can_user_edit_booking(user: User, booking: Booking) -> tuple[bool, str]:
        """
        Check if user can edit booking based on requirements:
        - Admin can edit most bookings but NOT cancelled trips
        - Users can only edit Pending or Confirmed bookings
        - Users cannot edit within 2 hours of pickup
        - Users cannot edit if pickup time has passed
        - Users cannot edit terminal status bookings (Cancelled, Rejected, etc.)
        """
        from datetime import datetime, timedelta
        from django.utils import timezone

        # Cannot edit cancelled bookings (applies to both admin and users)
        if booking.status in ['Cancelled', 'Cancelled_Full_Charge']:
            return (False, f"Cannot edit {booking.get_status_display()} bookings.")

        # Admin can edit all non-cancelled bookings
        if user.is_staff:
            return (True, "")

        # User must own the booking
        if booking.user != user:
            return (False, "You don't have permission to edit this booking.")

        # Cannot edit terminal status bookings
        if booking.is_terminal_status:
            return (False, f"Cannot edit {booking.get_status_display()} bookings.")

        # Only allow editing Pending or Confirmed bookings
        if booking.status not in ['Pending', 'Confirmed']:
            return (False, f"Cannot edit bookings with status: {booking.get_status_display()}")

        # Check pickup time
        pickup_datetime = datetime.combine(booking.pick_up_date, booking.pick_up_time)
        if timezone.is_naive(pickup_datetime):
            pickup_datetime = timezone.make_aware(
                pickup_datetime,
                timezone=timezone.get_current_timezone()
            )

        now = timezone.now()
        time_until_pickup = pickup_datetime - now
        hours_until = time_until_pickup.total_seconds() / 3600

        # Cannot edit if pickup has passed
        if hours_until <= 0:
            return (False, "Cannot edit bookings where pickup time has passed.")

        # Cannot edit within 2 hours of pickup
        if hours_until <= 2:
            return (False,
                    f"Cannot edit within 2 hours of pickup (currently {booking.time_until_pickup_formatted} away). "
                    "Please contact us for urgent changes.")

        return (True, "")
    
    @staticmethod
    def get_user_bookings(user: User, include_past: bool = False) -> QuerySet:
        """Get user's bookings with option to exclude past bookings."""
        bookings = Booking.objects.filter(user=user)
        
        if not include_past:
            bookings = bookings.upcoming()
        
        return bookings.with_related()
