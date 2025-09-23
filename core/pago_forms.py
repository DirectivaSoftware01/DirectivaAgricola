from django import forms
from decimal import Decimal
from .models import PagoFactura, Factura


class PagoFacturaForm(forms.ModelForm):
    """Formulario para registrar pagos de facturas"""
    
    class Meta:
        model = PagoFactura
        fields = ['monto_pago', 'tipo_pago', 'referencia_pago', 'observaciones']
        widgets = {
            'monto_pago': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01',
                'placeholder': '0.00'
            }),
            'tipo_pago': forms.Select(attrs={
                'class': 'form-select'
            }),
            'referencia_pago': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Referencia bancaria, transferencia, etc.'
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observaciones adicionales del pago'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.factura = kwargs.pop('factura', None)
        super().__init__(*args, **kwargs)
        
        if self.factura:
            # Establecer el monto máximo como saldo pendiente
            saldo_pendiente = self.factura.obtener_saldo_pendiente()
            self.fields['monto_pago'].widget.attrs['max'] = str(saldo_pendiente)
            self.fields['monto_pago'].help_text = f'Saldo pendiente: ${saldo_pendiente:,.2f}'
            
            # Si el saldo es muy pequeño, marcar como pago completo
            if saldo_pendiente <= Decimal('0.01'):
                self.fields['tipo_pago'].initial = 'COMPLETO'
                self.fields['monto_pago'].initial = saldo_pendiente
                self.fields['monto_pago'].widget.attrs['readonly'] = True
    
    def clean_monto_pago(self):
        monto = self.cleaned_data.get('monto_pago')
        
        if not monto or monto <= 0:
            raise forms.ValidationError('El monto del pago debe ser mayor a cero')
        
        if self.factura:
            # Comparar contra el saldo anterior real (antes de este pago)
            from django.db.models import Sum
            from django.utils import timezone
            # Considerar solo pagos timbrados
            pagos_anteriores = self.factura.pagos.filter(uuid__isnull=False).aggregate(total=Sum('monto_pago'))['total'] or 0
            saldo_anterior = self.factura.total - pagos_anteriores
            if monto > saldo_anterior:
                raise forms.ValidationError(
                    f'El monto del pago (${monto:,.2f}) no puede exceder el saldo pendiente (${saldo_anterior:,.2f})'
                )
        
        return monto
    
    def clean(self):
        cleaned_data = super().clean()
        monto = cleaned_data.get('monto_pago')
        tipo_pago = cleaned_data.get('tipo_pago')
        
        if self.factura and monto and tipo_pago:
            from django.db.models import Sum
            pagos_anteriores = self.factura.pagos.aggregate(total=Sum('monto_pago'))['total'] or 0
            saldo_pendiente = self.factura.total - pagos_anteriores
            
            # Validar consistencia entre monto y tipo de pago
            if tipo_pago == 'COMPLETO' and monto < saldo_pendiente:
                raise forms.ValidationError(
                    'Para un pago completo, el monto debe ser igual al saldo pendiente'
                )
            elif tipo_pago in ['PARCIAL', 'ABONO'] and monto >= saldo_pendiente:
                raise forms.ValidationError(
                    'Para un pago parcial o abono, el monto debe ser menor al saldo pendiente'
                )
        
        return cleaned_data


class FiltroEstadoCuentaForm(forms.Form):
    """Formulario para filtrar el estado de cuenta"""
    
    fecha_desde = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Fecha Desde'
    )
    
    fecha_hasta = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Fecha Hasta'
    )
    
    estado_pago = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'Todos los estados'),
            ('PENDIENTE', 'Pendiente'),
            ('PARCIAL', 'Pago Parcial'),
            ('PAGADA', 'Pagada'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Estado de Pago'
    )
    
    def clean(self):
        cleaned_data = super().clean()
        fecha_desde = cleaned_data.get('fecha_desde')
        fecha_hasta = cleaned_data.get('fecha_hasta')
        
        if fecha_desde and fecha_hasta and fecha_desde > fecha_hasta:
            raise forms.ValidationError('La fecha desde no puede ser mayor a la fecha hasta')
        
        return cleaned_data
