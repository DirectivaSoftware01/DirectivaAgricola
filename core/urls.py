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
    RemisionListView, RemisionCreateView, RemisionUpdateView, RemisionDeleteView, RemisionDetailView, RemisionImprimirView,
    RemisionDetalleCreateView, RemisionDetalleUpdateView, RemisionDetalleDeleteView,
    RemisionLiquidacionView, CobranzaListView, CobranzaImprimirView,
    # Vistas de Presupuestos (estructura anterior)
    PresupuestoGastoListView, PresupuestoGastoCreateView, PresupuestoGastoUpdateView, PresupuestoGastoDeleteView,
    presupuesto_gasto_ajax,
    # Vistas de Presupuestos (nueva estructura)
    PresupuestoListView, PresupuestoCreateView, PresupuestoUpdateView, PresupuestoDeleteView, PresupuestoDetailView,
    # Vistas de Gastos
    GastoListView, GastoCreateView, GastoUpdateView, GastoDeleteView, GastoDetailView,
    # Vistas de Formulario de Gastos
    PresupuestoGastoFormView, PresupuestoGastosReporteView,
    # Vistas AJAX
    get_cultivos_ajax, cancelar_remision_ajax, actualizar_estado_cobranza_ajax,
    # Vistas AJAX de Emisores
    listar_emisores_ajax, agregar_emisor_ajax, obtener_emisor_ajax, validar_emisor_ajax,
    agregar_cuenta_bancaria_ajax, listar_cuentas_bancarias_ajax, eliminar_cuenta_bancaria_ajax,
    capturar_pago_ajax, reporte_pagos_view, clasificaciones_gastos_ajax, presupuesto_detalle_ajax,
    proveedores_ajax, clasificaciones_gastos_presupuesto_ajax,
    eliminar_emisor_ajax,
    reactivar_emisor_ajax
)

# Importar vistas de salidas de inventario
from .salida_views import (
    salida_inventario_list, salida_inventario_create, salida_inventario_detail,
    salida_inventario_update, salida_inventario_delete, crear_tipo_salida,
    obtener_existencia_producto, salida_inventario_imprimir
)

# Importar vistas de facturación
from .factura_views import (
    FacturacionView, ListadoFacturasView, FacturaDetailView,
    validar_emisor_ajax, validar_cfdi_ajax, timbrar_factura_ajax, cancelar_factura_ajax,
    consultar_estatus_factura_ajax, probar_conexion_pac_ajax,
    generar_pdf_factura, vista_previa_pdf_factura, descargar_xml_factura
)
from .factura_ajax_views import (
    obtener_emisor_ajax, obtener_cliente_ajax, obtener_producto_ajax, guardar_factura_ajax, timbrar_factura_ajax,
    probar_conexion_pac_ajax
)
from .catalogos_ajax_views import obtener_usos_cfdi_ajax, obtener_autorizo_gastos_ajax, crear_autorizo_gasto_ajax
from .views.main_views import cancelar_gasto_ajax, almacenes_list, almacen_create, almacen_edit, almacen_delete, compras_list, compra_create, compra_edit, compra_delete, compra_detail, kardex_list, existencias_list, kardex_producto
from .otros_movimientos_views import otros_movimientos_list, otro_movimiento_create, otro_movimiento_detail, otro_movimiento_update, otro_movimiento_delete, obtener_existencia_producto_otro_movimiento
# Importar vistas de herramientas de mantenimiento
from .views.herramientas import (
    estado_sistema, verificar_certificados, actualizar_catalogos, probar_conexion_pac
)
from .views.herramientas_mantenimiento import HerramientasMantenimientoView
from .pago_views import (
    ComplementoPagoView, EstadoCuentaView, listado_estados_cuenta,
    registrar_pago, obtener_historial_pagos, obtener_info_factura_ajax,
    guardar_complemento_pago_ajax, imprimir_estado_cuenta, descargar_debug_xml,
    imprimir_complemento_pago, descargar_xml_complemento_pago, vista_previa_complemento_pago
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
    
    # URLs de almacenes
    path('almacenes/', almacenes_list, name='almacenes_list'),
    path('almacenes/nuevo/', almacen_create, name='almacen_create'),
    path('almacenes/<int:codigo>/editar/', almacen_edit, name='almacen_edit'),
    path('almacenes/<int:codigo>/eliminar/', almacen_delete, name='almacen_delete'),
    
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
    path('remisiones/<int:pk>/imprimir/', RemisionImprimirView.as_view(), name='remision_imprimir'),
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
    path('ajax/cuentas-bancarias/agregar/', agregar_cuenta_bancaria_ajax, name='agregar_cuenta_bancarias_ajax'),
    path('ajax/cuentas-bancarias/listar/', listar_cuentas_bancarias_ajax, name='listar_cuentas_bancarias_ajax'),
    path('ajax/cuentas-bancarias/eliminar/<int:codigo>/', eliminar_cuenta_bancaria_ajax, name='eliminar_cuenta_bancaria_ajax'),
    path('ajax/remisiones/<int:remision_id>/capturar-pago/', capturar_pago_ajax, name='capturar_pago_ajax'),
    path('cobranza/reporte-pagos/', reporte_pagos_view, name='reporte_pagos'),
    
    # URLs de Presupuestos (estructura anterior)
    path('presupuestos-gasto/', PresupuestoGastoListView.as_view(), name='presupuesto_gasto_list'),
    path('presupuestos-gasto/crear/', PresupuestoGastoCreateView.as_view(), name='presupuesto_gasto_create'),
    path('presupuestos-gasto/<int:pk>/editar/', PresupuestoGastoUpdateView.as_view(), name='presupuesto_gasto_update'),
    path('presupuestos-gasto/<int:pk>/eliminar/', PresupuestoGastoDeleteView.as_view(), name='presupuesto_gasto_delete'),
    path('ajax/presupuestos-gasto/<int:pk>/', presupuesto_gasto_ajax, name='presupuesto_gasto_ajax'),
    
    # URLs de Presupuestos (nueva estructura)
    path('presupuestos/', PresupuestoListView.as_view(), name='presupuesto_list'),
    path('presupuestos/crear/', PresupuestoCreateView.as_view(), name='presupuesto_create'),
    path('presupuestos/<int:pk>/', PresupuestoDetailView.as_view(), name='presupuesto_detail'),
    path('presupuestos/<int:pk>/editar/', PresupuestoUpdateView.as_view(), name='presupuesto_update'),
    path('presupuestos/<int:pk>/eliminar/', PresupuestoDeleteView.as_view(), name='presupuesto_delete'),
    path('ajax/presupuestos/<int:pk>/detalle/', presupuesto_detalle_ajax, name='presupuesto_detalle_ajax'),
    
    # URLs de Gastos
    path('gastos/', GastoListView.as_view(), name='gasto_list'),
    path('gastos/crear/', GastoCreateView.as_view(), name='gasto_create'),
    path('gastos/<int:pk>/', GastoDetailView.as_view(), name='gasto_detail'),
    path('gastos/<int:pk>/editar/', GastoUpdateView.as_view(), name='gasto_update'),
    path('gastos/<int:pk>/eliminar/', GastoDeleteView.as_view(), name='gasto_delete'),
    
    # Formulario de captura de gastos para presupuesto
    path('presupuestos/<str:pk>/capturar-gastos/', PresupuestoGastoFormView.as_view(), name='presupuesto_gasto_form'),
    # Reporte de gastos para presupuesto
    path('presupuestos/<str:pk>/gastos-reporte/', PresupuestoGastosReporteView.as_view(), name='presupuesto_gastos_reporte'),
    
    # URLs AJAX
    path('ajax/clasificaciones-gastos/', clasificaciones_gastos_ajax, name='clasificaciones_gastos_ajax'),
    path('ajax/proveedores/', proveedores_ajax, name='proveedores_ajax'),
    path('ajax/presupuestos/<int:presupuesto_id>/clasificaciones/', clasificaciones_gastos_presupuesto_ajax, name='clasificaciones_gastos_presupuesto_ajax'),
    
    # URLs AJAX para Emisores
    path('ajax/emisores/listar/', listar_emisores_ajax, name='listar_emisores_ajax'),
    path('ajax/emisores/agregar/', agregar_emisor_ajax, name='agregar_emisor_ajax'),
    path('ajax/emisores/<int:codigo>/', obtener_emisor_ajax, name='obtener_emisor_ajax'),
    # Nota: para evitar colisión con la validación usada en facturación, se renombra la ruta int
    path('ajax/emisores/<int:codigo>/validar-certificado/', validar_emisor_ajax, name='validar_emisor_certificado_ajax'),
    path('ajax/emisores/eliminar/<int:codigo>/', eliminar_emisor_ajax, name='eliminar_emisor_ajax'),
    path('ajax/emisores/reactivar/<int:codigo>/', reactivar_emisor_ajax, name='reactivar_emisor_ajax'),
    
    # URLs para Facturación
    path('facturacion/', FacturacionView.as_view(), name='facturacion'),
    path('listado-facturas/', ListadoFacturasView.as_view(), name='listado_facturas'),
    path('factura/<int:folio>/', FacturaDetailView.as_view(), name='factura_detail'),
    path('factura/<int:folio>/pdf/', generar_pdf_factura, name='generar_pdf_factura'),
    path('factura/<int:folio>/vista-previa/', vista_previa_pdf_factura, name='vista_previa_pdf_factura'),
    path('factura/<int:folio>/xml/', descargar_xml_factura, name='descargar_xml_factura'),
    path('ajax/emisores/<str:codigo>/', obtener_emisor_ajax, name='obtener_emisor_ajax'),
    path('ajax/clientes/<str:codigo>/', obtener_cliente_ajax, name='obtener_cliente_ajax'),
    path('ajax/productos/<str:codigo>/', obtener_producto_ajax, name='obtener_producto_ajax'),
    path('ajax/facturas/guardar/', guardar_factura_ajax, name='guardar_factura_ajax'),
    path('ajax/facturas/<int:folio>/cancelar/', cancelar_factura_ajax, name='cancelar_factura_ajax'),
    
    # URLs AJAX para validación y timbrado
    # Esta es la validación que usa facturación (devuelve {valido, errores, advertencias})
    path('ajax/emisores/<str:codigo>/validar/', validar_emisor_ajax, name='validar_emisor_ajax'),
    path('ajax/facturas/validar/', validar_cfdi_ajax, name='validar_cfdi_ajax'),
    path('ajax/facturas/timbrar/<int:folio>/', timbrar_factura_ajax, name='timbrar_factura_ajax'),
    path('ajax/facturas/<int:factura_id>/cancelar/', cancelar_factura_ajax, name='cancelar_factura_ajax'),
    path('ajax/facturas/<int:factura_id>/estatus/', consultar_estatus_factura_ajax, name='consultar_estatus_factura_ajax'),
    path('ajax/emisores/<int:emisor_id>/probar-conexion/', probar_conexion_pac_ajax, name='probar_conexion_pac_ajax'),
    
    # URLs AJAX para catálogos
    path('ajax/catalogos/usos-cfdi/', obtener_usos_cfdi_ajax, name='obtener_usos_cfdi_ajax'),
    path('ajax/catalogos/autorizo-gastos/', obtener_autorizo_gastos_ajax, name='obtener_autorizo_gastos_ajax'),
    path('ajax/catalogos/autorizo-gastos/crear/', crear_autorizo_gasto_ajax, name='crear_autorizo_gasto_ajax'),
    path('ajax/gastos/<int:gasto_id>/cancelar/', cancelar_gasto_ajax, name='cancelar_gasto_ajax'),
    
    # URLs para herramientas de mantenimiento
    path('herramientas/', HerramientasMantenimientoView.as_view(), name='herramientas_mantenimiento'),
    path('ajax/herramientas/estado-sistema/', estado_sistema, name='estado_sistema_ajax'),
    path('ajax/herramientas/verificar-certificados/', verificar_certificados, name='verificar_certificados_ajax'),
    path('ajax/herramientas/actualizar-catalogos/', actualizar_catalogos, name='actualizar_catalogos_ajax'),
    path('ajax/herramientas/probar-conexion-pac/', probar_conexion_pac, name='probar_conexion_pac_ajax'),
    
    # URLs para complemento de pago
    path('complemento-pago/', ComplementoPagoView.as_view(), name='complemento_pago'),
    path('estado-cuenta/<int:cliente_id>/', EstadoCuentaView.as_view(), name='estado_cuenta'),
    path('estado-cuenta/<int:cliente_id>/imprimir/', imprimir_estado_cuenta, name='imprimir_estado_cuenta'),
    path('estados-cuenta/', listado_estados_cuenta, name='listado_estados_cuenta'),
    
    # URLs AJAX para pagos
    path('ajax/factura/<int:factura_id>/registrar-pago/', registrar_pago, name='registrar_pago_ajax'),
    path('ajax/factura/<int:factura_id>/historial-pagos/', obtener_historial_pagos, name='historial_pagos_ajax'),
    path('ajax/factura/<int:factura_id>/info/', obtener_info_factura_ajax, name='info_factura_ajax'),
    path('ajax/factura/<int:factura_id>/complemento-pago/', guardar_complemento_pago_ajax, name='guardar_complemento_pago_ajax'),
    
    # URLs para debugging
    path('debug/xml/<str:tipo>/<str:factura_folio>/<str:timestamp>/', descargar_debug_xml, name='descargar_debug_xml'),
    
    # URLs para complemento de pago
    path('complemento-pago/<int:pago_id>/vista-previa/', vista_previa_complemento_pago, name='vista_previa_complemento_pago'),
    path('complemento-pago/<int:pago_id>/imprimir/', imprimir_complemento_pago, name='imprimir_complemento_pago'),
    path('complemento-pago/<int:pago_id>/xml/', descargar_xml_complemento_pago, name='descargar_xml_complemento_pago'),
    
    # URLs para compras
    path('compras/', compras_list, name='compras_list'),
    path('compras/nuevo/', compra_create, name='compra_create'),
    path('compras/<int:folio>/editar/', compra_edit, name='compra_edit'),
    path('compras/<int:folio>/eliminar/', compra_delete, name='compra_delete'),
    path('compras/<int:folio>/', compra_detail, name='compra_detail'),
    
    # URLs para kardex y existencias
    path('kardex/', kardex_list, name='kardex_list'),
    path('existencias/', existencias_list, name='existencias_list'),
    path('kardex/producto/<int:producto_codigo>/almacen/<int:almacen_codigo>/', kardex_producto, name='kardex_producto'),
    
    # URLs para salidas de inventario
    path('salidas-inventario/', salida_inventario_list, name='salida_inventario_list'),
    path('salidas-inventario/nuevo/', salida_inventario_create, name='salida_inventario_create'),
    path('salidas-inventario/<int:pk>/', salida_inventario_detail, name='salida_inventario_detail'),
    path('salidas-inventario/<int:pk>/editar/', salida_inventario_update, name='salida_inventario_update'),
    path('salidas-inventario/<int:pk>/eliminar/', salida_inventario_delete, name='salida_inventario_delete'),
    path('salidas-inventario/<int:pk>/imprimir/', salida_inventario_imprimir, name='salida_inventario_imprimir'),
    
    # URLs AJAX para salidas de inventario
    path('ajax/crear-tipo-salida/', crear_tipo_salida, name='crear_tipo_salida'),
    path('ajax/existencia-producto/', obtener_existencia_producto, name='obtener_existencia_producto'),
    
    # URLs para otros movimientos
    path('otros-movimientos/', otros_movimientos_list, name='otros_movimientos_list'),
    path('otros-movimientos/nuevo/', otro_movimiento_create, name='otro_movimiento_create'),
    path('otros-movimientos/<int:folio>/', otro_movimiento_detail, name='otro_movimiento_detail'),
    path('otros-movimientos/<int:folio>/editar/', otro_movimiento_update, name='otro_movimiento_update'),
    path('otros-movimientos/<int:folio>/eliminar/', otro_movimiento_delete, name='otro_movimiento_delete'),
    
    # URLs AJAX para otros movimientos
    path('ajax/existencia-producto-otro-movimiento/', obtener_existencia_producto_otro_movimiento, name='obtener_existencia_producto_otro_movimiento'),
]
