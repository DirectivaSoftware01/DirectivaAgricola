from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        # Registrar señales de la app
        try:
            from . import signals  # noqa: F401
        except Exception:
            # Evitar que errores de importación rompan el arranque
            pass
