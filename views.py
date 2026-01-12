# bookings/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, logout
from django.db import transaction
import logging

from models import Booking, FrequentPassenger
from booking_forms import (
    BookingForm, AdminBookingForm, BookingSearchForm,
    CancellationRequestForm, FrequentPassengerForm,
    UserProfileForm, AdminStatusUpdateForm, UserSignupForm
)
from booking_service import BookingService
from notification_service import NotificationService
from email_service import EmailService

logger = logging.getLogger('bookings')


# ============================================================================
# PUBLIC VIEWS
# ============================================================================

def home(request):
    """Render the landing page."""
    return render(request, 'bookings/landing.html')


def privacy_policy(request):
    """Render the privacy policy page."""
    return render(request, 'bookings/privacy_policy.html')


def user_guide(request):
    """Render the user guide page."""
    return render(request, 'bookings/user_guide.html')


def cookie_policy(request):
    """Render the cookie policy page."""
    return render(request, 'bookings/cookie_policy.html')


def contact(request):
    """Handle contact form submissions and send email with rate limiting."""
    if request.method == 'POST':
        from django.core.cache import cache
        from django.core.mail import send_mail
        from django.conf import settings
        import hashlib

        # Get user identifier (IP address)
        ip_address = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip() or \
                     request.META.get('REMOTE_ADDR', 'unknown')

        # Create rate limit keys
        minute_key = f'contact_form_minute_{ip_address}'
        hour_key = f'contact_form_hour_{ip_address}'

        # Check rate limits (3 per minute, 10 per hour)
        minute_count = cache.get(minute_key, 0)
        hour_count = cache.get(hour_key, 0)

        if minute_count >= 3:
            messages.error(request, 'Too many requests. Please wait a minute before trying again.')
            return render(request, 'bookings/contact.html')

        if hour_count >= 10:
            messages.error(request, 'You have reached the hourly limit. Please try again later.')
            return render(request, 'bookings/contact.html')

        # Get and validate form data
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        subject = request.POST.get('subject', '').strip()
        message_text = request.POST.get('message', '').strip()

        # Basic validation
        if not (name and email and subject and message_text):
            messages.error(request, 'Please fill in all required fields.')
            return render(request, 'bookings/contact.html')

        # Email validation
        if '@' not in email or '.' not in email.split('@')[-1]:
            messages.error(request, 'Please enter a valid email address.')
            return render(request, 'bookings/contact.html')

        # Length validation (prevent abuse)
        if len(name) > 100 or len(email) > 100 or len(message_text) > 2000:
            messages.error(request, 'One or more fields exceed the maximum length.')
            return render(request, 'bookings/contact.html')

        try:
            # Compose email
            email_subject = f"Contact Form: {subject}"
            email_body = f"""
New contact form submission from M1 Limousine website:

Name: {name}
Email: {email}
Phone: {phone if phone else 'Not provided'}
Subject: {subject}

Message:
{message_text}

---
This message was sent via the M1 Limousine contact form.
IP: {ip_address}
"""

            # Send email
            send_mail(
                subject=email_subject,
                message=email_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=['mo@m1limo.com'],
                fail_silently=False,
            )

            # Increment rate limit counters
            cache.set(minute_key, minute_count + 1, 60)  # 1 minute
            cache.set(hour_key, hour_count + 1, 3600)    # 1 hour

            messages.success(request, 'Thank you for your message! We will get back to you soon.')
            return redirect('contact')

        except Exception as e:
            messages.error(request, 'There was an error sending your message. Please try again or contact us directly.')

    return render(request, 'bookings/contact.html')


def signup(request):
    """Handle user registration and auto-login on success."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = UserSignupForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    user = form.save()
                login(request, user)
                messages.success(request, f"Welcome {user.first_name}! Your account has been created successfully.")
                logger.info(f"New user signup: {user.username} ({user.email})")
                return redirect('dashboard')
            except Exception as e:
                logger.error(f"Error during signup for user {form.cleaned_data.get('username')}: {e}", exc_info=True)
                messages.error(request, "An error occurred during signup. Please try again.")
        else:
            logger.warning(f"Signup form invalid: {form.errors.as_json()}")
            messages.error(request, "Please correct the errors below.")
    else:
        form = UserSignupForm()

    return render(request, 'registration/signup.html', {'form': form})


def user_login(request):
    """Authenticate user and redirect to requested page or dashboard."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        from django.contrib.auth import authenticate
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            # Use full name if available, otherwise fallback to username
            display_name = f"{user.first_name} {user.last_name}".strip() if user.first_name or user.last_name else user.username
            messages.success(request, f"Welcome back, {display_name}!")
            # Redirect to next parameter or dashboard
            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
        else:
            messages.error(request, "Invalid username or password.")
            logger.warning(f"Failed login attempt for username: {username}")

    return render(request, 'registration/login.html')


def user_logout(request):
    """Log out user and redirect to home page."""
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('home')


# ============================================================================
# USER VIEWS
# ============================================================================

@login_required
def dashboard(request):
    """Display user dashboard with filtered bookings and statistics."""
    if request.user.is_staff:
        base_queryset = Booking.objects.all()
        users_for_filter = User.objects.filter(is_active=True).order_by('first_name', 'last_name', 'username')
    else:
        base_queryset = Booking.objects.filter(user=request.user)
        users_for_filter = None

    # Apply filters to base queryset
    search_query = request.GET.get('search', '').strip()
    if search_query:
        from django.db.models import Q
        filters = (
            Q(passenger_name__icontains=search_query) |
            Q(phone_number__icontains=search_query) |
            Q(pick_up_address__icontains=search_query) |
            Q(drop_off_address__icontains=search_query) |
            Q(booking_reference__icontains=search_query)
        )
        # Add exact ID match if search query is numeric
        if search_query.isdigit():
            filters |= Q(id=int(search_query))
        base_queryset = base_queryset.filter(filters)

    date_filter = request.GET.get('date')
    if date_filter:
        from datetime import datetime
        if date_filter == 'today':
            # Special handling for "today" filter
            base_queryset = base_queryset.filter(pick_up_date=timezone.now().date())
        else:
            try:
                filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
                base_queryset = base_queryset.filter(pick_up_date=filter_date)
            except ValueError:
                pass

    status_filter = request.GET.get('status')
    if status_filter:
        base_queryset = base_queryset.filter(status=status_filter)

    # PART 2: Fix Date Search - When filtering by date/status, show ALL matching trips
    # including return trips. Only exclude return trips when no filters are applied.
    if date_filter or status_filter or search_query:
        # Filtering active: Show all matching trips (including return legs)
        queryset = base_queryset
    else:
        # No filters: Exclude return trips (they're shown as expandable rows under parent)
        queryset = base_queryset.exclude(is_return_trip=True)

    # Optimize queries to prevent N+1 problem with select_related and prefetch_related
    queryset = queryset.select_related(
        'user',
        'linked_booking',
        'linked_booking__user',
        'assigned_driver'
    ).prefetch_related(
        'stops',
        'linked_booking__stops',
        'notifications',
        'notifications__recipient'
    )

    today = timezone.now().date()
    now = timezone.now()

    if request.user.is_staff:
        today_pickups = Booking.objects.filter(
            pick_up_date=today,
            status='Confirmed'
        ).order_by('pick_up_time')
    else:
        today_pickups = Booking.objects.filter(
            user=request.user,
            pick_up_date=today,
            status='Confirmed'
        ).order_by('pick_up_time')

    from datetime import datetime, timedelta
    future_pickups = []
    for booking in today_pickups:
        pickup_datetime = datetime.combine(booking.pick_up_date, booking.pick_up_time)
        if timezone.is_naive(pickup_datetime):
            pickup_datetime = timezone.make_aware(pickup_datetime)
        if pickup_datetime > now:
            future_pickups.append(booking)
    today_pickups = future_pickups
    from django.core.paginator import Paginator
    paginator = Paginator(queryset.order_by('-pick_up_date', '-pick_up_time'), 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # Calculate display count: Count ALL trips including returns using base_queryset
    # This gives accurate count for "Total: X trips" display
    display_count = base_queryset.count()

    # Add unviewed status to each booking for notification indicators
    bookings_list = list(page_obj.object_list)
    for booking in bookings_list:
        booking.has_unviewed_changes = booking.has_unviewed_changes(request.user)

    context = {
        'bookings': bookings_list,
        'page_obj': page_obj,
        'display_count': display_count,
        'today_pickups': today_pickups,
        'is_admin': request.user.is_staff,
        'users': users_for_filter,
    }

    if request.user.is_staff:
        from models import BookingHistory
        stats = BookingService.get_dashboard_stats()
        stats['completed_today'] = Booking.objects.filter(
            status='Trip_Completed',
            pick_up_date=today
        ).count()
        context['stats'] = stats

        # Get complete booking history for admins (full audit trail)
        context['booking_history'] = BookingHistory.objects.select_related(
            'booking',
            'booking__user',
            'changed_by'
        ).order_by('-changed_at')[:50]
    else:
        context['stats'] = {
            'total_bookings': Booking.objects.filter(user=request.user).count(),
            'active_bookings': Booking.objects.filter(user=request.user, status__in=['Pending', 'Confirmed']).count(),
            'pending_count': Booking.objects.filter(user=request.user, status='Pending').count(),
            'confirmed_count': Booking.objects.filter(user=request.user, status='Confirmed').count(),
            'today_trips': Booking.objects.filter(user=request.user, pick_up_date=today).count(),
            'upcoming_trips': Booking.objects.filter(user=request.user, pick_up_date__gte=today).count(),
            'completed_trips': Booking.objects.filter(user=request.user, status='Trip_Completed').count(),
            'completed_today': Booking.objects.filter(user=request.user, status='Trip_Completed', pick_up_date=today).count(),
        }

    if request.headers.get('HX-Request'):
        if request.GET.get('list_only'):
            template_name = 'bookings/partials/booking_list.html'
        else:
            template_name = 'bookings/partials/dashboard_content.html'
    else:
        template_name = 'bookings/dashboard.html'

    return render(request, template_name, context)


@login_required
def new_booking(request):
    """Handle booking creation with stops and notification recipients."""
    logger.debug("Starting new_booking view")

    if request.method == "POST":
        form = BookingForm(request.POST)

        if form.is_valid():
            try:
                booking_data = {
                    field: form.cleaned_data[field]
                    for field in form.Meta.fields
                    if field in form.cleaned_data and field != 'user'
                }

                # Add phone_number and passenger_email from cleaned_data (set by passenger_contact field)
                if 'phone_number' in form.cleaned_data:
                    booking_data['phone_number'] = form.cleaned_data['phone_number']
                if 'passenger_email' in form.cleaned_data:
                    booking_data['passenger_email'] = form.cleaned_data['passenger_email']

                stops_data = []
                return_stops_data = []
                
                if form.cleaned_data.get('needs_stop'):
                    for key, value in request.POST.items():
                        if key.startswith('stop_address_') and value.strip():
                            try:
                                stop_number = int(key.replace('stop_address_', ''))
                                stops_data.append({
                                    'address': value.strip(),
                                    'stop_number': stop_number
                                })
                            except ValueError:
                                continue
                
                if booking_data.get('trip_type') == 'Round' and form.cleaned_data.get('needs_return_stop'):
                    for key, value in request.POST.items():
                        if key.startswith('return_stop_address_') and value.strip():
                            try:
                                stop_number = int(key.replace('return_stop_address_', ''))
                                return_stops_data.append({
                                    'address': value.strip(),
                                    'stop_number': stop_number
                                })
                            except ValueError:
                                continue

                notification_recipients = None
                if request.user.is_staff and 'notification_recipients' in form.cleaned_data:
                    notification_recipients = form.cleaned_data['notification_recipients']

                # Determine user - admin can create bookings for other users
                user = request.user
                if request.user.is_staff and form.cleaned_data.get('booking_for_user'):
                    user = form.cleaned_data['booking_for_user']
                    logger.info(f"Admin {request.user.username} creating booking for user {user.username}")

                booking = BookingService.create_booking(
                    user=user,
                    booking_data=booking_data,
                    stops_data=stops_data if stops_data else None,
                    return_stops_data=return_stops_data if return_stops_data else None,
                    notification_recipients=notification_recipients,
                    created_by=request.user
                )

                return redirect('booking_confirmation', booking_id=booking.id)
                
            except ValidationError as e:
                logger.error(f"Validation error creating booking: {e}")
                messages.error(request, str(e))
            except Exception as e:
                logger.error(f"Error creating booking: {e}", exc_info=True)
                messages.error(request, f"Error creating booking: {str(e)}")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        # Check if passenger_id is provided in query parameters
        passenger_id = request.GET.get('passenger')
        initial_data = {}

        if passenger_id:
            try:
                passenger = FrequentPassenger.objects.get(id=passenger_id, user=request.user)
                # Pre-populate form with passenger details
                # Use passenger_contact hybrid field (email takes priority if available)
                contact = passenger.email if passenger.email else passenger.phone_number
                initial_data = {
                    'passenger_name': passenger.name,
                    'passenger_contact': contact,
                    'pick_up_address': passenger.address if passenger.address else '',
                    'vehicle_type': passenger.preferred_vehicle_type if passenger.preferred_vehicle_type else '',
                }
            except FrequentPassenger.DoesNotExist:
                pass

        form = BookingForm(initial=initial_data) if initial_data else BookingForm()

    frequent_passengers = FrequentPassenger.objects.filter(user=request.user)

    return render(request, 'bookings/new_booking.html', {
        'form': form,
        'frequent_passengers': frequent_passengers,
    })


@login_required
def booking_confirmation(request, booking_id):
    """Display confirmation page after successful booking submission."""
    # Staff can view any booking confirmation, regular users only their own
    if request.user.is_staff:
        booking = get_object_or_404(Booking, id=booking_id)
    else:
        booking = get_object_or_404(Booking, id=booking_id, user=request.user)

    linked_booking = booking.linked_booking

    # Get notification recipients for display
    from notification_service import NotificationService
    notification_type = 'confirmed' if booking.status == 'Confirmed' else 'new'
    notification_recipients = NotificationService.get_recipients(booking, notification_type)

    # Get reminder recipients (24 hours before pickup)
    reminder_recipients = NotificationService.get_recipients(booking, 'reminder')

    context = {
        'booking': booking,
        'linked_booking': linked_booking,
        'notification_recipients': notification_recipients,
        'reminder_recipients': reminder_recipients,
    }

    return render(request, 'bookings/booking_confirmation.html', context)


@staff_member_required
def view_activity(request, activity_id):
    """
    Mark a booking activity as viewed and redirect to the booking detail page.
    This is used when admin clicks on an activity in the navbar dropdown.
    """
    from models import BookingHistory, ViewedActivity

    activity = get_object_or_404(BookingHistory, id=activity_id)

    # Mark activity as viewed (get_or_create prevents duplicates)
    ViewedActivity.objects.get_or_create(
        user=request.user,
        activity=activity
    )

    # Redirect to the booking detail page
    return redirect('booking_detail', booking_id=activity.booking.id)


@login_required
def view_user_booking(request, booking_id):
    """
    Mark a user booking as viewed and redirect to the booking detail page.
    This is used when users click on a booking in the My Bookings navbar dropdown.
    """
    from models import ViewedBooking

    booking = get_object_or_404(Booking, id=booking_id, user=request.user)

    # Mark booking as viewed (get_or_create prevents duplicates)
    ViewedBooking.objects.get_or_create(
        user=request.user,
        booking=booking
    )

    # Redirect to the booking detail page
    return redirect('booking_detail', booking_id=booking.id)


@login_required
def booking_detail(request, booking_id):
    """Display complete booking details with logs and cancellation info."""
    booking = get_object_or_404(Booking, id=booking_id)

    if not request.user.is_staff and booking.user != request.user:
        messages.error(request, "You don't have permission to view this booking.")
        return redirect('dashboard')

    # Mark booking as viewed by this user (for notification tracking)
    if request.user.is_authenticated and not request.user.is_staff:
        from models import ViewedBooking
        ViewedBooking.objects.update_or_create(
            user=request.user,
            booking=booking,
            defaults={'viewed_at': timezone.now()}
        )

    linked_booking = booking.linked_booking

    outbound_stops = booking.stops.filter(is_return_stop=False).order_by('stop_number')
    return_stops = booking.stops.filter(is_return_stop=True).order_by('stop_number')

    communications = booking.communications.all().order_by('-communication_date')

    admin_notes = booking.admin_notes.all().order_by('-created_at')

    notifications = booking.notification_log.all().order_by('-sent_at')[:10]

    # Get booking history for audit trail
    booking_history = booking.history.all().order_by('-changed_at')[:20]

    can_cancel, will_charge, hours_until = booking.can_cancel()

    context = {
        'booking': booking,
        'linked_booking': linked_booking,
        'outbound_stops': outbound_stops,
        'return_stops': return_stops,
        'communications': communications,
        'admin_notes': admin_notes,
        'notifications': notifications,
        'booking_history': booking_history,
        'can_cancel': can_cancel,
        'will_charge': will_charge,
        'hours_until_pickup': hours_until,
        'time_until_pickup_formatted': booking.time_until_pickup_formatted,
        'is_admin': request.user.is_staff,
    }

    return render(request, 'bookings/booking_detail.html', context)


@login_required
def update_booking(request, booking_id):
    """Edit existing booking with 2-hour restriction for non-admin users."""
    booking = get_object_or_404(Booking, id=booking_id)

    can_edit, error_message = BookingService.can_user_edit_booking(request.user, booking)
    if not can_edit:
        messages.error(request, error_message)
        return redirect('dashboard')

    # Store original trip_type and linked_booking BEFORE form binding
    original_trip_type = booking.trip_type
    original_linked_booking = booking.linked_booking

    if request.method == "POST":
        form = BookingForm(request.POST, instance=booking)

        if form.is_valid():
            try:
                booking_data = {
                    field: form.cleaned_data[field]
                    for field in form.Meta.fields
                    if field in form.cleaned_data and field != 'user'
                }

                # Preserve Round trip type for individual leg edits
                if original_trip_type == 'Round':
                    booking_data['trip_type'] = 'Round'

                # Add phone_number and passenger_email from passenger_contact hybrid field
                if 'phone_number' in form.cleaned_data:
                    booking_data['phone_number'] = form.cleaned_data['phone_number']
                if 'passenger_email' in form.cleaned_data:
                    booking_data['passenger_email'] = form.cleaned_data['passenger_email']

                stops_data = []
                return_stops_data = []
                
                if form.cleaned_data.get('needs_stop'):
                    for key, value in request.POST.items():
                        if key.startswith('stop_address_') and value.strip():
                            try:
                                stop_number = int(key.replace('stop_address_', ''))
                                stops_data.append({
                                    'address': value.strip(),
                                    'stop_number': stop_number
                                })
                            except ValueError:
                                continue
                
                if booking_data.get('trip_type') == 'Round' and form.cleaned_data.get('needs_return_stop'):
                    for key, value in request.POST.items():
                        if key.startswith('return_stop_address_') and value.strip():
                            try:
                                stop_number = int(key.replace('return_stop_address_', ''))
                                return_stops_data.append({
                                    'address': value.strip(),
                                    'stop_number': stop_number
                                })
                            except ValueError:
                                continue
                
                notification_recipients = None
                if request.user.is_staff and 'notification_recipients' in form.cleaned_data:
                    notification_recipients = form.cleaned_data['notification_recipients']

                BookingService.update_booking(
                    booking=booking,
                    booking_data=booking_data,
                    stops_data=stops_data if stops_data else None,
                    return_stops_data=return_stops_data if return_stops_data else None,
                    notification_recipients=notification_recipients,
                    changed_by=request.user
                )

                messages.success(request, "Booking updated successfully.")
                return redirect('dashboard')
                
            except ValidationError as e:
                logger.error(f"Validation error updating booking: {e}")
                messages.error(request, str(e))
            except Exception as e:
                logger.error(f"Error updating booking: {e}", exc_info=True)
                messages.error(request, f"Error updating booking: {str(e)}")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        # Always bind to instance
        form = BookingForm(instance=booking)

        # For individual trip editing of round trip legs, override trip_type to display as Point-to-Point
        if original_trip_type == 'Round':
            form.initial['trip_type'] = 'Point'
            form.fields['trip_type'].initial = 'Point'

    # Determine if this is part of a round trip for UI display
    is_round_trip_leg = original_trip_type == 'Round'
    linked_booking = original_linked_booking if not booking.is_return_trip else None

    context = {
        'form': form,
        'booking': booking,
        'is_single_leg_edit': is_round_trip_leg,
        'linked_booking': linked_booking,
    }
    return render(request, 'bookings/update_booking.html', context)


@login_required
def rebook_booking(request, booking_id):
    """
    Rebook a past trip with pre-filled information.
    Allows users to create a new booking based on a previous trip.
    Admin can rebook any booking.
    """
    # Admin can access all bookings, regular users only their own
    if request.user.is_staff:
        original_booking = get_object_or_404(Booking, id=booking_id)
    else:
        original_booking = get_object_or_404(Booking, id=booking_id, user=request.user)

    if request.method == "POST":
        form = BookingForm(request.POST)
        if form.is_valid():
            try:
                # Filter out form-only fields (not part of Booking model)
                booking_data = {
                    field: form.cleaned_data[field]
                    for field in form.Meta.fields
                    if field in form.cleaned_data and field not in ['user', 'booking_for_user', 'passenger_contact',
                                                                      'is_airport_trip', 'needs_stop', 'is_return_airport_trip',
                                                                      'needs_return_stop', 'notification_recipients']
                }

                # Add phone_number and passenger_email from cleaned_data (set by passenger_contact field)
                if 'phone_number' in form.cleaned_data:
                    booking_data['phone_number'] = form.cleaned_data['phone_number']
                if 'passenger_email' in form.cleaned_data:
                    booking_data['passenger_email'] = form.cleaned_data['passenger_email']

                # Extract stops data
                stops_data = []
                return_stops_data = []

                if form.cleaned_data.get('needs_stop'):
                    for key, value in request.POST.items():
                        if key.startswith('stop_address_') and value.strip():
                            try:
                                stop_number = int(key.replace('stop_address_', ''))
                                stops_data.append({
                                    'address': value.strip(),
                                    'stop_number': stop_number
                                })
                            except ValueError:
                                continue

                if booking_data.get('trip_type') == 'Round' and form.cleaned_data.get('needs_return_stop'):
                    for key, value in request.POST.items():
                        if key.startswith('return_stop_address_') and value.strip():
                            try:
                                stop_number = int(key.replace('return_stop_address_', ''))
                                return_stops_data.append({
                                    'address': value.strip(),
                                    'stop_number': stop_number
                                })
                            except ValueError:
                                continue

                # Get notification recipients if admin
                notification_recipients = None
                if request.user.is_staff and 'notification_recipients' in form.cleaned_data:
                    notification_recipients = form.cleaned_data['notification_recipients']

                # Determine user - admin can create bookings for other users
                user = request.user
                if request.user.is_staff and form.cleaned_data.get('booking_for_user'):
                    user = form.cleaned_data['booking_for_user']
                    logger.info(f"Admin {request.user.username} rebooking for user {user.username}")

                new_booking = BookingService.create_booking(
                    user=user,
                    booking_data=booking_data,
                    stops_data=stops_data if stops_data else None,
                    return_stops_data=return_stops_data if return_stops_data else None,
                    notification_recipients=notification_recipients,
                    created_by=request.user
                )
                messages.success(request, f"Booking #{new_booking.id} created successfully based on previous trip!")
                return redirect('booking_confirmation', booking_id=new_booking.id)
            except Exception as e:
                logger.error(f"Error rebooking trip: {e}")
                messages.error(request, str(e))
    else:
        # Pre-fill form with original booking data
        initial_data = {
            'trip_type': original_booking.trip_type,
            'vehicle_type': original_booking.vehicle_type,
            'passenger_name': original_booking.passenger_name,
            'number_of_passengers': original_booking.number_of_passengers,
            'pick_up_address': original_booking.pick_up_address,
            'drop_off_address': original_booking.drop_off_address,
            'flight_number': original_booking.flight_number,
            'notes': original_booking.notes,
        }

        # Set passenger contact (phone or email)
        if original_booking.phone_number:
            initial_data['passenger_contact'] = original_booking.phone_number
        elif original_booking.passenger_email:
            initial_data['passenger_contact'] = original_booking.passenger_email

        # For hourly trips
        if original_booking.trip_type == 'Hourly':
            initial_data['hours_booked'] = original_booking.hours_booked

        # For round trips
        if original_booking.trip_type == 'Round' and original_booking.linked_booking:
            linked = original_booking.linked_booking
            initial_data['return_pickup_address'] = linked.pick_up_address
            initial_data['return_dropoff_address'] = linked.drop_off_address
            initial_data['return_flight_number'] = linked.flight_number
            initial_data['return_special_requests'] = linked.notes

        form = BookingForm(initial=initial_data)

    context = {
        'form': form,
        'original_booking': original_booking,
        'is_rebook': True,
    }
    return render(request, 'bookings/new_booking.html', context)


@login_required
def cancel_booking(request, booking_id):
    """Handle booking cancellation with option for single trip or entire round trip."""
    booking = get_object_or_404(Booking, id=booking_id)

    if booking.user != request.user and not request.user.is_staff:
        messages.error(request, "You don't have permission to cancel this trip.")
        return redirect('dashboard')

    from models import Booking as BookingModel
    valid_transitions = BookingModel.VALID_TRANSITIONS.get(booking.status, [])
    can_cancel = 'Cancelled' in valid_transitions

    if not can_cancel:
        if booking.status == 'Trip_Completed':
            messages.error(request, "Cannot cancel a completed trip.")
        elif booking.status == 'Cancelled':
            messages.error(request, "This trip is already cancelled.")
        else:
            messages.error(request, f"Cannot cancel trips with status: {booking.get_status_display()}")
        return redirect('dashboard')

    # PART 1: User cancellation permissions - only allow if:
    # a) User created the reservation, b) Status is Pending, c) Admin hasn't reviewed it
    if not request.user.is_staff:
        if booking.status != 'Pending':
            messages.error(request, "You can only cancel bookings with 'Pending' status. Contact admin for confirmed bookings.")
            return redirect('dashboard')

        if booking.admin_reviewed:
            messages.error(request, "This booking has been reviewed by admin and cannot be cancelled. Please contact us.")
            return redirect('dashboard')

    is_round_trip = booking.linked_booking is not None

    linked_booking = booking.linked_booking if is_round_trip else None

    if request.method == "POST":
        cancellation_reason = request.POST.get('cancellation_reason', '')
        cancel_type = request.POST.get('cancel_type', 'entire')

        try:
            if is_round_trip and cancel_type == 'entire':
                logger.info(f"Cancelling entire round-trip booking (ID: {booking.id})")
                first_trip, return_trip = BookingService.cancel_entire_booking(booking, cancellation_reason)
                messages.success(request, "Entire round trip booking cancelled successfully.")
            else:
                logger.info(f"Cancelling single trip (ID: {booking.id})")
                BookingService.cancel_single_trip(booking, cancellation_reason)
                trip_label = booking.trip_label or "Trip"

                if is_round_trip:
                    messages.success(request, f"{trip_label} cancelled successfully. Your other trip remains active.")
                else:
                    messages.success(request, "Trip cancelled successfully.")

            return redirect('dashboard')

        except ValidationError as e:
            logger.error(f"Validation error cancelling booking: {e}")
            if hasattr(e, 'message'):
                error_msg = e.message
            elif hasattr(e, 'messages'):
                error_msg = '; '.join(e.messages)
            else:
                error_msg = str(e)
            messages.error(request, f"Cannot cancel trip: {error_msg}")
            return redirect('dashboard')
        except Exception as e:
            logger.error(f"Error cancelling booking: {e}", exc_info=True)
            messages.error(request, "An error occurred while cancelling the trip. Please try again.")
            return redirect('dashboard')

    context = {
        'booking': booking,
        'is_round_trip': is_round_trip,
        'linked_booking': linked_booking,
        'is_admin': request.user.is_staff,
    }
    return render(request, 'bookings/cancel_booking.html', context)


delete_booking = cancel_booking


@login_required
def update_round_trip(request, booking_id):
    """Edit entire round trip booking with both legs."""
    # Get the outbound booking (could be either leg, normalize it)
    booking = get_object_or_404(Booking, id=booking_id)

    # Determine which is outbound and which is return
    if booking.is_return_trip:
        # User clicked on return trip, get the outbound
        outbound_booking = booking.linked_booking
        return_booking = booking
    else:
        # User clicked on outbound
        outbound_booking = booking
        return_booking = booking.linked_booking

    if not return_booking:
        messages.error(request, "This is not a round trip booking.")
        return redirect('dashboard')

    # Check permissions for both legs
    can_edit_outbound, error_msg_outbound = BookingService.can_user_edit_booking(request.user, outbound_booking)
    can_edit_return, error_msg_return = BookingService.can_user_edit_booking(request.user, return_booking)

    if not can_edit_outbound:
        messages.error(request, f"Cannot edit outbound: {error_msg_outbound}")
        return redirect('dashboard')
    if not can_edit_return:
        messages.error(request, f"Cannot edit return: {error_msg_return}")
        return redirect('dashboard')

    if request.method == "POST":
        form = BookingForm(request.POST, instance=outbound_booking)

        if form.is_valid():
            try:
                # Outbound booking data
                outbound_data = {
                    'passenger_name': form.cleaned_data['passenger_name'],
                    'phone_number': form.cleaned_data['phone_number'],
                    'passenger_email': form.cleaned_data['passenger_email'],
                    'number_of_passengers': form.cleaned_data['number_of_passengers'],
                    'vehicle_type': form.cleaned_data['vehicle_type'],
                    'pick_up_address': form.cleaned_data['pick_up_address'],
                    'drop_off_address': form.cleaned_data['drop_off_address'],
                    'pick_up_date': form.cleaned_data['pick_up_date'],
                    'pick_up_time': form.cleaned_data['pick_up_time'],
                    'flight_number': form.cleaned_data.get('flight_number', ''),
                    'notes': form.cleaned_data.get('notes', ''),
                    'trip_type': 'Round',
                }

                # Return booking data
                return_data = {
                    'passenger_name': form.cleaned_data['passenger_name'],
                    'phone_number': form.cleaned_data['phone_number'],
                    'passenger_email': form.cleaned_data['passenger_email'],
                    'number_of_passengers': form.cleaned_data['number_of_passengers'],
                    'vehicle_type': form.cleaned_data['vehicle_type'],
                    'pick_up_address': form.cleaned_data.get('return_pickup_address'),
                    'drop_off_address': form.cleaned_data.get('return_dropoff_address'),
                    'pick_up_date': form.cleaned_data.get('return_date'),
                    'pick_up_time': form.cleaned_data.get('return_time'),
                    'flight_number': form.cleaned_data.get('return_flight_number', ''),
                    'notes': form.cleaned_data.get('return_special_requests', ''),
                    'trip_type': 'Round',
                }

                # Extract stops data
                stops_data = []
                return_stops_data = []

                if form.cleaned_data.get('needs_stop'):
                    for key, value in request.POST.items():
                        if key.startswith('stop_address_') and value.strip():
                            try:
                                stop_number = int(key.replace('stop_address_', ''))
                                stops_data.append({
                                    'address': value.strip(),
                                    'stop_number': stop_number
                                })
                            except ValueError:
                                continue

                if form.cleaned_data.get('needs_return_stop'):
                    for key, value in request.POST.items():
                        if key.startswith('return_stop_address_') and value.strip():
                            try:
                                stop_number = int(key.replace('return_stop_address_', ''))
                                return_stops_data.append({
                                    'address': value.strip(),
                                    'stop_number': stop_number
                                })
                            except ValueError:
                                continue

                # Update outbound booking
                BookingService.update_booking(
                    booking=outbound_booking,
                    booking_data=outbound_data,
                    stops_data=stops_data if stops_data else None,
                    changed_by=request.user
                )

                # Update return booking
                BookingService.update_booking(
                    booking=return_booking,
                    booking_data=return_data,
                    stops_data=return_stops_data if return_stops_data else None,
                    changed_by=request.user
                )

                messages.success(request, "Round trip booking updated successfully.")
                return redirect('booking_detail', booking_id=outbound_booking.id)

            except ValidationError as e:
                logger.error(f"Validation error updating round trip: {e}")
                messages.error(request, str(e))
            except Exception as e:
                logger.error(f"Error updating round trip: {e}", exc_info=True)
                messages.error(request, f"Error updating round trip: {str(e)}")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        # Pre-populate form with outbound data and return data
        initial_data = {
            'passenger_name': outbound_booking.passenger_name,
            'phone_number': outbound_booking.phone_number,
            'passenger_email': outbound_booking.passenger_email,
            'number_of_passengers': outbound_booking.number_of_passengers,
            'vehicle_type': outbound_booking.vehicle_type,
            'pick_up_address': outbound_booking.pick_up_address,
            'drop_off_address': outbound_booking.drop_off_address,
            'pick_up_date': outbound_booking.pick_up_date,
            'pick_up_time': outbound_booking.pick_up_time,
            'flight_number': outbound_booking.flight_number,
            'notes': outbound_booking.notes,
            'trip_type': 'Round',
            'return_pickup_address': return_booking.pick_up_address,
            'return_dropoff_address': return_booking.drop_off_address,
            'return_date': return_booking.pick_up_date,
            'return_time': return_booking.pick_up_time,
            'return_flight_number': return_booking.flight_number,
            'return_special_requests': return_booking.notes,
        }

        # Set passenger_contact based on what's available
        if outbound_booking.phone_number:
            initial_data['passenger_contact'] = outbound_booking.phone_number
        elif outbound_booking.passenger_email:
            initial_data['passenger_contact'] = outbound_booking.passenger_email

        form = BookingForm(initial=initial_data)

    context = {
        'form': form,
        'booking': outbound_booking,
        'return_booking': return_booking,
        'is_round_trip_edit': True,
    }
    return render(request, 'bookings/update_booking.html', context)


@login_required
def request_cancellation(request, booking_id):
    """Submit cancellation request for admin review."""
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    
    if request.method == "POST":
        form = CancellationRequestForm(request.POST, instance=booking)
        if form.is_valid():
            try:
                BookingService.request_cancellation(
                    booking=booking,
                    cancellation_reason=form.cleaned_data['cancellation_reason']
                )
                messages.success(request, "Cancellation request submitted.")
                return redirect('dashboard')
            except Exception as e:
                logger.error(f"Error requesting cancellation: {e}")
                messages.error(request, str(e))
    else:
        form = CancellationRequestForm(instance=booking)
    
    return render(request, 'bookings/request_cancellation.html', {
        'form': form,
        'booking': booking
    })


@login_required
def booking_actions(request, booking_id, action):
    """Handle admin quick actions: confirm, complete, resend notification, assign driver."""
    booking = get_object_or_404(Booking, id=booking_id)

    if not request.user.is_staff:
        messages.error(request, "Permission denied.")
        return redirect('dashboard')

    try:
        if action == 'confirm':
            BookingService.update_booking_status(booking, 'Confirmed', changed_by=request.user)
            messages.success(request, "Booking confirmed.")
        elif action == 'complete':
            from django.utils import timezone

            hours_until = booking.hours_until_pickup

            if hours_until > 0:
                messages.error(request,
                    f"Cannot mark trip as complete before pickup time. "
                    f"This trip is scheduled in {booking.time_until_pickup_formatted}. "
                    f"Please wait until after the pickup time."
                )
            else:
                BookingService.update_booking_status(booking, 'Trip_Completed', changed_by=request.user)
                messages.success(request, "Trip marked as completed.")
        elif action == 'resend_notification':
            notification_type = request.GET.get('type', 'new')
            NotificationService.resend_notification(booking, notification_type)
            messages.success(request, f"Notification resent.")
        elif action == 'assign_driver':
            return redirect('assign_driver', booking_id=booking_id)
        else:
            messages.error(request, "Unknown action.")
    except Exception as e:
        logger.error(f"Error performing action {action}: {e}")
        messages.error(request, str(e))

    return redirect('dashboard')


@login_required
def assign_driver(request, booking_id):
    """
    Manage driver assignment for a booking.
    Supports: assign, reassign, unassign, resend notification, and rate adjustment.
    """
    from models import Driver, BookingHistory, ViewedBooking
    from notification_service import NotificationService
    from django.utils import timezone

    if not request.user.is_staff:
        messages.error(request, "Permission denied.")
        return redirect('dashboard')

    booking = get_object_or_404(Booking, id=booking_id)

    # Prevent driver assignment for cancelled or completed trips
    if booking.status in ['Cancelled', 'Cancelled_Full_Charge', 'Trip_Completed']:
        messages.error(request, f"Cannot assign driver to {booking.get_status_display()} trips.")
        return redirect('booking_detail', booking_id=booking.id)

    drivers = Driver.objects.filter(is_active=True).order_by('full_name')

    # Track current assignment for history
    current_driver = booking.assigned_driver
    current_payment = booking.driver_payment_amount

    if request.method == 'POST':
        action = request.POST.get('action')

        # ================================================================
        # UNASSIGN DRIVER
        # ================================================================
        if action == 'unassign':
            if booking.assigned_driver:
                old_driver_name = booking.assigned_driver.full_name
                old_payment = booking.driver_payment_amount

                booking.assigned_driver = None
                booking.driver_notified_at = None
                booking.driver_payment_amount = None
                # Note: driver_response_status has a default, so we don't set it to None
                booking.save(update_fields=[
                    'assigned_driver', 'driver_notified_at', 'driver_payment_amount'
                ])

                # Create history entry for unassignment
                changes = {
                    'assigned_driver': {
                        'old': old_driver_name,
                        'new': None
                    }
                }
                if old_payment:
                    changes['driver_payment_amount'] = {
                        'old': f"${old_payment:.2f}",
                        'new': None
                    }

                BookingHistory.objects.create(
                    booking=booking,
                    action='driver_unassigned',
                    changed_by=request.user,
                    booking_snapshot={},
                    changes=changes,
                    change_reason=f"Driver {old_driver_name} unassigned from trip"
                )

                messages.success(request, f"Driver {old_driver_name} has been unassigned from this trip.")
                return redirect('booking_detail', booking_id=booking.id)
            else:
                messages.warning(request, "No driver is currently assigned to this trip.")
                return redirect('assign_driver', booking_id=booking_id)

        # ================================================================
        # RESEND NOTIFICATION (same driver, optionally update rate)
        # ================================================================
        elif action == 'resend':
            if booking.assigned_driver:
                # Update payment amount if provided
                payment_amount = request.POST.get('payment_amount', '').strip()
                old_payment = booking.driver_payment_amount

                if payment_amount:
                    try:
                        new_payment = float(payment_amount)
                        booking.driver_payment_amount = new_payment
                    except (ValueError, TypeError):
                        messages.error(request, "Invalid payment amount format.")
                        return redirect('assign_driver', booking_id=booking_id)

                # Handle share_driver_info checkbox
                share_driver_info = request.POST.get('share_driver_info') == '1'
                booking.share_driver_info = share_driver_info

                # Resend notification
                NotificationService.send_driver_notification(booking, booking.assigned_driver)
                booking.driver_notified_at = timezone.now()
                booking.save(update_fields=['driver_notified_at', 'driver_payment_amount', 'share_driver_info'])

                # Create history entry if payment changed
                if payment_amount and old_payment != booking.driver_payment_amount:
                    changes = {
                        'driver_payment_amount': {
                            'old': f"${old_payment:.2f}" if old_payment else None,
                            'new': f"${booking.driver_payment_amount:.2f}"
                        }
                    }
                    BookingHistory.objects.create(
                        booking=booking,
                        action='driver_rate_updated',
                        changed_by=request.user,
                        booking_snapshot={},
                        changes=changes,
                        change_reason=f"Driver payment amount updated and notification resent to {booking.assigned_driver.full_name}"
                    )
                    messages.success(request, f"Payment rate updated to ${booking.driver_payment_amount:.2f} and notification resent to {booking.assigned_driver.full_name}.")
                else:
                    messages.success(request, f"Notification resent to {booking.assigned_driver.full_name}.")

                return redirect('booking_detail', booking_id=booking.id)
            else:
                messages.error(request, "No driver is currently assigned. Please assign a driver first.")
                return redirect('assign_driver', booking_id=booking_id)

        # ================================================================
        # ASSIGN or REASSIGN DRIVER
        # ================================================================
        elif action == 'assign' or action == 'reassign':
            driver_id = request.POST.get('driver_id')
            if driver_id:
                try:
                    driver = Driver.objects.get(id=driver_id, is_active=True)

                    # Prevent reassigning the same driver
                    if booking.assigned_driver and booking.assigned_driver.id == driver.id:
                        messages.error(request, f"Driver {driver.full_name} is already assigned to this trip. Please select a different driver.")
                        return redirect('assign_driver', booking_id=booking_id)

                    old_driver_name = booking.assigned_driver.full_name if booking.assigned_driver else None
                    old_payment = booking.driver_payment_amount

                    # Update driver assignment
                    booking.assigned_driver = driver

                    # Handle payment amount if provided
                    payment_amount = request.POST.get('payment_amount', '').strip()
                    if payment_amount:
                        try:
                            booking.driver_payment_amount = float(payment_amount)
                        except (ValueError, TypeError):
                            booking.driver_payment_amount = old_payment  # Keep old payment if new one invalid

                    # Handle admin note if provided
                    admin_note = request.POST.get('admin_note', '').strip()
                    if admin_note:
                        booking.driver_admin_note = admin_note

                    # Handle share_driver_info checkbox
                    share_driver_info = request.POST.get('share_driver_info') == '1'
                    booking.share_driver_info = share_driver_info

                    # Send driver notification email
                    NotificationService.send_driver_notification(booking, driver)
                    booking.driver_notified_at = timezone.now()
                    booking.driver_response_status = 'accepted'  # Admin confirmed driver accepted verbally

                    # Auto-confirm Pending bookings when driver is assigned
                    status_changed = False
                    old_status = booking.status
                    if booking.status == 'Pending':
                        booking.status = 'Confirmed'
                        status_changed = True

                    # Save with specific fields to avoid validation issues
                    save_fields = ['assigned_driver', 'driver_notified_at', 'driver_response_status', 'driver_payment_amount', 'share_driver_info']
                    if admin_note:
                        save_fields.append('driver_admin_note')
                    if status_changed:
                        save_fields.append('status')
                    booking.save(update_fields=save_fields)

                    # Create history entry for assignment/reassignment
                    changes = {
                        'assigned_driver': {
                            'old': old_driver_name,
                            'new': driver.full_name
                        }
                    }
                    if booking.driver_payment_amount and booking.driver_payment_amount != old_payment:
                        changes['driver_payment_amount'] = {
                            'old': f"${old_payment:.2f}" if old_payment else None,
                            'new': f"${booking.driver_payment_amount:.2f}"
                        }
                    if admin_note:
                        changes['driver_admin_note'] = {
                            'old': None,
                            'new': admin_note
                        }
                    if status_changed:
                        changes['status'] = {
                            'old': old_status,
                            'new': 'Confirmed'
                        }

                    action_type = 'driver_reassigned' if old_driver_name else 'driver_assigned'
                    action_desc = f"Driver changed from {old_driver_name} to {driver.full_name}" if old_driver_name else f"Driver {driver.full_name} assigned to trip"
                    if status_changed:
                        action_desc += " and booking auto-confirmed"

                    BookingHistory.objects.create(
                        booking=booking,
                        action=action_type,
                        changed_by=request.user,
                        booking_snapshot={},
                        changes=changes,
                        change_reason=f"{action_desc} (verbally confirmed)"
                    )

                    # Clear any ViewedBooking records so this update appears in user's navbar
                    ViewedBooking.objects.filter(booking=booking, user=booking.user).delete()

                    if old_driver_name and old_driver_name != driver.full_name:
                        success_msg = f"Driver reassigned from {old_driver_name} to {driver.full_name} and notified successfully."
                    else:
                        success_msg = f"Driver {driver.full_name} assigned and notified successfully."

                    if status_changed:
                        success_msg += " Booking status changed to Confirmed."

                    messages.success(request, success_msg)

                    return redirect('booking_detail', booking_id=booking.id)

                except Driver.DoesNotExist:
                    messages.error(request, "Selected driver not found or inactive.")
            else:
                messages.error(request, "Please select a driver.")

    context = {
        'booking': booking,
        'drivers': drivers,
        'current_driver': current_driver,
        'current_payment': current_payment,
    }
    return render(request, 'bookings/assign_driver.html', context)


# ============================================================================
# FREQUENT PASSENGERS
# ============================================================================

@login_required
def frequent_passengers(request):
    """Display and manage user's frequent passengers list."""
    passengers = FrequentPassenger.objects.filter(user=request.user)

    if request.method == "POST":
        form = FrequentPassengerForm(request.POST)
        if form.is_valid():
            passenger = form.save(commit=False)
            passenger.user = request.user
            passenger.save()
            messages.success(request, "Passenger added successfully.")
            return redirect('frequent_passengers')
    else:
        form = FrequentPassengerForm()

    return render(request, 'bookings/frequent_passengers.html', {
        'passengers': passengers,
        'form': form
    })


@login_required
def edit_passenger(request, passenger_id):
    """Edit a frequent passenger's details."""
    passenger = get_object_or_404(FrequentPassenger, id=passenger_id, user=request.user)

    if request.method == "POST":
        form = FrequentPassengerForm(request.POST, instance=passenger)
        if form.is_valid():
            form.save()
            messages.success(request, f"'{passenger.name}' updated successfully.")
            return redirect('frequent_passengers')
    else:
        form = FrequentPassengerForm(instance=passenger)

    passengers = FrequentPassenger.objects.filter(user=request.user)

    return render(request, 'bookings/frequent_passengers.html', {
        'passengers': passengers,
        'form': form,
        'editing_passenger': passenger
    })


@login_required
def delete_passenger(request, passenger_id):
    """Remove a frequent passenger from user's list."""
    passenger = get_object_or_404(FrequentPassenger, id=passenger_id, user=request.user)

    if request.method == "POST":
        passenger.delete()
        messages.success(request, "Passenger deleted.")

    return redirect('frequent_passengers')


# ============================================================================
# USER PROFILE
# ============================================================================

@login_required
def edit_profile(request):
    """Manage user profile, password, and view booking history."""
    from django.contrib.auth.forms import PasswordChangeForm
    from django.contrib.auth import update_session_auth_hash

    profile_form = None
    password_form = None

    if request.method == "POST":
        if 'update_profile' in request.POST:
            profile_form = UserProfileForm(request.user, request.POST)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, "Profile updated successfully.")
                logger.info(f"User {request.user.username} updated their profile")
                return redirect('edit_profile')
            else:
                password_form = PasswordChangeForm(request.user)

        elif 'change_password' in request.POST:
            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, "Password changed successfully.")
                logger.info(f"User {request.user.username} changed their password")
                return redirect('edit_profile')
            else:
                profile_form = UserProfileForm(request.user)
    else:
        profile_form = UserProfileForm(request.user)
        password_form = PasswordChangeForm(request.user)

    user_bookings = Booking.objects.filter(user=request.user).order_by('-pick_up_date', '-pick_up_time')

    total_bookings = user_bookings.count()
    completed_trips = user_bookings.filter(status='Trip_Completed').count()
    active_bookings = user_bookings.filter(status__in=['Pending', 'Confirmed']).count()
    cancelled_bookings = user_bookings.filter(status__in=['Cancelled', 'Cancelled_Full_Charge']).count()

    recent_bookings = user_bookings[:10]

    from datetime import date
    upcoming_bookings = user_bookings.filter(
        pick_up_date__gte=date.today()
    ).exclude(
        status__in=['Cancelled', 'Trip_Completed']
    ).order_by('pick_up_date', 'pick_up_time')

    from models import UserProfile
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)

    context = {
        'profile_form': profile_form,
        'password_form': password_form,
        'user_profile': user_profile,
        'total_bookings': total_bookings,
        'completed_trips': completed_trips,
        'active_bookings': active_bookings,
        'cancelled_bookings': cancelled_bookings,
        'recent_bookings': recent_bookings,
        'upcoming_bookings': upcoming_bookings,
    }

    return render(request, 'bookings/edit_profile.html', context)


# ============================================================================
# DRIVER PORTAL
# ============================================================================

def driver_trip_response(request, booking_id, token):
    """
    Simple driver portal for reporting trip completion.
    Accessed via a unique URL sent in driver notification email.
    """
    from models import Driver
    import hashlib

    # Get the booking
    booking = get_object_or_404(Booking, id=booking_id)

    # Verify the booking has an assigned driver
    if not booking.assigned_driver:
        messages.error(request, "This trip does not have an assigned driver.")
        return render(request, 'driver/trip_response.html', {'booking': booking, 'invalid': True})

    # Simple token verification (token = hash of booking_id + driver email)
    expected_token = hashlib.md5(f"{booking_id}-{booking.assigned_driver.email}".encode()).hexdigest()[:16]
    if token != expected_token:
        messages.error(request, "Invalid access link. Please use the link from your email.")
        return render(request, 'driver/trip_response.html', {'booking': booking, 'invalid': True})

    if request.method == 'POST':
        action = request.POST.get('action')
        from models import BookingHistory

        if action == 'complete':
            # Enforce 5-hour rule: Can only mark complete AFTER 5 hours from scheduled pickup time
            from datetime import datetime, timedelta

            pickup_datetime = datetime.combine(booking.pick_up_date, booking.pick_up_time)
            now = timezone.now()

            # Convert pickup_datetime to aware datetime if needed
            if timezone.is_naive(pickup_datetime):
                pickup_datetime = timezone.make_aware(pickup_datetime)

            # Calculate time elapsed since pickup (negative if pickup is in future)
            time_since_pickup = now - pickup_datetime

            # Require at least 5 hours to have passed since scheduled pickup time
            if time_since_pickup < timedelta(hours=5):
                # Trip hasn't started yet or hasn't been running for 5 hours
                if time_since_pickup < timedelta(0):
                    # Pickup is in the future
                    hours_until = abs(int(time_since_pickup.total_seconds() / 3600))
                    messages.error(
                        request,
                        f"Cannot mark trip as completed. Trip is scheduled for {booking.pick_up_date.strftime('%B %d, %Y')} "
                        f"at {booking.pick_up_time.strftime('%I:%M %p')} ({hours_until} hours from now). "
                        f"You can mark it complete only after the trip has been running for at least 5 hours."
                    )
                else:
                    # Pickup has passed but less than 5 hours ago
                    hours_elapsed = int(time_since_pickup.total_seconds() / 3600)
                    hours_remaining = 5 - hours_elapsed
                    messages.error(
                        request,
                        f"Cannot mark trip as completed yet. Only {hours_elapsed} hour(s) have passed since pickup. "
                        f"You must wait {hours_remaining} more hour(s) before marking this trip as completed."
                    )
                return render(request, 'driver/trip_response.html', {'booking': booking})

            old_status = booking.status
            booking.driver_response_status = 'completed'
            booking.driver_completed_at = timezone.now()
            booking.driver_response_at = timezone.now()

            # Update trip status to Trip_Completed
            booking.status = 'Trip_Completed'
            booking.save()

            # Create history entry for driver completion
            BookingHistory.objects.create(
                booking=booking,
                action='driver_completed',
                changed_by=None,  # Driver action, not a system user
                booking_snapshot={},
                changes={
                    'driver_response_status': {
                        'old': 'accepted',
                        'new': 'completed'
                    },
                    'status': {
                        'old': old_status,
                        'new': 'Trip_Completed'
                    }
                },
                change_reason=f"Driver {booking.assigned_driver.full_name} marked trip as completed"
            )

            # Notify admin about trip completion
            NotificationService.send_driver_completion_notification(booking)

            messages.success(request, "Trip marked as completed. Thank you for your service!")

        else:
            messages.error(request, "Invalid action selected.")

    return render(request, 'driver/trip_response.html', {'booking': booking})


@login_required
@staff_member_required
def resend_driver_notification(request, booking_id):
    """Resend driver portal link (e.g., if driver deleted the email)."""
    booking = get_object_or_404(Booking, id=booking_id)

    if not booking.assigned_driver:
        messages.error(request, "No driver assigned to this trip.")
        return redirect('booking_detail', booking_id=booking.id)

    from notification_service import NotificationService
    success = NotificationService.send_driver_notification(booking, booking.assigned_driver)

    if success:
        messages.success(request, f"Driver notification resent to {booking.assigned_driver.full_name}.")
    else:
        messages.error(request, "Failed to resend driver notification. Please check email settings.")

    return redirect('booking_detail', booking_id=booking.id)


def driver_trips_list(request, driver_email, token):
    """
    Show all trips assigned to a driver (accessed via secure token).
    Allows driver to see all their assignments in one place and complete trips directly.
    Each leg of a round trip is treated as a separate assignment.
    """
    import hashlib
    from models import Driver, BookingHistory
    from datetime import datetime, timedelta

    # Find driver by email (use first() to handle duplicates gracefully)
    try:
        driver = Driver.objects.filter(email=driver_email, is_active=True).first()
        if not driver:
            raise Driver.DoesNotExist
    except Driver.DoesNotExist:
        messages.error(request, "Driver not found.")
        return render(request, 'driver/trips_list.html', {'invalid': True})

    # Verify token (token = hash of driver email)
    expected_token = hashlib.md5(driver_email.encode()).hexdigest()[:16]
    if token != expected_token:
        messages.error(request, "Invalid access link.")
        return render(request, 'driver/trips_list.html', {'invalid': True})

    # Handle trip completion POST request
    if request.method == 'POST':
        booking_id = request.POST.get('booking_id')
        action = request.POST.get('action')

        if action == 'complete' and booking_id:
            try:
                booking = Booking.objects.get(id=booking_id, assigned_driver=driver)

                # Verify token for this specific booking
                booking_token = hashlib.md5(f"{booking.id}-{driver.email}".encode()).hexdigest()[:16]
                submitted_token = request.POST.get('booking_token')

                if booking_token != submitted_token:
                    messages.error(request, "Invalid request token.")
                else:
                    # Check 5-hour rule: Can only mark complete AFTER 5 hours from scheduled pickup time
                    pickup_datetime = datetime.combine(booking.pick_up_date, booking.pick_up_time)
                    now = timezone.now()

                    if timezone.is_naive(pickup_datetime):
                        pickup_datetime = timezone.make_aware(pickup_datetime)

                    # Calculate time elapsed since pickup
                    time_since_pickup = now - pickup_datetime

                    # Require at least 5 hours to have passed since scheduled pickup time
                    if time_since_pickup < timedelta(hours=5):
                        # Trip hasn't been running for 5 hours yet
                        if time_since_pickup < timedelta(0):
                            # Pickup is in the future
                            hours_until = abs(int(time_since_pickup.total_seconds() / 3600))
                            messages.error(
                                request,
                                f"Cannot mark trip #{booking.id} as completed. Trip is scheduled for "
                                f"{booking.pick_up_date.strftime('%B %d, %Y')} at {booking.pick_up_time.strftime('%I:%M %p')} "
                                f"({hours_until} hours from now). You can mark it complete only after the trip has been running for at least 5 hours."
                            )
                        else:
                            # Pickup has passed but less than 5 hours ago
                            hours_elapsed = int(time_since_pickup.total_seconds() / 3600)
                            hours_remaining = 5 - hours_elapsed
                            messages.error(
                                request,
                                f"Cannot mark trip #{booking.id} as completed yet. Only {hours_elapsed} hour(s) have passed since pickup. "
                                f"You must wait {hours_remaining} more hour(s) before marking this trip as completed."
                            )
                    else:
                        # Mark as completed
                        old_status = booking.status
                        booking.driver_response_status = 'completed'
                        booking.driver_completed_at = timezone.now()
                        booking.driver_response_at = timezone.now()
                        booking.status = 'Trip_Completed'
                        booking.save()

                        # Create history entry
                        BookingHistory.objects.create(
                            booking=booking,
                            action='driver_completed',
                            changed_by=None,
                            booking_snapshot={},
                            changes={
                                'driver_response_status': {'old': 'accepted', 'new': 'completed'},
                                'status': {'old': old_status, 'new': 'Trip_Completed'}
                            },
                            change_reason=f"Driver {driver.full_name} marked trip as completed"
                        )

                        # Notify admin
                        from notification_service import NotificationService
                        NotificationService.send_driver_completion_notification(booking)

                        messages.success(request, f"Trip #{booking.id} marked as completed successfully!")

            except Booking.DoesNotExist:
                messages.error(request, "Trip not found or not assigned to you.")
            except Exception as e:
                messages.error(request, f"Error completing trip: {str(e)}")

        # Redirect to avoid form resubmission
        return redirect('driver_trips_list', driver_email=driver_email, token=token)

    # Get ALL trips assigned to this driver (including round-trip return legs)
    trips = Booking.objects.filter(
        assigned_driver=driver
    ).select_related(
        'user', 'linked_booking'
    ).order_by('pick_up_date', 'pick_up_time')

    # Separate into categories and generate trip-specific tokens
    upcoming_trips = []
    completed_trips = []

    for trip in trips:
        # Generate trip-specific token for URL generation and attach to trip object
        trip.trip_token = hashlib.md5(f"{trip.id}-{driver.email}".encode()).hexdigest()[:16]

        # Check if trip can be completed (only after 5 hours from scheduled pickup time)
        pickup_datetime = datetime.combine(trip.pick_up_date, trip.pick_up_time)
        now = timezone.now()
        if timezone.is_naive(pickup_datetime):
            pickup_datetime = timezone.make_aware(pickup_datetime)
        time_since_pickup = now - pickup_datetime
        # Can complete only if at least 5 hours have passed since pickup time
        trip.can_complete = time_since_pickup >= timedelta(hours=5)

        if trip.driver_response_status == 'completed' or trip.status == 'Trip_Completed':
            completed_trips.append(trip)
        else:
            upcoming_trips.append(trip)

    context = {
        'driver': driver,
        'upcoming_trips': upcoming_trips,
        'completed_trips': completed_trips,
        'token': token,
    }

    return render(request, 'driver/trips_list.html', context)


@login_required
@staff_member_required
def mark_driver_paid(request, booking_id):
    """Mark a driver as paid for a completed trip."""
    booking = get_object_or_404(Booking, id=booking_id)

    if not booking.assigned_driver:
        messages.error(request, "No driver assigned to this trip.")
        return redirect('booking_detail', booking_id=booking.id)

    if booking.driver_response_status != 'completed':
        messages.error(request, "Trip must be marked as completed by driver before marking as paid.")
        return redirect('booking_detail', booking_id=booking.id)

    if booking.driver_paid:
        messages.warning(request, "Driver has already been marked as paid.")
        return redirect('booking_detail', booking_id=booking.id)

    # Mark as paid
    from django.utils import timezone
    from models import BookingHistory

    booking.driver_paid = True
    booking.driver_paid_at = timezone.now()
    booking.driver_paid_by = request.user
    booking.save()

    # Create history entry
    BookingHistory.objects.create(
        booking=booking,
        action='updated',
        changed_by=request.user,
        booking_snapshot={},
        changes={
            'driver_paid': {
                'old': 'Unpaid',
                'new': 'Paid'
            }
        },
        change_reason=f"Driver {booking.assigned_driver.full_name} marked as paid by {request.user.username}"
    )

    payment_msg = f" (${booking.driver_payment_amount:.2f})" if booking.driver_payment_amount else ""
    messages.success(request, f"Driver {booking.assigned_driver.full_name} marked as paid{payment_msg}.")
    return redirect('booking_detail', booking_id=booking.id)


@login_required
@staff_member_required
def driver_list_by_driver(request, driver_id):
    """Admin view to see all bookings assigned to a specific driver."""
    from models import Driver, Booking
    from django.db import models

    driver = get_object_or_404(Driver, id=driver_id)

    trips = Booking.objects.filter(
        assigned_driver=driver
    ).exclude(
        is_return_trip=True
    ).select_related(
        'user'
    ).order_by('-pick_up_date', '-pick_up_time')

    # Calculate stats
    total_trips = trips.count()
    completed_trips = trips.filter(driver_response_status='completed').count()
    upcoming_trips = trips.exclude(driver_response_status='completed').count()

    # Payment stats
    total_owed = trips.filter(
        driver_response_status='completed',
        driver_paid=False,
        driver_payment_amount__isnull=False
    ).aggregate(total=models.Sum('driver_payment_amount'))['total'] or 0

    total_paid = trips.filter(
        driver_paid=True,
        driver_payment_amount__isnull=False
    ).aggregate(total=models.Sum('driver_payment_amount'))['total'] or 0

    context = {
        'driver': driver,
        'trips': trips,
        'total_trips': total_trips,
        'completed_trips': completed_trips,
        'upcoming_trips': upcoming_trips,
        'total_owed': total_owed,
        'total_paid': total_paid,
    }

    return render(request, 'bookings/driver_trip_list_admin.html', context)


# ============================================================================
# ADMIN UTILITIES
# ============================================================================

@staff_member_required
def test_email(request):
    """Send test email to verify email configuration."""
    results = {
        'success': False,
        'message': None
    }

    if request.method == "GET":
        admin_email = request.GET.get('email') or request.user.email
        results = EmailService.send_test_email(admin_email)

    return render(request, 'bookings/email_test.html', {
        'results': results
    })


@login_required
def special_request_response(request):
    """Handle admin response to customer special requests via AJAX."""
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)

    booking_id = request.POST.get('booking_id')
    customer_communication = request.POST.get('customer_communication', '').strip()
    send_email = request.POST.get('send_email', 'false') == 'true'

    if not booking_id:
        return JsonResponse({'success': False, 'error': 'Booking ID required'}, status=400)

    try:
        booking = get_object_or_404(Booking, id=booking_id)

        if not customer_communication:
            return JsonResponse({'success': False, 'error': 'Response message required'}, status=400)

        booking.customer_communication = customer_communication
        if send_email:
            booking.communication_sent_at = timezone.now()

        booking.save(update_fields=['customer_communication', 'communication_sent_at', 'updated_at'])

        if send_email:
            try:
                NotificationService.send_notification(
                    booking=booking,
                    notification_type='status_change',
                    subject=f'Message from M1 Limo - Booking #{booking.id}'
                )
            except Exception as e:
                logger.warning(f"Failed to send notification for customer communication: {e}")

        logger.info(f"Admin {request.user.username} sent customer communication for booking {booking.id}")

        return JsonResponse({
            'success': True,
            'message': 'Communication sent successfully' if send_email else 'Communication saved successfully',
            'booking_id': booking.id
        })

    except Exception as e:
        logger.error(f"Error in special_request_response: {e}", exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# Custom error handlers
def custom_404(request, exception):
    """Custom 404 error page."""
    return render(request, '404.html', status=404)

def custom_500(request):
    """Custom 500 error page."""
    return render(request, '500.html', status=500)

