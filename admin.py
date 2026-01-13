# bookings/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.contrib.auth.models import User
from datetime import timedelta
from models import (
    Booking, BookingStop, SystemSettings, BookingPermission,
    NotificationRecipient, BookingNotification, FrequentPassenger,
    Notification, CommunicationLog, AdminNote, Driver,
    BookingHistory, UserProfile, ViewedActivity, ViewedBooking,
    EmailTemplate
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
        'booking_reference', 'created_at', 'updated_at', 'driver_response_status',
        'driver_response_at', 'driver_rejection_reason', 'driver_completed_at',
        'driver_notified_at', 'communication_sent_at'
    )
    inlines = [BookingStopInline, CommunicationLogInline, AdminNoteInline]
    
    fieldsets = (
        ('Customer Information', {
            'fields': ('booking_reference', 'user', 'passenger_name', 'phone_number', 'passenger_email')
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
                'status', 'admin_comment', 'cancellation_reason',
                'customer_communication', 'communication_sent_at'
            )
        }),
        ('Round Trip Details', {
            'fields': (
                'is_return_trip', 'linked_booking'
            ),
            'classes': ('collapse',),
        }),
        ('Driver Assignment', {
            'fields': (
                'assigned_driver', 'share_driver_info', 'driver_admin_note',
                'driver_notified_at', 'driver_response_status', 'driver_response_at',
                'driver_rejection_reason', 'driver_completed_at'
            ),
            'classes': ('collapse',),
        }),
        ('Driver Payment', {
            'fields': (
                'driver_payment_amount', 'driver_paid',
                'driver_paid_at', 'driver_paid_by'
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


@admin.register(BookingHistory)
class BookingHistoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'booking_link', 'action', 'changed_by', 'changed_at', 'changes_preview')
    list_filter = ('action', 'changed_by', 'changed_at')
    search_fields = ('booking__booking_reference', 'booking__passenger_name', 'booking__id', 'change_reason')
    readonly_fields = ('booking', 'action', 'changed_by', 'changed_at', 'booking_snapshot', 'changes', 'change_reason', 'ip_address')
    date_hierarchy = 'changed_at'
    ordering = ('-changed_at',)

    fieldsets = (
        ('Basic Information', {
            'fields': ('booking', 'action', 'changed_by', 'changed_at')
        }),
        ('Change Details', {
            'fields': ('change_reason', 'changes', 'ip_address')
        }),
        ('Complete Snapshot', {
            'fields': ('booking_snapshot',),
            'classes': ('collapse',),
            'description': 'Complete booking data at this point in time'
        }),
    )

    def has_add_permission(self, request):
        """Prevent manual creation - audit trail only."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion - audit trail must be preserved."""
        return False

    def booking_link(self, obj):
        """Link to the related booking."""
        from django.urls import reverse
        from django.utils.html import format_html
        if obj.booking:
            url = reverse('admin:bookings_booking_change', args=[obj.booking.id])
            return format_html('<a href="{}">{} - {}</a>', url, obj.booking.booking_reference, obj.booking.passenger_name)
        return '-'
    booking_link.short_description = 'Booking'

    def changes_preview(self, obj):
        """Show preview of changes."""
        if obj.changes and isinstance(obj.changes, dict):
            fields = list(obj.changes.keys())[:3]
            preview = ', '.join(fields)
            if len(obj.changes) > 3:
                preview += f' (+{len(obj.changes) - 3} more)'
            return preview
        elif obj.change_reason:
            return obj.change_reason[:50] + '...' if len(obj.change_reason) > 50 else obj.change_reason
        return '-'
    changes_preview.short_description = 'Changes'


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'company_name', 'receive_booking_confirmations', 'receive_status_updates', 'receive_pickup_reminders')
    list_filter = ('receive_booking_confirmations', 'receive_status_updates', 'receive_pickup_reminders')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name', 'phone_number', 'company_name')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('user__username',)

    fieldsets = (
        ('User Information', {
            'fields': ('user', 'phone_number', 'company_name')
        }),
        ('Notification Preferences', {
            'fields': (
                'receive_booking_confirmations',
                'receive_status_updates',
                'receive_pickup_reminders'
            ),
            'description': 'Email notification preferences for this user'
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


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


@admin.register(ViewedActivity)
class ViewedActivityAdmin(admin.ModelAdmin):
    """Admin interface for debugging activity notifications."""
    list_display = ('user', 'activity_link', 'viewed_at')
    list_filter = ('user', 'viewed_at')
    search_fields = ('user__username', 'activity__booking__passenger_name', 'activity__booking__booking_reference')
    readonly_fields = ('user', 'activity', 'viewed_at')
    date_hierarchy = 'viewed_at'
    ordering = ('-viewed_at',)

    def has_add_permission(self, request):
        """Prevent manual creation - tracked automatically."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Allow deletion to reset notification states if needed."""
        return True

    def activity_link(self, obj):
        """Link to the activity in BookingHistory."""
        from django.urls import reverse
        from django.utils.html import format_html
        if obj.activity:
            url = reverse('admin:bookings_bookinghistory_change', args=[obj.activity.id])
            return format_html(
                '<a href="{}">Activity #{} - {}</a>',
                url,
                obj.activity.id,
                obj.activity.get_action_display()
            )
        return '-'
    activity_link.short_description = 'Activity'


@admin.register(ViewedBooking)
class ViewedBookingAdmin(admin.ModelAdmin):
    """Admin interface for debugging user booking notifications."""
    list_display = ('user', 'booking_link', 'viewed_at')
    list_filter = ('user', 'viewed_at')
    search_fields = ('user__username', 'booking__passenger_name', 'booking__booking_reference', 'booking__id')
    readonly_fields = ('user', 'booking', 'viewed_at')
    date_hierarchy = 'viewed_at'
    ordering = ('-viewed_at',)

    def has_add_permission(self, request):
        """Prevent manual creation - tracked automatically."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Allow deletion to reset notification states if needed."""
        return True

    def booking_link(self, obj):
        """Link to the booking."""
        from django.urls import reverse
        from django.utils.html import format_html
        if obj.booking:
            url = reverse('admin:bookings_booking_change', args=[obj.booking.id])
            return format_html(
                '<a href="{}">{} - {}</a>',
                url,
                obj.booking.booking_reference,
                obj.booking.passenger_name
            )
        return '-'
    booking_link.short_description = 'Booking'


@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    """Admin interface for managing email templates."""
    list_display = ('name', 'template_type', 'is_active', 'success_rate_display', 'total_sent', 'last_sent_at', 'updated_at')
    list_filter = ('is_active', 'template_type', 'send_to_user', 'send_to_admin')
    search_fields = ('name', 'description', 'subject_template')
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by', 'total_sent', 'total_failed', 'last_sent_at', 'success_rate', 'variable_documentation')
    ordering = ('template_type',)

    fieldsets = (
        ('Template Information', {
            'fields': ('template_type', 'name', 'description', 'is_active')
        }),
        ('Email Content', {
            'fields': ('subject_template', 'html_template'),
            'description': 'Use {variable_name} for dynamic content. See Available Variables section below.'
        }),
        ('Recipients Configuration', {
            'fields': ('send_to_user', 'send_to_admin', 'send_to_passenger'),
            'classes': ('collapse',)
        }),
        ('Available Variables', {
            'fields': ('variable_documentation',),
            'classes': ('collapse',),
            'description': 'Click to expand and view all available variables for this template type'
        }),
        ('Statistics', {
            'fields': ('total_sent', 'total_failed', 'success_rate', 'last_sent_at'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )

    actions = ['preview_template', 'send_test_email', 'duplicate_template']

    def success_rate_display(self, obj):
        """Display success rate with color coding."""
        rate = obj.success_rate
        if rate >= 95:
            color = 'green'
        elif rate >= 80:
            color = 'orange'
        else:
            color = 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} %</span>',
            color,
            rate
        )
    success_rate_display.short_description = 'Success Rate'

    def variable_documentation(self, obj):
        """Display available variables as formatted HTML."""
        if not obj.id:
            return format_html('<p style="color: #666;">Save template first to see available variables</p>')
        
        variables = obj.get_available_variables()
        html_parts = ['<div style="font-family: monospace; line-height: 1.8;">']
        html_parts.append('<table style="width: 100%; border-collapse: collapse;">')
        html_parts.append('<thead><tr style="background: #f0f0f0;"><th style="padding: 8px; text-align: left; border: 1px solid #ddd;">Variable</th><th style="padding: 8px; text-align: left; border: 1px solid #ddd;">Description</th></tr></thead>')
        html_parts.append('<tbody>')
        
        for var_name, description in sorted(variables.items()):
            html_parts.append(f'<tr><td style="padding: 8px; border: 1px solid #ddd; background: #fafafa;"><code>{{{var_name}}}</code></td><td style="padding: 8px; border: 1px solid #ddd;">{description}</td></tr>')
        
        html_parts.append('</tbody></table></div>')
        html_parts.append('<p style="margin-top: 12px; color: #666;"><strong>Usage Example:</strong> <code>Trip Confirmed: {passenger_name} - {pick_up_date}</code></p>')
        
        return format_html(''.join(html_parts))
    variable_documentation.short_description = 'Available Template Variables'

    def save_model(self, request, obj, form, change):
        """Track who created/updated the template."""
        if not obj.pk:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

    @admin.action(description='Preview template with sample data')
    def preview_template(self, request, queryset):
        """Preview selected templates with sample data."""
        from django.shortcuts import render
        
        if queryset.count() != 1:
            self.message_user(request, 'Please select exactly one template to preview', level='warning')
            return
        
        template = queryset.first()
        
        # Create sample context data
        sample_context = {
            'booking_reference': 'M1-260113-A5',
            'passenger_name': 'John Smith',
            'phone_number': '+1 (555) 123-4567',
            'passenger_email': 'john.smith@example.com',
            'pick_up_date': 'January 20, 2026',
            'pick_up_time': '2:00 PM',
            'pick_up_address': 'The Art Institute, 111 S Michigan Ave, Chicago, IL 60603',
            'drop_off_address': "O'Hare International Airport, Chicago, IL 60666",
            'vehicle_type': 'Sedan',
            'trip_type': 'Point-to-Point',
            'number_of_passengers': '2',
            'flight_number': 'UA1234',
            'notes': 'Please arrive 10 minutes early',
            'status': 'Confirmed',
            'old_status': 'Pending',
            'new_status': 'Confirmed',
            'user_email': 'customer@example.com',
            'user_username': 'jsmith',
            'company_name': 'M1 Limousine Service',
            'support_email': 'support@m1limo.com',
            'dashboard_url': 'http://62.169.19.39:8081/dashboard',
            'driver_name': 'Michael Johnson',
            'driver_phone': '+1 (555) 987-6543',
            'driver_vehicle': 'Black Sedan - ABC 123',
            'driver_portal_url': 'http://62.169.19.39:8081/driver/trip/123/abc',
            'return_pick_up_date': 'January 25, 2026',
            'return_pick_up_time': '4:00 PM',
            'return_pick_up_address': "O'Hare International Airport, Chicago, IL 60666",
            'return_drop_off_address': 'The Art Institute, 111 S Michigan Ave, Chicago, IL 60603',
        }
        
        rendered_subject = template.render_subject(sample_context)
        rendered_html = template.render_html(sample_context)
        
        context = {
            'template': template,
            'rendered_subject': rendered_subject,
            'rendered_html': rendered_html,
            'sample_data': sample_context,
        }
        
        return render(request, 'admin/email_template_preview.html', context)

    @admin.action(description='Send test email to yourself')
    def send_test_email(self, request, queryset):
        """Send test email using selected template."""
        from django.contrib import messages as django_messages
        from django.core.mail import EmailMessage
        
        if queryset.count() != 1:
            self.message_user(request, 'Please select exactly one template to test', level='warning')
            return
        
        template = queryset.first()
        recipient_email = request.user.email
        
        if not recipient_email:
            self.message_user(request, 'Your user account has no email address', level='error')
            return
        
        # Create sample context
        sample_context = {
            'booking_reference': 'M1-TEST-001',
            'passenger_name': 'Test Passenger',
            'phone_number': '+1 (555) 000-0000',
            'passenger_email': 'test@example.com',
            'pick_up_date': 'January 20, 2026',
            'pick_up_time': '2:00 PM',
            'pick_up_address': 'Test Pickup Location',
            'drop_off_address': 'Test Drop-off Location',
            'vehicle_type': 'Sedan',
            'trip_type': 'Point-to-Point',
            'number_of_passengers': '2',
            'flight_number': 'TEST123',
            'notes': 'This is a test email',
            'status': 'Confirmed',
            'old_status': 'Pending',
            'new_status': 'Confirmed',
            'user_email': recipient_email,
            'user_username': request.user.username,
            'company_name': 'M1 Limousine Service',
            'support_email': 'support@m1limo.com',
            'dashboard_url': 'http://62.169.19.39:8081/dashboard',
            'driver_name': 'Test Driver',
            'driver_phone': '+1 (555) 999-9999',
            'driver_vehicle': 'Test Vehicle',
            'driver_portal_url': 'http://62.169.19.39:8081/driver/test',
            'return_pick_up_date': 'January 25, 2026',
            'return_pick_up_time': '4:00 PM',
            'return_pick_up_address': 'Test Return Pickup',
            'return_drop_off_address': 'Test Return Dropoff',
        }
        
        try:
            subject = template.render_subject(sample_context)
            html_body = template.render_html(sample_context)
            
            # Add test notice to subject
            subject = f"[TEST] {subject}"
            
            # Add test notice to HTML
            test_notice = '<div style="background: #fef3c7; border-left: 4px solid #f59e0b; padding: 12px; margin-bottom: 20px;"><strong>🧪 TEST EMAIL</strong> - This is a test of the email template system</div>'
            html_body = test_notice + html_body
            
            email = EmailMessage(
                subject=subject,
                body=html_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[recipient_email],
            )
            email.content_subtype = "html"
            email.send(fail_silently=False)
            
            self.message_user(
                request,
                f'Test email sent successfully to {recipient_email}',
                level='success'
            )
            
        except Exception as e:
            self.message_user(
                request,
                f'Failed to send test email: {str(e)}',
                level='error'
            )
            logger.error(f"Test email failed: {e}", exc_info=True)

    @admin.action(description='Duplicate selected template')
    def duplicate_template(self, request, queryset):
        """Create a copy of selected template."""
        if queryset.count() != 1:
            self.message_user(request, 'Please select exactly one template to duplicate', level='warning')
            return
        
        template = queryset.first()
        
        # Create copy
        template.pk = None
        template.name = f"{template.name} (Copy)"
        template.template_type = None  # Must be set manually to avoid unique constraint
        template.is_active = False  # Start inactive
        template.total_sent = 0
        template.total_failed = 0
        template.last_sent_at = None
        template.created_by = request.user
        template.updated_by = request.user
        
        try:
            template.save()
            self.message_user(
                request,
                f'Template duplicated successfully. Please set a unique template type.',
                level='success'
            )
        except Exception as e:
            self.message_user(
                request,
                f'Failed to duplicate template: {str(e)}',
                level='error'
            )
