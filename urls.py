from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
import views

urlpatterns = [
    # Custom admin views (must come before Django admin to avoid conflicts)
    path('admin/past-confirmed-reservations/', views.past_confirmed_trips, name='past_confirmed_reservations'),
    path('admin/confirm-reservation-action/<int:booking_id>/<str:action>/', views.confirm_trip_action, name='confirm_reservation_action'),
    path('admin/past-pending-reservations/', views.past_pending_trips, name='past_pending_reservations'),
    path('admin/confirm-pending-action/<int:booking_id>/<str:action>/', views.confirm_pending_action, name='confirm_pending_action'),
    path('admin/reservation-activity/', views.booking_activity, name='reservation_activity'),
    
    # Django admin
    path('admin/', admin.site.urls),

    # Main views
    path('', views.home, name='home'),
    path('login/', views.user_login, name='login'),
    path('signup/', views.signup, name='signup'),
    path('logout/', views.user_logout, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),

    # Info pages
    path('privacy/', views.privacy_policy, name='privacy_policy'),
    path('cookies/', views.cookie_policy, name='cookie_policy'),
    path('guide/', views.user_guide, name='user_guide'),
    path('contact/', views.contact, name='contact'),

    # Password reset
    path('password-reset/',
         auth_views.PasswordResetView.as_view(template_name='registration/password_reset_form.html'),
         name='password_reset'),
    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'),
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'),
         name='password_reset_confirm'),
    path('password-reset-complete/',
         auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'),
         name='password_reset_complete'),
    
    # Reservation management
    path('reservation/new/', views.new_booking, name='new_reservation'),
    path('reservation/<int:booking_id>/', views.booking_detail, name='reservation_detail'),
    path('activity/<int:activity_id>/', views.view_activity, name='view_activity'),
    path('my-reservation/<int:booking_id>/', views.view_user_booking, name='view_user_reservation'),
    path('reservation/<int:booking_id>/confirmation/', views.booking_confirmation, name='reservation_confirmation'),
    path('reservation/<int:booking_id>/update/', views.update_booking, name='update_reservation'),
    path('reservation/<int:booking_id>/update-round-trip/', views.update_round_trip, name='update_round_trip'),
    path('reservation/<int:booking_id>/rebook/', views.rebook_booking, name='rebook_reservation'),
    path('reservation/<int:booking_id>/cancel/', views.cancel_booking, name='cancel_reservation'),
    path('reservation/<int:booking_id>/delete/', views.delete_booking, name='delete_reservation'),  # Backwards compat
    path('reservation/<int:booking_id>/request-cancellation/',
         views.request_cancellation, name='request_cancellation'),
    path('reservation/<int:booking_id>/actions/<str:action>/',
         views.booking_actions, name='reservation_actions'),
    path('reservation/<int:booking_id>/assign-driver/',
         views.assign_driver, name='assign_driver'),

    # User management
    path('profile/', views.edit_profile, name='edit_profile'),
    
    # Frequent passengers
    path('passengers/', views.frequent_passengers, name='frequent_passengers'),
    path('passengers/<int:passenger_id>/edit/', views.edit_passenger, name='edit_passenger'),
    path('passengers/<int:passenger_id>/delete/',
         views.delete_passenger, name='delete_passenger'),
    
    # Driver portal (no login required - uses token authentication)
    path('driver/trip/<int:booking_id>/<str:token>/', views.driver_trip_response, name='driver_trip_response'),
    path('driver/trips/<str:driver_email>/<str:token>/', views.driver_trips_list, name='driver_trips_list'),

    # Driver management (admin only)
    path('reservation/<int:booking_id>/resend-driver-notification/', views.resend_driver_notification, name='resend_driver_notification'),
    path('reservation/<int:booking_id>/mark-driver-paid/', views.mark_driver_paid, name='mark_driver_paid'),
    path('driver-assignments/<int:driver_id>/', views.driver_list_by_driver, name='driver_list_by_driver'),

    # Admin utilities
    path('test-email/', views.test_email, name='test_email'),
    path('special-request-response/', views.special_request_response, name='special_request_response'),
]

# Custom error handlers
handler404 = 'views.custom_404'
handler500 = 'views.custom_500'
