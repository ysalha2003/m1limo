# middleware_custom_errors.py
# This middleware forces custom error pages even when DEBUG = True
# This allows testing custom error pages during development

from django.conf import settings
from django.shortcuts import render


class ForceCustomErrorPagesMiddleware:
    """
    Middleware to force custom error pages even in DEBUG mode.

    Django only uses custom error handlers (handler404, handler500)
    when DEBUG = False. This middleware allows testing custom error
    pages during development without disabling DEBUG entirely.

    To enable/disable: See FORCE_CUSTOM_ERROR_PAGES in settings.py
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.force_custom_errors = getattr(settings, 'FORCE_CUSTOM_ERROR_PAGES', False)

    def __call__(self, request):
        response = self.get_response(request)

        # Only intervene if we're forcing custom error pages
        # and DEBUG is True (otherwise Django handles it normally)
        if self.force_custom_errors and settings.DEBUG:
            if response.status_code == 404:
                # Render custom 404 page
                return render(request, '404.html', status=404)
            elif response.status_code == 500:
                # Render custom 500 page
                return render(request, '500.html', status=500)

        return response
