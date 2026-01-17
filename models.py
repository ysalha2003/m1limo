# bookings/models.py
from django.db import models, transaction
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class UserProfile(models.Model):
    """Extended user profile with contact info and notification preferences"""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="User's contact phone number"
    )
    company_name = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="User's company name (optional)"
    )

    receive_booking_confirmations = models.BooleanField(
        default=True,
        help_text="Receive emails when bookings are confirmed"
    )
    receive_status_updates = models.BooleanField(
        default=True,
        help_text="Receive emails when booking status changes"
    )
    receive_pickup_reminders = models.BooleanField(
        default=True,
        help_text="Receive reminder emails before pickup"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'bookings'
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
        indexes = [
            models.Index(fields=['user']),
        ]

    def __str__(self):
        return f"Profile for {self.user.username}"


class SystemSettings(models.Model):
    """System-wide configuration using singleton pattern"""
    allow_confirmed_edits = models.BooleanField(
        default=False,
        help_text="Allow users to edit bookings after confirmation"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'bookings'
        verbose_name = 'System Settings'
        verbose_name_plural = 'System Settings'

    def save(self, *args, **kwargs):
        """Enforce singleton by preventing creation of multiple instances"""
        if not self.pk and SystemSettings.objects.exists():
            return
        return super().save(*args, **kwargs)

    @classmethod
    def get_settings(cls):
        """Retrieve or create the single settings instance"""
        settings = cls.objects.first()
        if not settings:
            settings = cls.objects.create()
        return settings
    
    def __str__(self):
        return "System Settings"


class BookingPermission(models.Model):
    """User-specific booking permissions"""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='booking_permission'
    )
    can_edit_confirmed = models.BooleanField(
        default=False,
        help_text="Allow this user to edit confirmed bookings"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'bookings'
        verbose_name = 'Booking Permission'
        verbose_name_plural = 'Booking Permissions'
        indexes = [
            models.Index(fields=['user']),
        ]

    def __str__(self):
        return f"{self.user.username} - {'Can' if self.can_edit_confirmed else 'Cannot'} edit confirmed"


class FrequentPassenger(models.Model):
    """Frequently used passenger profiles"""

    VEHICLE_CHOICES = [
        ("Sedan", "Sedan"),
        ("SUV", "SUV"),
        ("Sprinter Van", "Sprinter Van"),
        ("Others", "Others"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='frequent_passengers')
    name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    preferred_vehicle_type = models.CharField(
        max_length=20,
        choices=VEHICLE_CHOICES,
        blank=True,
        null=True,
        help_text="Preferred vehicle type for this passenger"
    )
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'bookings'
        ordering = ['name']
        unique_together = ['user', 'name', 'phone_number']
        indexes = [
            models.Index(fields=['user']),
        ]

    def __str__(self):
        return f"{self.name} ({self.user.username})"


class BookingManager(models.Manager):
    """Custom manager providing optimized booking queries and filters"""

    def by_status(self, status):
        return self.filter(status=status)

    def active(self):
        """Exclude bookings in terminal states"""
        terminal_statuses = ['Rejected', 'Cancelled', 'Cancelled_Full_Charge',
                           'Customer_No_Show', 'Trip_Not_Covered', 'Trip_Completed']
        return self.exclude(status__in=terminal_statuses)

    def completed(self):
        return self.filter(status='Trip_Completed')

    def pending(self):
        return self.filter(status='Pending')

    def confirmed(self):
        return self.filter(status='Confirmed')

    def upcoming(self):
        """Filter bookings scheduled for today or future dates"""
        today = timezone.now().date()
        return self.filter(pick_up_date__gte=today)

    def past(self):
        """Filter bookings with pickup date before today"""
        today = timezone.now().date()
        return self.filter(pick_up_date__lt=today)

    def today(self):
        """Filter bookings scheduled for today only"""
        today = timezone.now().date()
        return self.filter(pick_up_date=today)

    def search(self, query):
        """Search bookings by passenger, contact, or address"""
        return self.filter(
            models.Q(passenger_name__icontains=query) |
            models.Q(phone_number__icontains=query) |
            models.Q(pick_up_address__icontains=query) |
            models.Q(drop_off_address__icontains=query) |
            models.Q(user__username__icontains=query)
        )

    def with_related(self):
        """Optimize queries by prefetching related objects"""
        return self.select_related('user').prefetch_related('stops', 'notifications')


class Booking(models.Model):
    """Core booking model with trip details and status management"""

    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Confirmed", "Confirmed"),
        ("Cancelled", "Cancelled"),
        ("Cancelled_Full_Charge", "Cancelled (Full Charge)"),
        ("Customer_No_Show", "Customer No-Show"),
        ("Trip_Not_Covered", "Trip Not Covered"),
        ("Trip_Completed", "Trip Completed"),
    ]

    VALID_TRANSITIONS = {
        'Pending': ['Confirmed', 'Cancelled', 'Trip_Not_Covered'],
        'Confirmed': ['Cancelled', 'Cancelled_Full_Charge', 'Customer_No_Show',
                     'Trip_Not_Covered', 'Trip_Completed', 'Pending'],
        'Cancelled': [],
        'Cancelled_Full_Charge': [],
        'Customer_No_Show': [],
        'Trip_Not_Covered': [],
        'Trip_Completed': []
    }

    VEHICLE_CHOICES = [
        ("Sedan", "Sedan"),
        ("SUV", "SUV"),
        ("Sprinter Van", "Sprinter Van"),
        ("Others", "Others"),
    ]

    TRIP_TYPE_CHOICES = [
        ("Point", "Point-to-Point"),
        ("Round", "Round Trip"),
        ("Hourly", "Hourly"),
    ]

    VEHICLE_CAPACITY = {
        "Sedan": 2,
        "SUV": 6,
        "Sprinter Van": 12,
    }

    booking_reference = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        null=True,
        help_text="Unique booking reference number"
    )

    passenger_name = models.CharField(max_length=255, help_text="Full name of passenger")
    phone_number = models.CharField(max_length=20, null=False, blank=False, help_text="Passenger phone number for contact")
    passenger_email = models.EmailField(null=False, blank=False, help_text="Passenger email for communication and notifications")

    pick_up_address = models.CharField(max_length=255)
    drop_off_address = models.CharField(max_length=255, blank=True, null=True)
    pick_up_date = models.DateField()
    pick_up_time = models.TimeField()

    # Legacy return trip fields - kept for backward compatibility
    return_date = models.DateField(null=True, blank=True)
    return_time = models.TimeField(null=True, blank=True)
    return_pickup_address = models.CharField(max_length=255, blank=True, null=True)
    return_dropoff_address = models.CharField(max_length=255, blank=True, null=True)
    return_flight_number = models.CharField(max_length=50, blank=True, null=True)
    return_special_requests = models.TextField(blank=True, null=True)
    return_admin_response = models.TextField(blank=True, null=True)
    return_processed = models.BooleanField(default=False)

    # Round trip linking - links outbound and return legs
    is_return_trip = models.BooleanField(
        default=False,
        help_text="True if this booking is the return leg of a round trip"
    )
    linked_booking = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='linked_trips',
        help_text="For round trips, links outbound and return bookings together"
    )

    vehicle_type = models.CharField(max_length=20, choices=VEHICLE_CHOICES)
    trip_type = models.CharField(max_length=10, choices=TRIP_TYPE_CHOICES)
    hours_booked = models.PositiveIntegerField(null=True, blank=True)

    number_of_passengers = models.PositiveIntegerField(default=1)
    flight_number = models.CharField(max_length=50, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default="Pending", db_index=True)
    admin_reviewed = models.BooleanField(
        default=False,
        help_text="True if admin has reviewed/confirmed this booking"
    )
    admin_comment = models.TextField(blank=True, null=True, help_text="Internal admin notes (not visible to customer)")
    cancellation_reason = models.TextField(blank=True, null=True)

    customer_communication = models.TextField(
        blank=True,
        null=True,
        help_text="Admin response to customer special requests (visible to customer)"
    )
    communication_sent_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Timestamp when customer communication was sent"
    )

    # Notification preferences
    send_passenger_notifications = models.BooleanField(
        default=True,
        help_text="Send booking confirmations and updates to passenger email"
    )
    additional_recipients = models.TextField(
        blank=True,
        null=True,
        help_text="Additional email addresses (comma-separated) to receive notifications"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = BookingManager()

    class Meta:
        app_label = 'bookings'
        ordering = ['-pick_up_date', '-pick_up_time']
        indexes = [
            models.Index(fields=['status', 'pick_up_date']),  # Dashboard filtering
            models.Index(fields=['user', 'status']),  # User bookings by status
            models.Index(fields=['user', 'pick_up_date']),  # User bookings by date
            models.Index(fields=['status']),  # Status filtering
            models.Index(fields=['pick_up_date']),  # Date range queries
            models.Index(fields=['created_at']),  # Recent bookings
            models.Index(fields=['booking_reference']),  # Lookup by reference
            models.Index(fields=['pick_up_date', 'status']),  # Date + status combined
        ]

    def __str__(self):
        return f"{self.passenger_name} - {self.pick_up_date} {self.pick_up_time}"

    @property
    def status_color(self):
        """Return Tailwind CSS classes for status badge"""
        colors = {
            'Pending': 'bg-yellow-100 text-yellow-800',
            'Confirmed': 'bg-green-100 text-green-800',
            'Rejected': 'bg-red-100 text-red-800',
            'Cancelled': 'bg-gray-100 text-gray-800',
            'Cancelled_Full_Charge': 'bg-orange-100 text-orange-800',
            'Customer_No_Show': 'bg-purple-100 text-purple-800',
            'Trip_Not_Covered': 'bg-pink-100 text-pink-800',
            'Trip_Completed': 'bg-blue-100 text-blue-800',
        }
        return colors.get(self.status, 'bg-gray-100 text-gray-800')

    @property
    def is_past(self):
        """Check if pickup date has passed"""
        return self.pick_up_date < timezone.now().date()

    @property
    def is_upcoming(self):
        """Check if pickup is in the future"""
        return self.pick_up_date >= timezone.now().date()

    @property
    def trip_label(self):
        """Display 'Round Trip' label for linked bookings"""
        if self.is_return_trip or (self.linked_booking and not self.is_return_trip):
            return "Round Trip"
        else:
            return None

    @property
    def is_terminal_status(self):
        """True if booking is in a final non-editable state"""
        return self.status in ['Rejected', 'Cancelled', 'Cancelled_Full_Charge',
                              'Customer_No_Show', 'Trip_Not_Covered', 'Trip_Completed']

    @property
    def hours_until_pickup(self):
        """
        Calculate hours until pickup (negative for past bookings).
        Uses application timezone for accurate calculations.
        """
        from datetime import datetime

        pickup_datetime = datetime.combine(self.pick_up_date, self.pick_up_time)

        if timezone.is_naive(pickup_datetime):
            pickup_datetime = timezone.make_aware(
                pickup_datetime,
                timezone=timezone.get_current_timezone()
            )

        now = timezone.now()
        time_until_pickup = pickup_datetime - now
        return time_until_pickup.total_seconds() / 3600

    @property
    def time_until_pickup_formatted(self):
        """Format time until pickup as 'Xd Yh Zm' (e.g., '5d 20h 30m', '2h 30m', '-1d 5h 15m')"""
        hours = self.hours_until_pickup
        is_negative = hours < 0
        total_minutes = abs(int(hours * 60))

        days = total_minutes // (60 * 24)
        remaining_minutes = total_minutes % (60 * 24)
        h = remaining_minutes // 60
        m = remaining_minutes % 60

        parts = []
        if days > 0:
            parts.append(f"{days}d")
        if h > 0 or days > 0:  # Show hours if there are days, or if hours > 0
            parts.append(f"{h}h")
        if m > 0 or (days == 0 and h == 0):  # Always show minutes if nothing else
            parts.append(f"{m}m")

        formatted = " ".join(parts)
        return f"-{formatted}" if is_negative else formatted

    def can_cancel(self):
        """
        Determine cancellation eligibility based on policy:
        - Confirmed bookings: 2-hour policy (full charge within 2 hours)
        - Pending bookings: 4-hour policy (full charge within 4 hours)
        Returns: (can_cancel: bool, will_charge: bool, hours_until_pickup: float)
        """
        hours_until_pickup = self.hours_until_pickup

        can_cancel = hours_until_pickup > 0
        
        # Apply different policies based on booking status
        if self.status == 'Confirmed':
            # Confirmed bookings: 2-hour policy
            will_charge = hours_until_pickup <= 2 and hours_until_pickup > 0
        else:
            # Pending bookings: 4-hour policy
            will_charge = hours_until_pickup <= 4 and hours_until_pickup > 0

        return (can_cancel, will_charge, hours_until_pickup)

    def can_cancel_formatted(self):
        """
        Same as can_cancel() but returns formatted time string.
        Returns: (can_cancel: bool, will_charge: bool, time_str: str)
        """
        can_cancel, will_charge, _ = self.can_cancel()
        return (can_cancel, will_charge, self.time_until_pickup_formatted)

    @property
    def is_past_trip(self):
        """
        Check if the trip is in the past (5+ hours after scheduled pickup).
        Past trips should be grayed out and only allow Rebook action.
        """
        hours_until = self.hours_until_pickup
        return hours_until < -5  # 5 hours after pickup time has passed

    def has_unviewed_changes(self, user):
        """
        Check if booking has been updated since user last viewed it.
        Returns True if there are unviewed changes (status updates, admin comments, etc.)
        """
        if not user or not user.is_authenticated:
            return False

        try:
            viewed_record = self.viewed_by_users.filter(user=user).first()
            if not viewed_record:
                # Never viewed before - show notification for non-Pending bookings
                return self.status != 'Pending'

            # Check if booking was updated after last view
            return self.updated_at > viewed_record.viewed_at
        except Exception:
            return False

    def validate_status_transition(self, old_status: str, new_status: str):
        """Ensure status changes follow valid transition rules"""
        if old_status == new_status:
            return

        valid_transitions = self.VALID_TRANSITIONS.get(old_status, [])
        if new_status not in valid_transitions:
            raise ValidationError(
                f"Cannot transition from '{old_status}' to '{new_status}'. "
                f"Valid transitions: {', '.join(valid_transitions) if valid_transitions else 'None'}"
            )

    def validate_vehicle_capacity(self):
        """Ensure passenger count doesn't exceed vehicle capacity"""
        if self.vehicle_type in self.VEHICLE_CAPACITY:
            max_capacity = self.VEHICLE_CAPACITY[self.vehicle_type]
            if self.number_of_passengers > max_capacity:
                raise ValidationError({
                    'number_of_passengers': f"{self.vehicle_type} can accommodate maximum {max_capacity} passengers."
                })

    def validate_hourly_booking(self):
        """Enforce 3-hour minimum for hourly service. Drop-off address automatically cleared."""
        if self.trip_type == 'Hourly':
            if not self.hours_booked or self.hours_booked < 3:
                raise ValidationError({
                    'hours_booked': 'Hourly service requires minimum 3 hours.'
                })
            # Auto-clear drop_off_address for hourly service instead of raising error
            if self.drop_off_address:
                self.drop_off_address = None

    def validate_point_to_point(self):
        """Require drop-off address for point-to-point trips"""
        if self.trip_type == 'Point' and not self.drop_off_address:
            raise ValidationError({
                'drop_off_address': 'Drop-off address required for point-to-point trips.'
            })

    def clean(self):
        """Run all model-level validation checks"""
        # Both phone and email are now required at field level (not blank, not null)
        
        # CRITICAL FIX #5: Validate past date bookings
        # Skip validation for existing bookings being marked as completed or cancelled
        is_new = self._state.adding
        skip_past_date_validation = False

        if not is_new:
            # Allow past dates when marking as completed, cancelled, confirmed, or other final statuses
            # This allows admins to update status on past bookings
            if self.status in ['Trip_Completed', 'Cancelled', 'Cancelled_Full_Charge', 
                               'Customer_No_Show', 'Trip_Not_Covered', 'Confirmed']:
                skip_past_date_validation = True

        if self.pick_up_date and not skip_past_date_validation:
            from django.utils import timezone
            from datetime import datetime

            today = timezone.now().date()

            if self.pick_up_date < today:
                raise ValidationError({
                    'pick_up_date': f'Pickup date cannot be in the past. Please select {today} or later.'
                })

            # If pickup is today, validate time hasn't passed (also skip if handling past bookings)
            if self.pick_up_date == today and self.pick_up_time and not skip_past_date_validation:
                now = timezone.now()
                pickup_datetime = timezone.make_aware(
                    datetime.combine(self.pick_up_date, self.pick_up_time)
                )

                if pickup_datetime < now:
                    raise ValidationError({
                        'pick_up_time': f'Pickup time has already passed. Current time: {now.strftime("%H:%M")}'
                    })

        self.validate_vehicle_capacity()
        self.validate_hourly_booking()
        self.validate_point_to_point()

        # Only validate return trip fields for outbound round trips (not for the return leg itself)
        if self.trip_type == 'Round' and not self.is_return_trip:
            if not self.return_date or not self.return_time:
                raise ValidationError({
                    'return_date': 'Return date and time required for round trips.',
                    'return_time': 'Return date and time required for round trips.'
                })
            if not self.return_pickup_address or not self.return_dropoff_address:
                raise ValidationError({
                    'return_pickup_address': 'Return addresses required for round trips.',
                    'return_dropoff_address': 'Return addresses required for round trips.'
                })

        if self.vehicle_type == 'Others' and not self.notes:
            raise ValidationError({
                'notes': 'Please specify vehicle requirements for "Others" selection.'
            })

    def generate_booking_reference(self):
        """
        Generate unique booking reference: M1-YYMMDD-XX (e.g., M1-251224-A5)
        Uses retry limit and UUID fallback to prevent infinite loops.
        """
        import random
        import string
        import uuid
        from datetime import datetime

        date_part = datetime.now().strftime('%y%m%d')
        MAX_ATTEMPTS = 10

        for attempt in range(MAX_ATTEMPTS):
            random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=2))
            reference = f"M1-{date_part}-{random_part}"

            if not Booking.objects.filter(booking_reference=reference).exists():
                if attempt > 0:
                    logger.info(f"Generated booking reference after {attempt + 1} attempts: {reference}")
                return reference

        # UUID fallback for high-volume days
        uuid_part = uuid.uuid4().hex[:2].upper()
        reference = f"M1-{date_part}-{uuid_part}"

        logger.warning(
            f"Booking reference generation exhausted {MAX_ATTEMPTS} attempts. "
            f"Using UUID-based reference: {reference}. "
            f"This may indicate high booking volume for date {date_part}."
        )

        return reference

    def save(self, *args, **kwargs):
        """Generate booking reference and validate status transitions before saving"""
        is_new = self._state.adding

        if is_new and not self.booking_reference:
            self.booking_reference = self.generate_booking_reference()

        if not is_new:
            try:
                old_status = Booking.objects.values_list('status', flat=True).get(pk=self.pk)
                if old_status != self.status:
                    self.validate_status_transition(old_status, self.status)
            except Booking.DoesNotExist:
                pass

        self.full_clean()
        super().save(*args, **kwargs)


class BookingStop(models.Model):
    """Intermediate stops for bookings"""
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='stops')
    address = models.CharField(max_length=255)
    stop_number = models.PositiveIntegerField()
    is_return_stop = models.BooleanField(default=False)

    class Meta:
        app_label = 'bookings'
        ordering = ['is_return_stop', 'stop_number']
        verbose_name = 'Booking Stop'
        verbose_name_plural = 'Booking Stops'
        unique_together = [['booking', 'stop_number', 'is_return_stop']]
        indexes = [
            models.Index(fields=['booking']),
        ]

    def __str__(self):
        trip_type = "Return" if self.is_return_stop else "Outbound"
        return f"{trip_type} Stop {self.stop_number} - {self.booking.passenger_name}"


class NotificationRecipient(models.Model):
    """Admin email recipients for booking notifications with granular preferences"""
    name = models.CharField(max_length=100)
    email = models.EmailField()
    is_active = models.BooleanField(default=True)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notification_recipient"
    )

    notify_new = models.BooleanField(default=True)
    notify_confirmed = models.BooleanField(default=True)
    notify_cancelled = models.BooleanField(default=True)
    notify_status_changes = models.BooleanField(
        default=True,
        help_text="Receive emails for booking status changes"
    )
    notify_reminders = models.BooleanField(
        default=True,
        help_text="Receive pickup reminder emails"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'bookings'
        verbose_name = "Notification Recipient"
        verbose_name_plural = "Notification Recipients"
        ordering = ["name"]
        indexes = [
            models.Index(fields=['is_active']),
            models.Index(fields=['email']),
        ]

    def __str__(self):
        return f"{self.name} ({self.email})"


class BookingNotification(models.Model):
    """Links bookings to notification recipients for targeted notifications"""
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='notifications')
    recipient = models.ForeignKey(
        NotificationRecipient,
        on_delete=models.CASCADE,
        related_name='booking_notifications'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'bookings'
        verbose_name = "Booking Notification"
        verbose_name_plural = "Booking Notifications"
        unique_together = ('booking', 'recipient')
        indexes = [
            models.Index(fields=['booking']),
            models.Index(fields=['recipient']),
        ]

    def __str__(self):
        return f"Notification for {self.booking.id} to {self.recipient.name}"


class Notification(models.Model):
    """Audit log for all sent notifications (email/SMS) with delivery status"""

    NOTIFICATION_TYPES = [
        ('new', 'New Booking'),
        ('confirmed', 'Booking Confirmed'),
        ('cancelled', 'Booking Cancelled'),
        ('status_change', 'Status Changed'),
        ('reminder', 'Pickup Reminder'),
        ('driver_assignment', 'Driver Assignment'),
    ]

    CHANNEL_CHOICES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
    ]

    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='notification_log')
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES)
    channel = models.CharField(max_length=10, choices=CHANNEL_CHOICES, default='email')
    recipient = models.CharField(max_length=255)
    sent_at = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True, null=True)

    class Meta:
        app_label = 'bookings'
        ordering = ['-sent_at']
        indexes = [
            models.Index(fields=['booking', 'notification_type']),
            models.Index(fields=['sent_at']),
            models.Index(fields=['success']),
        ]

    def __str__(self):
        return f"{self.get_notification_type_display()} via {self.get_channel_display()} for Booking {self.booking.id}"


class CommunicationLog(models.Model):
    """Audit trail of staff-customer interactions across all channels"""

    COMMUNICATION_TYPES = [
        ('phone', 'Phone Call'),
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('in_person', 'In Person'),
        ('other', 'Other'),
    ]

    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='communications')
    communication_type = models.CharField(max_length=20, choices=COMMUNICATION_TYPES)
    staff_member = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='communications_logged')
    notes = models.TextField(help_text='Details of the communication')
    communication_date = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'bookings'
        ordering = ['-communication_date']
        verbose_name = 'Communication Log'
        verbose_name_plural = 'Communication Logs'
        indexes = [
            models.Index(fields=['booking', '-communication_date']),
            models.Index(fields=['staff_member']),
        ]

    def __str__(self):
        return f"{self.get_communication_type_display()} - {self.booking.passenger_name} ({self.communication_date.strftime('%Y-%m-%d %H:%M')})"


class AdminNote(models.Model):
    """Internal staff notes with chronological timeline per booking"""

    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='admin_notes')
    staff_member = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='admin_notes')
    note = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'bookings'
        ordering = ['-created_at']
        verbose_name = 'Admin Note'
        verbose_name_plural = 'Admin Notes'
        indexes = [
            models.Index(fields=['booking', '-created_at']),
            models.Index(fields=['staff_member']),
        ]

    def __str__(self):
        return f"Note by {self.staff_member.username if self.staff_member else 'Unknown'} on {self.created_at.strftime('%Y-%m-%d %H:%M')}"


class BookingHistory(models.Model):
    """Audit trail tracking all changes to bookings for compliance and analysis"""

    ACTION_CHOICES = [
        ('created', 'Created'),
        ('updated', 'Updated'),
        ('status_changed', 'Status Changed'),
        ('cancelled', 'Cancelled'),
        ('driver_assigned', 'Driver Assigned'),
        ('driver_rejected', 'Driver Rejected'),
        ('driver_completed', 'Driver Completed Trip'),
    ]

    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='history')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='booking_changes')
    changed_at = models.DateTimeField(auto_now_add=True)

    # Store the complete booking state as JSON
    booking_snapshot = models.JSONField(help_text="Complete booking data at this point in time")

    # Track specific field changes
    changes = models.JSONField(
        null=True,
        blank=True,
        help_text="Dictionary of field changes: {'field_name': {'old': value, 'new': value}}"
    )

    # Additional context
    change_reason = models.TextField(blank=True, null=True, help_text="Reason for the change")
    ip_address = models.GenericIPAddressField(null=True, blank=True, help_text="IP address of user making change")

    class Meta:
        app_label = 'bookings'
        ordering = ['-changed_at']
        verbose_name = 'Booking History'
        verbose_name_plural = 'Booking Histories'
        indexes = [
            models.Index(fields=['booking', '-changed_at']),
            models.Index(fields=['changed_by']),
            models.Index(fields=['action']),
        ]

    def __str__(self):
        return f"{self.get_action_display()} by {self.changed_by.username if self.changed_by else 'System'} on {self.changed_at.strftime('%Y-%m-%d %H:%M')}"

    def get_changed_fields(self):
        """Return list of fields that were changed"""
        if self.changes:
            # Handle both dict (proper format) and string (legacy/simplified format)
            if isinstance(self.changes, dict):
                return list(self.changes.keys())
            # If changes is a string, return empty list (no specific fields tracked)
        return []

    def get_field_change(self, field_name):
        """Get old and new values for a specific field"""
        if self.changes and isinstance(self.changes, dict) and field_name in self.changes:
            return self.changes[field_name]
        return None

    @staticmethod
    def format_field_name(field_name):
        """Convert field_name to human-readable format (e.g., pick_up_time → Pick-up Time)"""
        # Custom mappings for specific fields
        field_labels = {
            'pick_up_address': 'Pick-up Address',
            'drop_off_address': 'Drop-off Address',
            'pick_up_date': 'Pick-up Date',
            'pick_up_time': 'Pick-up Time',
            'passenger_name': 'Passenger Name',
            'passenger_email': 'Passenger Email',
            'phone_number': 'Phone Number',
            'number_of_passengers': 'Number of Passengers',
            'vehicle_type': 'Vehicle Type',
            'trip_type': 'Trip Type',
            'hours_booked': 'Hours Booked',
            'flight_number': 'Flight Number',
            'notes': 'Special Requests',
            'admin_comment': 'Admin Comment',
            'customer_communication': 'Customer Communication',
            'cancellation_reason': 'Cancellation Reason',
            'return_date': 'Return Date',
            'return_time': 'Return Time',
            'return_pickup_address': 'Return Pick-up Address',
            'return_dropoff_address': 'Return Drop-off Address',
            'return_flight_number': 'Return Flight Number',
            'return_special_requests': 'Return Special Requests',
            'status': 'Status',
        }

        # Return custom label if exists, otherwise convert snake_case to Title Case
        if field_name in field_labels:
            return field_labels[field_name]
        else:
            return field_name.replace('_', ' ').title()


class Driver(models.Model):
    """Driver model for managing M1Limosie drivers and external contractors"""

    full_name = models.CharField(max_length=100, help_text="Driver's full name")
    phone_number = models.CharField(max_length=20, help_text="Driver's phone number")
    email = models.EmailField(help_text="Driver's email address for trip assignments")
    car_number = models.CharField(max_length=50, verbose_name="Plate Number", help_text="License plate or car identification number")
    car_type = models.CharField(max_length=50, help_text="Vehicle type (e.g., Sedan, SUV, Van)")
    is_active = models.BooleanField(default=True, help_text="Whether driver is currently available")
    notes = models.TextField(blank=True, help_text="Internal notes about this driver")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'bookings'
        ordering = ['full_name']
        verbose_name = 'Driver'
        verbose_name_plural = 'Drivers'

    def __str__(self):
        return f"{self.full_name} ({self.car_type} - {self.car_number})"


class ViewedActivity(models.Model):
    """Tracks which booking activities admin users have viewed in the navbar dropdown"""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='viewed_activities',
        help_text="Admin user who viewed this activity"
    )
    activity = models.ForeignKey(
        BookingHistory,
        on_delete=models.CASCADE,
        related_name='viewed_by',
        help_text="The activity that was viewed"
    )
    viewed_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this activity was viewed"
    )

    class Meta:
        app_label = 'bookings'
        unique_together = ('user', 'activity')
        ordering = ['-viewed_at']
        verbose_name = 'Viewed Activity'
        verbose_name_plural = 'Viewed Activities'
        indexes = [
            models.Index(fields=['user', 'activity']),
            models.Index(fields=['viewed_at']),
        ]

    def __str__(self):
        return f"{self.user.username} viewed activity #{self.activity.id} at {self.viewed_at}"


class ViewedBooking(models.Model):
    """Tracks which bookings users have viewed in the My Bookings navbar dropdown"""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='viewed_bookings',
        help_text="User who viewed this booking"
    )
    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name='viewed_by_users',
        help_text="The booking that was viewed"
    )
    viewed_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this booking was viewed"
    )

    class Meta:
        app_label = 'bookings'
        unique_together = ('user', 'booking')
        ordering = ['-viewed_at']
        verbose_name = 'Viewed Booking'
        verbose_name_plural = 'Viewed Bookings'
        indexes = [
            models.Index(fields=['user', 'booking']),
            models.Index(fields=['viewed_at']),
        ]

    def __str__(self):
        return f"{self.user.username} viewed booking #{self.booking.id} at {self.viewed_at}"


# Add driver assignment to Booking model
Booking.add_to_class(
    'assigned_driver',
    models.ForeignKey(
        Driver,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_bookings',
        help_text="Driver assigned to this trip"
    )
)
Booking.add_to_class(
    'driver_notified_at',
    models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the driver was notified about this assignment"
    )
)
Booking.add_to_class(
    'driver_response_status',
    models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending Response'),
            ('accepted', 'Accepted'),
            ('rejected', 'Rejected'),
            ('completed', 'Trip Completed'),
        ],
        default='pending',
        help_text="Driver's response to the trip assignment"
    )
)
Booking.add_to_class(
    'driver_rejection_reason',
    models.TextField(
        blank=True,
        null=True,
        help_text="Reason provided by driver for rejecting the trip"
    )
)
Booking.add_to_class(
    'driver_response_at',
    models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the driver responded to the assignment"
    )
)
Booking.add_to_class(
    'driver_completed_at',
    models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the driver marked the trip as completed"
    )
)
Booking.add_to_class(
    'driver_payment_amount',
    models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Agreed payment amount for the driver"
    )
)
Booking.add_to_class(
    'driver_paid',
    models.BooleanField(
        default=False,
        help_text="Whether the driver has been paid for this trip"
    )
)
Booking.add_to_class(
    'driver_paid_at',
    models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the driver was marked as paid"
    )
)
Booking.add_to_class(
    'driver_paid_by',
    models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='driver_payments_processed',
        help_text="Admin who marked the driver as paid"
    )
)
Booking.add_to_class(
    'driver_admin_note',
    models.TextField(
        blank=True,
        null=True,
        help_text="Admin note visible to driver about this trip (e.g., check portal for updates)"
    )
)
Booking.add_to_class(
    'share_driver_info',
    models.BooleanField(
        default=False,
        help_text="Share driver name, vehicle, and phone with customer"
    )
)


class EmailTemplate(models.Model):
    """Admin-manageable email templates for automated notifications"""

    TEMPLATE_TYPE_CHOICES = [
        # Customer notifications
        ('booking_new', 'New Booking'),
        ('booking_confirmed', 'Booking Confirmed'),
        ('booking_cancelled', 'Booking Cancelled'),
        ('booking_status_change', 'Status Change'),
        ('booking_reminder', 'Pickup Reminder'),
        
        # Driver notifications
        ('driver_assignment', 'Driver Assignment'),
        ('driver_notification', 'Driver Trip Notification'),
        ('driver_rejection', 'Driver Rejection (Admin Alert)'),
        ('driver_completion', 'Driver Trip Completion (Admin Alert)'),
        
        # Round trip notifications
        ('round_trip_new', 'Round Trip - New'),
        ('round_trip_confirmed', 'Round Trip - Confirmed'),
        ('round_trip_cancelled', 'Round Trip - Cancelled'),
        ('round_trip_status_change', 'Round Trip - Status Change'),
    ]

    # Identification
    template_type = models.CharField(
        max_length=30,
        choices=TEMPLATE_TYPE_CHOICES,
        unique=True,
        help_text="Type of notification this template is used for"
    )
    name = models.CharField(
        max_length=100,
        help_text="Friendly name for this template"
    )
    description = models.TextField(
        blank=True,
        help_text="Internal notes about this template's purpose"
    )

    # Content (Admin-editable)
    subject_template = models.CharField(
        max_length=200,
        help_text="Subject line. Use {variable_name} for dynamic content. Example: Trip Confirmed: {passenger_name} - {pick_up_date}"
    )
    html_template = models.TextField(
        help_text="HTML email body. Use {variable_name} for dynamic content. Available variables documented below."
    )

    # Configuration
    is_active = models.BooleanField(
        default=True,
        help_text="Inactive templates will fall back to file-based templates"
    )
    send_to_user = models.BooleanField(
        default=True,
        help_text="Send to booking user's email"
    )
    send_to_admin = models.BooleanField(
        default=True,
        help_text="Send to admin emails"
    )
    send_to_passenger = models.BooleanField(
        default=False,
        help_text="Send to passenger email (if different from user)"
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_email_templates'
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updated_email_templates'
    )

    # Statistics
    total_sent = models.IntegerField(
        default=0,
        help_text="Total number of emails sent using this template"
    )
    total_failed = models.IntegerField(
        default=0,
        help_text="Total number of failed sends"
    )
    last_sent_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last time this template was used"
    )

    class Meta:
        app_label = 'bookings'
        verbose_name = 'Email Template'
        verbose_name_plural = 'Email Templates'
        ordering = ['template_type']
        indexes = [
            models.Index(fields=['template_type', 'is_active']),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_template_type_display()})"

    @property
    def success_rate(self):
        """Calculate success rate percentage"""
        total = self.total_sent + self.total_failed
        if total == 0:
            return 0
        return round((self.total_sent / total) * 100, 1)

    def get_available_variables(self):
        """Return list of available variables for this template type"""
        # Common variables for all templates
        common_vars = {
            'booking_reference': 'Unique booking reference number',
            'passenger_name': 'Passenger full name',
            'phone_number': 'Contact phone number',
            'passenger_email': 'Passenger email address',
            'pick_up_date': 'Pickup date',
            'pick_up_time': 'Pickup time',
            'pick_up_address': 'Pickup location address',
            'drop_off_address': 'Drop-off location address',
            'vehicle_type': 'Type of vehicle (Sedan, SUV, etc.)',
            'trip_type': 'Point-to-Point, Round Trip, or Hourly',
            'number_of_passengers': 'Number of passengers',
            'flight_number': 'Flight number (if provided)',
            'notes': 'Special requests or notes',
            'status': 'Current booking status',
            'user_email': 'User account email',
            'user_username': 'User account username',
            'company_name': 'M1 Limousine Service',
            'support_email': 'Support contact email',
            'dashboard_url': 'Link to user dashboard',
        }

        # Template-specific variables
        if 'status_change' in self.template_type:
            common_vars.update({
                'old_status': 'Previous booking status',
                'new_status': 'New booking status',
            })

        if self.template_type == 'driver_notification':
            # Driver notification has specific variables
            common_vars.update({
                'driver_full_name': 'Driver full name',
                'driver_email': 'Driver email address',
                'pickup_location': 'Pickup address',
                'pickup_date': 'Pickup date (formatted)',
                'pickup_time': 'Pickup time (formatted)',
                'drop_off_location': 'Drop-off address (optional for hourly)',
                'payment_amount': 'Driver payment amount (optional)',
                'driver_portal_url': 'Link to driver portal for this trip',
                'all_trips_url': 'Link to view all assigned trips',
                'support_phone': 'Support phone number',
            })
        elif 'driver' in self.template_type:
            common_vars.update({
                'driver_name': 'Assigned driver name',
                'driver_phone': 'Driver phone number',
                'driver_vehicle': 'Driver vehicle information',
                'driver_portal_url': 'Driver action portal link',
            })

        if 'round_trip' in self.template_type:
            common_vars.update({
                'return_pick_up_date': 'Return trip pickup date',
                'return_pick_up_time': 'Return trip pickup time',
                'return_pick_up_address': 'Return trip pickup address',
                'return_drop_off_address': 'Return trip drop-off address',
            })

        return common_vars

    def render_subject(self, context):
        """Render subject line with context variables using Django template engine"""
        from django.template import Template, Context
        try:
            template = Template(self.subject_template)
            return template.render(Context(context))
        except Exception as e:
            logger.error(f"Error rendering subject: {e}")
            return self.subject_template

    def render_html(self, context):
        """Render HTML body with context variables using Django template engine"""
        from django.template import Template, Context
        try:
            template = Template(self.html_template)
            return template.render(Context(context))
        except Exception as e:
            logger.error(f"Error rendering HTML: {e}")
            return self.html_template

    def increment_sent(self):
        """Increment sent counter and update last_sent_at"""
        self.total_sent += 1
        self.last_sent_at = timezone.now()
        self.save(update_fields=['total_sent', 'last_sent_at'])

    def increment_failed(self):
        """Increment failed counter"""
        self.total_failed += 1
        self.save(update_fields=['total_failed'])
