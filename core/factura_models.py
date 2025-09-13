from django.db import models
from decimal import Decimal
from .models import Emisor, Cliente, ProductoServicio, Usuario


class Factura(models.Model):
    """Modelo para gestión de facturas"""
    
    # Identificación de la factura
    serie = models.CharField(
        max_length=10,
        verbose_name="Serie",
        help_text="Serie de la factura"
    )
    folio = models.AutoField(
        primary_key=True,
        verbose_name="Folio",
        help_text="Folio consecutivo de la factura"
    )
    
    # Fecha y hora de emisión
    fecha_emision = models.DateTimeField(
        verbose_name="Fecha de Emisión",
        help_text="Fecha y hora de emisión de la factura"
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
    
    # Uso CFDI
    USO_CFDI_CHOICES = [
        ('G01', 'G01 - Adquisición de mercancías'),
        ('G02', 'G02 - Devoluciones, descuentos o bonificaciones'),
        ('G03', 'G03 - Gastos en general'),
        ('I01', 'I01 - Construcciones'),
        ('I02', 'I02 - Mobilario y equipo de oficina por inversiones'),
        ('I03', 'I03 - Equipo de transporte'),
        ('I04', 'I04 - Equipo de computo y accesorios'),
        ('I05', 'I05 - Dados, troqueles, moldes, matrices y herramental'),
        ('I06', 'I06 - Comunicaciones telefónicas'),
        ('I07', 'I07 - Comunicaciones satelitales'),
        ('I08', 'I08 - Otra maquinaria y equipo'),
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
        ('P01', 'P01 - Por definir'),
    ]
    
    uso_cfdi = models.CharField(
        max_length=3,
        choices=USO_CFDI_CHOICES,
        verbose_name="Uso CFDI",
        help_text="Uso del comprobante fiscal"
    )
    
    # Exportación
    EXPORTACION_CHOICES = [
        ('01', '01 - No aplica'),
        ('02', '02 - Definitiva (bloqueado)'),
        ('03', '03 - Temporal'),
    ]
    
    exportacion = models.CharField(
        max_length=2,
        choices=EXPORTACION_CHOICES,
        default='01',
        verbose_name="Exportación",
        help_text="Tipo de exportación"
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
    
    # Totales
    subtotal = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        verbose_name="Subtotal",
        help_text="Subtotal de la factura"
    )
    
    impuesto = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        verbose_name="Impuesto",
        help_text="Total de impuestos"
    )
    
    total = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        verbose_name="Total",
        help_text="Total de la factura"
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
    
    class Meta:
        verbose_name = "Factura"
        verbose_name_plural = "Facturas"
        db_table = 'facturas'
        ordering = ['-fecha_creacion']
        unique_together = ['serie', 'folio']
        indexes = [
            models.Index(fields=['serie', 'folio']),
            models.Index(fields=['fecha_emision']),
            models.Index(fields=['emisor']),
            models.Index(fields=['receptor']),
        ]
    
    def __str__(self):
        return f"{self.serie}-{self.folio:06d}"
    
    def clean(self):
        """Validaciones adicionales del modelo"""
        super().clean()
        
        # Normalizar serie
        if self.serie:
            self.serie = self.serie.strip().upper()
    
    def save(self, *args, **kwargs):
        """Guardar con validaciones"""
        self.full_clean()
        super().save(*args, **kwargs)


class FacturaDetalle(models.Model):
    """Modelo para detalle de facturas"""
    
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
    
    no_identificacion = models.CharField(
        max_length=50,
        verbose_name="No. Identificación",
        help_text="Número de identificación del producto"
    )
    
    concepto = models.CharField(
        max_length=200,
        verbose_name="Concepto",
        help_text="Descripción del concepto"
    )
    
    cantidad = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Cantidad",
        help_text="Cantidad del producto"
    )
    
    precio = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name="Precio",
        help_text="Precio unitario del producto"
    )
    
    clave_prod_serv = models.CharField(
        max_length=20,
        verbose_name="ClaveProdServ",
        help_text="Clave del producto o servicio"
    )
    
    unidad = models.CharField(
        max_length=20,
        verbose_name="Unidad",
        help_text="Unidad de medida"
    )
    
    # Objeto de impuesto
    OBJETO_IMPUESTO_CHOICES = [
        ('01', '01 - No objeto del impuesto'),
        ('02', '02 - Sí objeto del impuesto'),
        ('03', '03 - Sí objeto del impuesto y no obligado al desglose'),
    ]
    
    objeto_impuesto = models.CharField(
        max_length=2,
        choices=OBJETO_IMPUESTO_CHOICES,
        default='02',
        verbose_name="Objeto de Impuesto",
        help_text="Objeto del impuesto"
    )
    
    # Cálculos
    importe = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name="Importe",
        help_text="Importe del concepto (cantidad * precio)"
    )
    
    impuesto_concepto = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        verbose_name="Impuesto",
        help_text="Impuesto del concepto"
    )
    
    class Meta:
        verbose_name = "Detalle de Factura"
        verbose_name_plural = "Detalles de Factura"
        db_table = 'factura_detalles'
        ordering = ['id']
    
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
        
        # Calcular impuesto (16% por defecto, se puede personalizar)
        if self.objeto_impuesto == '02':
            self.impuesto_concepto = self.importe * Decimal('0.16')
        else:
            self.impuesto_concepto = Decimal('0.00')
        
        self.full_clean()
        super().save(*args, **kwargs)
