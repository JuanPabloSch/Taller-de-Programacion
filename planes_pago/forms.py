from django import forms
from .models import PlanPago
from .models import Regularizacion
from .models import ReglaEstructura
from .models import ReglaMora

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


class RegularizacionForm(forms.ModelForm):
    class Meta:
        model = Regularizacion
        fields = ['nombre', 'carrera', 'modalidad', 'cohorte']
        labels = {
                'nombre': 'Nombre de la Regularización',
                'carrera': 'Carrera',
                'modalidad': 'Modalidad',
                'cohorte': 'Cohorte',
            }
        widgets = {
                'nombre': forms.TextInput(attrs={
                    'class': 'form-control',
                    'placeholder': 'Ej: Regularización Analista 2025',
                    'required': True
                }),
                'carrera': forms.Select(attrs={
                    'class': 'form-select',
                    'placeholder':'---Seleccione---',
                    'required': True
                }),
                'modalidad': forms.Select(attrs={
                    'class': 'form-select',
                    'placeholder':'---Seleccione---',
                    'required': True
                }),
                'cohorte': forms.TextInput(attrs={
                    'class': 'form-control',
                    'placeholder': 'Ej: 2025',
                    'required': True
                }),
            }
class ReglaEstructuraForm(forms.ModelForm):
    class Meta:
        model = ReglaEstructura
        fields = [
            'origen_deuda', 
            'valor',
            'tasa', 
            'pago_incial', # ¡Nuevo!
            'cantidad_de_cuotas',
            'frecuencia_de_pago',
            'dia_vencimiento' # ¡Nuevo!
        ]
        labels = {
                'origen_deuda': 'Origen de la Deuda',
                'valor': 'Valor',
                'tasa': 'Tasa (%)',
                'pago_incial': 'Pago Inicial',
                'cantidad_de_cuotas': 'Cantidad de Cuotas',
                'frecuencia_de_pago': 'Frecuencia de Pago',
                'dia_vencimiento': 'Día de Vencimiento',
            }

        widgets = {
                'origen_deuda': forms.Select(attrs={
                    'class': 'form-select',
                    
                }),
                'valor': forms.NumberInput(attrs={  
                    'class': 'form-control',
                    'placeholder': 'Ej: 5000.00',
                    'required': True
                }),
                'tasa': forms.NumberInput(attrs={
                    'class': 'form-control',
                    'placeholder': 'Ej: 10.5',
                    'required': True
                }),
                'pago_incial': forms.NumberInput(attrs={
                    'class': 'form-control',
                    'placeholder': 'Ej: 2000.00',
                    'required': True
                }),
                'cantidad_de_cuotas': forms.NumberInput(attrs={
                    'class': 'form-control',
                    'placeholder': 'Ej: 12',
                    'required': True
                }),
                'frecuencia_de_pago': forms.Select(attrs={
                    'class': 'form-select',
                    'required': True
                }),
                'dia_vencimiento': forms.NumberInput(attrs={
                    'class': 'form-control',
                    'placeholder': 'Ej: 15',
                    'required': True
                }),
            }
class ReglaMoraForm(forms.ModelForm):
    # Definiciones explícitas para asegurar required=False y usar los choices del modelo

    tipo_de_recargo = forms.ChoiceField(
        # Asume que ReglaMora.TIPO_RECARGO_CHOICES está disponible aquí
        choices=ReglaMora.TIPO_RECARGO_CHOICES,
        required=False, # <--- Es opcional ahora
        label="Tipo de Recargo"
    )

    cantidad_recargo = forms.DecimalField(
        max_digits=5, 
        decimal_places=2,
        required=False, # <--- Es opcional ahora
        label="Tasa/Monto de Recargo"
    )
    veces_aplicacion = forms.IntegerField(
        required=False,
        label='Veces de Aplicación'
    )  
    frecuencia_aplicacion = forms.ChoiceField(
        # Asume que ReglaMora.FRECUENCIA_APLICACION_CHOICES está disponible aquí
        choices=ReglaMora.FRECUENCIA_APLICACION_CHOICES,
        required=False, # <--- Es opcional ahora
        label="Frecuencia de aplicación"
    )

    
    # dias_gracia es IntegerField y no necesita definición explícita
    # si no le cambiaste el tipo de widget o required (default=True en forms)
    # PERO, si quieres que los días de gracia sean opcionales y se guarden como NULL si no se llenan:
    dias_gracia = forms.IntegerField(
        required=False,
        label='Días de Gracia'
    )
    
    class Meta:
        model = ReglaMora
        # ¡IMPORTANTE! Lista solo los campos que existen en el modelo (sin aplica_reglas_mora)
        fields = [
            'tipo_de_recargo', 
            'cantidad_recargo', 
            'frecuencia_aplicacion', 
            'dias_gracia'
        ]
        
    def clean(self):
        # NOTA: Debes ELIMINAR CUALQUIER LÓGICA DE VALIDACIÓN (clean)
        # que dependiera del checkbox 'aplica_reglas_mora' o de campos obligatorios.
        # Si tenías un método 'clean', asegúrate de que esté ajustado a la nueva lógica opcional.
        return super().clean()