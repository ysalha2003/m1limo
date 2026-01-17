# forms/booking_forms.py
from typing import Dict, Any
import re
from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.contrib.auth.models import User
from django.utils import timezone
from models import (
    Booking, FrequentPassenger, BookingPermission,
    NotificationRecipient, SystemSettings
)
from base import BaseModelForm, BaseForm


class UserChoiceField(forms.ModelChoiceField):
    """Custom ModelChoiceField that displays: First Last "username" """

    def label_from_instance(self, obj):
        """Display user as: First Last "username" or just username if no name"""
        full_name = f"{obj.first_name} {obj.last_name}".strip()
        if full_name:
            return f'{full_name} "{obj.username}"'
        return obj.username


class BookingForm(BaseModelForm):
    """User booking form with hybrid phone/email validation"""

    # Admin-only field for selecting user
    booking_for_user = UserChoiceField(
        queryset=User.objects.filter(is_active=True).order_by('first_name', 'last_name', 'username'),
        required=False,
        help_text='Select a user to create this booking on their behalf',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    # Separate required fields for phone and email
    phone_number = forms.CharField(
        required=True,
        label="Passenger Phone Number *",
        max_length=20,
        widget=forms.TextInput(attrs={
            'type': 'tel',
            'placeholder': 'Enter phone number',
            'class': 'form-input',
            'maxlength': '20'
        }),
        help_text="Required: Contact phone number"
    )
    
    passenger_email = forms.EmailField(
        required=True,
        label="Passenger Email *",
        widget=forms.EmailInput(attrs={
            'placeholder': 'Enter email address',
            'class': 'form-input',
            'maxlength': '100'
        }),
        help_text="Required: Email for booking confirmations and updates"
    )
    
    # Notification preferences
    send_passenger_notifications = forms.BooleanField(
        required=False,
        initial=False,  # Default to False - admin opts in to send passenger notifications
        label="Send notifications to passenger",
        widget=forms.CheckboxInput(attrs={
            'class': 'form-checkbox'
            # DO NOT hardcode 'checked' - Django will set it based on field value
        }),
        help_text="Passenger will receive booking confirmation, updates, and reminders"
    )
    
    additional_recipients = forms.CharField(
        required=False,
        label="Additional Recipients (Optional)",
        widget=forms.Textarea(attrs={
            'placeholder': 'john@example.com, jane@example.com',
            'class': 'form-input',
            'rows': '2',
            'maxlength': '500'
        }),
        help_text="Enter additional email addresses separated by commas. They will receive all booking notifications."
    )

    # Additional fields for trip configuration
    is_airport_trip = forms.BooleanField(required=False, label="Airport Pickup/Dropoff?")
    needs_stop = forms.BooleanField(required=False, label="Need intermediate stops?")
    is_return_airport_trip = forms.BooleanField(required=False, label="Return is Airport Pickup/Dropoff?")
    needs_return_stop = forms.BooleanField(required=False, label="Need intermediate stops on return?")

    def __init__(self, *args, **kwargs):
        """Initialize form"""
        super().__init__(*args, **kwargs)
        # Set Admin as default for booking_for_user field if no instance
        if not self.instance.pk and 'booking_for_user' in self.fields:
            try:
                admin_user = User.objects.filter(username='Admin').first()
                if admin_user:
                    self.fields['booking_for_user'].initial = admin_user.pk
            except User.DoesNotExist:
                pass

    class Meta:
        model = Booking
        fields = [
            'passenger_name',
            'phone_number',
            'passenger_email',
            'send_passenger_notifications',
            'additional_recipients',
            'number_of_passengers',
            'vehicle_type',
            'trip_type',
            'hours_booked',
            'pick_up_address',
            'drop_off_address',
            'pick_up_date',
            'pick_up_time',
            'flight_number',
            'notes',
            'return_date',
            'return_time',
            'return_pickup_address',
            'return_dropoff_address',
            'return_flight_number',
            'return_special_requests',
        ]
        widgets = {
            'passenger_name': forms.TextInput(attrs={'placeholder': 'Enter passenger name'}),
            # phone_number and passenger_email defined as form fields above, not in Meta widgets
            'number_of_passengers': forms.NumberInput(attrs={'min': '1', 'placeholder': 'Number of passengers'}),
            'pick_up_address': forms.TextInput(attrs={'placeholder': 'Enter pick-up address'}),
            'drop_off_address': forms.TextInput(attrs={'placeholder': 'Enter drop-off address'}),
            'pick_up_date': forms.DateInput(attrs={'type': 'date'}),
            'pick_up_time': forms.TimeInput(attrs={'type': 'time'}),
            'return_date': forms.DateInput(attrs={'type': 'date'}),
            'return_time': forms.TimeInput(attrs={'type': 'time'}),
            'return_pickup_address': forms.TextInput(attrs={'placeholder': 'Return pick-up address'}),
            'return_dropoff_address': forms.TextInput(attrs={'placeholder': 'Return drop-off address'}),
            'hours_booked': forms.NumberInput(attrs={'min': '3', 'placeholder': 'Minimum 3 hours'}),
            'flight_number': forms.TextInput(attrs={'placeholder': 'Flight number if applicable'}),
            'return_flight_number': forms.TextInput(attrs={'placeholder': 'Return flight number'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Special requirements'}),
            'return_special_requests': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Return journey requests'}),
        }
    
    def clean_phone_number(self) -> str:
        """
        Validate phone number format.
        """
        phone = self.cleaned_data.get('phone_number', '').strip()
        
        if not phone:
            raise ValidationError('Phone number is required.')
        
        # Remove common phone number separators for validation
        phone_cleaned = re.sub(r'[\s\-\(\)\.]+', '', phone)
        
        # Basic phone number validation (digits and optional + prefix)
        if not re.match(r'^\+?\d{10,15}$', phone_cleaned):
            raise ValidationError(
                'Please enter a valid phone number with 10-15 digits.'
            )
        
        return phone

    def clean(self) -> Dict[str, Any]:
        """Validate booking data"""
        cleaned_data = super().clean()
        
        # Both phone and email are required - validated at field level
        trip_type = cleaned_data.get('trip_type')
        vehicle_type = cleaned_data.get('vehicle_type')
        hours_booked = cleaned_data.get('hours_booked')
        drop_off_address = cleaned_data.get('drop_off_address')

        # Validate "Others" vehicle type requires specification
        if vehicle_type == 'Others' and not cleaned_data.get('notes'):
            self.add_error('notes', 'Please specify vehicle requirements for "Others"')

        # Validate hourly service requirements
        if trip_type == 'Hourly':
            if not hours_booked or hours_booked < 3:
                self.add_error('hours_booked', 'Hourly service requires minimum 3 hours')
            # Auto-clear drop-off address for hourly bookings
            if cleaned_data.get('drop_off_address'):
                cleaned_data['drop_off_address'] = None
                self.instance.drop_off_address = None

        # Validate point-to-point requirements
        if trip_type == 'Point' and not drop_off_address:
            self.add_error('drop_off_address', 'Drop-off address required for point-to-point')

        # Validate round trip requirements
        if trip_type == 'Round':
            if not cleaned_data.get('return_date') or not cleaned_data.get('return_time'):
                self.add_error('return_date', 'Return date/time required for round trips')
                self.add_error('return_time', 'Return date/time required for round trips')

            if not cleaned_data.get('return_pickup_address'):
                self.add_error('return_pickup_address', 'Return pickup address required')

            if not cleaned_data.get('return_dropoff_address'):
                self.add_error('return_dropoff_address', 'Return dropoff address required')

        return cleaned_data
    
    def clean_additional_recipients(self) -> str:
        """Validate additional recipients email addresses"""
        additional_recipients = self.cleaned_data.get('additional_recipients', '').strip()
        
        if not additional_recipients:
            return ''
        
        # Parse comma-separated emails
        emails = [email.strip() for email in additional_recipients.split(',')]
        valid_emails = []
        invalid_emails = []
        
        for email in emails:
            if not email:
                continue
            try:
                validate_email(email)
                valid_emails.append(email)
            except ValidationError:
                invalid_emails.append(email)
        
        if invalid_emails:
            raise ValidationError(
                f"Invalid email address(es): {', '.join(invalid_emails)}"
            )
        
        # Return cleaned comma-separated string
        return ', '.join(valid_emails)


class AdminBookingForm(BookingForm):
    """Admin form with user selection, status control, and notification routing"""

    user = UserChoiceField(
        queryset=User.objects.filter(is_active=True).order_by('first_name', 'last_name', 'username'),
        required=True,
        label='Customer',
        help_text='Select the customer for this booking'
    )

    status = forms.ChoiceField(
        choices=Booking.STATUS_CHOICES,
        required=True,
        label='Booking Status'
    )

    notification_recipients = forms.ModelMultipleChoiceField(
        queryset=NotificationRecipient.objects.filter(is_active=True),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label='Additional Recipients'
    )

    class Meta(BookingForm.Meta):
        fields = ['user'] + BookingForm.Meta.fields + [
            'status', 'admin_comment', 'cancellation_reason'
        ]
        widgets = {
            **BookingForm.Meta.widgets,
            'admin_comment': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Internal admin notes (not visible to customer)'
            }),
            'cancellation_reason': forms.Textarea(attrs={
                'rows': 2,
                'placeholder': 'Reason for cancellation (if applicable)'
            }),
        }
    
    def clean(self) -> Dict[str, Any]:
        """Validate admin booking, allowing past dates for administrative purposes"""
        cleaned_data = super().clean()

        # Allow admin to create bookings with past dates
        if 'pick_up_date' in self.errors:
            errors = [e for e in self.errors['pick_up_date'] if 'past' not in str(e).lower()]
            if errors:
                self.errors['pick_up_date'] = errors
            else:
                del self.errors['pick_up_date']

        if not cleaned_data.get('user'):
            self.add_error('user', 'Please select a user for this booking')

        return cleaned_data


class BookingSearchForm(BaseForm):
    """Search and filter form for bookings"""
    
    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Search by name, phone, address...'})
    )
    
    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + Booking.STATUS_CHOICES,
        required=False
    )
    
    date_range = forms.ChoiceField(
        choices=[
            ('', 'All Dates'),
            ('today', 'Today'),
            ('tomorrow', 'Tomorrow'),
            ('week', 'Next 7 Days'),
            ('month', 'Next 30 Days'),
            ('upcoming', 'All Upcoming'),
            ('past', 'Past Trips'),
        ],
        required=False
    )
    
    vehicle_type = forms.ChoiceField(
        choices=[('', 'All Vehicles')] + Booking.VEHICLE_CHOICES,
        required=False
    )
    
    trip_type = forms.ChoiceField(
        choices=[('', 'All Types')] + Booking.TRIP_TYPE_CHOICES,
        required=False
    )


class CancellationRequestForm(BaseModelForm):
    """Form for users to request booking cancellation"""

    class Meta:
        model = Booking
        fields = ['cancellation_reason']
        widgets = {
            'cancellation_reason': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Please explain why you need to cancel this booking...',
                'required': True
            })
        }

    def clean_cancellation_reason(self) -> str:
        reason = self.cleaned_data.get('cancellation_reason', '').strip()
        if not reason:
            raise ValidationError('Cancellation reason is required')
        if len(reason) < 10:
            raise ValidationError('Please provide a detailed reason (at least 10 characters)')
        return reason

    def _post_clean(self):
        """Override to skip full model validation since we're only updating cancellation_reason"""
        # Skip model.clean() to avoid validation errors for fields not in this form
        pass


class FrequentPassengerForm(BaseModelForm):
    """Form for managing frequent passengers"""

    class Meta:
        model = FrequentPassenger
        fields = ['name', 'phone_number', 'email', 'address', 'preferred_vehicle_type', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Passenger name'}),
            'phone_number': forms.TextInput(attrs={'type': 'tel', 'placeholder': 'Phone number'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Email (optional)'}),
            'address': forms.TextInput(attrs={'placeholder': 'Default address (optional)'}),
            'preferred_vehicle_type': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Additional notes'}),
        }


class UserSignupForm(forms.ModelForm):
    """User registration form with contact details and password validation"""

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': 'Email address'
        })
    )

    phone_number = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'input input-bordered w-full',
            'type': 'tel',
            'placeholder': 'Phone number (optional)'
        })
    )

    company_name = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': 'Company name (optional)'
        })
    )

    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': 'Enter password'
        })
    )

    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': 'Confirm password'
        })
    )

    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': 'First name'
        })
    )

    last_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': 'Last name'
        })
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'Choose a username'
            })
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('This email address is already registered.')
        return email

    def clean_password2(self):
        """Validate password match and strength requirements"""
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            raise ValidationError('Passwords do not match.')

        if len(password1) < 8:
            raise ValidationError('Password must be at least 8 characters long.')

        return password2

    def save(self, commit=True):
        """Create user and associated profile with phone number"""
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']

        if commit:
            user.save()
            # UserProfile is auto-created by signal, just update phone number and company name if provided
            from models import UserProfile
            profile, created = UserProfile.objects.get_or_create(user=user)
            phone_number = self.cleaned_data.get('phone_number', '')
            company_name = self.cleaned_data.get('company_name', '')
            if phone_number:
                profile.phone_number = phone_number
            if company_name:
                profile.company_name = company_name
            if phone_number or company_name:
                profile.save()
        return user


class UserProfileForm(forms.Form):
    """User profile editor with contact info and notification preferences"""

    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'First name'
        })
    )

    last_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Last name'
        })
    )

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'Email address'
        })
    )

    phone_number = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'type': 'tel',
            'placeholder': 'Phone number'
        })
    )

    company_name = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Company name (optional)'
        })
    )

    receive_booking_confirmations = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-checkbox'})
    )

    receive_status_updates = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-checkbox'})
    )

    receive_pickup_reminders = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-checkbox'})
    )

    def __init__(self, user, *args, **kwargs):
        """Initialize form with user's current data"""
        super().__init__(*args, **kwargs)
        self.user = user
        if not kwargs.get('data'):
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['email'].initial = user.email
            from models import UserProfile
            profile, created = UserProfile.objects.get_or_create(user=user)
            self.fields['phone_number'].initial = profile.phone_number
            self.fields['company_name'].initial = profile.company_name
            self.fields['receive_booking_confirmations'].initial = profile.receive_booking_confirmations
            self.fields['receive_status_updates'].initial = profile.receive_status_updates
            self.fields['receive_pickup_reminders'].initial = profile.receive_pickup_reminders

    def clean_email(self):
        """Validate email uniqueness across users"""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exclude(pk=self.user.pk).exists():
            raise ValidationError('This email address is already in use.')
        return email

    def save(self):
        """Update user model and profile with form data"""
        from models import UserProfile
        self.user.first_name = self.cleaned_data['first_name']
        self.user.last_name = self.cleaned_data['last_name']
        self.user.email = self.cleaned_data['email']
        self.user.save()

        profile, created = UserProfile.objects.get_or_create(user=self.user)
        profile.phone_number = self.cleaned_data.get('phone_number', '')
        profile.company_name = self.cleaned_data.get('company_name', '')
        profile.receive_booking_confirmations = self.cleaned_data.get('receive_booking_confirmations', True)
        profile.receive_status_updates = self.cleaned_data.get('receive_status_updates', True)
        profile.receive_pickup_reminders = self.cleaned_data.get('receive_pickup_reminders', True)
        profile.save()

        return self.user


class AdminStatusUpdateForm(BaseModelForm):
    """Admin form for quick status updates"""

    class Meta:
        model = Booking
        fields = ['status', 'admin_comment']
        widgets = {
            'status': forms.RadioSelect(),
            'admin_comment': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Internal admin notes (not visible to customer)'
            }),
        }
