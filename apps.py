from django.apps import AppConfig
import os


class BookingsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = '__main__'
    label = 'bookings'
    path = os.path.dirname(os.path.abspath(__file__))

    def ready(self):
        """Import signals and admin when app is ready"""
        try:
            import signals
        except ImportError:
            pass

        try:
            import admin
        except ImportError:
            pass
