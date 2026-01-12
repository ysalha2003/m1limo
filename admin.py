# bookings/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.contrib.auth.models import User
from datetime import timedelta
from models import (
    Booking, BookingStop, SystemSettings, BookingPermission,
    NotificationRecipient, BookingNotification, FrequentPassenger,
    Notification, CommunicationLog, AdminNote, Driver
)
from booking_service import BookingService
import logging

logger = logging.getLogger('bookings')


@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    list_display = ('allow_confirmed_edits', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')

    def has_add_permission(self, request):
        return not SystemSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(BookingPermission)
class BookingPermissionAdmin(admin.ModelAdmin):
    list_display = ('user', 'can_edit_confirmed', 'updated_at')
    list_filter = ('can_edit_confirmed',)
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')


class BookingStopInline(admin.TabularInline):
    model = BookingStop
    extra = 0
    fields = ('stop_number', 'address', 'is_return_stop')


class CommunicationLogInline(admin.TabularInline):
    model = CommunicationLog
    extra = 1
    fields = ('communication_type', 'staff_member', 'communication_date', 'notes')
    readonly_fields = ('created_at',)

    def save_model(self, request, obj, form, change):
        if not obj.staff_member:
            obj.staff_member = request.user
        super().save_model(request, obj, form, change)


class AdminNoteInline(admin.StackedInline):
    model = AdminNote
    extra = 1
    fields = ('note', 'staff_member', 'created_at')
    readonly_fields = ('staff_member', 'created_at')
    can_delete = False

    def save_model(self, request, obj, form, change):
        if not obj.staff_member:
            obj.staff_member = request.user
        super().save_model(request, obj, form, change)


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'passenger_name', 'status_badge', 'pick_up_date',
        'pick_up_time', 'vehicle_type', 'trip_type', 'user'
    )
    list_filter = ('status', 'vehicle_type', 'trip_type', 'pick_up_date')
    search_fields = ('passenger_name', 'phone_number', 'pick_up_address', 'user__username')
    date_hierarchy = 'pick_up_date'
    readonly_fields = (
        'created_at', 'updated_at', 'driver_response_status',
        'driver_response_at', 'driver_rejection_reason', 'driver_completed_at'
    )
    inlines = [BookingStopInline, CommunicationLogInline, AdminNoteInline]
    
    fieldsets = (
        ('Customer Information', {
            'fields': ('user', 'passenger_name', 'phone_number', 'passenger_email')
        }),
        ('Trip Details', {
            'fields': (
                'trip_type', 'vehicle_type', 'number_of_passengers',
                'pick_up_address', 'drop_off_address',
                'pick_up_date', 'pick_up_time',
                'flight_number', 'notes'
            )
        }),
        ('Return Trip Details', {
            'fields': (
                'return_date', 'return_time',
                'return_pickup_address', 'return_dropoff_address',
                'return_flight_number', 'return_special_requests'
            ),
            'classes': ('collapse',),
        }),
        ('Hourly Service', {
            'fields': ('hours_booked',),
            'classes': ('collapse',),
        }),
        ('Status & Admin', {
            'fields': (
                'status', 'admin_comment', 'cancellation_reason'
            )
        }),
        ('Driver Assignment', {
            'fields': (
                'assigned_driver', 'driver_notified_at',
                'driver_response_status', 'driver_response_at',
                'driver_rejection_reason', 'driver_completed_at'
            ),
            'classes': ('collapse',),
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        """Display colored status badge."""
        return format_html(
            '<span class="badge {}">{}</span>',
            obj.status_color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def save_model(self, request, obj, form, change):
        """Handle all updates through service layer with validation and history tracking."""
        from django.core.exceptions import ValidationError as DjangoValidationError
        from django.contrib import messages as django_messages

        if change:
            try:
                old_obj = Booking.objects.get(pk=obj.pk)

                # Collect all changed fields
                changed_fields = {}
                for field in form.changed_data:
                    if hasattr(obj, field):
                        changed_fields[field] = getattr(obj, field)

                if changed_fields:
                    # If only status changed, use update_booking_status
                    if len(changed_fields) == 1 and 'status' in changed_fields:
                        try:
                            BookingService.update_booking_status(
                                booking=old_obj,
                                new_status=obj.status,
                                admin_comment=obj.admin_comment,
                                changed_by=request.user
                            )
                            django_messages.success(request, f"Booking status updated to {obj.get_status_display()}")
                            return
                        except DjangoValidationError as e:
                            error_messages = e.messages if hasattr(e, 'messages') else [str(e)]
                            for error_msg in error_messages:
                                if "Cannot transition" in error_msg:
                                    django_messages.error(
                                        request,
                                        f"Cannot change status from '{old_obj.get_status_display()}' to '{obj.get_status_display()}'. "
                                        f"This status change is not allowed for this booking."
                                    )
                                else:
                                    django_messages.error(request, error_msg)
                            obj.status = old_obj.status
                            return
                    else:
                        # Multiple fields changed or non-status fields changed - use update_booking
                        try:
                            BookingService.update_booking(
                                booking=old_obj,
                                booking_data=changed_fields,
                                changed_by=request.user
                            )
                            django_messages.success(request, "Booking updated successfully")
                            return
                        except DjangoValidationError as e:
                            error_messages = e.messages if hasattr(e, 'messages') else [str(e)]
                            for error_msg in error_messages:
                                django_messages.error(request, error_msg)
                            return
            except Booking.DoesNotExist:
                pass

        super().save_model(request, obj, form, change)
    
    actions = [
        'mark_as_confirmed', 'mark_as_pending',
        'mark_as_completed', 'mark_as_cancelled', 'mark_as_no_show'
    ]

    def mark_as_confirmed(self, request, queryset):
        """Mark selected bookings as Confirmed."""
        count = 0
        for booking in queryset:
            if booking.status != 'Confirmed':
                try:
                    BookingService.update_booking_status(booking, 'Confirmed', changed_by=request.user)
                    count += 1
                except Exception as e:
                    logger.error(f"Error confirming booking {booking.id}: {e}")

        self.message_user(request, f"Confirmed {count} booking(s)")
    mark_as_confirmed.short_description = "Mark as Confirmed"

    def mark_as_pending(self, request, queryset):
        """Mark selected bookings as Pending."""
        count = 0
        for booking in queryset:
            if booking.status != 'Pending':
                try:
                    BookingService.update_booking_status(booking, 'Pending', changed_by=request.user)
                    count += 1
                except Exception as e:
                    logger.error(f"Error marking booking {booking.id} as pending: {e}")

        self.message_user(request, f"Marked {count} booking(s) as Pending")
    mark_as_pending.short_description = "Mark as Pending"

    def mark_as_completed(self, request, queryset):
        """Mark selected bookings as Trip Completed."""
        count = 0
        for booking in queryset:
            if booking.status != 'Trip_Completed':
                try:
                    BookingService.update_booking_status(booking, 'Trip_Completed', changed_by=request.user)
                    count += 1
                except Exception as e:
                    logger.error(f"Error completing booking {booking.id}: {e}")

        self.message_user(request, f"Marked {count} booking(s) as Completed")
    mark_as_completed.short_description = "Mark as Trip Completed"

    def mark_as_cancelled(self, request, queryset):
        """Cancel selected bookings with 4-hour policy enforcement."""
        from django.contrib import messages
        count = 0
        charged_count = 0
        past_count = 0

        for booking in queryset:
            if booking.status not in ['Cancelled', 'Cancelled_Full_Charge']:
                try:
                    can_cancel, will_charge, hours_until = booking.can_cancel()

                    if can_cancel:
                        new_status = 'Cancelled_Full_Charge' if will_charge else 'Cancelled'
                        BookingService.update_booking_status(booking, new_status, changed_by=request.user)
                        count += 1
                        if will_charge:
                            charged_count += 1
                    else:
                        past_count += 1
                        logger.warning(f"Cannot cancel past booking #{booking.id}")

                except Exception as e:
                    logger.error(f"Error cancelling booking {booking.id}: {e}")

        msg = f"Cancelled {count} booking(s)"
        if charged_count > 0:
            msg += f" ({charged_count} with full charge due to 4-hour policy)"
        if past_count > 0:
            self.message_user(
                request,
                f"{msg}. Could not cancel {past_count} past booking(s).",
                level=messages.WARNING
            )
        else:
            self.message_user(request, msg)

    mark_as_cancelled.short_description = "Mark as Cancelled (applies 4-hour policy)"

    def mark_as_no_show(self, request, queryset):
        """Mark selected bookings as Customer No-Show."""
        count = 0
        for booking in queryset:
            if booking.status != 'Customer_No_Show':
                try:
                    BookingService.update_booking_status(booking, 'Customer_No_Show', changed_by=request.user)
                    count += 1
                except Exception as e:
                    logger.error(f"Error marking booking {booking.id} as no-show: {e}")

        self.message_user(request, f"Marked {count} booking(s) as No-Show")
    mark_as_no_show.short_description = "Mark as Customer No-Show"


@admin.register(BookingStop)
class BookingStopAdmin(admin.ModelAdmin):
    list_display = ('booking', 'stop_number', 'address', 'is_return_stop')
    list_filter = ('is_return_stop',)
    search_fields = ('booking__passenger_name', 'address')


@admin.register(NotificationRecipient)
class NotificationRecipientAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'is_active', 'notify_new', 'notify_confirmed', 'notify_cancelled', 'notify_status_changes', 'notify_reminders')
    list_filter = ('is_active', 'notify_new', 'notify_confirmed', 'notify_cancelled', 'notify_status_changes', 'notify_reminders')
    search_fields = ('name', 'email')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(BookingNotification)
class BookingNotificationAdmin(admin.ModelAdmin):
    list_display = ('booking', 'recipient', 'created_at')
    search_fields = ('booking__passenger_name', 'recipient__name', 'recipient__email')


@admin.register(FrequentPassenger)
class FrequentPassengerAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone_number', 'email', 'user')
    list_filter = ('user',)
    search_fields = ('name', 'phone_number', 'email', 'user__username')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('booking', 'notification_type', 'channel', 'recipient', 'sent_at', 'success_badge')
    list_filter = ('notification_type', 'channel', 'success', 'sent_at')
    search_fields = ('booking__passenger_name', 'recipient')
    readonly_fields = ('sent_at',)
    date_hierarchy = 'sent_at'

    def success_badge(self, obj):
        """Display success/failure badge."""
        if obj.success:
            return format_html('<span style="color: green;">{} Success</span>', '✓')
        else:
            return format_html('<span style="color: red;">{} Failed</span>', '✗')
    success_badge.short_description = 'Status'


@admin.register(CommunicationLog)
class CommunicationLogAdmin(admin.ModelAdmin):
    list_display = ('booking', 'communication_type', 'staff_member', 'communication_date', 'notes_preview')
    list_filter = ('communication_type', 'staff_member', 'communication_date')
    search_fields = ('booking__passenger_name', 'notes', 'staff_member__username')
    readonly_fields = ('created_at',)
    date_hierarchy = 'communication_date'

    def notes_preview(self, obj):
        """Show first 50 characters of notes."""
        return obj.notes[:50] + '...' if len(obj.notes) > 50 else obj.notes
    notes_preview.short_description = 'Notes'

    def save_model(self, request, obj, form, change):
        if not obj.staff_member:
            obj.staff_member = request.user
        super().save_model(request, obj, form, change)


@admin.register(AdminNote)
class AdminNoteAdmin(admin.ModelAdmin):
    list_display = ('booking', 'staff_member', 'note_preview', 'created_at')
    list_filter = ('staff_member', 'created_at')
    search_fields = ('booking__passenger_name', 'note', 'staff_member__username')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'

    def note_preview(self, obj):
        """Show first 100 characters of note."""
        return obj.note[:100] + '...' if len(obj.note) > 100 else obj.note
    note_preview.short_description = 'Note'

    def save_model(self, request, obj, form, change):
        if not obj.staff_member:
            obj.staff_member = request.user
        super().save_model(request, obj, form, change)


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'car_type', 'car_number', 'phone_number', 'email', 'is_active')
    list_filter = ('is_active', 'car_type')
    search_fields = ('full_name', 'car_number', 'email', 'phone_number')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('full_name',)

    fieldsets = (
        ('Driver Information', {
            'fields': ('full_name', 'phone_number', 'email')
        }),
        ('Vehicle Information', {
            'fields': ('car_type', 'car_number')
        }),
        ('Status & Notes', {
            'fields': ('is_active', 'notes')
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
