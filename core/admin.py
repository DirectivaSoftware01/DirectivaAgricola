from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, AutorizoGasto, Almacen, Compra, CompraDetalle, Kardex

# Register your models here.

@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ('username', 'nombre', 'email', 'puesto', 'is_admin', 'is_active')
    list_filter = ('is_admin', 'is_active', 'is_staff', 'is_superuser')
    search_fields = ('username', 'nombre', 'email')
    ordering = ('nombre',)
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Información Personal', {'fields': ('nombre', 'puesto', 'email')}),
        ('Permisos', {'fields': ('is_active', 'is_staff', 'is_superuser', 'is_admin', 'groups', 'user_permissions')}),
        ('Fechas Importantes', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'nombre', 'puesto', 'email', 'is_admin'),
        }),
    )


@admin.register(AutorizoGasto)
class AutorizoGastoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'activo', 'fecha_creacion')
    list_filter = ('activo', 'fecha_creacion')
    search_fields = ('nombre',)
    ordering = ('nombre',)
    list_editable = ('activo',)


@admin.register(Almacen)
class AlmacenAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'descripcion', 'activo', 'fecha_creacion')
    list_filter = ('activo', 'fecha_creacion')
    search_fields = ('descripcion', 'codigo')
    ordering = ('descripcion',)
    readonly_fields = ('codigo', 'fecha_creacion', 'fecha_modificacion')
    
    fieldsets = (
        ('Información General', {
            'fields': ('codigo', 'descripcion', 'activo')
        }),
        ('Auditoría', {
            'fields': ('fecha_creacion', 'fecha_modificacion'),
            'classes': ('collapse',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # Si estamos editando un objeto existente
            return self.readonly_fields + ('codigo',)
        return self.readonly_fields


@admin.register(Compra)
class CompraAdmin(admin.ModelAdmin):
    list_display = ('folio', 'fecha', 'proveedor', 'factura', 'serie', 'subtotal', 'impuestos', 'total', 'estado', 'fecha_creacion')
    list_filter = ('estado', 'fecha', 'proveedor', 'fecha_creacion')
    search_fields = ('folio', 'proveedor__nombre', 'factura', 'serie')
    ordering = ('-fecha', '-folio')
    readonly_fields = ('folio', 'fecha_creacion', 'fecha_modificacion')
    
    fieldsets = (
        ('Información General', {
            'fields': ('folio', 'fecha', 'proveedor', 'estado')
        }),
        ('Facturación', {
            'fields': ('factura', 'serie', 'subtotal', 'impuestos', 'total')
        }),
        ('Auditoría', {
            'fields': ('fecha_creacion', 'fecha_modificacion'),
            'classes': ('collapse',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # Si estamos editando un objeto existente
            return self.readonly_fields + ('folio',)
        return self.readonly_fields


@admin.register(CompraDetalle)
class CompraDetalleAdmin(admin.ModelAdmin):
    list_display = ('compra', 'producto', 'almacen', 'cantidad', 'precio', 'subtotal', 'fecha_creacion')
    list_filter = ('compra', 'producto', 'almacen', 'fecha_creacion')
    search_fields = ('compra__folio', 'producto__descripcion', 'almacen__descripcion')
    ordering = ('-fecha_creacion',)
    readonly_fields = ('subtotal', 'fecha_creacion')
    
    fieldsets = (
        ('Información General', {
            'fields': ('compra', 'producto', 'almacen')
        }),
        ('Detalles', {
            'fields': ('cantidad', 'precio', 'subtotal')
        }),
        ('Auditoría', {
            'fields': ('fecha_creacion',),
            'classes': ('collapse',)
        }),
    )


@admin.register(Kardex)
class KardexAdmin(admin.ModelAdmin):
    list_display = ('producto', 'almacen', 'fecha', 'tipo_movimiento', 'cantidad', 'precio_unitario', 'costo_total', 'existencia_actual', 'costo_promedio_actual', 'referencia')
    list_filter = ('tipo_movimiento', 'producto', 'almacen', 'fecha', 'fecha_creacion')
    search_fields = ('producto__descripcion', 'almacen__descripcion', 'referencia')
    ordering = ('-fecha', '-id')
    readonly_fields = ('costo_total', 'existencia_anterior', 'existencia_actual', 'costo_promedio_anterior', 'costo_promedio_actual', 'fecha_creacion')
    
    fieldsets = (
        ('Información General', {
            'fields': ('producto', 'almacen', 'fecha', 'tipo_movimiento', 'referencia')
        }),
        ('Movimiento', {
            'fields': ('cantidad', 'precio_unitario', 'costo_total')
        }),
        ('Existencias', {
            'fields': ('existencia_anterior', 'existencia_actual')
        }),
        ('Costos', {
            'fields': ('costo_promedio_anterior', 'costo_promedio_actual')
        }),
        ('Auditoría', {
            'fields': ('fecha_creacion',),
            'classes': ('collapse',)
        }),
    )
