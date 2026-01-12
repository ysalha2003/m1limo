# context_processors.py
from models import BookingHistory, Booking, ViewedActivity, ViewedBooking
from django.utils import timezone
from datetime import timedelta

def recent_activity(request):
    """Add recent booking activity to all page contexts for navbar dropdown."""
    context = {
        'recent_activities': [],
        'recent_activity_count': 0,
        'user_recent_bookings': [],
        'user_upcoming_bookings': [],
        'user_bookings_count': 0,
    }

    if request.user.is_authenticated:
        # For admin users: system-wide activity audit trail
        # Show activities from USER actions (bookings created/updated by users)
        # Exclude admin's own actions since they already know what they did
        if request.user.is_staff:
            # Get IDs of activities this user has already viewed
            viewed_activity_ids = ViewedActivity.objects.filter(
                user=request.user
            ).values_list('activity_id', flat=True)

            # Get recent activities created by NON-STAFF users (customer actions)
            # Exclude activities where admin was the one who made the change
            activities_queryset = BookingHistory.objects.select_related(
                'booking',
                'booking__user',
                'changed_by'
            ).filter(
                changed_by__is_staff=False  # Only show activities from regular users
            ).exclude(
                id__in=viewed_activity_ids
            ).order_by('-changed_at')

            # Count total unviewed activities
            context['recent_activity_count'] = activities_queryset.count()
            # Get last 10 for dropdown display
            context['recent_activities'] = activities_queryset[:10]

        # For all authenticated users: their personal booking activity
        # Show bookings that have been updated by admin (status changes, confirmations, etc.)
        today = timezone.now().date()

        # Get IDs of bookings this user has already viewed
        viewed_booking_ids = ViewedBooking.objects.filter(
            user=request.user
        ).values_list('booking_id', flat=True)

        # Get bookings that have been updated by admin (changed_by is staff)
        # This shows bookings with admin actions like status changes, confirmations, driver assignments
        bookings_with_admin_updates = BookingHistory.objects.filter(
            booking__user=request.user,
            changed_by__is_staff=True  # Only show updates made by admin
        ).values_list('booking_id', flat=True).distinct()

        # Get user's upcoming bookings with admin updates, excluding viewed ones
        upcoming = Booking.objects.filter(
            user=request.user,
            pick_up_date__gte=today,
            status__in=['Pending', 'Confirmed'],
            id__in=bookings_with_admin_updates  # Only show bookings with admin updates
        ).exclude(
            is_return_trip=True
        ).exclude(
            id__in=viewed_booking_ids
        ).order_by('pick_up_date', 'pick_up_time')[:5]

        # Get user's recent bookings with admin updates, excluding viewed ones
        recent = Booking.objects.filter(
            user=request.user,
            id__in=bookings_with_admin_updates  # Only show bookings with admin updates
        ).exclude(
            is_return_trip=True
        ).exclude(
            id__in=viewed_booking_ids
        ).order_by('-pick_up_date', '-pick_up_time')[:5]

        context['user_upcoming_bookings'] = upcoming
        context['user_recent_bookings'] = recent
        # Count only unviewed bookings with admin updates for badge
        context['user_bookings_count'] = Booking.objects.filter(
            user=request.user,
            id__in=bookings_with_admin_updates  # Only count bookings with admin updates
        ).exclude(
            is_return_trip=True
        ).exclude(
            id__in=viewed_booking_ids
        ).count()

    return context
