from django import forms
from django.utils import timezone
from decimal import Decimal
from .models import TipoSalida, SalidaInventario, SalidaInventarioDetalle, ProductoServicio, Almacen, CentroCosto, ConfiguracionSistema, AutorizoGasto
from .forms import DecimalFieldWithRounding


class TipoSalidaForm(forms.ModelForm):
    """Formulario para crear tipos de salida"""
    
    class Meta:
        model = TipoSalida
        fields = ['descripcion']
        widgets = {
            'descripcion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Descripción del tipo de salida'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['descripcion'].required = True


class SalidaInventarioForm(forms.ModelForm):
    """Formulario para crear/editar salidas de inventario"""
    
    class Meta:
        model = SalidaInventario
        fields = ['fecha', 'ciclo', 'autorizo', 'tipo_salida', 'observaciones']
        widgets = {
            'fecha': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'ciclo': forms.TextInput(attrs={
                'class': 'form-control',
                'readonly': True
            }),
            'autorizo': forms.Select(attrs={
                'class': 'form-select'
            }),
            'tipo_salida': forms.Select(attrs={
                'class': 'form-select'
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observaciones adicionales'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Establecer fecha actual por defecto solo si no hay datos POST
        if not self.instance.pk and not self.data:
            fecha_actual = timezone.now().date()
            self.fields['fecha'].initial = fecha_actual
            # También establecer el valor del widget
            self.fields['fecha'].widget.attrs['value'] = fecha_actual.strftime('%Y-%m-%d')
        
        # Cargar configuración del ciclo
        try:
            config = ConfiguracionSistema.objects.first()
            if config:
                self.fields['ciclo'].initial = config.ciclo_actual
        except:
            pass
        
        # Cargar autorizaciones activas
        self.fields['autorizo'].queryset = AutorizoGasto.objects.filter(activo=True).order_by('nombre')
        
        # Cargar tipos de salida activos
        self.fields['tipo_salida'].queryset = TipoSalida.objects.filter(activo=True).order_by('descripcion')
        
        # Marcar campos requeridos
        for field_name, field in self.fields.items():
            if field_name in ['fecha', 'ciclo', 'autorizo', 'tipo_salida']:
                field.required = True


class SalidaInventarioDetalleForm(forms.ModelForm):
    """Formulario para crear/editar detalles de salida de inventario"""
    
    class Meta:
        model = SalidaInventarioDetalle
        fields = ['producto', 'almacen', 'cantidad', 'centro_costo']
        widgets = {
            'producto': forms.Select(attrs={
                'class': 'form-select',
                'data-live-search': 'true'
            }),
            'almacen': forms.Select(attrs={
                'class': 'form-select'
            }),
            'cantidad': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01'
            }),
            'centro_costo': forms.Select(attrs={
                'class': 'form-select'
            })
        }
    
    cantidad = DecimalFieldWithRounding(
        label="Cantidad",
        help_text="Cantidad que se da de salida"
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Cargar productos activos
        self.fields['producto'].queryset = ProductoServicio.objects.filter(activo=True).order_by('descripcion')
        
        # Cargar almacenes activos
        self.fields['almacen'].queryset = Almacen.objects.filter(activo=True).order_by('descripcion')
        
        # Cargar centros de costo activos
        self.fields['centro_costo'].queryset = CentroCosto.objects.filter(activo=True).order_by('descripcion')
        
        # Marcar campos requeridos
        for field_name, field in self.fields.items():
            field.required = True
    
    def clean(self):
        cleaned_data = super().clean()
        cantidad = cleaned_data.get('cantidad')
        producto = cleaned_data.get('producto')
        almacen = cleaned_data.get('almacen')
        
        # Validar cantidad positiva
        if cantidad and cantidad <= 0:
            raise forms.ValidationError('La cantidad debe ser mayor a cero.')
        
        # Validar existencia disponible
        if cantidad and producto and almacen:
            from .models import Kardex
            
            # Obtener la existencia actual del producto en el almacén
            ultimo_movimiento = Kardex.objects.filter(
                producto=producto,
                almacen=almacen
            ).order_by('-fecha', '-id').first()
            
            existencia_disponible = ultimo_movimiento.existencia_actual if ultimo_movimiento else 0
            
            if cantidad > existencia_disponible:
                raise forms.ValidationError(
                    f'La cantidad solicitada ({cantidad}) excede la existencia disponible '
                    f'({existencia_disponible}) en el almacén {almacen.descripcion}.'
                )
        
        return cleaned_data
