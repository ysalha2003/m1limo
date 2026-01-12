"""
Custom middleware for the booking system.
"""

import time
import logging
from django.core.cache import cache
from django.http import HttpResponseForbidden
from django.conf import settings

logger = logging.getLogger(__name__)


class RateLimitMiddleware:
    """
    Simple rate limiting middleware for booking endpoints.

    Limits requests per user per time window to prevent spam/abuse.
    """

    def __init__(self, get_response):
        self.get_response = get_response

        # Rate limit configuration
        self.limits = {
            '/booking/new/': {'max_requests': 10, 'window': 3600},  # 10 per hour
            '/booking/': {'max_requests': 20, 'window': 3600},  # 20 updates per hour
            'default': {'max_requests': 100, 'window': 3600},  # 100 per hour for other endpoints
        }

    def __call__(self, request):
        # Skip rate limiting for staff users
        if request.user.is_authenticated and request.user.is_staff:
            return self.get_response(request)

        # Only rate limit POST requests (form submissions)
        if request.method == 'POST':
            if not self.check_rate_limit(request):
                logger.warning(
                    f"Rate limit exceeded for user {request.user.username if request.user.is_authenticated else 'anonymous'} "
                    f"on path {request.path}"
                )
                return HttpResponseForbidden(
                    "Too many requests. Please wait before trying again."
                )

        response = self.get_response(request)
        return response

    def check_rate_limit(self, request):
        """
        Check if the request should be rate limited.

        Returns:
            True if request is allowed, False if rate limit exceeded
        """
        # Skip rate limiting for staff users
        if request.user.is_authenticated and request.user.is_staff:
            return True

        # Get user identifier
        if request.user.is_authenticated:
            user_id = f"user_{request.user.id}"
        else:
            # Use IP address for anonymous users
            user_id = f"ip_{self.get_client_ip(request)}"

        # Get rate limit for this path
        path = request.path
        limit_config = self.get_limit_config(path)

        # Create cache key
        cache_key = f"rate_limit:{path}:{user_id}"

        # Get current request count
        request_data = cache.get(cache_key, {'count': 0, 'reset_time': time.time() + limit_config['window']})

        # Reset if window expired
        if time.time() > request_data['reset_time']:
            request_data = {'count': 0, 'reset_time': time.time() + limit_config['window']}

        # Increment counter
        request_data['count'] += 1

        # Check limit
        if request_data['count'] > limit_config['max_requests']:
            return False

        # Save updated count
        cache.set(cache_key, request_data, limit_config['window'])

        return True

    def get_limit_config(self, path):
        """Get rate limit configuration for a specific path."""
        for pattern, config in self.limits.items():
            if pattern in path:
                return config
        return self.limits['default']

    def get_client_ip(self, request):
        """Get the client's IP address from the request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
