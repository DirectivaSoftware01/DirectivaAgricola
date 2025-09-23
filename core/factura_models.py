from django.db import models
from decimal import Decimal
from .models import Emisor, Cliente, ProductoServicio, Usuario


class Factura(models.Model):
    """Modelo para gestión de facturas CFDI 4.0 según Anexo 20 RMF 2022"""
    
    # Identificación de la factura (CFDI 4.0)
    serie = models.CharField(
        max_length=25,
        blank=True,
        null=True,
        verbose_name="Serie",
        help_text="Serie para control interno del contribuyente (opcional)"
    )
    folio = models.AutoField(
        primary_key=True,
        verbose_name="Folio",
        help_text="Folio consecutivo de la factura (clave primaria)"
    )
    
    
    # Fecha y hora de emisión (CFDI 4.0 - Requerido)
    fecha_emision = models.DateTimeField(
        verbose_name="Fecha de Emisión",
        help_text="Fecha y hora de emisión del comprobante (AAAA-MM-DDThh:mm:ss)"
    )
    
    # Emisor
    emisor = models.ForeignKey(
        Emisor,
        on_delete=models.PROTECT,
        verbose_name="Emisor",
        help_text="Emisor de la factura"
    )
    lugar_expedicion = models.CharField(
        max_length=5,
        verbose_name="Lugar de Expedición",
        help_text="Código postal del lugar de expedición"
    )
    
    # Receptor (Cliente)
    receptor = models.ForeignKey(
        Cliente,
        on_delete=models.PROTECT,
        verbose_name="Receptor",
        help_text="Cliente receptor de la factura"
    )
    
    # Uso CFDI - Catálogo completo del SAT
    USO_CFDI_CHOICES = [
        # Adquisiciones y gastos generales
        ('G01', 'G01 - Adquisición de mercancías'),
        ('G02', 'G02 - Devoluciones, descuentos o bonificaciones'),
        ('G03', 'G03 - Gastos en general'),
        
        # Inversiones y equipos
        ('I01', 'I01 - Construcciones'),
        ('I02', 'I02 - Mobilario y equipo de oficina por inversiones'),
        ('I03', 'I03 - Equipo de transporte'),
        ('I04', 'I04 - Equipo de computo y accesorios'),
        ('I05', 'I05 - Dados, troqueles, moldes, matrices y herramental'),
        ('I06', 'I06 - Comunicaciones telefónicas'),
        ('I07', 'I07 - Comunicaciones satelitales'),
        ('I08', 'I08 - Otra maquinaria y equipo'),
        
        # Deducciones personales
        ('D01', 'D01 - Honorarios médicos, dentales y gastos hospitalarios'),
        ('D02', 'D02 - Gastos médicos por incapacidad o discapacidad'),
        ('D03', 'D03 - Gastos funerales'),
        ('D04', 'D04 - Donativos'),
        ('D05', 'D05 - Intereses reales efectivamente pagados por créditos hipotecarios (casa habitación)'),
        ('D06', 'D06 - Aportaciones voluntarias al SAR'),
        ('D07', 'D07 - Primas por seguros de gastos médicos'),
        ('D08', 'D08 - Gastos de transportación escolar obligatoria'),
        ('D09', 'D09 - Depósitos en cuentas para el ahorro, primas que tengan como base planes de pensiones'),
        ('D10', 'D10 - Pagos por servicios educativos (colegiaturas)'),
        
        # Actividades empresariales
        ('CP01', 'CP01 - Pagos'),
        ('CN01', 'CN01 - Nómina'),
        
        # Comercio exterior
        ('S01', 'S01 - Sin efectos fiscales'),
        
        # Por definir
        ('P01', 'P01 - Por definir'),
        
        # Deducciones CFDI 4.0
        ('DI01', 'DI01 - Honorarios médicos, dentales y gastos hospitalarios'),
        ('DI02', 'DI02 - Gastos médicos por incapacidad o discapacidad'),
        ('DI03', 'DI03 - Gastos funerales'),
        ('DI04', 'DI04 - Donativos'),
        ('DI05', 'DI05 - Intereses reales efectivamente pagados por créditos hipotecarios (casa habitación)'),
        ('DI06', 'DI06 - Aportaciones voluntarias al SAR'),
        ('DI07', 'DI07 - Primas por seguros de gastos médicos'),
        ('DI08', 'DI08 - Gastos de transportación escolar obligatoria'),
        ('DI09', 'DI09 - Depósitos en cuentas para el ahorro, primas que tengan como base planes de pensiones'),
        ('DI10', 'DI10 - Pagos por servicios educativos (colegiaturas)'),
        
        # Actividades empresariales CFDI 4.0
        ('DCP01', 'DCP01 - Pagos'),
        ('DCN01', 'DCN01 - Nómina'),
        
        # Comercio exterior CFDI 4.0
        ('DS01', 'DS01 - Sin efectos fiscales'),
        
        # Por definir CFDI 4.0
        ('DP01', 'DP01 - Por definir'),
    ]
    
    uso_cfdi = models.CharField(
        max_length=5,
        choices=USO_CFDI_CHOICES,
        verbose_name="Uso CFDI",
        help_text="Uso del comprobante fiscal"
    )
    
    # Exportación (CFDI 4.0 - Requerido)
    EXPORTACION_CHOICES = [
        ('01', '01 - No aplica'),
        ('02', '02 - Definitiva'),
        ('03', '03 - Temporal'),
    ]
    
    exportacion = models.CharField(
        max_length=2,
        choices=EXPORTACION_CHOICES,
        default='01',
        verbose_name="Exportacion",
        help_text="Tipo de exportación (requerido)"
    )
    
    # Tipo de Comprobante (CFDI 4.0 - Requerido)
    TIPO_COMPROBANTE_CHOICES = [
        ('I', 'I - Ingreso'),
        ('E', 'E - Egreso'),
        ('T', 'T - Traslado'),
        ('N', 'N - Nómina'),
        ('P', 'P - Pago'),
    ]
    
    tipo_comprobante = models.CharField(
        max_length=1,
        choices=TIPO_COMPROBANTE_CHOICES,
        default='I',
        verbose_name="TipoDeComprobante",
        help_text="Tipo de comprobante (requerido)"
    )
    
    # Confirmación (CFDI 4.0 - Opcional)
    confirmacion = models.CharField(
        max_length=2,
        blank=True,
        null=True,
        verbose_name="Confirmacion",
        help_text="Confirmación del comprobante (opcional)"
    )
    
    # Método de pago
    METODO_PAGO_CHOICES = [
        ('PUE', 'PUE - Pago en una sola exhibición'),
        ('PPD', 'PPD - Pago en parcialidades o diferido'),
    ]
    
    metodo_pago = models.CharField(
        max_length=3,
        choices=METODO_PAGO_CHOICES,
        default='PUE',
        verbose_name="Método de Pago",
        help_text="Método de pago"
    )
    
    # Moneda
    moneda = models.CharField(
        max_length=3,
        default='MXN',
        verbose_name="Moneda",
        help_text="Moneda de la factura"
    )
    
    # Forma de pago
    FORMA_PAGO_CHOICES = [
        ('01', '01 - Efectivo'),
        ('02', '02 - Cheque nominativo'),
        ('03', '03 - Transferencia electrónica de fondos'),
        ('04', '04 - Tarjeta de crédito'),
        ('05', '05 - Monedero electrónico'),
        ('06', '06 - Dinero electrónico'),
        ('08', '08 - Vales de despensa'),
        ('12', '12 - Dación en pago'),
        ('13', '13 - Pago por subrogación'),
        ('14', '14 - Pago por consignación'),
        ('15', '15 - Condonación'),
        ('17', '17 - Compensación'),
        ('23', '23 - Novación'),
        ('24', '24 - Confusión'),
        ('25', '25 - Remisión de deuda'),
        ('26', '26 - Prescripción o caducidad'),
        ('27', '27 - A satisfacción del acreedor'),
        ('28', '28 - Tarjeta de débito'),
        ('29', '29 - Tarjeta de servicios'),
        ('30', '30 - Aplicación de anticipos'),
        ('31', '31 - Intermediario pagos'),
        ('99', '99 - Por definir'),
    ]
    
    forma_pago = models.CharField(
        max_length=2,
        choices=FORMA_PAGO_CHOICES,
        default='99',
        verbose_name="Forma de Pago",
        help_text="Forma de pago"
    )
    
    # Tipo de cambio
    tipo_cambio = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=1.0000,
        verbose_name="Tipo de Cambio",
        help_text="Tipo de cambio"
    )
    
    # Totales (CFDI 4.0 - Requeridos)
    subtotal = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        verbose_name="SubTotal",
        help_text="Subtotal del comprobante (requerido)"
    )
    
    descuento = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        default=0.0000,
        blank=True,
        null=True,
        verbose_name="Descuento",
        help_text="Descuento aplicado al comprobante (opcional)"
    )
    
    total = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        verbose_name="Total",
        help_text="Total del comprobante (requerido)"
    )
    
    # Impuestos (CFDI 4.0 - Requerido para cálculo de totales)
    impuesto = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        default=0.0000,
        verbose_name="Impuesto",
        help_text="Total de impuestos trasladados"
    )
    
    # Auditoría
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    fecha_modificacion = models.DateTimeField(auto_now=True, verbose_name="Fecha de Modificación")
    usuario_creacion = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name='facturas_creadas',
        verbose_name="Usuario de Creación"
    )
    usuario_modificacion = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name='facturas_modificadas',
        verbose_name="Usuario de Modificación",
        blank=True,
        null=True
    )
    
    # Estado de la factura
    cancelada = models.BooleanField(
        default=False,
        verbose_name="Cancelada",
        help_text="Indica si la factura está cancelada"
    )
    
    # Campos de timbrado CFDI 4.0 (según Anexo 20)
    uuid = models.CharField(
        max_length=36,
        blank=True,
        null=True,
        verbose_name="UUID",
        help_text="UUID del comprobante fiscal timbrado"
    )
    
    fecha_timbrado = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Fecha de Timbrado",
        help_text="Fecha y hora del timbrado"
    )
    
    no_cert_sat = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="NoCertificadoSAT",
        help_text="Número de serie del certificado SAT (20 posiciones)"
    )
    
    sello_sat = models.TextField(
        blank=True,
        null=True,
        verbose_name="SelloSAT",
        help_text="Sello digital del SAT en Base64"
    )
    
    codigo_qr = models.TextField(
        blank=True,
        null=True,
        verbose_name="Código QR",
        help_text="Código QR de la factura en Base64 (proporcionado por el PAC)"
    )
    
    cadena_original_sat = models.TextField(
        blank=True,
        null=True,
        verbose_name="Cadena Original complemento SAT",
        help_text="Cadena original del complemento SAT (SelloCFD del timbre fiscal)"
    )
    
    # Campos de sello digital del emisor (CFDI 4.0)
    sello = models.TextField(
        blank=True,
        null=True,
        verbose_name="Sello",
        help_text="Sello digital del comprobante en Base64"
    )
    
    no_certificado = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="NoCertificado",
        help_text="Número de serie del certificado del emisor"
    )
    
    certificado = models.TextField(
        blank=True,
        null=True,
        verbose_name="Certificado",
        help_text="Certificado del emisor en Base64"
    )
    
    ESTADO_TIMBRADO_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('TIMBRADO', 'Timbrado'),
        ('CANCELADO', 'Cancelado'),
        ('ERROR', 'Error'),
    ]
    
    estado_timbrado = models.CharField(
        max_length=20,
        choices=ESTADO_TIMBRADO_CHOICES,
        default='PENDIENTE',
        verbose_name="Estado de Timbrado",
        help_text="Estado del timbrado"
    )
    
    # Información Global (requerida para RFC XAXX010101000)
    periodicidad = models.CharField(
        max_length=2,
        choices=[
            ('01', '01 - Mensual'),
            ('02', '02 - Bimestral'),
            ('03', '03 - Trimestral'),
            ('04', '04 - Cuatrimestral'),
            ('05', '05 - Semestral'),
            ('06', '06 - Anual'),
        ],
        blank=True,
        null=True,
        verbose_name="Periodicidad",
        help_text="Periodicidad de la información global"
    )
    
    meses = models.CharField(
        max_length=2,
        choices=[
            ('01', '01 - Enero'),
            ('02', '02 - Febrero'),
            ('03', '03 - Marzo'),
            ('04', '04 - Abril'),
            ('05', '05 - Mayo'),
            ('06', '06 - Junio'),
            ('07', '07 - Julio'),
            ('08', '08 - Agosto'),
            ('09', '09 - Septiembre'),
            ('10', '10 - Octubre'),
            ('11', '11 - Noviembre'),
            ('12', '12 - Diciembre'),
        ],
        blank=True,
        null=True,
        verbose_name="Meses",
        help_text="Meses del período de la información global"
    )
    
    año_informacion_global = models.IntegerField(
        blank=True,
        null=True,
        verbose_name="Año",
        help_text="Año del período de la información global"
    )
    
    # Archivos XML
    xml_original = models.TextField(
        blank=True,
        null=True,
        verbose_name="XML Original",
        help_text="XML original antes del timbrado"
    )
    
    xml_timbrado = models.TextField(
        blank=True,
        null=True,
        verbose_name="XML Timbrado",
        help_text="XML timbrado por el PAC"
    )
    
    # Datos de cancelación
    fecha_cancelacion = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Fecha de Cancelación",
        help_text="Fecha y hora de cancelación"
    )
    
    motivo_cancelacion = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name="Motivo de Cancelación",
        help_text="Motivo de la cancelación"
    )
    
    acuse_cancelacion = models.TextField(
        blank=True,
        null=True,
        verbose_name="Acuse de Cancelación",
        help_text="Acuse de cancelación del SAT"
    )
    
    # Datos de validación
    errores_validacion = models.TextField(
        blank=True,
        null=True,
        verbose_name="Errores de Validación",
        help_text="Errores encontrados en la validación"
    )
    
    # Bitácora de timbrado
    intentos_timbrado = models.PositiveIntegerField(
        default=0,
        verbose_name="Intentos de Timbrado",
        help_text="Número de intentos de timbrado"
    )
    
    ultimo_intento = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Último Intento",
        help_text="Fecha del último intento de timbrado"
    )
    
    class Meta:
        verbose_name = "Factura CFDI 4.0"
        verbose_name_plural = "Facturas CFDI 4.0"
        db_table = 'facturas'
        ordering = ['-fecha_creacion']
        unique_together = [['serie', 'folio']]  # Serie y folio únicos juntos
        indexes = [
            models.Index(fields=['serie', 'folio']),
            models.Index(fields=['fecha_emision']),
            models.Index(fields=['emisor']),
            models.Index(fields=['receptor']),
            models.Index(fields=['uuid']),
            models.Index(fields=['estado_timbrado']),
            models.Index(fields=['fecha_timbrado']),
            models.Index(fields=['cancelada']),
            models.Index(fields=['tipo_comprobante']),
            models.Index(fields=['exportacion']),
        ]
    
    def __str__(self):
        if self.serie and self.folio:
            return f"{self.serie}-{self.folio}"
        elif self.folio:
            return f"F-{self.folio}"
        else:
            return f"Factura #{self.id}"
    
    def clean(self):
        """Validaciones adicionales del modelo"""
        super().clean()
        
        # Normalizar serie
        if self.serie:
            self.serie = self.serie.strip().upper()
    
    def save(self, *args, **kwargs):
        """Guardar con validaciones y actualización de fecha de emisión"""
        # Actualizar fecha de emisión con zona horaria correcta si no está establecida
        if not self.fecha_emision:
            from core.utils.timezone_utils import obtener_fecha_actual_mexico
            self.fecha_emision = obtener_fecha_actual_mexico(self.lugar_expedicion)
        
        self.full_clean()
        super().save(*args, **kwargs)
    
    @classmethod
    def obtener_siguiente_folio_por_serie(cls, serie=None):
        """Obtiene el siguiente folio disponible para una serie específica"""
        # Si no hay serie, usar None para agrupar todas las facturas sin serie
        serie = serie if serie else None
        
        # Buscar el último folio para esta serie
        ultima_factura = cls.objects.filter(serie=serie).order_by('-folio').first()
        
        if ultima_factura:
            return ultima_factura.folio + 1
        else:
            return 1
    
    def obtener_saldo_pendiente(self):
        """Obtiene el saldo pendiente de pago para facturas PPD"""
        if self.metodo_pago != 'PPD':
            return Decimal('0.00')
        
        # Calcular total de pagos realizados (solo pagos timbrados)
        from django.db.models import Sum
        total_pagado = self.pagos.filter(uuid__isnull=False).aggregate(
            total=Sum('monto_pago')
        )['total'] or Decimal('0.00')
        
        # Saldo pendiente = Total factura - Total pagado
        return self.total - total_pagado
    
    def obtener_total_pagado(self):
        """Obtiene el total pagado de la factura"""
        from django.db.models import Sum
        return self.pagos.filter(uuid__isnull=False).aggregate(
            total=Sum('monto_pago')
        )['total'] or Decimal('0.00')
    
    def esta_pagada(self):
        """Verifica si la factura está completamente pagada"""
        return self.obtener_saldo_pendiente() <= Decimal('0.00')
    
    def obtener_estado_pago(self):
        """Obtiene el estado del pago de la factura"""
        if self.metodo_pago != 'PPD':
            return 'No aplica'
        
        saldo_pendiente = self.obtener_saldo_pendiente()
        total_pagado = self.obtener_total_pagado()
        
        if saldo_pendiente <= Decimal('0.00'):
            return 'Pagada'
        elif total_pagado > Decimal('0.00'):
            return 'Pago parcial'
        else:
            return 'Pendiente'


class FacturaDetalle(models.Model):
    """Modelo para detalle de facturas CFDI 4.0 según Anexo 20 RMF 2022"""
    
    factura = models.ForeignKey(
        Factura,
        on_delete=models.CASCADE,
        related_name='detalles',
        verbose_name="Factura",
        help_text="Factura a la que pertenece el detalle"
    )
    
    # Producto/Servicio
    producto_servicio = models.ForeignKey(
        ProductoServicio,
        on_delete=models.PROTECT,
        verbose_name="Producto/Servicio",
        help_text="Producto o servicio facturado"
    )
    
    # Campos del concepto según Anexo 20
    no_identificacion = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="NoIdentificacion",
        help_text="Número de identificación del producto (opcional)"
    )
    
    concepto = models.CharField(
        max_length=1000,
        verbose_name="Descripcion",
        help_text="Descripción del concepto (requerido)"
    )
    
    cantidad = models.DecimalField(
        max_digits=15,
        decimal_places=6,
        verbose_name="Cantidad",
        help_text="Cantidad del producto (requerido)"
    )
    
    precio = models.DecimalField(
        max_digits=15,
        decimal_places=6,
        verbose_name="ValorUnitario",
        help_text="Valor unitario del producto (requerido)"
    )
    
    clave_prod_serv = models.CharField(
        max_length=20,
        verbose_name="ClaveProdServ",
        help_text="Clave del producto o servicio (requerido)"
    )
    
    # Unidad de medida (CFDI 4.0)
    clave_unidad = models.CharField(
        max_length=3,
        default='H87',
        verbose_name="ClaveUnidad",
        help_text="Clave de la unidad de medida (requerido)"
    )
    
    unidad = models.CharField(
        max_length=20,
        default='Pieza',
        verbose_name="Unidad",
        help_text="Unidad de medida (requerido)"
    )
    
    # Objeto de impuesto (CFDI 4.0)
    OBJETO_IMPUESTO_CHOICES = [
        ('01', '01 - No objeto del impuesto'),
        ('02', '02 - Sí objeto del impuesto'),
        ('03', '03 - Sí objeto del impuesto y no obligado al desglose'),
    ]
    
    objeto_impuesto = models.CharField(
        max_length=2,
        choices=OBJETO_IMPUESTO_CHOICES,
        default='02',
        verbose_name="ObjetoImp",
        help_text="Objeto del impuesto (requerido)"
    )
    
    # Cálculos (CFDI 4.0)
    importe = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name="Importe",
        help_text="Importe del concepto (cantidad * precio) (requerido)"
    )
    
    impuesto_concepto = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        default=0.0000,
        verbose_name="Impuesto",
        help_text="Impuesto del concepto"
    )
    
    # Descuento del concepto (CFDI 4.0 - Opcional)
    descuento = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        blank=True,
        null=True,
        verbose_name="Descuento",
        help_text="Descuento aplicado al concepto (opcional)"
    )
    
    class Meta:
        verbose_name = "Concepto CFDI 4.0"
        verbose_name_plural = "Conceptos CFDI 4.0"
        db_table = 'factura_detalles'
        ordering = ['id']
        indexes = [
            models.Index(fields=['factura']),
            models.Index(fields=['clave_prod_serv']),
            models.Index(fields=['objeto_impuesto']),
        ]
    
    def __str__(self):
        return f"{self.factura} - {self.concepto}"
    
    def clean(self):
        """Validaciones adicionales del modelo"""
        super().clean()
        
        # Normalizar campos de texto
        if self.no_identificacion:
            self.no_identificacion = self.no_identificacion.strip()
        if self.concepto:
            self.concepto = self.concepto.strip()
        if self.clave_prod_serv:
            self.clave_prod_serv = self.clave_prod_serv.strip()
        if self.unidad:
            self.unidad = self.unidad.strip()
    
    def save(self, *args, **kwargs):
        """Guardar con validaciones y cálculos"""
        # Calcular importe
        self.importe = self.cantidad * self.precio
        
        # Calcular impuesto basado en el tipo de impuesto del producto
        from core.utils.tax_utils import calcular_impuesto_concepto
        self.impuesto_concepto = calcular_impuesto_concepto(
            self.importe, 
            self.producto_servicio.impuesto, 
            self.objeto_impuesto
        )
        
        self.full_clean()
        super().save(*args, **kwargs)
