from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from ..models import Emisor

@method_decorator(login_required, name='dispatch')
class HerramientasMantenimientoView(TemplateView):
    """
    Vista para la página de herramientas de mantenimiento.
    """
    template_name = 'core/herramientas_mantenimiento.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Herramientas de Mantenimiento'
        
        # Obtener emisores para los selectores
        context['emisores'] = Emisor.objects.filter(activo=True).order_by('razon_social')
        
        return context
