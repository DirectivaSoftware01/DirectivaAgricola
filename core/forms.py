from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.db import models
from decimal import Decimal
from .models import Usuario, Cliente, RegimenFiscal, Proveedor, Transportista, LoteOrigen, ClasificacionGasto, CentroCosto, ProductoServicio, ConfiguracionSistema, Cultivo, Remision, RemisionDetalle, PresupuestoGasto, Presupuesto, PresupuestoDetalle, Gasto, GastoDetalle
import re

class DecimalFieldWithRounding(forms.DecimalField):
    """Campo decimal personalizado que permite más decimales en entrada pero redondea a 2"""
    
    def __init__(self, *args, **kwargs):
        # Permitir más decimales en la entrada
        kwargs.setdefault('max_digits', 15)
        kwargs.setdefault('decimal_places', 4)
        super().__init__(*args, **kwargs)
    
    def clean(self, value):
        value = super().clean(value)
        if value is not None:
            # Redondear a 2 decimales
            value = round(value, 2)
        return value

class LoginForm(AuthenticationForm):
    """Formulario de login personalizado"""
    username = forms.CharField(
        label='Usuario',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese su usuario'
        })
    )
    password = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese su contraseña'
        })
    )

class UsuarioForm(forms.ModelForm):
    """Formulario para crear/editar usuarios"""
    password = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese la contraseña'
        }),
        required=False
    )
    password_confirm = forms.CharField(
        label='Confirmar Contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirme la contraseña'
        }),
        required=False
    )

    class Meta:
        model = Usuario
        fields = ['nombre', 'puesto', 'email', 'username', 'is_admin']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre completo'
            }),
            'puesto': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Puesto de trabajo'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Correo electrónico'
            }),
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de usuario'
            }),
            'is_admin': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username:
            # Verificar si el username ya existe (excluyendo el usuario actual si estamos editando)
            queryset = Usuario.objects.filter(username=username)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            
            if queryset.exists():
                raise forms.ValidationError("Este nombre de usuario ya está en uso.")
        
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            # Verificar si el email ya existe (excluyendo el usuario actual si estamos editando)
            queryset = Usuario.objects.filter(email=email)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            
            if queryset.exists():
                raise forms.ValidationError("Este correo electrónico ya está registrado.")
        
        return email

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if password:
            # Validaciones de contraseña
            if len(password) < 8:
                raise forms.ValidationError("La contraseña debe tener al menos 8 caracteres.")
            
            if password.isdigit():
                raise forms.ValidationError("La contraseña no puede ser completamente numérica.")
            
            if password.isalpha():
                raise forms.ValidationError("La contraseña debe contener al menos un número.")
        
        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        # Si es un nuevo usuario, la contraseña es requerida
        if not self.instance.pk and not password:
            raise forms.ValidationError("La contraseña es requerida para nuevos usuarios.")

        if password and password != password_confirm:
            raise forms.ValidationError("Las contraseñas no coinciden.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('password')
        
        # Si es un nuevo usuario o se proporcionó una nueva contraseña
        if not user.pk or password:
            if password:
                user.set_password(password)
            else:
                # Para usuarios existentes sin nueva contraseña, mantener la actual
                pass
        
        if commit:
            user.save()
        return user


class RegimenFiscalForm(forms.ModelForm):
    """Formulario para crear/editar régimen fiscal"""
    
    class Meta:
        model = RegimenFiscal
        fields = ['codigo', 'descripcion', 'activo']
        widgets = {
            'codigo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Código del régimen (ej: 601)',
                'maxlength': '10'
            }),
            'descripcion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Descripción del régimen fiscal',
                'maxlength': '200'
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def clean_codigo(self):
        codigo = self.cleaned_data.get('codigo')
        if codigo:
            codigo = codigo.strip().upper()
            
            # Verificar si el código ya existe (excluyendo el registro actual si estamos editando)
            queryset = RegimenFiscal.objects.filter(codigo=codigo)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            
            if queryset.exists():
                raise forms.ValidationError("Este código de régimen fiscal ya está registrado.")
        
        return codigo


class ClienteForm(forms.ModelForm):
    """Formulario para crear/editar clientes"""
    
    class Meta:
        model = Cliente
        fields = [
            'razon_social', 'regimen_fiscal', 'codigo_postal', 'rfc',
            'domicilio', 'telefono', 'email_principal', 'email_alterno',
            'direccion_entrega', 'numero_bodega', 'telefono_bodega', 'ciudad', 'estado', 'activo'
        ]
        widgets = {
            'razon_social': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre completo o razón social del cliente',
                'maxlength': '200'
            }),
            'regimen_fiscal': forms.Select(attrs={
                'class': 'form-select'
            }),
            'codigo_postal': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '12345',
                'maxlength': '5',
                'pattern': '[0-9]{5}'
            }),
            'rfc': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'XAXX010101000 o ABC123456T1A',
                'maxlength': '13',
                'style': 'text-transform: uppercase;'
            }),
            'domicilio': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Dirección completa del cliente',
                'rows': 3
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '55-1234-5678 o (55) 1234-5678',
                'maxlength': '15'
            }),
            'email_principal': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'correo@ejemplo.com'
            }),
            'email_alterno': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'correo.alterno@ejemplo.com (opcional)'
            }),
            'direccion_entrega': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Dirección específica para entregas (opcional)',
                'rows': 3
            }),
            'numero_bodega': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número o identificador de la bodega (opcional)',
                'maxlength': '50'
            }),
            'telefono_bodega': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Teléfono de la bodega (opcional)',
                'maxlength': '15'
            }),
            'ciudad': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ciudad del cliente (opcional)',
                'maxlength': '100'
            }),
            'estado': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Estado del cliente (opcional)',
                'maxlength': '100'
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar solo regímenes fiscales activos
        self.fields['regimen_fiscal'].queryset = RegimenFiscal.objects.filter(activo=True)
        
        # Agregar clases CSS adicionales
        for field_name, field in self.fields.items():
            if field_name in ['razon_social', 'rfc', 'email_principal']:
                field.required = True
    
    def clean_rfc(self):
        rfc = self.cleaned_data.get('rfc')
        if rfc:
            # Normalizar RFC
            rfc = rfc.strip().upper().replace(' ', '')
            
            # Validar formato usando la función del modelo
            from .models import validar_rfc
            try:
                rfc = validar_rfc(rfc)
            except forms.ValidationError as e:
                raise forms.ValidationError(str(e))
            
            # Verificar si el RFC ya existe (excluyendo el cliente actual si estamos editando)
            queryset = Cliente.objects.filter(rfc=rfc)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            
            if queryset.exists():
                raise forms.ValidationError("Ya existe un cliente registrado con este RFC.")
        
        return rfc
    
    def clean_codigo_postal(self):
        cp = self.cleaned_data.get('codigo_postal')
        if cp:
            # Remover espacios y validar que sean solo dígitos
            cp = cp.strip()
            if not cp.isdigit() or len(cp) != 5:
                raise forms.ValidationError("El código postal debe tener exactamente 5 dígitos.")
        
        return cp
    
    def clean_telefono(self):
        telefono = self.cleaned_data.get('telefono')
        if telefono:
            # Limpiar el teléfono de espacios extra
            telefono = telefono.strip()
            
            # Validar que tenga al menos 10 dígitos (sin contar espacios, guiones, etc.)
            digitos = re.findall(r'\d', telefono)
            if len(digitos) < 10:
                raise forms.ValidationError("El teléfono debe tener al menos 10 dígitos.")
        
        return telefono
    
    def clean_email_principal(self):
        email = self.cleaned_data.get('email_principal')
        if email:
            email = email.strip().lower()
        return email
    
    def clean_email_alterno(self):
        email_alterno = self.cleaned_data.get('email_alterno')
        if email_alterno:
            email_alterno = email_alterno.strip().lower()
        return email_alterno
    
    def clean_telefono_bodega(self):
        telefono_bodega = self.cleaned_data.get('telefono_bodega')
        if telefono_bodega:
            telefono_bodega = telefono_bodega.strip()
            digitos = re.findall(r'\d', telefono_bodega)
            if len(digitos) < 10:
                raise forms.ValidationError("El teléfono de bodega debe tener al menos 10 dígitos.")
        return telefono_bodega
    
    def clean(self):
        cleaned_data = super().clean()
        email_principal = cleaned_data.get('email_principal')
        email_alterno = cleaned_data.get('email_alterno')
        
        # Validar que los emails sean diferentes
        if email_principal and email_alterno and email_principal == email_alterno:
            raise forms.ValidationError({
                'email_alterno': 'El correo electrónico alterno debe ser diferente al principal.'
            })
        
        return cleaned_data


class ClienteSearchForm(forms.Form):
    """Formulario para buscar clientes"""
    busqueda = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por razón social, RFC o código...',
            'autocomplete': 'off'
        }),
        label='Buscar cliente'
    )
    
    regimen_fiscal = forms.ModelChoiceField(
        queryset=RegimenFiscal.objects.filter(activo=True),
        required=False,
        empty_label="Todos los regímenes",
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Régimen fiscal'
    )
    
    activo = forms.ChoiceField(
        choices=[
            ('', 'Todos'),
            ('1', 'Activos'),
            ('0', 'Inactivos')
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Estado'
    )


class ProveedorForm(forms.ModelForm):
    """Formulario para crear/editar proveedores"""
    
    class Meta:
        model = Proveedor
        fields = ['nombre', 'rfc', 'domicilio', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre completo o razón social del proveedor',
                'maxlength': '200'
            }),
            'rfc': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'XAXX010101000 o ABC123456T1A',
                'maxlength': '13',
                'style': 'text-transform: uppercase;'
            }),
            'domicilio': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Dirección completa del proveedor',
                'rows': 3
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Marcar campos requeridos
        for field_name, field in self.fields.items():
            if field_name in ['nombre', 'rfc', 'domicilio']:
                field.required = True
    
    def clean_rfc(self):
        rfc = self.cleaned_data.get('rfc')
        if rfc:
            rfc = rfc.strip().upper().replace(' ', '')
            from .models import validar_rfc
            try:
                rfc = validar_rfc(rfc)
            except forms.ValidationError as e:
                raise forms.ValidationError(str(e))
            
            # Verificar que el RFC no esté duplicado
            queryset = Proveedor.objects.filter(rfc=rfc)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise forms.ValidationError("Ya existe un proveedor registrado con este RFC.")
        return rfc


class ProveedorSearchForm(forms.Form):
    """Formulario para buscar proveedores"""
    busqueda = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por nombre, RFC o código...',
            'autocomplete': 'off'
        }),
        label='Buscar proveedor'
    )
    
    activo = forms.ChoiceField(
        choices=[
            ('', 'Todos'),
            ('1', 'Activos'),
            ('0', 'Inactivos')
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Estado'
    )
class TransportistaForm(forms.ModelForm):
    """Formulario para crear/editar transportistas"""
    
    class Meta:
        model = Transportista
        fields = ['nombre_completo', 'licencia', 'domicilio', 'telefono', 'tipo_camion', 'placas_unidad', 'placas_remolque', 'activo']
        widgets = {
            'nombre_completo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre completo del transportista',
                'maxlength': '200'
            }),
            'licencia': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número de licencia de conducir',
                'maxlength': '50'
            }),
            'domicilio': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Dirección completa del transportista',
                'rows': 3
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número de teléfono del transportista',
                'maxlength': '15'
            }),
            'tipo_camion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tipo o modelo del camión',
                'maxlength': '100'
            }),
            'placas_unidad': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Placas del camión principal',
                'maxlength': '20',
                'style': 'text-transform: uppercase;'
            }),
            'placas_remolque': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Placas del remolque (opcional)',
                'maxlength': '20',
                'style': 'text-transform: uppercase;'
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Marcar campos requeridos
        for field_name, field in self.fields.items():
            if field_name in ['nombre_completo', 'licencia', 'domicilio', 'telefono', 'tipo_camion', 'placas_unidad']:
                field.required = True
    
    def clean_telefono(self):
        telefono = self.cleaned_data.get('telefono')
        if telefono:
            telefono = telefono.strip()
            digitos = re.findall(r'\d', telefono)
            if len(digitos) < 10:
                raise forms.ValidationError("El teléfono debe tener al menos 10 dígitos.")
        return telefono


class TransportistaSearchForm(forms.Form):
    """Formulario para buscar transportistas"""
    busqueda = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por nombre, licencia, placas o código...',
            'autocomplete': 'off'
        }),
        label='Buscar transportista'
    )
    
    activo = forms.ChoiceField(
        choices=[
            ('', 'Todos'),
            ('1', 'Activos'),
            ('0', 'Inactivos')
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Estado'
    )
class LoteOrigenForm(forms.ModelForm):
    """Formulario para crear/editar lotes de origen"""
    
    class Meta:
        model = LoteOrigen
        fields = ['nombre', 'observaciones', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del lote de origen',
                'maxlength': '200'
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Observaciones adicionales sobre el lote de origen (opcional)',
                'rows': 4
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Marcar campos requeridos
        for field_name, field in self.fields.items():
            if field_name in ['nombre']:
                field.required = True


class LoteOrigenSearchForm(forms.Form):
    """Formulario para buscar lotes de origen"""
    busqueda = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por nombre, observaciones o código...',
            'autocomplete': 'off'
        }),
        label='Buscar lote de origen'
    )
    
    activo = forms.ChoiceField(
        choices=[
            ('', 'Todos'),
            ('1', 'Activos'),
            ('0', 'Inactivos')
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Estado'
    )
class ClasificacionGastoForm(forms.ModelForm):
    """Formulario para crear/editar clasificaciones de gastos"""
    
    class Meta:
        model = ClasificacionGasto
        fields = ['descripcion', 'observaciones', 'activo']
        widgets = {
            'descripcion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Descripción de la clasificación de gasto',
                'maxlength': '200'
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Observaciones adicionales sobre la clasificación de gasto (opcional)',
                'rows': 4
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Marcar campos requeridos
        for field_name, field in self.fields.items():
            if field_name in ['descripcion']:
                field.required = True


class ClasificacionGastoSearchForm(forms.Form):
    """Formulario para buscar clasificaciones de gastos"""
    busqueda = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por descripción, observaciones o código...',
            'autocomplete': 'off'
        }),
        label='Buscar clasificación de gasto'
    )
    
    activo = forms.ChoiceField(
        choices=[
            ('', 'Todos'),
            ('1', 'Activos'),
            ('0', 'Inactivos')
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Estado'
    )
class CentroCostoForm(forms.ModelForm):
    """Formulario para crear/editar centros de costos"""
    
    class Meta:
        model = CentroCosto
        fields = ['descripcion', 'hectareas', 'observaciones', 'activo']
        widgets = {
            'descripcion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Descripción del centro de costo',
                'maxlength': '200'
            }),
            'hectareas': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número de hectáreas',
                'step': '0.01',
                'min': '0'
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Observaciones adicionales sobre el centro de costo (opcional)',
                'rows': 4
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Marcar campos requeridos
        for field_name, field in self.fields.items():
            if field_name in ['descripcion', 'hectareas']:
                field.required = True
    
    def clean_hectareas(self):
        hectareas = self.cleaned_data.get('hectareas')
        if hectareas is not None and hectareas < 0:
            raise forms.ValidationError("Las hectáreas no pueden ser negativas.")
        return hectareas


class CentroCostoSearchForm(forms.Form):
    """Formulario para buscar centros de costos"""
    busqueda = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por descripción, observaciones o código...',
            'autocomplete': 'off'
        }),
        label='Buscar centro de costo'
    )
    
    activo = forms.ChoiceField(
        choices=[
            ('', 'Todos'),
            ('1', 'Activos'),
            ('0', 'Inactivos')
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Estado'
    )
class ProductoServicioForm(forms.ModelForm):
    """Formulario para crear/editar productos y servicios"""
    

    
    class Meta:
        model = ProductoServicio
        fields = ['sku', 'descripcion', 'producto_servicio', 'unidad_medida', 'clave_sat', 'impuesto', 'activo']
        widgets = {
            'sku': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Clave alfanumérica única',
                'maxlength': '50',
                'style': 'text-transform: uppercase;'
            }),
            'descripcion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Descripción del producto o servicio',
                'maxlength': '200'
            }),
            'producto_servicio': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'unidad_medida': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Unidad de medida (ej: H87, E48, KGM, LTR, MTR)',
                'maxlength': '50'
            }),
            'clave_sat': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Clave del catálogo SAT',
                'maxlength': '20'
            }),
            'impuesto': forms.Select(attrs={
                'class': 'form-select'
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Marcar campos requeridos
        for field_name, field in self.fields.items():
            if field_name in ['sku', 'descripcion', 'unidad_medida', 'clave_sat', 'impuesto']:
                field.required = True
    
    def clean_sku(self):
        sku = self.cleaned_data.get('sku')
        if sku:
            sku = sku.upper().strip()
            # Verificar que no exista otro registro con el mismo SKU
            queryset = ProductoServicio.objects.filter(sku=sku)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise forms.ValidationError("Ya existe un producto o servicio con este SKU.")
        return sku


class ProductoServicioSearchForm(forms.Form):
    """Formulario para buscar productos y servicios"""
    busqueda = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por SKU, descripción, clave SAT o código...',
            'autocomplete': 'off'
        }),
        label='Buscar producto o servicio'
    )
    
    tipo = forms.ChoiceField(
        choices=[
            ('', 'Todos'),
            ('1', 'Productos'),
            ('0', 'Servicios')
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Tipo'
    )
    
    activo = forms.ChoiceField(
        choices=[
            ('', 'Todos'),
            ('1', 'Activos'),
            ('0', 'Inactivos')
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Estado'
    )
class ConfiguracionSistemaForm(forms.ModelForm):
    """Formulario para configuración del sistema"""
    
    # Campos para archivos (no se guardan en el modelo directamente)
    certificado_file = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.cer'
        }),
        label='Certificado (.cer)',
        help_text='Seleccione el archivo de certificado (.cer)'
    )
    
    llave_file = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.key'
        }),
        label='Llave (.key)',
        help_text='Seleccione el archivo de llave privada (.key)'
    )
    
    class Meta:
        model = ConfiguracionSistema
        fields = [
            'ciclo_actual',
            'razon_social', 'rfc', 'direccion', 'telefono',
            'nombre_pac', 'contrato', 'usuario_pac', 'password_pac',
            'password_llave'
        ]
        widgets = {
            'ciclo_actual': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Ciclo 2024-2025'
            }),
            'razon_social': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Razón social de la empresa'
            }),
            'rfc': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'RFC de la empresa'
            }),
            'direccion': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Dirección de la empresa',
                'rows': 3
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Teléfono de la empresa',
                'type': 'tel'
            }),
            'nombre_pac': forms.Select(attrs={
                'class': 'form-select'
            }),
            'contrato': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número de contrato'
            }),
            'usuario_pac': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Usuario del PAC'
            }),
            'password_pac': forms.PasswordInput(attrs={
                'class': 'form-control',
                'placeholder': 'Contraseña del PAC'
            }),
            'password_llave': forms.PasswordInput(attrs={
                'class': 'form-control',
                'placeholder': 'Contraseña de la llave privada'
            }),
        }
        labels = {
            'ciclo_actual': 'Ciclo actual',
            'razon_social': 'Razón Social',
            'rfc': 'RFC',
            'direccion': 'Dirección',
            'telefono': 'Teléfono',
            'nombre_pac': 'Nombre de PAC',
            'contrato': 'Contrato',
            'usuario_pac': 'Usuario',
            'password_pac': 'Contraseña',
            'password_llave': 'Contraseña de la llave',
        }
        help_texts = {
            'ciclo_actual': 'Nombre del ciclo de producción actual',
            'razon_social': 'Razón social de la empresa',
            'rfc': 'Registro Federal de Contribuyentes de la empresa',
            'direccion': 'Dirección de la empresa',
            'telefono': 'Número de teléfono de la empresa',
            'nombre_pac': 'Proveedor Autorizado de Certificación',
            'contrato': 'Número de contrato con el PAC',
            'usuario_pac': 'Usuario para el PAC',
            'password_pac': 'Contraseña para el PAC',
            'password_llave': 'Contraseña para la llave privada',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Agregar campos de archivo al formulario
        self.fields['certificado_file'] = forms.FileField(
            required=False,
            widget=forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.cer'
            }),
            label='Certificado (.cer)',
            help_text='Seleccione el archivo de certificado (.cer)'
        )
        
        self.fields['llave_file'] = forms.FileField(
            required=False,
            widget=forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.key'
            }),
            label='Llave (.key)',
            help_text='Seleccione el archivo de llave privada (.key)'
        )
    
    def clean_certificado_file(self):
        """Validar archivo de certificado"""
        certificado_file = self.cleaned_data.get('certificado_file')
        if certificado_file:
            if not certificado_file.name.endswith('.cer'):
                raise forms.ValidationError('El archivo debe tener extensión .cer')
            if certificado_file.size > 5 * 1024 * 1024:  # 5MB
                raise forms.ValidationError('El archivo no puede ser mayor a 5MB')
        return certificado_file
    
    def clean_llave_file(self):
        """Validar archivo de llave"""
        llave_file = self.cleaned_data.get('llave_file')
        if llave_file:
            if not llave_file.name.endswith('.key'):
                raise forms.ValidationError('El archivo debe tener extensión .key')
            if llave_file.size > 5 * 1024 * 1024:  # 5MB
                raise forms.ValidationError('El archivo no puede ser mayor a 5MB')
        return llave_file
    
    def save(self, commit=True):
        """Guardar con conversión de archivos a base64"""
        instance = super().save(commit=False)
        
        # Convertir archivos a base64 si se proporcionaron
        if self.cleaned_data.get('certificado_file'):
            certificado_file = self.cleaned_data['certificado_file']
            instance.certificado = certificado_file.read().decode('latin-1')
        
        if self.cleaned_data.get('llave_file'):
            llave_file = self.cleaned_data['llave_file']
            instance.llave = llave_file.read().decode('latin-1')
        
        if commit:
            instance.save()
        return instance
class CultivoForm(forms.ModelForm):
    """Formulario para crear/editar cultivos"""
    
    class Meta:
        model = Cultivo
        fields = ['nombre', 'variedad', 'observaciones', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Maíz, Trigo, Frijol'
            }),
            'variedad': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Híbrido, Criollo, Mejorado'
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observaciones adicionales sobre el cultivo'
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        labels = {
            'nombre': 'Nombre del cultivo',
            'variedad': 'Variedad',
            'observaciones': 'Observaciones',
            'activo': 'Activo'
        }
        help_texts = {
            'nombre': 'Nombre del cultivo',
            'variedad': 'Variedad del cultivo',
            'observaciones': 'Observaciones adicionales',
            'activo': 'Indica si el cultivo está activo'
        }
    
    def clean_nombre(self):
        """Validar nombre del cultivo"""
        nombre = self.cleaned_data.get('nombre')
        if nombre:
            nombre = nombre.strip()
            if len(nombre) < 2:
                raise forms.ValidationError('El nombre del cultivo debe tener al menos 2 caracteres.')
        return nombre
    
    def clean_variedad(self):
        """Validar variedad del cultivo"""
        variedad = self.cleaned_data.get('variedad')
        if variedad:
            variedad = variedad.strip()
            if len(variedad) < 2:
                raise forms.ValidationError('La variedad debe tener al menos 2 caracteres.')
        return variedad


class CultivoSearchForm(forms.Form):
    """Formulario de búsqueda para cultivos"""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por nombre o variedad...',
            'autocomplete': 'off'
        }),
        label='Buscar cultivo'
    )
    
    activo = forms.ChoiceField(
        choices=[
            ('', 'Todos'),
            ('1', 'Activos'),
            ('0', 'Inactivos')
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Estado'
    )


class RemisionForm(forms.ModelForm):
    """Formulario para crear/editar remisiones"""
    
    class Meta:
        model = Remision
        fields = ['ciclo', 'folio', 'fecha', 'cliente', 'lote_origen', 'transportista', 'costo_flete', 'observaciones']
        widgets = {
            'ciclo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ciclo de producción actual',
                'readonly': True
            }),
            'folio': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número de folio',
                'min': '1',
                'readonly': True
            }),
            'fecha': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'cliente': forms.Select(attrs={
                'class': 'form-select'
            }),
            'lote_origen': forms.Select(attrs={
                'class': 'form-select'
            }),
            'transportista': forms.Select(attrs={
                'class': 'form-select'
            }),
            'costo_flete': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0'
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Observaciones adicionales (opcional)',
                'rows': 3
            })
        }
        labels = {
            'ciclo': 'Ciclo',
            'folio': 'Folio',
            'fecha': 'Fecha',
            'cliente': 'Cliente',
            'lote_origen': 'Lote - Origen',
            'transportista': 'Transportista',
            'costo_flete': 'Costo de Flete',
            'observaciones': 'Observaciones'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filtrar solo registros activos
        self.fields['cliente'].queryset = Cliente.objects.filter(activo=True)
        self.fields['lote_origen'].queryset = LoteOrigen.objects.filter(activo=True)
        self.fields['transportista'].queryset = Transportista.objects.filter(activo=True)
        
        # Obtener el ciclo actual de la configuración
        from .models import ConfiguracionSistema
        configuracion = ConfiguracionSistema.objects.first()
        if configuracion and configuracion.ciclo_actual:
            self.fields['ciclo'].initial = configuracion.ciclo_actual
        
        # Generar folio automáticamente para nuevas remisiones
        if not self.instance.pk:  # Solo para nuevas remisiones
            if configuracion and configuracion.ciclo_actual:
                # Obtener el último folio del ciclo actual
                ultimo_folio = Remision.objects.filter(ciclo=configuracion.ciclo_actual).aggregate(
                    max_folio=models.Max('folio')
                )['max_folio']
                
                # Si no hay remisiones en este ciclo, empezar con 1, sino incrementar
                siguiente_folio = 1 if ultimo_folio is None else ultimo_folio + 1
                self.fields['folio'].initial = siguiente_folio
                # También establecer el valor en el campo para que se muestre
                self.initial['folio'] = siguiente_folio
        
        # Marcar campos requeridos
        for field_name, field in self.fields.items():
            if field_name in ['folio', 'fecha', 'cliente', 'lote_origen', 'transportista']:
                field.required = True
    
    def clean_folio(self):
        folio = self.cleaned_data.get('folio')
        if folio is not None and folio <= 0:
            raise forms.ValidationError("El folio debe ser un número positivo.")
        return folio
    
    def clean_costo_flete(self):
        costo_flete = self.cleaned_data.get('costo_flete')
        if costo_flete is not None and costo_flete < 0:
            raise forms.ValidationError("El costo de flete no puede ser negativo.")
        return costo_flete
    
    def clean(self):
        cleaned_data = super().clean()
        ciclo = cleaned_data.get('ciclo')
        folio = cleaned_data.get('folio')
        
        # Solo validar para nuevas remisiones
        if not self.instance.pk and ciclo and folio:
            # Verificar si ya existe una remisión con este ciclo y folio
            if Remision.objects.filter(ciclo=ciclo, folio=folio).exists():
                # Si existe, calcular el siguiente folio disponible
                ultimo_folio = Remision.objects.filter(ciclo=ciclo).aggregate(
                    max_folio=models.Max('folio')
                )['max_folio']
                
                siguiente_folio = 1 if ultimo_folio is None else ultimo_folio + 1
                cleaned_data['folio'] = siguiente_folio
                
                # Agregar mensaje informativo
                self.add_error('folio', f'El folio {folio} ya existe para el ciclo {ciclo}. Se asignó automáticamente el folio {siguiente_folio}.')
        
        return cleaned_data


class RemisionDetalleForm(forms.ModelForm):
    """Formulario para crear/editar detalles de remisiones"""
    
    # Usar campos personalizados para redondeo automático
    kgs_enviados = DecimalFieldWithRounding(
        label='Kgs Enviados',
        help_text='Kilogramos enviados',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0.00',
            'step': '0.01',
            'min': '0'
        })
    )
    
    kgs_liquidados = DecimalFieldWithRounding(
        label='Kgs Liquidados',
        help_text='Kilogramos liquidados',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0.00',
            'step': '0.01',
            'min': '0'
        })
    )
    
    kgs_merma = DecimalFieldWithRounding(
        label='Kgs Merma',
        help_text='Kilogramos de merma',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0.00',
            'step': '0.01',
            'min': '0'
        })
    )
    
    precio = DecimalFieldWithRounding(
        label='Precio',
        help_text='Precio por kilogramo',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0.00',
            'step': '0.01',
            'min': '0'
        })
    )
    
    importe_liquidado = DecimalFieldWithRounding(
        label='Importe Liquidado',
        help_text='Importe total liquidado',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0.00',
            'step': '0.01',
            'min': '0'
        })
    )
    
    class Meta:
        model = RemisionDetalle
        fields = ['cultivo', 'calidad', 'no_arps', 'kgs_enviados', 'merma_arps', 'kgs_liquidados', 'kgs_merma', 'precio', 'importe_liquidado']
        widgets = {
            'cultivo': forms.Select(attrs={
                'class': 'form-select'
            }),
            'calidad': forms.Select(attrs={
                'class': 'form-select'
            }),
            'no_arps': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número de arps',
                'min': '1'
            }),
            'merma_arps': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0',
                'min': '0'
            })
        }
        labels = {
            'cultivo': 'Cultivo',
            'calidad': 'Calidad',
            'no_arps': 'No Arps',
            'merma_arps': 'Merma/Arps'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filtrar solo cultivos activos
        self.fields['cultivo'].queryset = Cultivo.objects.filter(activo=True)
        
        # Marcar campos requeridos
        for field_name, field in self.fields.items():
            if field_name in ['cultivo', 'calidad', 'no_arps', 'kgs_enviados', 'merma_arps']:
                field.required = True
    
    def clean_no_arps(self):
        no_arps = self.cleaned_data.get('no_arps')
        if no_arps is not None and no_arps <= 0:
            raise forms.ValidationError("El número de arps debe ser positivo.")
        return no_arps
    
    def clean_kgs_enviados(self):
        kgs_enviados = self.cleaned_data.get('kgs_enviados')
        if kgs_enviados is not None:
            if kgs_enviados <= 0:
                raise forms.ValidationError("Los kilogramos enviados deben ser positivos.")
            # Redondear a 2 decimales
            kgs_enviados = round(kgs_enviados, 2)
        return kgs_enviados
    
    def clean_merma_arps(self):
        merma_arps = self.cleaned_data.get('merma_arps')
        if merma_arps is not None and merma_arps < 0:
            raise forms.ValidationError("La merma por arps no puede ser negativa.")
        return merma_arps
    
    def clean_kgs_liquidados(self):
        kgs_liquidados = self.cleaned_data.get('kgs_liquidados')
        if kgs_liquidados is not None:
            if kgs_liquidados < 0:
                raise forms.ValidationError("Los kilogramos liquidados no pueden ser negativos.")
            # Redondear a 2 decimales
            kgs_liquidados = round(kgs_liquidados, 2)
        return kgs_liquidados
    
    def clean_kgs_merma(self):
        kgs_merma = self.cleaned_data.get('kgs_merma')
        if kgs_merma is not None:
            if kgs_merma < 0:
                raise forms.ValidationError("Los kilogramos de merma no pueden ser negativos.")
            # Redondear a 2 decimales
            kgs_merma = round(kgs_merma, 2)
        return kgs_merma
    
    def clean_precio(self):
        precio = self.cleaned_data.get('precio')
        if precio is not None:
            if precio < 0:
                raise forms.ValidationError("El precio no puede ser negativo.")
            # Redondear a 2 decimales
            precio = round(precio, 2)
        return precio
    
    def clean_importe_liquidado(self):
        importe_liquidado = self.cleaned_data.get('importe_liquidado')
        if importe_liquidado is not None:
            if importe_liquidado < 0:
                raise forms.ValidationError("El importe liquidado no puede ser negativo.")
            # Redondear a 2 decimales
            importe_liquidado = round(importe_liquidado, 2)
        return importe_liquidado


class RemisionSearchForm(forms.Form):
    """Formulario para buscar remisiones"""
    busqueda = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por ciclo, folio, cliente...',
            'autocomplete': 'off'
        }),
        label='Buscar remisión'
    )
    
    cliente = forms.ModelChoiceField(
        queryset=Cliente.objects.filter(activo=True),
        required=False,
        empty_label="Todos los clientes",
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Cliente'
    )
    
    lote_origen = forms.ModelChoiceField(
        queryset=LoteOrigen.objects.filter(activo=True),
        required=False,
        empty_label="Todos los lotes",
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Lote - Origen'
    )
    
    transportista = forms.ModelChoiceField(
        queryset=Transportista.objects.filter(activo=True),
        required=False,
        empty_label="Todos los transportistas",
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Transportista'
    )
    
    fecha_desde = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Fecha desde'
    )
    
    fecha_hasta = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Fecha hasta'
    )


class RemisionLiquidacionForm(forms.ModelForm):
    """Formulario para liquidar remisiones"""
    
    class Meta:
        model = RemisionDetalle
        fields = ['kgs_liquidados', 'kgs_merma', 'precio', 'importe_liquidado']
        widgets = {
            'kgs_liquidados': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'kgs_merma': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'precio': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'importe_liquidado': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            })
        }
        labels = {
            'kgs_liquidados': 'Kgs Liquidados',
            'kgs_merma': 'Kgs Merma',
            'precio': 'Precio por Kg',
            'importe_liquidado': 'Importe Liquidado'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Establecer valores iniciales si el detalle ya tiene datos
        if self.instance and self.instance.pk:
            self.fields['kgs_liquidados'].initial = self.instance.kgs_liquidados
            self.fields['kgs_merma'].initial = self.instance.kgs_merma
            self.fields['precio'].initial = self.instance.precio
            self.fields['importe_liquidado'].initial = self.instance.importe_liquidado


class RemisionCancelacionForm(forms.Form):
    """Formulario para cancelar una remisión"""
    
    motivo_cancelacion = forms.CharField(
        max_length=500,
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Ingrese el motivo de la cancelación...',
            'required': True
        }),
        label='Motivo de cancelación',
        help_text='Campo obligatorio. Describa el motivo por el cual se cancela esta remisión.'
    )
    
    folio_sustituto = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 2024-2025-000123 (opcional)'
        }),
        label='Folio que sustituye',
        help_text='Campo opcional. Si esta remisión es sustituida por otra, indique el folio de la nueva remisión.'
    )
    
    def clean_motivo_cancelacion(self):
        motivo = self.cleaned_data.get('motivo_cancelacion')
        if motivo and len(motivo.strip()) < 10:
            raise forms.ValidationError('El motivo de cancelación debe tener al menos 10 caracteres.')
        return motivo.strip()
    
    def clean_folio_sustituto(self):
        folio = self.cleaned_data.get('folio_sustituto')
        if folio:
            folio = folio.strip()
            if len(folio) < 3:
                raise forms.ValidationError('El folio sustituto debe tener al menos 3 caracteres.')
        return folio


class CobranzaSearchForm(forms.Form):
    """Formulario para buscar remisiones en cobranza"""
    busqueda = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por ciclo, folio, cliente...',
            'autocomplete': 'off'
        }),
        label='Buscar remisión'
    )
    
    cliente = forms.ModelChoiceField(
        queryset=Cliente.objects.filter(activo=True),
        required=False,
        empty_label="Todos los clientes",
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Cliente'
    )
    
    estado_facturacion = forms.ChoiceField(
        choices=[
            ('', 'Todos los estados'),
            ('pendiente', 'Pendiente de facturar'),
            ('facturado', 'Facturado'),
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Estado de Facturación'
    )
    
    estado_pago = forms.ChoiceField(
        choices=[
            ('', 'Todos los estados'),
            ('pendiente', 'Pendiente de pago'),
            ('pagado', 'Pagado'),
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Estado de Pago'
    )
    
    fecha_desde = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Fecha desde'
    )
    
    fecha_hasta = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Fecha hasta'
    )
class PresupuestoGastoForm(forms.ModelForm):
    """Formulario para crear/editar presupuestos de gastos"""
    
    class Meta:
        model = PresupuestoGasto
        fields = ['centro_costo', 'clasificacion_gasto', 'importe', 'observaciones']
        widgets = {
            'centro_costo': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'clasificacion_gasto': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'importe': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observaciones adicionales...'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar solo centros de costos y clasificaciones activas
        self.fields['centro_costo'].queryset = CentroCosto.objects.filter(activo=True)
        self.fields['clasificacion_gasto'].queryset = ClasificacionGasto.objects.filter(activo=True)
        
        # Hacer el campo de importe requerido
        self.fields['importe'].required = True


class PresupuestoGastoSearchForm(forms.Form):
    """Formulario para buscar presupuestos de gastos"""
    busqueda = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por centro de costo, clasificación, ciclo...',
            'autocomplete': 'off'
        }),
        label='Buscar presupuesto'
    )
    
    centro_costo = forms.ModelChoiceField(
        queryset=CentroCosto.objects.filter(activo=True),
        required=False,
        empty_label="Todos los centros de costo",
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Centro de Costo'
    )
    
    clasificacion_gasto = forms.ModelChoiceField(
        queryset=ClasificacionGasto.objects.filter(activo=True),
        required=False,
        empty_label="Todas las clasificaciones",
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Clasificación de Gasto'
    )
    
    ciclo = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ciclo de producción...'
        }),
        label='Ciclo'
    )


# ===========================
# FORMULARIOS PARA PRESUPUESTOS (NUEVA ESTRUCTURA)
# ===========================

class PresupuestoForm(forms.ModelForm):
    """Formulario para crear y editar presupuestos"""
    
    class Meta:
        model = Presupuesto
        fields = ['centro_costo', 'ciclo', 'observaciones', 'activo']
        widgets = {
            'centro_costo': forms.Select(attrs={'class': 'form-select'}),
            'ciclo': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'centro_costo': 'Centro de Costo',
            'ciclo': 'Ciclo',
            'observaciones': 'Observaciones',
            'activo': 'Activo',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['centro_costo'].queryset = CentroCosto.objects.filter(activo=True)
        self.fields['centro_costo'].required = True
        self.fields['ciclo'].required = True
        
        # Inicializar el campo ciclo con el ciclo actual
        try:
            config = ConfiguracionSistema.objects.first()
            ciclo_actual = config.ciclo_actual if config else '2025-2026'
            self.fields['ciclo'].initial = ciclo_actual
        except:
            self.fields['ciclo'].initial = '2025-2026'


class PresupuestoDetalleForm(forms.ModelForm):
    """Formulario para crear y editar detalles de presupuesto"""
    
    importe = DecimalFieldWithRounding(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal('0.00'),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        label='Importe Presupuestado'
    )
    
    class Meta:
        model = PresupuestoDetalle
        fields = ['clasificacion_gasto', 'importe', 'activo']
        widgets = {
            'clasificacion_gasto': forms.Select(attrs={'class': 'form-select'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'clasificacion_gasto': 'Clasificación de Gasto',
            'activo': 'Activo',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['clasificacion_gasto'].queryset = ClasificacionGasto.objects.filter(activo=True)
        self.fields['clasificacion_gasto'].required = True
        self.fields['importe'].required = True


class PresupuestoSearchForm(forms.Form):
    """Formulario para buscar presupuestos"""
    busqueda = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por centro de costo, ciclo...',
            'autocomplete': 'off'
        }),
        label='Buscar presupuesto'
    )
    
    centro_costo = forms.ModelChoiceField(
        queryset=CentroCosto.objects.filter(activo=True),
        required=False,
        empty_label="Todos los centros de costo",
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Centro de Costo'
    )
    
    ciclo = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej. 2025-2026',
            'autocomplete': 'off'
        }),
        label='Ciclo'
    )

class GastoForm(forms.ModelForm):
    """Formulario para crear y editar gastos"""
    
    class Meta:
        model = Gasto
        fields = ['presupuesto', 'ciclo', 'fecha_gasto', 'observaciones', 'activo']
        widgets = {
            'presupuesto': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'ciclo': forms.TextInput(attrs={
                'class': 'form-control',
                'readonly': True,
                'autocomplete': 'off'
            }),
            'fecha_gasto': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observaciones adicionales del gasto'
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        labels = {
            'presupuesto': 'Presupuesto',
            'ciclo': 'Ciclo',
            'fecha_gasto': 'Fecha del Gasto',
            'observaciones': 'Observaciones',
            'activo': 'Activo'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Obtener el ciclo actual de la configuración
        try:
            config = ConfiguracionSistema.objects.first()
            if config:
                self.fields['ciclo'].initial = config.ciclo_actual
        except:
            pass
        
        # Filtrar presupuestos activos
        self.fields['presupuesto'].queryset = Presupuesto.objects.filter(activo=True).order_by('centro_costo__descripcion')


class GastoDetalleForm(forms.ModelForm):
    """Formulario para crear y editar detalles de gastos"""
    
    importe = DecimalFieldWithRounding(
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0.01',
            'required': True,
            'placeholder': '0.00'
        }),
        label='Importe'
    )
    
    class Meta:
        model = GastoDetalle
        fields = ['proveedor', 'factura', 'clasificacion_gasto', 'concepto', 'importe', 'activo']
        widgets = {
            'proveedor': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'factura': forms.TextInput(attrs={
                'class': 'form-control',
                'required': True,
                'placeholder': 'Número de factura'
            }),
            'clasificacion_gasto': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'concepto': forms.TextInput(attrs={
                'class': 'form-control',
                'required': True,
                'placeholder': 'Concepto o descripción del gasto'
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        labels = {
            'proveedor': 'Proveedor',
            'factura': 'Factura',
            'clasificacion_gasto': 'Clasificación de Gasto',
            'concepto': 'Concepto',
            'importe': 'Importe',
            'activo': 'Activo'
        }

    def __init__(self, *args, **kwargs):
        presupuesto = kwargs.pop('presupuesto', None)
        super().__init__(*args, **kwargs)
        
        # Filtrar proveedores activos
        self.fields['proveedor'].queryset = Proveedor.objects.filter(activo=True).order_by('razon_social')
        
        # Filtrar clasificaciones de gastos según el presupuesto
        if presupuesto:
            clasificaciones_ids = presupuesto.detalles.filter(activo=True).values_list('clasificacion_gasto_id', flat=True)
            self.fields['clasificacion_gasto'].queryset = ClasificacionGasto.objects.filter(
                id__in=clasificaciones_ids,
                activo=True
            ).order_by('descripcion')
