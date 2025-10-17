from django import forms
from .models import OtroMovimiento, OtroMovimientoDetalle, ProductoServicio, Almacen


class OtroMovimientoForm(forms.ModelForm):
    """Formulario para crear/editar otros movimientos"""
    
    class Meta:
        model = OtroMovimiento
        fields = ['fecha', 'tipo_movimiento', 'observaciones']
        widgets = {
            'fecha': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'tipo_movimiento': forms.Select(attrs={
                'class': 'form-select'
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observaciones del movimiento...'
            })
        }
        labels = {
            'fecha': 'Fecha del Movimiento',
            'tipo_movimiento': 'Tipo de Movimiento',
            'observaciones': 'Observaciones'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['fecha'].required = True
        self.fields['tipo_movimiento'].required = True


class OtroMovimientoDetalleForm(forms.ModelForm):
    """Formulario para crear/editar detalles de otros movimientos"""
    
    class Meta:
        model = OtroMovimientoDetalle
        fields = ['producto', 'almacen_origen', 'almacen_destino', 'cantidad', 'precio_unitario', 'observaciones']
        widgets = {
            'producto': forms.Select(attrs={
                'class': 'form-select'
            }),
            'almacen_origen': forms.Select(attrs={
                'class': 'form-select'
            }),
            'almacen_destino': forms.Select(attrs={
                'class': 'form-select'
            }),
            'cantidad': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01'
            }),
            'precio_unitario': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Observaciones del detalle...'
            })
        }
        labels = {
            'producto': 'Producto/Servicio',
            'almacen_origen': 'Almacén de Origen',
            'almacen_destino': 'Almacén de Destino',
            'cantidad': 'Cantidad',
            'precio_unitario': 'Precio Unitario',
            'observaciones': 'Observaciones'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['producto'].queryset = ProductoServicio.objects.filter(activo=True).order_by('descripcion')
        self.fields['almacen_origen'].queryset = Almacen.objects.filter(activo=True).order_by('descripcion')
        self.fields['almacen_destino'].queryset = Almacen.objects.filter(activo=True).order_by('descripcion')
        
        # Hacer campos requeridos según el contexto
        self.fields['producto'].required = True
        self.fields['cantidad'].required = True
        self.fields['precio_unitario'].required = True


class OtroMovimientoSearchForm(forms.Form):
    """Formulario para buscar otros movimientos"""
    folio = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por folio...',
            'autocomplete': 'off'
        }),
        label='Folio'
    )
    
    tipo_movimiento = forms.ChoiceField(
        choices=[
            ('', 'Todos'),
            ('entrada', 'Otras entradas'),
            ('salida', 'Otras salidas'),
            ('traspaso', 'Traspaso entre almacenes')
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Tipo de Movimiento'
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
