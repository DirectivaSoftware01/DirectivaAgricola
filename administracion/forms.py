from django import forms
from .models import Empresa


class EmpresaForm(forms.ModelForm):
    class Meta:
        model = Empresa
        fields = ['nombre', 'rfc', 'db_name', 'activo', 'suspendido']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de la empresa'
            }),
            'rfc': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'RFC de la empresa',
                'maxlength': '13'
            }),
            'db_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de la base de datos'
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'suspendido': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        labels = {
            'nombre': 'Nombre de la Empresa',
            'rfc': 'RFC',
            'db_name': 'Nombre de Base de Datos',
            'activo': 'Activa',
            'suspendido': 'Suspendida'
        }

    def clean_rfc(self):
        rfc = self.cleaned_data.get('rfc', '').strip().upper()
        if not rfc:
            raise forms.ValidationError('El RFC es obligatorio.')
        
        # Validar formato básico de RFC
        if len(rfc) < 10 or len(rfc) > 13:
            raise forms.ValidationError('El RFC debe tener entre 10 y 13 caracteres.')
        
        return rfc

    def clean_db_name(self):
        db_name = self.cleaned_data.get('db_name', '').strip()
        if not db_name:
            raise forms.ValidationError('El nombre de la base de datos es obligatorio.')
        
        # Validar que no contenga caracteres especiales
        if not db_name.replace('_', '').replace('-', '').isalnum():
            raise forms.ValidationError('El nombre de la base de datos solo puede contener letras, números, guiones y guiones bajos.')
        
        return db_name
