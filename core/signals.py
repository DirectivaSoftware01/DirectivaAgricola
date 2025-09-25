from django.contrib.auth.signals import user_logged_in
from django.contrib.sessions.models import Session
from django.dispatch import receiver
from django.utils import timezone


@receiver(user_logged_in)
def logout_other_sessions(sender, user, request, **kwargs):
    """Al iniciar sesión, cerrar sesiones activas de este usuario en otros navegadores/equipos."""
    try:
        current_session_key = request.session.session_key
        if not current_session_key:
            # Asegurar que exista sesión; fuerza guardado para obtener clave
            request.session.save()
            current_session_key = request.session.session_key

        # Recorrer sesiones vigentes y eliminar las del mismo usuario, excepto la actual
        now = timezone.now()
        sessions = Session.objects.filter(expire_date__gt=now)
        for session in sessions:
            if session.session_key == current_session_key:
                continue
            data = session.get_decoded()
            if data.get('_auth_user_id') == str(user.pk):
                session.delete()
    except Exception:
        # No bloquear login si falla la limpieza de sesiones
        pass


