from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario

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
