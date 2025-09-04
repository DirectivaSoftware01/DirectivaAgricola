from django.urls import path
from .views import (
    DashboardView, login_view, logout_view, ConfiguracionView,
    UsuarioCreateView, UsuarioUpdateView, UsuarioDeleteView,
    # Vistas de Clientes
    ClienteListView, ClienteCreateView, ClienteUpdateView, ClienteDeleteView, ClienteDetailView,
    # Vistas de Proveedores
    ProveedorListView, ProveedorCreateView, ProveedorUpdateView, ProveedorDeleteView, ProveedorDetailView,
    # Vistas de Transportistas
    TransportistaListView, TransportistaCreateView, TransportistaUpdateView, TransportistaDeleteView, TransportistaDetailView,
    # Vistas de Lotes - Origen
    LoteOrigenListView, LoteOrigenCreateView, LoteOrigenUpdateView, LoteOrigenDeleteView, LoteOrigenDetailView,
    # Vistas de Clasificación de Gastos
    ClasificacionGastoListView, ClasificacionGastoCreateView, ClasificacionGastoUpdateView, ClasificacionGastoDeleteView, ClasificacionGastoDetailView,
    # Vistas de Centro de Costos
    CentroCostoListView, CentroCostoCreateView, CentroCostoUpdateView, CentroCostoDeleteView, CentroCostoDetailView,
    # Vistas de Productos y Servicios
    ProductoServicioListView, ProductoServicioCreateView, ProductoServicioUpdateView, ProductoServicioDeleteView, ProductoServicioDetailView,
    # Vistas de Régimen Fiscal
    RegimenFiscalListView, RegimenFiscalCreateView, RegimenFiscalUpdateView, RegimenFiscalDeleteView,
    # Vistas de Configuración del Sistema
    ConfiguracionSistemaView,
    # Vistas de Cultivos
    CultivoListView, CultivoCreateView, CultivoUpdateView, CultivoDeleteView, CultivoDetailView,
    # Vistas de Remisiones
    RemisionListView, RemisionCreateView, RemisionUpdateView, RemisionDeleteView, RemisionDetailView,
    RemisionDetalleCreateView, RemisionDetalleUpdateView, RemisionDetalleDeleteView,
    RemisionLiquidacionView, CobranzaListView, CobranzaImprimirView,
    # Vistas AJAX
    get_cultivos_ajax, cancelar_remision_ajax, actualizar_estado_cobranza_ajax
)

app_name = 'core'

urlpatterns = [
    # URLs principales
    path('', DashboardView.as_view(), name='dashboard'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    
    # URLs de configuración y usuarios
    path('configuracion/', ConfiguracionView.as_view(), name='configuracion'),
    path('configuracion/sistema/', ConfiguracionSistemaView.as_view(), name='configuracion_sistema'),
    path('configuracion/usuario/nuevo/', UsuarioCreateView.as_view(), name='usuario_create'),
    path('configuracion/usuario/<int:pk>/editar/', UsuarioUpdateView.as_view(), name='usuario_update'),
    path('configuracion/usuario/<int:pk>/eliminar/', UsuarioDeleteView.as_view(), name='usuario_delete'),
    
    # URLs de clientes
    path('clientes/', ClienteListView.as_view(), name='cliente_list'),
    path('clientes/nuevo/', ClienteCreateView.as_view(), name='cliente_create'),
    path('clientes/<int:pk>/', ClienteDetailView.as_view(), name='cliente_detail'),
    path('clientes/<int:pk>/editar/', ClienteUpdateView.as_view(), name='cliente_update'),
    path('clientes/<int:pk>/eliminar/', ClienteDeleteView.as_view(), name='cliente_delete'),
    
    # URLs de proveedores
    path('proveedores/', ProveedorListView.as_view(), name='proveedor_list'),
    path('proveedores/nuevo/', ProveedorCreateView.as_view(), name='proveedor_create'),
    path('proveedores/<int:pk>/', ProveedorDetailView.as_view(), name='proveedor_detail'),
    path('proveedores/<int:pk>/editar/', ProveedorUpdateView.as_view(), name='proveedor_update'),
    path('proveedores/<int:pk>/eliminar/', ProveedorDeleteView.as_view(), name='proveedor_delete'),
    
    # URLs de transportistas
    path('transportistas/', TransportistaListView.as_view(), name='transportista_list'),
    path('transportistas/nuevo/', TransportistaCreateView.as_view(), name='transportista_create'),
    path('transportistas/<int:pk>/', TransportistaDetailView.as_view(), name='transportista_detail'),
    path('transportistas/<int:pk>/editar/', TransportistaUpdateView.as_view(), name='transportista_update'),
    path('transportistas/<int:pk>/eliminar/', TransportistaDeleteView.as_view(), name='transportista_delete'),
    
    # URLs de lotes - origen
    path('lotes-origen/', LoteOrigenListView.as_view(), name='lote_origen_list'),
    path('lotes-origen/nuevo/', LoteOrigenCreateView.as_view(), name='lote_origen_create'),
    path('lotes-origen/<int:pk>/', LoteOrigenDetailView.as_view(), name='lote_origen_detail'),
    path('lotes-origen/<int:pk>/editar/', LoteOrigenUpdateView.as_view(), name='lote_origen_update'),
    path('lotes-origen/<int:pk>/eliminar/', LoteOrigenDeleteView.as_view(), name='lote_origen_delete'),
    
    # URLs de clasificación de gastos
    path('clasificacion-gastos/', ClasificacionGastoListView.as_view(), name='clasificacion_gasto_list'),
    path('clasificacion-gastos/nuevo/', ClasificacionGastoCreateView.as_view(), name='clasificacion_gasto_create'),
    path('clasificacion-gastos/<int:pk>/', ClasificacionGastoDetailView.as_view(), name='clasificacion_gasto_detail'),
    path('clasificacion-gastos/<int:pk>/editar/', ClasificacionGastoUpdateView.as_view(), name='clasificacion_gasto_update'),
    path('clasificacion-gastos/<int:pk>/eliminar/', ClasificacionGastoDeleteView.as_view(), name='clasificacion_gasto_delete'),
    
    # URLs de centro de costos
    path('centro-costos/', CentroCostoListView.as_view(), name='centro_costo_list'),
    path('centro-costos/nuevo/', CentroCostoCreateView.as_view(), name='centro_costo_create'),
    path('centro-costos/<int:pk>/', CentroCostoDetailView.as_view(), name='centro_costo_detail'),
    path('centro-costos/<int:pk>/editar/', CentroCostoUpdateView.as_view(), name='centro_costo_update'),
    path('centro-costos/<int:pk>/eliminar/', CentroCostoDeleteView.as_view(), name='centro_costo_delete'),
    
    # URLs de productos y servicios
    path('productos-servicios/', ProductoServicioListView.as_view(), name='producto_servicio_list'),
    path('productos-servicios/nuevo/', ProductoServicioCreateView.as_view(), name='producto_servicio_create'),
    path('productos-servicios/<int:pk>/', ProductoServicioDetailView.as_view(), name='producto_servicio_detail'),
    path('productos-servicios/<int:pk>/editar/', ProductoServicioUpdateView.as_view(), name='producto_servicio_update'),
    path('productos-servicios/<int:pk>/eliminar/', ProductoServicioDeleteView.as_view(), name='producto_servicio_delete'),
    
    # URLs de régimen fiscal
    path('regimen-fiscal/', RegimenFiscalListView.as_view(), name='regimen_fiscal_list'),
    path('regimen-fiscal/nuevo/', RegimenFiscalCreateView.as_view(), name='regimen_fiscal_create'),
    path('regimen-fiscal/<int:pk>/editar/', RegimenFiscalUpdateView.as_view(), name='regimen_fiscal_update'),
    path('regimen-fiscal/<int:pk>/eliminar/', RegimenFiscalDeleteView.as_view(), name='regimen_fiscal_delete'),
    
    # URLs de cultivos
    path('cultivos/', CultivoListView.as_view(), name='cultivo_list'),
    path('cultivos/nuevo/', CultivoCreateView.as_view(), name='cultivo_create'),
    path('cultivos/<int:pk>/', CultivoDetailView.as_view(), name='cultivo_detail'),
    path('cultivos/<int:pk>/editar/', CultivoUpdateView.as_view(), name='cultivo_update'),
    path('cultivos/<int:pk>/eliminar/', CultivoDeleteView.as_view(), name='cultivo_delete'),
    
    # URLs de remisiones
    path('remisiones/', RemisionListView.as_view(), name='remision_list'),
    path('remisiones/nuevo/', RemisionCreateView.as_view(), name='remision_create'),
    path('remisiones/<int:pk>/', RemisionDetailView.as_view(), name='remision_detail'),
    path('remisiones/<int:pk>/editar/', RemisionUpdateView.as_view(), name='remision_update'),
    path('remisiones/<int:pk>/eliminar/', RemisionDeleteView.as_view(), name='remision_delete'),
    path('remisiones/<int:pk>/liquidar/', RemisionLiquidacionView.as_view(), name='remision_liquidar'),
    
    # URLs de cobranza
    path('cobranza/', CobranzaListView.as_view(), name='cobranza_list'),
    path('cobranza/imprimir/', CobranzaImprimirView.as_view(), name='cobranza_imprimir'),
    
    # URLs de detalles de remisiones
    path('remisiones/<int:remision_id>/detalle/nuevo/', RemisionDetalleCreateView.as_view(), name='remision_detalle_create'),
    path('remisiones/detalle/<int:pk>/editar/', RemisionDetalleUpdateView.as_view(), name='remision_detalle_update'),
    path('remisiones/detalle/<int:pk>/eliminar/', RemisionDetalleDeleteView.as_view(), name='remision_detalle_delete'),
    
    # URLs AJAX
    path('ajax/cultivos/', get_cultivos_ajax, name='get_cultivos_ajax'),
    path('ajax/remisiones/<int:pk>/cancelar/', cancelar_remision_ajax, name='cancelar_remision_ajax'),
    path('ajax/remisiones/<int:pk>/cobranza/', actualizar_estado_cobranza_ajax, name='actualizar_estado_cobranza_ajax'),
]
