from django.apps import AppConfig

class NetworkEduConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'network_edu'
    
    def ready(self):
        import network_edu.signals
