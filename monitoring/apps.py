from django.apps import AppConfig


class MonitoringConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'monitoring'
    verbose_name = 'Slack Monitoring & Notifications'

    def ready(self):
        # Import signals when app is ready
        import monitoring.signals  # noqa: F401
