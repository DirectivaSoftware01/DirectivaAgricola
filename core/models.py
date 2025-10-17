from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.hashers import make_password
from django.core.validators import RegexValidator, EmailValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.conf import settings
import re

# Create your models here.

class Impuesto(models.Model):
    """Catálogo de impuestos (ej. IVA 16%, IVA 0%)"""
    codigo = models.CharField(
        max_length=3,
        verbose_name="Código SAT",
        help_text="Código del SAT (ej. 002 para IVA)"
    )
    nombre = models.CharField(
        max_length=100,
        verbose_name="Nombre",
        help_text="Nombre del impuesto (ej. IVA Tasa 16%)"
    )
    tasa = models.DecimalField(
        max_digits=6,
        decimal_places=4,
        verbose_name="Tasa",
        help_text="Tasa decimal (ej. 0.1600 para 16%)"
    )
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'tipo_impuesto'
        verbose_name = 'Impuesto'
        verbose_name_plural = 'Impuestos'
        ordering = ['codigo', 'tasa']
        indexes = [
            models.Index(fields=['codigo']),
            models.Index(fields=['activo']),
        ]

    def __str__(self):
        return f"{self.codigo} - {self.nombre} ({self.tasa})"

class Usuario(AbstractUser):
    """Modelo de usuario personalizado"""
    nombre = models.CharField(max_length=100, verbose_name="Nombre completo")
    puesto = models.CharField(max_length=100, verbose_name="Puesto")
    email = models.EmailField(unique=True, verbose_name="Correo electrónico")
    is_admin = models.BooleanField(default=False, verbose_name="Es administrador")
    
    # Campos requeridos por Django
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'nombre', 'puesto']
    
    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
        db_table = 'usuarios'
    
    def __str__(self):
        return f"{self.nombre} ({self.username})"
    
    def save(self, *args, **kwargs):
        # Encriptar la contraseña si se proporciona
        if self.password and not self.password.startswith('pbkdf2_'):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)


class RegimenFiscal(models.Model):
    """Catálogo de Régimen Fiscal según el SAT"""
    codigo = models.CharField(
        max_length=10, 
        unique=True, 
        verbose_name="Código",
        help_text="Código del régimen fiscal según el SAT"
    )
    descripcion = models.CharField(
        max_length=200, 
        verbose_name="Descripción",
        help_text="Descripción del régimen fiscal"
    )
    activo = models.BooleanField(
        default=True, 
        verbose_name="Activo",
        help_text="Indica si el régimen fiscal está activo"
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    fecha_modificacion = models.DateTimeField(auto_now=True, verbose_name="Fecha de modificación")
    
    class Meta:
        verbose_name = "Régimen Fiscal"
        verbose_name_plural = "Regímenes Fiscales"
        db_table = 'regimen_fiscal'
        ordering = ['codigo']
    
    def __str__(self):
        return f"{self.codigo} - {self.descripcion}"


def validar_rfc(value):
    """Validador personalizado para RFC mexicano"""
    # Remover espacios y convertir a mayúsculas
    rfc = value.strip().upper()
    
    # Patrón para persona física (13 caracteres)
    patron_fisica = r'^[A-ZÑ&]{4}[0-9]{6}[A-Z0-9]{3}$'
    
    # Patrón para persona moral (12 caracteres)
    patron_moral = r'^[A-ZÑ&]{3}[0-9]{6}[A-Z0-9]{3}$'
    
    if not (re.match(patron_fisica, rfc) or re.match(patron_moral, rfc)):
        raise ValidationError(
            'El RFC debe tener el formato válido para persona física (13 caracteres) '
            'o persona moral (12 caracteres). Ejemplo: XAXX010101000 o ABC123456T1A'
        )
    
    return rfc


class Cliente(models.Model):
    """Modelo para gestión de clientes"""
    
    # Campo auto numérico (se maneja automáticamente con el ID)
    codigo = models.AutoField(
        primary_key=True, 
        verbose_name="Código"
    )
    
    razon_social = models.CharField(
        max_length=200, 
        verbose_name="Razón Social",
        help_text="Nombre completo o razón social del cliente"
    )
    
    regimen_fiscal = models.ForeignKey(
        RegimenFiscal,
        on_delete=models.PROTECT,
        verbose_name="Régimen Fiscal",
        help_text="Régimen fiscal del cliente según el SAT"
    )
    
    codigo_postal = models.CharField(
        max_length=5,
        validators=[RegexValidator(
            regex=r'^\d{5}$',
            message='El código postal debe tener exactamente 5 dígitos'
        )],
        verbose_name="Código Postal",
        help_text="Código postal de 5 dígitos"
    )
    
    rfc = models.CharField(
        max_length=13,
        unique=True,
        validators=[validar_rfc],
        verbose_name="RFC",
        help_text="Registro Federal de Contribuyentes (12 o 13 caracteres)"
    )
    
    domicilio = models.TextField(
        verbose_name="Domicilio",
        help_text="Dirección completa del cliente"
    )
    
    telefono = models.CharField(
        max_length=15,
        validators=[RegexValidator(
            regex=r'^[\d\s\-\+\(\)]+$',
            message='El teléfono solo puede contener números, espacios, guiones, paréntesis y el signo más'
        )],
        verbose_name="Teléfono",
        help_text="Número de teléfono del cliente"
    )
    
    email_principal = models.EmailField(
        verbose_name="Correo Electrónico Principal",
        help_text="Correo electrónico principal del cliente"
    )
    
    email_alterno = models.EmailField(
        blank=True,
        null=True,
        verbose_name="Correo Electrónico Alterno",
        help_text="Correo electrónico alternativo del cliente (opcional)"
    )
    
    # Información de entrega
    direccion_entrega = models.TextField(
        blank=True,
        null=True,
        verbose_name="Dirección de Entrega",
        help_text="Dirección específica para entregas (opcional)"
    )
    
    numero_bodega = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Número de Bodega",
        help_text="Número o identificador de la bodega (opcional)"
    )
    
    telefono_bodega = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        validators=[RegexValidator(
            regex=r'^[\d\s\-\+\(\)]+$',
            message='El teléfono solo puede contener números, espacios, guiones, paréntesis y el signo más'
        )],
        verbose_name="Teléfono de Bodega",
        help_text="Número de teléfono de la bodega (opcional)"
    )
    
    ciudad = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Ciudad",
        help_text="Ciudad del cliente (opcional)"
    )
    
    estado = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Estado",
        help_text="Estado del cliente (opcional)"
    )
    
    activo = models.BooleanField(
        default=True,
        verbose_name="Activo",
        help_text="Indica si el cliente está activo en el sistema"
    )
    
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    fecha_modificacion = models.DateTimeField(auto_now=True, verbose_name="Fecha de modificación")
    usuario_creacion = models.ForeignKey(
        Usuario, 
        on_delete=models.PROTECT,
        related_name='clientes_creados',
        verbose_name="Usuario que creó el registro"
    )
    usuario_modificacion = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name='clientes_modificados',
        verbose_name="Usuario que modificó el registro",
        blank=True,
        null=True
    )
    
    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        db_table = 'clientes'
        ordering = ['razon_social']
        indexes = [
            models.Index(fields=['rfc']),
            models.Index(fields=['razon_social']),
            models.Index(fields=['activo']),
        ]
    
    def __str__(self):
        return f"{self.codigo:06d} - {self.razon_social}"
    
    def clean(self):
        """Validaciones adicionales del modelo"""
        super().clean()
        
        # Validar que el email alterno sea diferente al principal
        if self.email_alterno and self.email_principal == self.email_alterno:
            raise ValidationError({
                'email_alterno': 'El correo electrónico alterno debe ser diferente al principal.'
            })
        
        # Normalizar RFC
        if self.rfc:
            self.rfc = self.rfc.strip().upper()
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class Proveedor(models.Model):
    """Modelo para gestión de proveedores"""
    
    # Campo auto numérico (se maneja automáticamente con el ID)
    codigo = models.AutoField(
        primary_key=True, 
        verbose_name="Código"
    )
    
    nombre = models.CharField(
        max_length=200, 
        verbose_name="Nombre",
        help_text="Nombre completo o razón social del proveedor"
    )
    
    rfc = models.CharField(
        max_length=13,
        unique=True,
        validators=[validar_rfc],
        verbose_name="RFC",
        help_text="Registro Federal de Contribuyentes (12 o 13 caracteres)"
    )
    
    domicilio = models.TextField(
        verbose_name="Domicilio",
        help_text="Dirección completa del proveedor"
    )
    
    activo = models.BooleanField(
        default=True,
        verbose_name="Activo",
        help_text="Indica si el proveedor está activo en el sistema"
    )
    
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    fecha_modificacion = models.DateTimeField(auto_now=True, verbose_name="Fecha de modificación")
    usuario_creacion = models.ForeignKey(
        Usuario, 
        on_delete=models.PROTECT,
        related_name='proveedores_creados',
        verbose_name="Usuario que creó el registro"
    )
    usuario_modificacion = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name='proveedores_modificados',
        verbose_name="Usuario que modificó el registro",
        blank=True,
        null=True
    )
    
    class Meta:
        verbose_name = "Proveedor"
        verbose_name_plural = "Proveedores"
        db_table = 'proveedores'
        ordering = ['nombre']
        indexes = [
            models.Index(fields=['rfc']),
            models.Index(fields=['nombre']),
            models.Index(fields=['activo']),
        ]
    
    def __str__(self):
        return f"{self.codigo:06d} - {self.nombre}"
    
    def clean(self):
        """Validaciones adicionales del modelo"""
        super().clean()
        
        # Normalizar RFC
        if self.rfc:
            self.rfc = self.rfc.strip().upper()
    
    def save(self, *args, **kwargs):
        """Guardar con validaciones"""
        self.full_clean()
        super().save(*args, **kwargs)


class Transportista(models.Model):
    """Modelo para gestión de transportistas"""
    
    # Campo auto numérico (se maneja automáticamente con el ID)
    codigo = models.AutoField(
        primary_key=True, 
        verbose_name="Código"
    )
    
    nombre_completo = models.CharField(
        max_length=200, 
        verbose_name="Nombre Completo",
        help_text="Nombre completo del transportista"
    )
    
    licencia = models.CharField(
        max_length=50,
        verbose_name="Licencia",
        help_text="Número de licencia de conducir"
    )
    
    domicilio = models.TextField(
        verbose_name="Domicilio",
        help_text="Dirección completa del transportista"
    )
    
    telefono = models.CharField(
        max_length=15,
        validators=[RegexValidator(regex=r'^[\d\s\-\+\(\)]+$', message='El teléfono solo puede contener números, espacios, guiones, paréntesis y el signo más')],
        verbose_name="Teléfono",
        help_text="Número de teléfono del transportista"
    )
    
    tipo_camion = models.CharField(
        max_length=100,
        verbose_name="Tipo de Camión",
        help_text="Tipo o modelo del camión"
    )
    
    placas_unidad = models.CharField(
        max_length=20,
        verbose_name="Placas de Unidad",
        help_text="Placas del camión principal"
    )
    
    placas_remolque = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Placas de Remolque",
        help_text="Placas del remolque (opcional)"
    )
    
    activo = models.BooleanField(
        default=True,
        verbose_name="Activo",
        help_text="Indica si el transportista está activo en el sistema"
    )
    
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    fecha_modificacion = models.DateTimeField(auto_now=True, verbose_name="Fecha de modificación")
    usuario_creacion = models.ForeignKey(
        Usuario, 
        on_delete=models.PROTECT,
        related_name='transportistas_creados',
        verbose_name="Usuario que creó el registro"
    )
    usuario_modificacion = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name='transportistas_modificados',
        verbose_name="Usuario que modificó el registro",
        blank=True,
        null=True
    )
    
    class Meta:
        verbose_name = "Transportista"
        verbose_name_plural = "Transportistas"
        db_table = 'transportistas'
        ordering = ['nombre_completo']
        indexes = [
            models.Index(fields=['licencia']),
            models.Index(fields=['nombre_completo']),
            models.Index(fields=['placas_unidad']),
            models.Index(fields=['activo']),
        ]
    
    def __str__(self):
        return f"{self.codigo:06d} - {self.nombre_completo}"
    
    def clean(self):
        """Validaciones adicionales del modelo"""
        super().clean()
        
        # Validar teléfono
        if self.telefono:
            self.telefono = self.telefono.strip()
            digitos = re.findall(r'\d', self.telefono)
            if len(digitos) < 10:
                raise ValidationError({
                    'telefono': 'El teléfono debe tener al menos 10 dígitos.'
                })
    
    def save(self, *args, **kwargs):
        """Guardar con validaciones"""
        self.full_clean()
        super().save(*args, **kwargs)


class LoteOrigen(models.Model):
    """Modelo para gestión de lotes de origen"""
    
    # Campo auto numérico (se maneja automáticamente con el ID)
    codigo = models.AutoField(
        primary_key=True, 
        verbose_name="Código"
    )
    
    nombre = models.CharField(
        max_length=200, 
        verbose_name="Nombre",
        help_text="Nombre del lote de origen"
    )
    
    observaciones = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observaciones",
        help_text="Observaciones adicionales sobre el lote de origen"
    )
    
    activo = models.BooleanField(
        default=True,
        verbose_name="Activo",
        help_text="Indica si el lote de origen está activo en el sistema"
    )
    
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    fecha_modificacion = models.DateTimeField(auto_now=True, verbose_name="Fecha de modificación")
    usuario_creacion = models.ForeignKey(
        Usuario, 
        on_delete=models.PROTECT,
        related_name='lotes_origen_creados',
        verbose_name="Usuario que creó el registro"
    )
    usuario_modificacion = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name='lotes_origen_modificados',
        verbose_name="Usuario que modificó el registro",
        blank=True,
        null=True
    )
    
    class Meta:
        verbose_name = "Lote de Origen"
        verbose_name_plural = "Lotes de Origen"
        db_table = 'lotes_origen'
        ordering = ['nombre']
        indexes = [
            models.Index(fields=['nombre']),
            models.Index(fields=['activo']),
        ]
    
    def __str__(self):
        return f"{self.codigo:06d} - {self.nombre}"
    
    def clean(self):
        """Validaciones adicionales del modelo"""
        super().clean()
    
    def save(self, *args, **kwargs):
        """Guardar con validaciones"""
        self.full_clean()
        super().save(*args, **kwargs)


class ClasificacionGasto(models.Model):
    """Modelo para gestión de clasificaciones de gastos"""
    
    # Campo auto numérico (se maneja automáticamente con el ID)
    codigo = models.AutoField(
        primary_key=True, 
        verbose_name="Código"
    )
    
    descripcion = models.CharField(
        max_length=200, 
        verbose_name="Descripción",
        help_text="Descripción de la clasificación de gasto"
    )
    
    observaciones = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observaciones",
        help_text="Observaciones adicionales sobre la clasificación de gasto"
    )
    
    activo = models.BooleanField(
        default=True,
        verbose_name="Activo",
        help_text="Indica si la clasificación de gasto está activa en el sistema"
    )
    
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    fecha_modificacion = models.DateTimeField(auto_now=True, verbose_name="Fecha de modificación")
    usuario_creacion = models.ForeignKey(
        Usuario, 
        on_delete=models.PROTECT,
        related_name='clasificaciones_gasto_creadas',
        verbose_name="Usuario que creó el registro"
    )
    usuario_modificacion = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name='clasificaciones_gasto_modificadas',
        verbose_name="Usuario que modificó el registro",
        blank=True,
        null=True
    )
    
    class Meta:
        verbose_name = "Clasificación de Gasto"
        verbose_name_plural = "Clasificaciones de Gastos"
        db_table = 'clasificaciones_gasto'
        ordering = ['descripcion']
        indexes = [
            models.Index(fields=['descripcion']),
            models.Index(fields=['activo']),
        ]
    
    def __str__(self):
        return f"{self.codigo:06d} - {self.descripcion}"
    
    def clean(self):
        """Validaciones adicionales del modelo"""
        super().clean()
    
    def save(self, *args, **kwargs):
        """Guardar con validaciones"""
        self.full_clean()
        super().save(*args, **kwargs)


class CentroCosto(models.Model):
    """Modelo para gestión de centros de costos"""
    
    # Campo auto numérico (se maneja automáticamente con el ID)
    codigo = models.AutoField(
        primary_key=True, 
        verbose_name="Código"
    )
    
    descripcion = models.CharField(
        max_length=200, 
        verbose_name="Descripción",
        help_text="Descripción del centro de costo"
    )
    
    hectareas = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Hectáreas",
        help_text="Número de hectáreas del centro de costo"
    )
    
    observaciones = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observaciones",
        help_text="Observaciones adicionales sobre el centro de costo"
    )
    
    activo = models.BooleanField(
        default=True,
        verbose_name="Activo",
        help_text="Indica si el centro de costo está activo en el sistema"
    )
    
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    fecha_modificacion = models.DateTimeField(auto_now=True, verbose_name="Fecha de modificación")
    usuario_creacion = models.ForeignKey(
        Usuario, 
        on_delete=models.PROTECT,
        related_name='centros_costo_creados',
        verbose_name="Usuario que creó el registro"
    )
    usuario_modificacion = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name='centros_costo_modificados',
        verbose_name="Usuario que modificó el registro",
        blank=True,
        null=True
    )
    
    class Meta:
        verbose_name = "Centro de Costo"
        verbose_name_plural = "Centros de Costos"
        db_table = 'centros_costo'
        ordering = ['descripcion']
        indexes = [
            models.Index(fields=['descripcion']),
            models.Index(fields=['activo']),
        ]
    
    def __str__(self):
        return f"{self.codigo:06d} - {self.descripcion}"
    
    def clean(self):
        """Validaciones adicionales del modelo"""
        super().clean()
        
        # Validar hectáreas
        if self.hectareas is not None and self.hectareas < 0:
            raise ValidationError({
                'hectareas': 'Las hectáreas no pueden ser negativas.'
            })
    
    def save(self, *args, **kwargs):
        """Guardar con validaciones"""
        self.full_clean()
        super().save(*args, **kwargs)


class ProductoServicio(models.Model):
    """Modelo para gestión de productos y servicios"""
    
    # Campo auto numérico (se maneja automáticamente con el ID)
    codigo = models.AutoField(
        primary_key=True, 
        verbose_name="Código"
    )
    
    sku = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="SKU",
        help_text="Clave alfanumérica única del producto o servicio"
    )
    
    descripcion = models.CharField(
        max_length=200, 
        verbose_name="Descripción",
        help_text="Descripción del producto o servicio"
    )
    
    producto_servicio = models.BooleanField(
        default=True,
        verbose_name="Tipo",
        help_text="True = Producto, False = Servicio"
    )
    
    unidad_medida = models.CharField(
        max_length=50,
        verbose_name="Unidad de Medida",
        help_text="Unidad de medida del producto o servicio"
    )
    
    clave_sat = models.CharField(
        max_length=20,
        verbose_name="Clave SAT",
        help_text="Clave del catálogo ClaveProdServ del SAT"
    )
    
    # Referencia futura a catálogo de impuestos (se añadirá FK en migración posterior)
    impuesto = models.CharField(
        max_length=20,
        choices=[
            ('IVA_16', 'IVA Tasa 16%'),
            ('IVA_0', 'IVA Tasa cero'),
            ('IVA_EXENTO', 'IVA exento')
        ],
        verbose_name="Impuesto",
        help_text="Tipo de impuesto aplicable (legado). Se usará el catálogo si está asignado."
    )
    impuesto_catalogo = models.ForeignKey(
        'Impuesto',
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        verbose_name="Impuesto (catálogo)",
        help_text="Impuesto desde catálogo"
    )
    
    clasificacion_gasto = models.ForeignKey(
        ClasificacionGasto,
        on_delete=models.PROTECT,
        verbose_name="Clasificación de Gasto",
        help_text="Clasificación de gasto para este producto o servicio",
        blank=True,
        null=True
    )
    
    activo = models.BooleanField(
        default=True,
        verbose_name="Activo",
        help_text="Indica si el producto o servicio está activo en el sistema"
    )
    
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    fecha_modificacion = models.DateTimeField(auto_now=True, verbose_name="Fecha de modificación")
    usuario_creacion = models.ForeignKey(
        Usuario, 
        on_delete=models.PROTECT,
        related_name='productos_servicios_creados',
        verbose_name="Usuario que creó el registro"
    )
    usuario_modificacion = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name='productos_servicios_modificados',
        verbose_name="Usuario que modificó el registro",
        blank=True,
        null=True
    )
    
    class Meta:
        verbose_name = "Producto o Servicio"
        verbose_name_plural = "Productos y Servicios"
        db_table = 'productos_servicios'
        ordering = ['descripcion']
        indexes = [
            models.Index(fields=['sku']),
            models.Index(fields=['descripcion']),
            models.Index(fields=['producto_servicio']),
            models.Index(fields=['clave_sat']),
            models.Index(fields=['activo']),
        ]
    
    def __str__(self):
        tipo = "Producto" if self.producto_servicio else "Servicio"
        return f"{self.codigo:06d} - {self.sku} - {self.descripcion} ({tipo})"
    
    @property
    def tipo_display(self):
        """Retorna el tipo como string"""
        return "Producto" if self.producto_servicio else "Servicio"
    
    @property
    def impuesto_display(self):
        """Retorna el impuesto como string legible"""
        impuesto_map = {
            'IVA_16': 'IVA Tasa 16%',
            'IVA_0': 'IVA Tasa cero',
            'IVA_EXENTO': 'IVA exento'
        }
        return impuesto_map.get(self.impuesto, self.impuesto)
    
    def clean(self):
        """Validaciones adicionales del modelo"""
        super().clean()
        
        # Validar SKU único
        if self.sku:
            self.sku = self.sku.upper().strip()
    
    def save(self, *args, **kwargs):
        """Guardar con validaciones"""
        self.full_clean()
        super().save(*args, **kwargs)


class ConfiguracionSistema(models.Model):
    """Configuración del sistema"""
    
    # Datos del ciclo de producción
    ciclo_actual = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Ciclo actual",
        help_text="Nombre del ciclo de producción actual"
    )
    
    # Datos de la empresa
    razon_social = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Razón Social",
        help_text="Razón social de la empresa"
    )
    
    rfc = models.CharField(
        max_length=13,
        blank=True,
        validators=[validar_rfc],
        verbose_name="RFC",
        help_text="Registro Federal de Contribuyentes de la empresa"
    )
    
    direccion = models.TextField(
        blank=True,
        verbose_name="Dirección",
        help_text="Dirección de la empresa"
    )
    
    telefono = models.CharField(
        max_length=15,
        blank=True,
        validators=[RegexValidator(
            regex=r'^[\d\s\-\+\(\)]+$',
            message='El teléfono solo puede contener números, espacios, guiones, paréntesis y el signo más'
        )],
        verbose_name="Teléfono",
        help_text="Número de teléfono de la empresa"
    )
    
    logo_empresa = models.ImageField(
        upload_to='logos_empresa/',
        blank=True,
        null=True,
        verbose_name="Logo de la Empresa",
        help_text="Logotipo de la empresa"
    )
    
    # Configuración de timbrado
    PAC_CHOICES = [
        ('PRODIGIA', 'Prodigia'),
    ]
    
    nombre_pac = models.CharField(
        max_length=50,
        choices=PAC_CHOICES,
        default='PRODIGIA',
        verbose_name="Nombre de PAC",
        help_text="Proveedor Autorizado de Certificación"
    )
    
    contrato = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Contrato",
        help_text="Número de contrato con el PAC"
    )
    
    usuario_pac = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Usuario",
        help_text="Usuario para el PAC"
    )
    
    password_pac = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Contraseña",
        help_text="Contraseña para el PAC"
    )
    
    # Certificados
    certificado = models.TextField(
        blank=True,
        null=True,
        verbose_name="Certificado",
        help_text="Certificado en formato base64"
    )
    
    certificado_nombre = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Nombre del certificado",
        help_text="Nombre original del archivo de certificado"
    )
    
    llave = models.TextField(
        blank=True,
        null=True,
        verbose_name="Llave",
        help_text="Llave privada en formato base64"
    )
    
    llave_nombre = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Nombre de la llave",
        help_text="Nombre original del archivo de llave"
    )
    
    password_llave = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Contraseña de la llave",
        help_text="Contraseña para la llave privada"
    )
    
    # Campos de auditoría
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    fecha_modificacion = models.DateTimeField(auto_now=True, verbose_name="Fecha de modificación")
    usuario_creacion = models.ForeignKey(
        Usuario, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='configuraciones_creadas',
        verbose_name="Usuario de creación"
    )
    usuario_modificacion = models.ForeignKey(
        Usuario, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='configuraciones_modificadas',
        verbose_name="Usuario de modificación"
    )
    
    # Control de catálogos SAT
    ultima_actualizacion_catalogos = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Última actualización de catálogos",
        help_text="Fecha y hora de la última actualización de catálogos SAT"
    )
    
    class Meta:
        verbose_name = "Configuración del Sistema"
        verbose_name_plural = "Configuraciones del Sistema"
        db_table = 'configuracion_sistema'
    
    def __str__(self):
        return f"Configuración - {self.ciclo_actual}"
    
    def save(self, *args, **kwargs):
        """Guardar configuración del sistema"""
        # No hacer validaciones estrictas para permitir guardado parcial
        super().save(*args, **kwargs)


class Cultivo(models.Model):
    """Modelo para cultivos"""
    codigo = models.AutoField(primary_key=True, verbose_name="Código")
    nombre = models.CharField(
        max_length=100,
        verbose_name="Nombre del cultivo",
        help_text="Nombre del cultivo"
    )
    variedad = models.CharField(
        max_length=100,
        verbose_name="Variedad",
        help_text="Variedad del cultivo"
    )
    observaciones = models.TextField(
        blank=True,
        verbose_name="Observaciones",
        help_text="Observaciones adicionales"
    )
    activo = models.BooleanField(
        default=True,
        verbose_name="Activo",
        help_text="Indica si el cultivo está activo"
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    fecha_modificacion = models.DateTimeField(auto_now=True, verbose_name="Fecha de modificación")
    usuario_creacion = models.ForeignKey(
        Usuario, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='cultivos_creados',
        verbose_name="Usuario de creación"
    )
    usuario_modificacion = models.ForeignKey(
        Usuario, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='cultivos_modificados',
        verbose_name="Usuario de modificación"
    )
    
    class Meta:
        verbose_name = "Cultivo"
        verbose_name_plural = "Cultivos"
        db_table = 'cultivos'
        ordering = ['nombre', 'variedad']
    
    def __str__(self):
        return f"{self.nombre} - {self.variedad}"
    
    def clean(self):
        """Validaciones adicionales del modelo"""
        super().clean()
        
        # Validar que el nombre no esté vacío
        if self.nombre:
            self.nombre = self.nombre.strip()
        
        # Validar que la variedad no esté vacía
        if self.variedad:
            self.variedad = self.variedad.strip()
    
    def save(self, *args, **kwargs):
        """Guardar con validaciones"""
        self.full_clean()
        super().save(*args, **kwargs)


class Remision(models.Model):
    """Modelo para gestión de remisiones (master)"""
    
    # Campo auto numérico (se maneja automáticamente con el ID)
    codigo = models.AutoField(
        primary_key=True, 
        verbose_name="Código"
    )
    
    ciclo = models.CharField(
        max_length=100,
        verbose_name="Ciclo",
        help_text="Ciclo de producción actual"
    )
    
    folio = models.PositiveIntegerField(
        verbose_name="Folio",
        help_text="Número de folio de la remisión"
    )
    
    fecha = models.DateField(
        verbose_name="Fecha",
        help_text="Fecha de la remisión"
    )
    
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.PROTECT,
        verbose_name="Cliente",
        help_text="Cliente de la remisión"
    )
    
    lote_origen = models.ForeignKey(
        LoteOrigen,
        on_delete=models.PROTECT,
        verbose_name="Lote - Origen",
        help_text="Lote de origen de la remisión"
    )
    
    transportista = models.ForeignKey(
        Transportista,
        on_delete=models.PROTECT,
        verbose_name="Transportista",
        help_text="Transportista de la remisión"
    )
    
    costo_flete = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name="Costo de Flete",
        help_text="Costo del flete de transporte"
    )
    
    peso_bruto_embarque = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        verbose_name="Peso Bruto de Embarque",
        help_text="Peso total bruto de la remisión en kilogramos"
    )
    
    merma_arps_global = models.PositiveIntegerField(
        default=0,
        verbose_name="Merma/Arps Global",
        help_text="Número total de arps con merma en la remisión"
    )
    
    # Campos para liquidación
    peso_bruto_liquidado = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        verbose_name="Peso Bruto Liquidado",
        help_text="Peso bruto liquidado en kilogramos"
    )
    
    merma_arps_liquidados = models.PositiveIntegerField(
        default=0,
        verbose_name="Merma/Arps Liquidados",
        help_text="Número de arps con merma liquidados"
    )
    
    observaciones = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observaciones",
        help_text="Observaciones adicionales sobre la remisión"
    )
    
    # Campos de estado de pago
    pagado = models.BooleanField(
        default=False,
        verbose_name="Pagado",
        help_text="Indica si la remisión ha sido pagada"
    )
    
    fecha_pago = models.DateField(
        blank=True,
        null=True,
        verbose_name="Fecha de Pago",
        help_text="Fecha en que se realizó el pago"
    )
    
    # Campos de auditoría
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    fecha_modificacion = models.DateTimeField(auto_now=True, verbose_name="Fecha de modificación")
    usuario_creacion = models.ForeignKey(
        Usuario, 
        on_delete=models.PROTECT,
        related_name='remisiones_creadas',
        verbose_name="Usuario que creó el registro"
    )
    usuario_modificacion = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name='remisiones_modificadas',
        verbose_name="Usuario que modificó el registro",
        blank=True,
        null=True
    )
    
    # Campos de cancelación
    cancelada = models.BooleanField(
        default=False,
        verbose_name="Remisión cancelada"
    )
    
    motivo_cancelacion = models.TextField(
        blank=True,
        null=True,
        verbose_name="Motivo de cancelación"
    )
    
    folio_sustituto = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Folio que sustituye"
    )
    
    usuario_cancelacion = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name='remisiones_canceladas',
        blank=True,
        null=True,
        verbose_name="Usuario que canceló la remisión"
    )
    
    fecha_cancelacion = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Fecha de cancelación"
    )
    
    # Campos de cobranza
    facturado = models.BooleanField(
        default=False,
        verbose_name="Facturado",
        help_text="Indica si la remisión ha sido facturada"
    )
    
    pagado = models.BooleanField(
        default=False,
        verbose_name="Pagado",
        help_text="Indica si la remisión ha sido pagada"
    )
    
    class Meta:
        verbose_name = "Remisión"
        verbose_name_plural = "Remisiones"
        db_table = 'remisiones'
        ordering = ['-fecha_creacion']
        unique_together = ['ciclo', 'folio']
        indexes = [
            models.Index(fields=['ciclo', 'folio']),
            models.Index(fields=['fecha']),
            models.Index(fields=['cliente']),
            models.Index(fields=['lote_origen']),
            models.Index(fields=['transportista']),
        ]
    
    def esta_liquidada(self):
        """Determinar si una remisión está liquidada basándose en los campos de liquidación"""
        detalles = self.detalles.all()
        if not detalles.exists():
            return False
        
        # Una remisión está liquidada si al menos un detalle tiene valores de liquidación
        # Y tiene información de auditoría (usuario_liquidacion y fecha_liquidacion)
        for detalle in detalles:
            if ((detalle.kgs_liquidados > 0 or 
                 detalle.kgs_merma > 0 or 
                 detalle.precio > 0 or 
                 detalle.importe_liquidado > 0) and
                detalle.usuario_liquidacion is not None and
                detalle.fecha_liquidacion is not None):
                return True
        return False
    
    @property
    def saldo_pendiente(self):
        """Calcular el saldo pendiente de la remisión (importe liquidado - pagos realizados)"""
        from django.db import models
        
        # Calcular el importe total liquidado de la remisión
        importe_total = self.detalles.aggregate(
            total=models.Sum('importe_liquidado')
        )['total'] or 0
        
        # Calcular el total de pagos realizados
        total_pagos = self.pagos.filter(activo=True).aggregate(
            total=models.Sum('monto')
        )['total'] or 0
        
        # El saldo pendiente es la diferencia
        return importe_total - total_pagos
    
    def __str__(self):
        return f"{self.ciclo} - {self.folio:06d}"
    
    def clean(self):
        """Validaciones adicionales del modelo"""
        super().clean()
        
        # Validar que el folio sea positivo
        if self.folio is not None and self.folio <= 0:
            raise ValidationError({
                'folio': 'El folio debe ser un número positivo.'
            })
        
        # Validar que el costo de flete no sea negativo
        if self.costo_flete is not None and self.costo_flete < 0:
            raise ValidationError({
                'costo_flete': 'El costo de flete no puede ser negativo.'
            })
    
    def save(self, *args, **kwargs):
        """Guardar con validaciones"""
        self.full_clean()
        super().save(*args, **kwargs)


class RemisionDetalle(models.Model):
    """Modelo para gestión de detalles de remisiones (detail)"""
    
    # Campo auto numérico (se maneja automáticamente con el ID)
    codigo = models.AutoField(
        primary_key=True, 
        verbose_name="Código"
    )
    
    remision = models.ForeignKey(
        Remision,
        on_delete=models.CASCADE,
        related_name='detalles',
        verbose_name="Remisión",
        help_text="Remisión a la que pertenece este detalle"
    )
    
    cultivo = models.ForeignKey(
        Cultivo,
        on_delete=models.PROTECT,
        verbose_name="Cultivo",
        help_text="Cultivo del detalle"
    )
    
    CALIDAD_CHOICES = [
        ('1ras/2das', '1ras/2das'),
        ('3as', '3as'),
        ('4as', '4as'),
        ('Mixtas', 'Mixtas'),
    ]
    
    calidad = models.CharField(
        max_length=20,
        choices=CALIDAD_CHOICES,
        verbose_name="Calidad",
        help_text="Calidad del producto"
    )
    
    no_arps = models.PositiveIntegerField(
        verbose_name="No Arps",
        help_text="Número de arps"
    )
    
    kgs_enviados = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name="Kgs Enviados",
        help_text="Kilogramos enviados"
    )
    
    merma_arps = models.PositiveIntegerField(
        verbose_name="Merma/Arps",
        help_text="Merma por arps"
    )
    
    peso_promedio = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        verbose_name="Peso Promedio",
        help_text="Peso promedio calculado automáticamente"
    )
    
    # Campos para liquidación (valores por defecto en cero)
    no_arps_liquidados = models.PositiveIntegerField(
        default=0,
        verbose_name="No Arps Liquidados",
        help_text="Número de arps liquidados"
    )
    
    kgs_merma_liquidados = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        verbose_name="Kgs Merma Liquidados",
        help_text="Kilogramos de merma liquidados"
    )
    
    peso_promedio_liquidado = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        verbose_name="Peso Promedio Liquidado",
        help_text="Peso promedio liquidado calculado automáticamente"
    )
    
    kgs_liquidados = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        verbose_name="Kgs Liquidados",
        help_text="Kilogramos liquidados"
    )
    
    kgs_merma = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        verbose_name="Kgs Merma",
        help_text="Kilogramos de merma"
    )
    
    precio = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        verbose_name="Precio",
        help_text="Precio por kilogramo"
    )
    
    importe_liquidado = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        default=0.00,
        verbose_name="Importe Liquidado",
        help_text="Importe total liquidado"
    )
    
    # Campos de diferencias (calculados automáticamente)
    dif_peso_promedio = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        verbose_name="Dif Peso Promedio",
        help_text="Diferencia entre Peso Promedio y Peso Promedio Liquidado"
    )
    
    dif_no_arps = models.IntegerField(
        default=0,
        verbose_name="Dif No Arps",
        help_text="Diferencia entre No Arps y No Arps Liquidados"
    )
    
    dif_kgs_merma = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        verbose_name="Dif Kgs Merma",
        help_text="Diferencia entre Kgs Merma y Kgs Merma Liquidados"
    )
    
    dif_kgs_liquidados = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        verbose_name="Dif Kgs Liquidados",
        help_text="Diferencia entre Kgs Enviados y Kgs Liquidados"
    )
    
    dif_precio = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        verbose_name="Dif Precio",
        help_text="Diferencia entre Precio Envío y Precio por Kg"
    )
    
    dif_importes = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        default=0.00,
        verbose_name="Dif Importes",
        help_text="Diferencia entre Importe Neto Envío e Importe Liquidado"
    )
    
    # Campos para envío
    precio_envio = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        verbose_name="Precio Envío",
        help_text="Precio por kilogramo para envío"
    )
    
    importe_envio = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        default=0.00,
        verbose_name="Importe Envío",
        help_text="Importe total de envío (Precio Envío × Kgs Enviados)"
    )
    
    kgs_neto_envio = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        verbose_name="Kgs Neto Envío",
        help_text="Kilogramos netos de envío (Kgs Enviados - Kgs Merma)"
    )
    
    importe_neto_envio = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        default=0.00,
        verbose_name="Importe Neto Envío",
        help_text="Importe neto de envío (Precio Envío × Kgs Neto Envío)"
    )
    
    # Campos de auditoría
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    fecha_modificacion = models.DateTimeField(auto_now=True, verbose_name="Fecha de modificación")
    usuario_creacion = models.ForeignKey(
        Usuario, 
        on_delete=models.PROTECT,
        related_name='remisiones_detalles_creados',
        verbose_name="Usuario que creó el registro"
    )
    usuario_modificacion = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name='remisiones_detalles_modificados',
        verbose_name="Usuario que modificó el registro",
        blank=True,
        null=True
    )
    
    # Campos de auditoría para liquidación
    usuario_liquidacion = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name='remisiones_detalles_liquidadas',
        blank=True,
        null=True,
        verbose_name="Usuario que liquidó el detalle"
    )
    
    fecha_liquidacion = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Fecha de liquidación"
    )
    
    class Meta:
        verbose_name = "Detalle de Remisión"
        verbose_name_plural = "Detalles de Remisiones"
        db_table = 'remisiones_detalles'
        ordering = ['codigo']
        indexes = [
            models.Index(fields=['remision']),
            models.Index(fields=['cultivo']),
            models.Index(fields=['calidad']),
        ]
    
    def __str__(self):
        return f"{self.remision} - {self.cultivo} ({self.calidad})"
    
    def clean(self):
        """Validaciones adicionales del modelo"""
        super().clean()
        
        # Validar que no_arps sea positivo
        if self.no_arps is not None and self.no_arps <= 0:
            raise ValidationError({
                'no_arps': 'El número de arps debe ser positivo.'
            })
        
        # Validar que kgs_enviados sea positivo
        if self.kgs_enviados is not None and self.kgs_enviados <= 0:
            raise ValidationError({
                'kgs_enviados': 'Los kilogramos enviados deben ser positivos.'
            })
        
        # Validar que merma_arps sea positivo
        if self.merma_arps is not None and self.merma_arps < 0:
            raise ValidationError({
                'merma_arps': 'La merma por arps no puede ser negativa.'
            })
        
        # Validar que los campos de liquidación no sean negativos
        if self.kgs_liquidados is not None and self.kgs_liquidados < 0:
            raise ValidationError({
                'kgs_liquidados': 'Los kilogramos liquidados no pueden ser negativos.'
            })
        
        if self.kgs_merma is not None and self.kgs_merma < 0:
            raise ValidationError({
                'kgs_merma': 'Los kilogramos de merma no pueden ser negativos.'
            })
        
        if self.precio is not None and self.precio < 0:
            raise ValidationError({
                'precio': 'El precio no puede ser negativo.'
            })
        
        if self.importe_liquidado is not None and self.importe_liquidado < 0:
            raise ValidationError({
                'importe_liquidado': 'El importe liquidado no puede ser negativo.'
            })
        
        # Validar campos de envío
        if self.precio_envio is not None and self.precio_envio < 0:
            raise ValidationError({
                'precio_envio': 'El precio de envío no puede ser negativo.'
            })
        
        if self.importe_envio is not None and self.importe_envio < 0:
            raise ValidationError({
                'importe_envio': 'El importe de envío no puede ser negativo.'
            })
        
        if self.kgs_neto_envio is not None and self.kgs_neto_envio < 0:
            raise ValidationError({
                'kgs_neto_envio': 'Los kilogramos netos de envío no pueden ser negativos.'
            })
        
        if self.importe_neto_envio is not None and self.importe_neto_envio < 0:
            raise ValidationError({
                'importe_neto_envio': 'El importe neto de envío no puede ser negativo.'
            })
    
    def save(self, *args, **kwargs):
        """Guardar con validaciones y cálculos automáticos"""
        # Calcular peso promedio automáticamente
        if self.no_arps and self.no_arps > 0 and self.kgs_enviados:
            self.peso_promedio = round(self.kgs_enviados / self.no_arps, 2)
        else:
            self.peso_promedio = 0.00
        
        # Los demás cálculos se realizan en el frontend y se envían ya calculados
        # No recalcular aquí para mantener consistencia con los valores del frontend
        
        # Validar solo si no estamos en el proceso de creación inicial
        if self.pk is not None:
            self.full_clean()
        super().save(*args, **kwargs)


class CuentaBancaria(models.Model):
    """Modelo para gestión de cuentas bancarias"""
    
    # Campo auto numérico (se maneja automáticamente con el ID)
    codigo = models.AutoField(
        primary_key=True, 
        verbose_name="Código"
    )
    
    nombre_banco = models.CharField(
        max_length=200, 
        verbose_name="Nombre del Banco",
        help_text="Nombre completo del banco"
    )
    
    numero_cuenta = models.CharField(
        max_length=50,
        verbose_name="Número de Cuenta",
        help_text="Número de cuenta bancaria"
    )
    
    nombre_corto = models.CharField(
        max_length=100,
        verbose_name="Nombre Corto",
        help_text="Nombre corto para identificar la cuenta (ej: BBVA Principal)"
    )
    
    activo = models.BooleanField(
        default=True,
        verbose_name="Activo",
        help_text="Indica si la cuenta bancaria está activa en el sistema"
    )
    
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    fecha_modificacion = models.DateTimeField(auto_now=True, verbose_name="Fecha de modificación")
    usuario_creacion = models.ForeignKey(
        Usuario, 
        on_delete=models.PROTECT,
        related_name='cuentas_bancarias_creadas',
        verbose_name="Usuario que creó el registro"
    )
    usuario_modificacion = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name='cuentas_bancarias_modificadas',
        verbose_name="Usuario que modificó el registro",
        blank=True,
        null=True
    )
    
    class Meta:
        verbose_name = "Cuenta Bancaria"
        verbose_name_plural = "Cuentas Bancarias"
        db_table = 'cuentas_bancarias'
        ordering = ['nombre_corto']
        indexes = [
            models.Index(fields=['nombre_banco']),
            models.Index(fields=['numero_cuenta']),
            models.Index(fields=['nombre_corto']),
            models.Index(fields=['activo']),
        ]
    
    def __str__(self):
        return f"{self.nombre_corto} - {self.nombre_banco}"
    
    def clean(self):
        """Validaciones adicionales del modelo"""
        super().clean()
        
        # Validar que el nombre del banco no esté vacío
        if self.nombre_banco:
            self.nombre_banco = self.nombre_banco.strip()
        
        # Validar que el número de cuenta no esté vacío
        if self.numero_cuenta:
            self.numero_cuenta = self.numero_cuenta.strip()
        
        # Validar que el nombre corto no esté vacío
        if self.nombre_corto:
            self.nombre_corto = self.nombre_corto.strip()
    
    def save(self, *args, **kwargs):
        """Guardar con validaciones"""
        self.full_clean()
        super().save(*args, **kwargs)


class PagoRemision(models.Model):
    """Modelo para registrar pagos de remisiones"""
    codigo = models.AutoField(primary_key=True, verbose_name="Código")
    remision = models.ForeignKey(Remision, on_delete=models.CASCADE, related_name='pagos', verbose_name="Remisión")
    cuenta_bancaria = models.ForeignKey(CuentaBancaria, on_delete=models.CASCADE, verbose_name="Cuenta Bancaria", blank=True, null=True)
    metodo_pago = models.CharField(
        max_length=20,
        choices=[
            ('efectivo', 'Efectivo'),
            ('transferencia', 'Transferencia'),
            ('cheque', 'Cheque'),
        ],
        verbose_name="Método de Pago"
    )
    monto = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Monto")
    fecha_pago = models.DateField(verbose_name="Fecha de Pago")
    referencia = models.CharField(max_length=100, blank=True, null=True, verbose_name="Referencia/Comprobante")
    observaciones = models.TextField(blank=True, null=True, verbose_name="Observaciones")
    activo = models.BooleanField(default=True, verbose_name="Activo")
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    usuario_creacion = models.ForeignKey('Usuario', on_delete=models.SET_NULL, null=True, blank=True, related_name='pagos_creados', verbose_name="Usuario de Creación")
    fecha_modificacion = models.DateTimeField(auto_now=True, verbose_name="Fecha de Última Modificación")
    usuario_modificacion = models.ForeignKey('Usuario', on_delete=models.SET_NULL, null=True, blank=True, related_name='pagos_modificados', verbose_name="Usuario de Última Modificación")

    class Meta:
        verbose_name = "Pago de Remisión"
        verbose_name_plural = "Pagos de Remisiones"
        ordering = ['-fecha_pago', '-fecha_creacion']

    def __str__(self):
        return f"Pago {self.codigo} - {self.remision.ciclo} - {self.remision.folio:06d} - ${self.monto}"


class Presupuesto(models.Model):
    """Modelo maestro para gestión de presupuestos de gastos por centro de costos y ciclo"""
    
    codigo = models.AutoField(primary_key=True, verbose_name="Código")
    centro_costo = models.ForeignKey(
        CentroCosto,
        on_delete=models.PROTECT,
        verbose_name="Centro de Costo",
        help_text="Centro de costo al que pertenece el presupuesto"
    )
    ciclo = models.CharField(
        max_length=100,
        verbose_name="Ciclo",
        help_text="Ciclo de producción para el cual se define el presupuesto"
    )
    observaciones = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observaciones",
        help_text="Observaciones adicionales sobre el presupuesto"
    )
    activo = models.BooleanField(
        default=True,
        verbose_name="Activo",
        help_text="Indica si el presupuesto está activo en el sistema"
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    usuario_creacion = models.ForeignKey(
        'Usuario',
        on_delete=models.PROTECT,
        related_name='presupuestos_creados',
        verbose_name="Usuario de Creación"
    )
    fecha_modificacion = models.DateTimeField(auto_now=True, verbose_name="Fecha de Última Modificación")
    usuario_modificacion = models.ForeignKey(
        'Usuario',
        on_delete=models.PROTECT,
        related_name='presupuestos_modificados',
        verbose_name="Usuario de Última Modificación",
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = "Presupuesto"
        verbose_name_plural = "Presupuestos"
        db_table = 'presupuestos'
        ordering = ['-fecha_creacion']
        unique_together = ['centro_costo', 'ciclo']
        indexes = [
            models.Index(fields=['centro_costo', 'ciclo']),
            models.Index(fields=['ciclo']),
            models.Index(fields=['activo']),
        ]

    def __str__(self):
        return f"{self.centro_costo.descripcion} - {self.ciclo}"

    @property
    def total_presupuestado(self):
        """Calcula el total presupuestado sumando todos los detalles"""
        return self.detalles.aggregate(total=models.Sum('importe'))['total'] or 0

    def clean(self):
        """Validaciones adicionales del modelo"""
        super().clean()

    def save(self, *args, **kwargs):
        """Guardar con validaciones"""
        self.full_clean()
        super().save(*args, **kwargs)


class PresupuestoDetalle(models.Model):
    """Modelo detalle para las clasificaciones de gastos del presupuesto"""
    
    codigo = models.AutoField(primary_key=True, verbose_name="Código")
    presupuesto = models.ForeignKey(
        Presupuesto,
        on_delete=models.CASCADE,
        related_name='detalles',
        verbose_name="Presupuesto",
        help_text="Presupuesto al que pertenece este detalle"
    )
    clasificacion_gasto = models.ForeignKey(
        ClasificacionGasto,
        on_delete=models.PROTECT,
        verbose_name="Clasificación de Gasto",
        help_text="Clasificación de gasto presupuestada"
    )
    importe = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Importe",
        help_text="Importe presupuestado para esta clasificación de gasto"
    )
    activo = models.BooleanField(
        default=True,
        verbose_name="Activo",
        help_text="Indica si el detalle está activo en el sistema"
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    usuario_creacion = models.ForeignKey(
        'Usuario',
        on_delete=models.PROTECT,
        related_name='presupuesto_detalles_creados',
        verbose_name="Usuario de Creación"
    )
    fecha_modificacion = models.DateTimeField(auto_now=True, verbose_name="Fecha de Última Modificación")
    usuario_modificacion = models.ForeignKey(
        'Usuario',
        on_delete=models.PROTECT,
        related_name='presupuesto_detalles_modificados',
        verbose_name="Usuario de Última Modificación",
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = "Detalle de Presupuesto"
        verbose_name_plural = "Detalles de Presupuesto"
        db_table = 'presupuesto_detalles'
        ordering = ['fecha_creacion']
        unique_together = ['presupuesto', 'clasificacion_gasto']
        indexes = [
            models.Index(fields=['presupuesto']),
            models.Index(fields=['clasificacion_gasto']),
            models.Index(fields=['activo']),
        ]

    def __str__(self):
        return f"{self.presupuesto} - {self.clasificacion_gasto.descripcion} - ${self.importe}"

    def clean(self):
        """Validaciones adicionales del modelo"""
        super().clean()
        
        # Validar importe
        if self.importe is not None and self.importe < 0:
            raise ValidationError({
                'importe': 'El importe no puede ser negativo.'
            })

    def save(self, *args, **kwargs):
        """Guardar con validaciones"""
        self.full_clean()
        super().save(*args, **kwargs)


# Mantener el modelo anterior para compatibilidad (se puede eliminar después)
class PresupuestoGasto(models.Model):
    """Modelo para gestión de presupuestos de gastos por centro de costos y ciclo (DEPRECATED)"""
    
    codigo = models.AutoField(primary_key=True, verbose_name="Código")
    centro_costo = models.ForeignKey(
        CentroCosto,
        on_delete=models.PROTECT,
        verbose_name="Centro de Costo",
        help_text="Centro de costo al que pertenece el presupuesto"
    )
    clasificacion_gasto = models.ForeignKey(
        ClasificacionGasto,
        on_delete=models.PROTECT,
        verbose_name="Clasificación de Gasto",
        help_text="Clasificación de gasto presupuestada"
    )
    ciclo = models.CharField(
        max_length=100,
        verbose_name="Ciclo",
        help_text="Ciclo de producción para el cual se define el presupuesto"
    )
    importe = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Importe",
        help_text="Importe presupuestado para esta clasificación de gasto"
    )
    observaciones = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observaciones",
        help_text="Observaciones adicionales sobre el presupuesto"
    )
    activo = models.BooleanField(
        default=True,
        verbose_name="Activo",
        help_text="Indica si el presupuesto está activo en el sistema"
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    usuario_creacion = models.ForeignKey(
        'Usuario',
        on_delete=models.PROTECT,
        related_name='presupuestos_gasto_creados',
        verbose_name="Usuario de Creación"
    )
    fecha_modificacion = models.DateTimeField(auto_now=True, verbose_name="Fecha de Última Modificación")
    usuario_modificacion = models.ForeignKey(
        'Usuario',
        on_delete=models.PROTECT,
        related_name='presupuestos_gasto_modificados',
        verbose_name="Usuario de Última Modificación",
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = "Presupuesto de Gasto (DEPRECATED)"
        verbose_name_plural = "Presupuestos de Gastos (DEPRECATED)"
        db_table = 'presupuestos_gasto'
        ordering = ['-fecha_creacion']
        unique_together = ['centro_costo', 'clasificacion_gasto', 'ciclo']
        indexes = [
            models.Index(fields=['centro_costo', 'ciclo']),
            models.Index(fields=['ciclo']),
            models.Index(fields=['activo']),
        ]

    def __str__(self):
        return f"{self.centro_costo.descripcion} - {self.clasificacion_gasto.descripcion} - {self.ciclo} - ${self.importe}"

    def clean(self):
        """Validaciones adicionales del modelo"""
        super().clean()
        
        # Validar importe
        if self.importe is not None and self.importe < 0:
            raise ValidationError({
                'importe': 'El importe no puede ser negativo.'
            })

    def save(self, *args, **kwargs):
        """Guardar con validaciones"""
        self.full_clean()
        super().save(*args, **kwargs)

class Gasto(models.Model):
    """Modelo para capturar gastos basados en presupuestos"""
    
    codigo = models.AutoField(primary_key=True, verbose_name="Código")
    presupuesto = models.ForeignKey(
        Presupuesto,
        on_delete=models.PROTECT,
        related_name='gastos',
        verbose_name="Presupuesto",
        help_text="Presupuesto al que pertenece este gasto"
    )
    ciclo = models.CharField(
        max_length=10,
        verbose_name="Ciclo",
        help_text="Ciclo al que pertenece el gasto"
    )
    fecha_gasto = models.DateField(
        verbose_name="Fecha del Gasto",
        help_text="Fecha en que se realizó el gasto"
    )
    observaciones = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observaciones",
        help_text="Observaciones adicionales del gasto"
    )
    activo = models.BooleanField(
        default=True,
        verbose_name="Activo",
        help_text="Indica si el gasto está activo en el sistema"
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    usuario_creacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='gastos_creados',
        verbose_name="Usuario de Creación"
    )
    fecha_modificacion = models.DateTimeField(auto_now=True, verbose_name="Fecha de Modificación")
    usuario_modificacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='gastos_modificados',
        verbose_name="Usuario de Última Modificación",
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = "Gasto"
        verbose_name_plural = "Gastos"
        db_table = 'gastos'
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['presupuesto', 'ciclo']),
            models.Index(fields=['fecha_gasto']),
            models.Index(fields=['activo']),
        ]

    def __str__(self):
        return f"Gasto {self.codigo} - {self.presupuesto.centro_costo.descripcion} - {self.fecha_gasto}"

    @property
    def total_gastado(self):
        """Calcula el total gastado en este gasto"""
        return self.detalles.filter(activo=True).aggregate(
            total=models.Sum('importe')
        )['total'] or 0

    def clean(self):
        """Validaciones adicionales del modelo"""
        super().clean()
        
        # Validar que la fecha del gasto no sea futura
        if self.fecha_gasto and self.fecha_gasto > timezone.now().date():
            raise ValidationError({
                'fecha_gasto': 'La fecha del gasto no puede ser futura.'
            })

    def save(self, *args, **kwargs):
        """Guardar con validaciones"""
        self.full_clean()
        super().save(*args, **kwargs)


class GastoDetalle(models.Model):
    """Modelo detalle para los gastos capturados"""
    
    codigo = models.AutoField(primary_key=True, verbose_name="Código")
    gasto = models.ForeignKey(
        Gasto,
        on_delete=models.CASCADE,
        related_name='detalles',
        verbose_name="Gasto",
        help_text="Gasto al que pertenece este detalle"
    )
    proveedor = models.ForeignKey(
        Proveedor,
        on_delete=models.PROTECT,
        verbose_name="Proveedor",
        help_text="Proveedor que emitió la factura",
        blank=True,
        null=True
    )
    factura = models.CharField(
        max_length=100,
        verbose_name="Factura",
        help_text="Número de factura del proveedor"
    )
    clasificacion_gasto = models.ForeignKey(
        ClasificacionGasto,
        on_delete=models.PROTECT,
        verbose_name="Clasificación de Gasto",
        help_text="Clasificación de gasto según el presupuesto"
    )
    concepto = models.CharField(
        max_length=255,
        verbose_name="Concepto",
        help_text="Concepto o descripción del gasto"
    )
    forma_pago = models.CharField(
        max_length=2,
        choices=[
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
        ],
        verbose_name="Forma de Pago",
        help_text="Forma de pago según catálogo SAT",
        blank=True,
        null=True
    )
    autorizo = models.ForeignKey(
        'AutorizoGasto',
        on_delete=models.PROTECT,
        verbose_name="Autorizó",
        help_text="Persona que autorizó el gasto",
        blank=True,
        null=True
    )
    importe = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Importe",
        help_text="Importe del gasto"
    )
    activo = models.BooleanField(
        default=True,
        verbose_name="Activo",
        help_text="Indica si el detalle está activo en el sistema"
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    usuario_creacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='gasto_detalles_creados',
        verbose_name="Usuario de Creación"
    )
    fecha_modificacion = models.DateTimeField(auto_now=True, verbose_name="Fecha de Modificación")
    usuario_modificacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='gasto_detalles_modificados',
        verbose_name="Usuario de Última Modificación",
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = "Detalle de Gasto"
        verbose_name_plural = "Detalles de Gastos"
        db_table = 'gasto_detalles'
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['gasto']),
            models.Index(fields=['proveedor']),
            models.Index(fields=['factura']),
            models.Index(fields=['activo']),
        ]

    def __str__(self):
        return f"{self.gasto.codigo} - {self.proveedor.razon_social} - {self.factura} - ${self.importe}"

    def clean(self):
        """Validaciones adicionales del modelo"""
        super().clean()
        
        # Validar importe
        if self.importe is not None and self.importe <= 0:
            raise ValidationError({
                'importe': 'El importe debe ser mayor a cero.'
            })
        
        # Validar que la clasificación de gasto esté en el presupuesto
        if self.gasto and self.clasificacion_gasto:
            if not self.gasto.presupuesto.detalles.filter(
                clasificacion_gasto=self.clasificacion_gasto,
                activo=True
            ).exists():
                raise ValidationError({
                    'clasificacion_gasto': 'Esta clasificación de gasto no está incluida en el presupuesto seleccionado.'
                })

    def save(self, *args, **kwargs):
        """Guardar con validaciones"""
        self.full_clean()
        super().save(*args, **kwargs)


class Emisor(models.Model):
    """Modelo para gestión de emisores con sus certificados"""
    
    codigo = models.AutoField(primary_key=True, verbose_name="Código")
    razon_social = models.CharField(
        max_length=200,
        verbose_name="Razón Social",
        help_text="Razón social del emisor"
    )
    rfc = models.CharField(
        max_length=13,
        validators=[validar_rfc],
        verbose_name="RFC",
        help_text="Registro Federal de Contribuyentes del emisor"
    )
    codigo_postal = models.CharField(
        max_length=5,
        validators=[RegexValidator(
            regex=r'^\d{5}$',
            message='El código postal debe tener exactamente 5 dígitos'
        )],
        verbose_name="Código Postal",
        help_text="Código postal de 5 dígitos"
    )
    
    # Régimen Fiscal
    REGIMEN_FISCAL_CHOICES = [
        ('601', '601 - General de Ley Personas Morales'),
        ('603', '603 - Personas Morales con Fines no Lucrativos'),
        ('605', '605 - Sueldos y Salarios e Ingresos Asimilados a Salarios'),
        ('606', '606 - Arrendamiento'),
        ('608', '608 - Demás ingresos'),
        ('610', '610 - Residentes en el Extranjero sin Establecimiento Permanente en México'),
        ('611', '611 - Ingresos por Dividendos (socios y accionistas)'),
        ('612', '612 - Personas Físicas con Actividades Empresariales y Profesionales'),
        ('614', '614 - Ingresos por intereses'),
        ('615', '615 - Régimen de los ingresos por obtención de premios'),
        ('616', '616 - Sin obligaciones fiscales'),
        ('620', '620 - Sociedades Cooperativas de Producción que optan por diferir sus ingresos'),
        ('621', '621 - Incorporación Fiscal'),
        ('622', '622 - Actividades Agrícolas, Ganaderas, Silvícolas y Pesqueras'),
        ('623', '623 - Opcional para Grupos de Sociedades'),
        ('624', '624 - Coordinados'),
        ('625', '625 - Régimen de las Actividades Empresariales con ingresos a través de Plataformas Tecnológicas'),
        ('626', '626 - Régimen Simplificado de Confianza'),
        ('628', '628 - Hidrocarburos'),
        ('629', '629 - De los Regímenes Fiscales Preferentes y de las Empresas Multinacionales'),
        ('630', '630 - Enajenación de acciones en bolsa de valores'),
        ('615', '615 - Régimen de los ingresos por obtención de premios'),
    ]
    
    regimen_fiscal = models.CharField(
        max_length=3,
        choices=REGIMEN_FISCAL_CHOICES,
        default='626',
        verbose_name="Régimen Fiscal",
        help_text="Régimen fiscal según el SAT"
    )
    
    serie = models.CharField(
        max_length=10,
        default='A',
        verbose_name="Serie",
        help_text="Serie para las facturas de este emisor"
    )
    
    # Archivos de certificado (almacenados en base64)
    archivo_certificado = models.TextField(
        blank=True,
        null=True,
        verbose_name="Archivo de Certificado (Base64)",
        help_text="Archivo .cer del certificado codificado en base64"
    )
    nombre_archivo_certificado = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Nombre del Archivo de Certificado",
        help_text="Nombre original del archivo .cer"
    )
    archivo_llave = models.TextField(
        blank=True,
        null=True,
        verbose_name="Archivo de Llave (Base64)",
        help_text="Archivo .key de la llave privada codificado en base64"
    )
    nombre_archivo_llave = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Nombre del Archivo de Llave",
        help_text="Nombre original del archivo .key"
    )
    password_llave = models.CharField(
        max_length=100,
        verbose_name="Contraseña de la Llave",
        help_text="Contraseña para la llave privada"
    )
    
    # Datos de timbrado
    PAC_CHOICES = [
        ('PRODIGIA', 'Prodigia'),
    ]
    
    nombre_pac = models.CharField(
        max_length=50,
        choices=PAC_CHOICES,
        default='PRODIGIA',
        verbose_name="Nombre de PAC",
        help_text="Proveedor Autorizado de Certificación"
    )
    
    contrato = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Contrato",
        help_text="Número de contrato con el PAC"
    )
    
    usuario_pac = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Usuario PAC",
        help_text="Usuario para el PAC"
    )
    
    password_pac = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Contraseña PAC",
        help_text="Contraseña para el PAC"
    )
    
    timbrado_prueba = models.BooleanField(
        default=True,
        verbose_name="Timbrado de Prueba",
        help_text="Indica si el timbrado será en modo prueba o producción"
    )
    
    activo = models.BooleanField(
        default=True,
        verbose_name="Activo",
        help_text="Indica si el emisor está activo en el sistema"
    )
    
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    fecha_modificacion = models.DateTimeField(auto_now=True, verbose_name="Fecha de Modificación")
    usuario_creacion = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name='emisores_creados',
        verbose_name="Usuario de Creación"
    )
    usuario_modificacion = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name='emisores_modificados',
        verbose_name="Usuario de Modificación",
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = "Emisor"
        verbose_name_plural = "Emisores"
        db_table = 'emisores'
        ordering = ['razon_social']
        indexes = [
            models.Index(fields=['rfc']),
            models.Index(fields=['razon_social']),
            models.Index(fields=['activo']),
        ]

    def __str__(self):
        return f"{self.razon_social} ({self.rfc})"

    def clean(self):
        """Validaciones adicionales del modelo"""
        super().clean()
        
        # Normalizar RFC
        if self.rfc:
            self.rfc = self.rfc.strip().upper()
        
        # Validar que la razón social no esté vacía
        if self.razon_social:
            self.razon_social = self.razon_social.strip()

    def save(self, *args, **kwargs):
        """Guardar con validaciones"""
        self.full_clean()
        super().save(*args, **kwargs)


# Importar modelos de factura
from .factura_models import Factura, FacturaDetalle


class PagoFactura(models.Model):
    """Modelo para gestionar pagos de facturas con método PPD (crédito)"""
    
    TIPO_PAGO_CHOICES = [
        ('PARCIAL', 'Pago Parcial'),
        ('COMPLETO', 'Pago Completo'),
        ('ABONO', 'Abono a Cuenta'),
    ]
    
    factura = models.ForeignKey(
        Factura,
        on_delete=models.CASCADE,
        related_name='pagos',
        verbose_name="Factura",
        help_text="Factura a la que corresponde el pago"
    )
    
    fecha_pago = models.DateTimeField(
        default=timezone.now,
        verbose_name="Fecha de Pago",
        help_text="Fecha y hora del pago"
    )
    
    monto_pago = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name="Monto del Pago",
        help_text="Monto pagado en esta transacción"
    )
    
    tipo_pago = models.CharField(
        max_length=10,
        choices=TIPO_PAGO_CHOICES,
        default='PARCIAL',
        verbose_name="Tipo de Pago",
        help_text="Tipo de pago realizado"
    )
    
    referencia_pago = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Referencia de Pago",
        help_text="Referencia bancaria, transferencia, etc."
    )
    
    observaciones = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observaciones",
        help_text="Observaciones adicionales del pago"
    )
    
    num_parcialidad = models.PositiveIntegerField(
        default=1,
        verbose_name="Número de Parcialidad",
        help_text="Número de parcialidad del pago"
    )
    
    forma_pago = models.CharField(
        max_length=2,
        default='03',
        verbose_name="Forma de Pago",
        help_text="Código de forma de pago según catálogo SAT"
    )
    
    usuario_registro = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        verbose_name="Usuario que Registró",
        help_text="Usuario que registró el pago"
    )
    
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de Creación"
    )
    
    fecha_modificacion = models.DateTimeField(
        auto_now=True,
        verbose_name="Fecha de Modificación"
    )
    
    # Campos para timbrado del complemento de pago
    uuid = models.CharField(
        max_length=36,
        blank=True,
        null=True,
        verbose_name="UUID",
        help_text="UUID del complemento de pago timbrado"
    )
    
    xml_timbrado = models.TextField(
        blank=True,
        null=True,
        verbose_name="XML Timbrado",
        help_text="XML del complemento de pago timbrado en Base64"
    )
    
    sello = models.TextField(
        blank=True,
        null=True,
        verbose_name="Sello CFD",
        help_text="Sello del complemento de pago"
    )
    
    sello_sat = models.TextField(
        blank=True,
        null=True,
        verbose_name="Sello SAT",
        help_text="Sello del timbre fiscal digital"
    )
    
    no_certificado_sat = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="No. Certificado SAT",
        help_text="Número de certificado del SAT"
    )
    
    fecha_timbrado = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Fecha Timbrado",
        help_text="Fecha de timbrado del complemento de pago"
    )
    
    codigo_qr = models.TextField(
        blank=True,
        null=True,
        verbose_name="Código QR",
        help_text="Código QR del complemento de pago en Base64"
    )
    
    cadena_original_sat = models.TextField(
        blank=True,
        null=True,
        verbose_name="Cadena Original complemento SAT",
        help_text="Cadena original del complemento SAT (SelloCFD del timbre fiscal)"
    )
    
    class Meta:
        verbose_name = "Pago de Factura"
        verbose_name_plural = "Pagos de Facturas"
        db_table = 'pagos_factura'
        ordering = ['-fecha_pago']
    
    def __str__(self):
        return f"Pago {self.monto_pago} - {self.factura.serie} {self.factura.folio} ({self.fecha_pago.strftime('%d/%m/%Y')})"
    
    def clean(self):
        """Validaciones del modelo"""
        super().clean()
        
        # Validar que la factura sea PPD
        if self.factura and self.factura.metodo_pago != 'PPD':
            raise ValidationError("Solo se pueden registrar pagos para facturas con método PPD (crédito)")
        
        # Validar monto positivo
        if self.monto_pago <= 0:
            raise ValidationError("El monto del pago debe ser mayor a cero")
        
        # Validar que el pago no exceda el saldo anterior real (antes de aplicar este pago)
        # Esto evita usar saldos impactados por la UI (que muestran saldo insoluto = 0 en pagos completos)
        if self.factura:
            # Calcular saldo antes de este pago sin depender de zonas horarias (suma de pagos existentes)
            # Considerar solo pagos timbrados para el saldo previo
            pagos_anteriores = self.factura.pagos.filter(uuid__isnull=False).aggregate(total=models.Sum('monto_pago'))['total'] or 0
            saldo_anterior = self.factura.total - pagos_anteriores
            if self.monto_pago > saldo_anterior:
                raise ValidationError(f"El monto del pago (${self.monto_pago}) no puede exceder el saldo pendiente (${saldo_anterior})")
    
    def save(self, *args, **kwargs):
        """Guardar con validaciones"""
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def saldo_anterior(self):
        """Obtiene el saldo antes de este pago"""
        pagos_anteriores = self.factura.pagos.filter(
            fecha_pago__lt=self.fecha_pago
        ).aggregate(total=models.Sum('monto_pago'))['total'] or 0
        
        return self.factura.total - pagos_anteriores
    
    @property
    def saldo_despues(self):
        """Obtiene el saldo después de este pago"""
        return self.saldo_anterior - self.monto_pago


class AutorizoGasto(models.Model):
    """Catálogo de personas que autorizan gastos"""
    nombre = models.CharField(
        max_length=200, 
        verbose_name="Nombre completo",
        help_text="Nombre completo de la persona que autoriza gastos"
    )
    activo = models.BooleanField(
        default=True, 
        verbose_name="Activo",
        help_text="Indica si la persona está activa para autorizar gastos"
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True, 
        verbose_name="Fecha de creación"
    )
    
    class Meta:
        verbose_name = "Autorizó Gasto"
        verbose_name_plural = "Autorizó Gastos"
        db_table = 'autorizo_gasto'
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre


class Almacen(models.Model):
    """Modelo para gestión de almacenes"""
    
    codigo = models.AutoField(
        primary_key=True, 
        verbose_name="Código"
    )
    
    descripcion = models.CharField(
        max_length=200, 
        verbose_name="Descripción",
        help_text="Descripción del almacén"
    )
    
    activo = models.BooleanField(
        default=True, 
        verbose_name="Activo",
        help_text="Indica si el almacén está activo"
    )
    
    fecha_creacion = models.DateTimeField(
        auto_now_add=True, 
        verbose_name="Fecha de creación"
    )
    
    fecha_modificacion = models.DateTimeField(
        auto_now=True, 
        verbose_name="Fecha de modificación"
    )
    
    class Meta:
        verbose_name = "Almacén"
        verbose_name_plural = "Almacenes"
        db_table = 'almacenes'
        ordering = ['descripcion']
    
    def __str__(self):
        return f"{self.codigo} - {self.descripcion}"


class Compra(models.Model):
    """Modelo para gestión de compras de productos"""
    
    ESTADO_CHOICES = [
        ('activa', 'Activa'),
        ('cancelada', 'Cancelada'),
    ]
    
    folio = models.AutoField(
        primary_key=True,
        verbose_name="Folio"
    )
    
    fecha = models.DateField(
        verbose_name="Fecha de compra",
        help_text="Fecha en que se realizó la compra"
    )
    
    proveedor = models.ForeignKey(
        Proveedor,
        on_delete=models.PROTECT,
        verbose_name="Proveedor",
        help_text="Proveedor de la compra"
    )
    
    factura = models.CharField(
        max_length=50,
        verbose_name="Factura",
        help_text="Número de factura del proveedor",
        blank=True,
        null=True
    )
    
    serie = models.CharField(
        max_length=20,
        verbose_name="Serie",
        help_text="Serie de la factura",
        blank=True,
        null=True
    )
    
    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        verbose_name="Subtotal",
        help_text="Subtotal de la compra"
    )
    
    impuestos = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        verbose_name="Impuestos",
        help_text="Impuestos de la compra"
    )
    
    total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        verbose_name="Total",
        help_text="Total de la compra"
    )
    
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='activa',
        verbose_name="Estado",
        help_text="Estado de la compra"
    )
    
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creación"
    )
    
    fecha_modificacion = models.DateTimeField(
        auto_now=True,
        verbose_name="Fecha de modificación"
    )
    
    class Meta:
        verbose_name = "Compra"
        verbose_name_plural = "Compras"
        db_table = 'compras'
        ordering = ['-fecha', '-folio']
    
    def __str__(self):
        return f"Compra {self.folio:06d} - {self.proveedor.nombre}"


class CompraDetalle(models.Model):
    """Modelo para detalle de compras de productos"""
    
    compra = models.ForeignKey(
        Compra,
        on_delete=models.CASCADE,
        related_name='detalles',
        verbose_name="Compra"
    )
    
    producto = models.ForeignKey(
        ProductoServicio,
        on_delete=models.PROTECT,
        verbose_name="Producto/Servicio",
        help_text="Producto o servicio comprado"
    )
    
    almacen = models.ForeignKey(
        Almacen,
        on_delete=models.PROTECT,
        verbose_name="Almacén",
        help_text="Almacén donde se almacenará el producto"
    )
    
    cantidad = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Cantidad",
        help_text="Cantidad comprada"
    )
    
    precio = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Precio Unitario",
        help_text="Precio unitario del producto"
    )
    
    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Subtotal",
        help_text="Subtotal del detalle (cantidad × precio)"
    )
    
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creación"
    )
    
    class Meta:
        verbose_name = "Detalle de Compra"
        verbose_name_plural = "Detalles de Compra"
        db_table = 'compra_detalles'
        ordering = ['id']
    
    def __str__(self):
        return f"{self.compra.folio:06d} - {self.producto.descripcion}"
    
    def save(self, *args, **kwargs):
        # Calcular subtotal automáticamente
        self.subtotal = self.cantidad * self.precio
        super().save(*args, **kwargs)


class Kardex(models.Model):
    """Modelo para control de existencias y costos (Kardex)"""
    
    TIPO_MOVIMIENTO_CHOICES = [
        ('entrada', 'Entrada'),
        ('salida', 'Salida'),
        ('ajuste', 'Ajuste'),
    ]
    
    producto = models.ForeignKey(
        ProductoServicio,
        on_delete=models.CASCADE,
        verbose_name="Producto/Servicio"
    )
    
    almacen = models.ForeignKey(
        Almacen,
        on_delete=models.CASCADE,
        verbose_name="Almacén"
    )
    
    fecha = models.DateTimeField(
        verbose_name="Fecha del movimiento"
    )
    
    tipo_movimiento = models.CharField(
        max_length=20,
        choices=TIPO_MOVIMIENTO_CHOICES,
        verbose_name="Tipo de Movimiento"
    )
    
    cantidad = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Cantidad"
    )
    
    precio_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Precio Unitario"
    )
    
    costo_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Costo Total"
    )
    
    existencia_anterior = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Existencia Anterior"
    )
    
    existencia_actual = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Existencia Actual"
    )
    
    costo_promedio_anterior = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Costo Promedio Anterior"
    )
    
    costo_promedio_actual = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Costo Promedio Actual"
    )
    
    referencia = models.CharField(
        max_length=100,
        verbose_name="Referencia",
        help_text="Referencia del movimiento (folio de compra, etc.)",
        blank=True,
        null=True
    )
    
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creación"
    )
    
    class Meta:
        verbose_name = "Kardex"
        verbose_name_plural = "Kardex"
        db_table = 'kardex'
        ordering = ['-fecha', '-id']
        unique_together = ['producto', 'almacen', 'fecha', 'tipo_movimiento']
    
    def __str__(self):
        return f"{self.producto.descripcion} - {self.almacen.descripcion} - {self.get_tipo_movimiento_display()}"
    
    def save(self, *args, **kwargs):
        # Calcular costo total
        self.costo_total = self.cantidad * self.precio_unitario
        
        # Obtener el último movimiento para calcular existencias y costo promedio
        ultimo_movimiento = Kardex.objects.filter(
            producto=self.producto,
            almacen=self.almacen
        ).exclude(id=self.id).order_by('-fecha', '-id').first()
        
        if ultimo_movimiento:
            self.existencia_anterior = ultimo_movimiento.existencia_actual
            self.costo_promedio_anterior = ultimo_movimiento.costo_promedio_actual
        else:
            self.existencia_anterior = 0
            self.costo_promedio_anterior = 0
        
        # Calcular existencia actual según el tipo de movimiento
        if self.tipo_movimiento == 'entrada':
            self.existencia_actual = self.existencia_anterior + self.cantidad
        elif self.tipo_movimiento == 'salida':
            self.existencia_actual = self.existencia_anterior - self.cantidad
        else:  # ajuste
            self.existencia_actual = self.cantidad
        
        # Calcular costo promedio actual (método de costo promedio)
        if self.tipo_movimiento == 'entrada':
            if self.existencia_anterior > 0:
                costo_total_anterior = self.existencia_anterior * self.costo_promedio_anterior
                costo_total_actual = costo_total_anterior + self.costo_total
                self.costo_promedio_actual = costo_total_actual / self.existencia_actual
            else:
                self.costo_promedio_actual = self.precio_unitario
        else:
            self.costo_promedio_actual = self.costo_promedio_anterior
        
        super().save(*args, **kwargs)


class TipoSalida(models.Model):
    """Modelo para tipos de salida de inventario"""
    
    codigo = models.AutoField(
        primary_key=True,
        verbose_name="Código"
    )
    
    descripcion = models.CharField(
        max_length=100,
        verbose_name="Descripción",
        help_text="Descripción del tipo de salida"
    )
    
    activo = models.BooleanField(
        default=True,
        verbose_name="Activo",
        help_text="Indica si el tipo de salida está activo"
    )
    
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creación"
    )
    
    class Meta:
        verbose_name = "Tipo de Salida"
        verbose_name_plural = "Tipos de Salida"
        db_table = 'tipos_salida'
        ordering = ['descripcion']
    
    def __str__(self):
        return self.descripcion


class SalidaInventario(models.Model):
    """Modelo maestro para salidas de inventario"""
    
    codigo = models.AutoField(
        primary_key=True,
        verbose_name="Código"
    )
    
    folio = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Folio",
        help_text="Folio único de la salida"
    )
    
    fecha = models.DateField(
        verbose_name="Fecha de salida",
        help_text="Fecha en que se realiza la salida"
    )
    
    ciclo = models.CharField(
        max_length=10,
        verbose_name="Ciclo",
        help_text="Ciclo de producción actual"
    )
    
    autorizo = models.ForeignKey(
        'AutorizoGasto',
        on_delete=models.PROTECT,
        verbose_name="Autorizó",
        help_text="Persona que autoriza la salida"
    )
    
    tipo_salida = models.ForeignKey(
        TipoSalida,
        on_delete=models.PROTECT,
        verbose_name="Tipo de salida",
        help_text="Tipo de salida de inventario"
    )
    
    observaciones = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observaciones",
        help_text="Observaciones adicionales"
    )
    
    activo = models.BooleanField(
        default=True,
        verbose_name="Activo",
        help_text="Indica si la salida está activa"
    )
    
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creación"
    )
    
    usuario_creacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='salidas_inventario_creadas',
        verbose_name="Usuario que creó el registro"
    )
    
    fecha_modificacion = models.DateTimeField(
        auto_now=True,
        verbose_name="Fecha de modificación"
    )
    
    usuario_modificacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='salidas_inventario_modificadas',
        verbose_name="Usuario que modificó el registro",
        blank=True,
        null=True
    )
    
    class Meta:
        verbose_name = "Salida de Inventario"
        verbose_name_plural = "Salidas de Inventario"
        db_table = 'salidas_inventario'
        ordering = ['-fecha', '-folio']
    
    def __str__(self):
        return f"Salida {self.folio} - {self.fecha}"
    
    def save(self, *args, **kwargs):
        """Generar folio automáticamente si no existe"""
        if not self.folio:
            # Obtener el último folio
            ultima_salida = SalidaInventario.objects.filter(
                folio__startswith='SAL'
            ).order_by('-folio').first()
            
            if ultima_salida:
                # Extraer el número del folio
                try:
                    numero = int(ultima_salida.folio.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    numero = 1
            else:
                numero = 1
            
            self.folio = f"SAL-{numero:06d}"
        
        super().save(*args, **kwargs)


class SalidaInventarioDetalle(models.Model):
    """Modelo detalle para salidas de inventario"""
    
    salida = models.ForeignKey(
        SalidaInventario,
        on_delete=models.CASCADE,
        related_name='detalles',
        verbose_name="Salida de inventario"
    )
    
    producto = models.ForeignKey(
        ProductoServicio,
        on_delete=models.PROTECT,
        verbose_name="Producto/Servicio",
        help_text="Producto que se está dando de salida"
    )
    
    almacen = models.ForeignKey(
        Almacen,
        on_delete=models.PROTECT,
        verbose_name="Almacén",
        help_text="Almacén del cual se saca el producto"
    )
    
    cantidad = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Cantidad",
        help_text="Cantidad que se da de salida"
    )
    
    centro_costo = models.ForeignKey(
        CentroCosto,
        on_delete=models.PROTECT,
        verbose_name="Centro de Costo",
        help_text="Centro de costo al que se asigna la salida"
    )
    
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creación"
    )
    
    class Meta:
        verbose_name = "Detalle de Salida de Inventario"
        verbose_name_plural = "Detalles de Salidas de Inventario"
        db_table = 'salidas_inventario_detalles'
        ordering = ['id']
    
    def __str__(self):
        return f"{self.salida.folio} - {self.producto.descripcion} - {self.cantidad}"
    
    def save(self, *args, **kwargs):
        """Crear movimiento de Kardex y gasto automático al guardar"""
        super().save(*args, **kwargs)
        
        # Crear movimiento de Kardex
        self._crear_movimiento_kardex()
        
        # Crear gasto automático en el presupuesto
        self._crear_gasto_automatico()
    
    def _crear_movimiento_kardex(self):
        """Crear movimiento de Kardex para la salida"""
        # Obtener el último movimiento del producto en el almacén
        ultimo_movimiento = Kardex.objects.filter(
            producto=self.producto,
            almacen=self.almacen
        ).order_by('-fecha', '-id').first()
        
        # Calcular existencia anterior y actual
        existencia_anterior = ultimo_movimiento.existencia_actual if ultimo_movimiento else 0
        existencia_actual = existencia_anterior - self.cantidad
        
        # Calcular costo promedio (usar el del último movimiento)
        costo_promedio_anterior = ultimo_movimiento.costo_promedio_actual if ultimo_movimiento else 0
        costo_promedio_actual = costo_promedio_anterior  # No cambia en salidas
        
        # Crear el movimiento de Kardex
        Kardex.objects.create(
            producto=self.producto,
            almacen=self.almacen,
            fecha=timezone.now(),
            tipo_movimiento='salida',
            cantidad=self.cantidad,
            precio_unitario=costo_promedio_anterior,
            costo_total=self.cantidad * costo_promedio_anterior,
            existencia_anterior=existencia_anterior,
            existencia_actual=existencia_actual,
            costo_promedio_anterior=costo_promedio_anterior,
            costo_promedio_actual=costo_promedio_actual,
            referencia=f"Salida {self.salida.folio}"
        )
    
    def _crear_gasto_automatico(self):
        """Crear gasto automático en el presupuesto del centro de costo"""
        try:
            # Verificar que el producto tenga clasificación de gasto
            if not self.producto.clasificacion_gasto:
                return  # No crear gasto si no hay clasificación
            
            # Obtener el presupuesto del centro de costo para el ciclo actual
            presupuesto = Presupuesto.objects.filter(
                centro_costo=self.centro_costo,
                ciclo=self.salida.ciclo,
                activo=True
            ).first()
            
            if not presupuesto:
                return  # No crear gasto si no hay presupuesto
            
            # Verificar que la clasificación de gasto esté en el presupuesto
            if not presupuesto.detalles.filter(
                clasificacion_gasto=self.producto.clasificacion_gasto,
                activo=True
            ).exists():
                return  # No crear gasto si la clasificación no está en el presupuesto
            
            # Obtener el costo unitario del producto (del último movimiento de Kardex)
            ultimo_movimiento = Kardex.objects.filter(
                producto=self.producto,
                almacen=self.almacen
            ).order_by('-fecha', '-id').first()
            
            costo_unitario = ultimo_movimiento.costo_promedio_actual if ultimo_movimiento else 0
            importe_gasto = self.cantidad * costo_unitario
            
            # Redondear el importe a 2 decimales
            from decimal import Decimal, ROUND_HALF_UP
            importe_gasto = importe_gasto.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            
            # Crear el gasto principal si no existe uno para esta salida
            gasto, created = Gasto.objects.get_or_create(
                presupuesto=presupuesto,
                ciclo=self.salida.ciclo,
                fecha_gasto=self.salida.fecha,
                defaults={
                    'observaciones': f'Gasto automático por salida de inventario {self.salida.folio}',
                    'activo': True,
                    'usuario_creacion': self.salida.usuario_creacion
                }
            )
            
            # Crear el detalle del gasto
            concepto = f"Salida de inventario - {self.salida.tipo_salida.descripcion} - {self.producto.descripcion}"
            
            GastoDetalle.objects.create(
                gasto=gasto,
                proveedor=None,  # No hay proveedor en salidas internas
                factura=f"SAL-{self.salida.folio}",  # Usar el folio como referencia
                clasificacion_gasto=self.producto.clasificacion_gasto,
                concepto=concepto,
                forma_pago='01',  # Efectivo por defecto para salidas internas
                importe=importe_gasto,
                autorizo=self.salida.autorizo,
                activo=True,
                usuario_creacion=self.salida.usuario_creacion
            )
            
        except Exception as e:
            # Log del error pero no interrumpir el flujo principal
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error al crear gasto automático para salida {self.salida.folio}: {str(e)}")


class OtroMovimiento(models.Model):
    """Modelo para otros movimientos de inventario (entradas, salidas, traspasos)"""
    
    TIPO_MOVIMIENTO_CHOICES = [
        ('entrada', 'Otras entradas'),
        ('salida', 'Otras salidas'),
        ('traspaso', 'Traspaso entre almacenes'),
    ]
    
    folio = models.AutoField(primary_key=True, verbose_name="Folio")
    fecha = models.DateField(verbose_name="Fecha del movimiento")
    tipo_movimiento = models.CharField(
        max_length=20,
        choices=TIPO_MOVIMIENTO_CHOICES,
        verbose_name="Tipo de Movimiento"
    )
    observaciones = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observaciones"
    )
    activo = models.BooleanField(default=True, verbose_name="Activo")
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    fecha_modificacion = models.DateTimeField(auto_now=True, verbose_name="Fecha de modificación")
    usuario_creacion = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name='otros_movimientos_creados',
        verbose_name="Usuario de creación"
    )
    
    class Meta:
        verbose_name = "Otro Movimiento"
        verbose_name_plural = "Otros Movimientos"
        db_table = 'otros_movimientos'
        ordering = ['-fecha', '-folio']
    
    def __str__(self):
        return f"{self.folio} - {self.get_tipo_movimiento_display()} - {self.fecha}"


class OtroMovimientoDetalle(models.Model):
    """Detalle de productos en otros movimientos"""
    
    movimiento = models.ForeignKey(
        OtroMovimiento,
        on_delete=models.CASCADE,
        related_name='detalles',
        verbose_name="Movimiento"
    )
    producto = models.ForeignKey(
        ProductoServicio,
        on_delete=models.PROTECT,
        verbose_name="Producto/Servicio"
    )
    almacen_origen = models.ForeignKey(
        Almacen,
        on_delete=models.PROTECT,
        related_name='movimientos_origen',
        verbose_name="Almacén de origen",
        null=True,
        blank=True
    )
    almacen_destino = models.ForeignKey(
        Almacen,
        on_delete=models.PROTECT,
        related_name='movimientos_destino',
        verbose_name="Almacén de destino",
        null=True,
        blank=True
    )
    cantidad = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Cantidad"
    )
    precio_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Precio Unitario"
    )
    costo_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Costo Total"
    )
    observaciones = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observaciones"
    )
    activo = models.BooleanField(default=True, verbose_name="Activo")
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    
    class Meta:
        verbose_name = "Detalle de Otro Movimiento"
        verbose_name_plural = "Detalles de Otros Movimientos"
        db_table = 'otros_movimientos_detalle'
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"{self.movimiento.folio} - {self.producto.descripcion} - {self.cantidad}"
    
    def save(self, *args, **kwargs):
        # Calcular costo total
        self.costo_total = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)
        
        # Crear movimientos en Kardex según el tipo
        self._crear_movimientos_kardex()
    
    def _crear_movimientos_kardex(self):
        """Crear movimientos en Kardex según el tipo de movimiento"""
        from decimal import Decimal
        from django.utils import timezone
        
        try:
            if self.movimiento.tipo_movimiento == 'entrada':
                # Solo entrada al almacén destino
                self._crear_movimiento_kardex_entrada()
            elif self.movimiento.tipo_movimiento == 'salida':
                # Solo salida del almacén origen
                self._crear_movimiento_kardex_salida()
            elif self.movimiento.tipo_movimiento == 'traspaso':
                # Salida del origen y entrada al destino
                self._crear_movimiento_kardex_salida()
                self._crear_movimiento_kardex_entrada()
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error al crear movimientos Kardex para otro movimiento {self.movimiento.folio}: {str(e)}")
    
    def _crear_movimiento_kardex_entrada(self):
        """Crear movimiento de entrada en Kardex"""
        from decimal import Decimal
        from django.utils import timezone
        
        almacen = self.almacen_destino or self.almacen_origen
        if not almacen:
            return
            
        # Obtener último movimiento
        ultimo_movimiento = Kardex.objects.filter(
            producto=self.producto,
            almacen=almacen
        ).order_by('-fecha', '-id').first()
        
        existencia_anterior = ultimo_movimiento.existencia_actual if ultimo_movimiento else Decimal('0')
        costo_promedio_anterior = ultimo_movimiento.costo_promedio_actual if ultimo_movimiento else Decimal('0')
        
        # Calcular nueva existencia y costo promedio
        existencia_actual = existencia_anterior + self.cantidad
        
        if existencia_anterior > 0:
            # Calcular costo promedio ponderado
            costo_total_anterior = existencia_anterior * costo_promedio_anterior
            costo_total_nuevo = self.cantidad * self.precio_unitario
            costo_promedio_actual = (costo_total_anterior + costo_total_nuevo) / existencia_actual
        else:
            costo_promedio_actual = self.precio_unitario
        
        # Crear movimiento
        Kardex.objects.create(
            producto=self.producto,
            almacen=almacen,
            fecha=timezone.now(),
            tipo_movimiento='entrada',
            cantidad=self.cantidad,
            precio_unitario=self.precio_unitario,
            costo_total=self.costo_total,
            existencia_anterior=existencia_anterior,
            existencia_actual=existencia_actual,
            costo_promedio_anterior=costo_promedio_anterior,
            costo_promedio_actual=costo_promedio_actual,
            referencia=f"OTRO-{self.movimiento.folio}"
        )
    
    def _crear_movimiento_kardex_salida(self):
        """Crear movimiento de salida en Kardex"""
        from decimal import Decimal
        from django.utils import timezone
        
        almacen = self.almacen_origen
        if not almacen:
            return
            
        # Obtener último movimiento
        ultimo_movimiento = Kardex.objects.filter(
            producto=self.producto,
            almacen=almacen
        ).order_by('-fecha', '-id').first()
        
        if not ultimo_movimiento or ultimo_movimiento.existencia_actual < self.cantidad:
            raise ValueError(f"Existencia insuficiente en {almacen.descripcion}")
        
        existencia_anterior = ultimo_movimiento.existencia_actual
        costo_promedio_anterior = ultimo_movimiento.costo_promedio_actual
        
        # Calcular nueva existencia (costo promedio se mantiene)
        existencia_actual = existencia_anterior - self.cantidad
        costo_promedio_actual = costo_promedio_anterior
        
        # Crear movimiento
        Kardex.objects.create(
            producto=self.producto,
            almacen=almacen,
            fecha=timezone.now(),
            tipo_movimiento='salida',
            cantidad=self.cantidad,
            precio_unitario=self.precio_unitario,
            costo_total=self.costo_total,
            existencia_anterior=existencia_anterior,
            existencia_actual=existencia_actual,
            costo_promedio_anterior=costo_promedio_anterior,
            costo_promedio_actual=costo_promedio_actual,
            referencia=f"OTRO-{self.movimiento.folio}"
        )
