from django import forms
from .models import PlanPago

class PlanPagoForm(forms.ModelForm):
    class Meta:
        model = PlanPago
        fields = ['nombre', 'carrera', 'cohorte', 'modalidad', 'iEstado']

        labels = {
            'nombre': 'Nombre del plan',
            'carrera': 'Carrera',
            'cohorte': 'Cohorte',
            'modalidad': 'Modalidad',
            'iEstado': 'Activo',
        }

        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Plan Regular 2025'
            }),
            'carrera': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Analista de Sistemas'
            }),
            'cohorte': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 2025'
            }),
            'modalidad': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Presencial o Virtual'
            }),
            'iEstado': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
