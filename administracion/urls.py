from django.urls import path
from . import views

app_name = 'administracion'

urlpatterns = [
    path('', views.configuracion_view, name='configuracion'),
    path('empresas/', views.empresas_view, name='empresas'),
    path('empresas/nueva/', views.empresa_create_view, name='empresa_create'),
    path('empresas/<int:empresa_id>/', views.empresa_detail_view, name='empresa_detail'),
    path('empresas/<int:empresa_id>/editar/', views.empresa_edit_view, name='empresa_edit'),
    path('empresas/<int:empresa_id>/toggle-suspend/', views.empresa_toggle_suspend, name='empresa_toggle_suspend'),
]
