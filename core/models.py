from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.hashers import make_password
from django.core.validators import RegexValidator, EmailValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.conf import settings
import re

# Create your models here.

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
    
    impuesto = models.CharField(
        max_length=20,
        choices=[
            ('IVA_16', 'IVA Tasa 16%'),
            ('IVA_0', 'IVA Tasa cero'),
            ('IVA_EXENTO', 'IVA exento')
        ],
        verbose_name="Impuesto",
        help_text="Tipo de impuesto aplicable"
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
    
    def save(self, *args, **kwargs):
        """Guardar con validaciones y cálculos automáticos"""
        # Calcular peso promedio automáticamente
        if self.no_arps and self.kgs_enviados and self.no_arps > 0:
            peso_calculado = self.kgs_enviados / self.no_arps
            # Redondear a 2 decimales
            self.peso_promedio = round(peso_calculado, 2)
        
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
        help_text="Proveedor que emitió la factura"
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
