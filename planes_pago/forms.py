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
        fields = ['tipo', 'nombre', 'carrera', 'modalidad', 'cohorte']
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
    # Definición explícita de campos numéricos para agregar validación min_value
    valor = forms.DecimalField(
        label='Precio Base',
        max_digits=10,
        decimal_places=2,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 88000.00 (monto del año escolar)',
            'required': True
        })
    )

    tasa = forms.DecimalField(
        label='Tasa de Interés (%)',
        max_digits=5,
        decimal_places=2,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 10.5',
            'required': True
        })
    )

    pago_incial = forms.DecimalField(
        label='Matrícula',
        max_digits=10,
        decimal_places=2,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 2000.00 (pago inicial)',
            'required': True
        })
    )

    cantidad_de_cuotas = forms.IntegerField(
        label='Cantidad de Cuotas',
        min_value=1,  # Al menos 1 cuota
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 12',
            'required': True
        })
    )

    dia_vencimiento = forms.IntegerField(
        label='Día de Vencimiento',
        min_value=1,
        max_value=31,  # Los días del mes van del 1 al 31
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 15',
            'required': True
        })
    )

    class Meta:
        model = ReglaEstructura
        fields = [
            'valor',
            'tasa',
            'pago_incial',
            'cantidad_de_cuotas',
            'frecuencia_de_pago',
            'dia_vencimiento'
        ]
        widgets = {
            'frecuencia_de_pago': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
        }

class ReglaEstructuraRegularizacionForm(forms.ModelForm):
    """Formulario de estructura específico para Regularizaciones"""

    valor = forms.DecimalField(
        label='Monto',
        max_digits=10,
        decimal_places=2,
        min_value=0,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 50000.00 (solo si es Monto Fijo)',
            'id': 'id_estructura_reg-valor'
        })
    )

    tasa = forms.DecimalField(
        label='Tasa de Interés (%)',
        max_digits=5,
        decimal_places=2,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 10.5',
            'required': True
        })
    )

    pago_incial = forms.DecimalField(
        label='Pago Inicial',
        max_digits=10,
        decimal_places=2,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 2000.00',
            'required': True
        })
    )

    cantidad_de_cuotas = forms.IntegerField(
        label='Cantidad de Cuotas',
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 12',
            'required': True
        })
    )

    dia_vencimiento = forms.IntegerField(
        label='Día de Vencimiento',
        min_value=1,
        max_value=31,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 15',
            'required': True
        })
    )

    class Meta:
        model = ReglaEstructura
        fields = [
            'origen_deuda',
            'valor',
            'tasa',
            'pago_incial',
            'cantidad_de_cuotas',
            'frecuencia_de_pago',
            'dia_vencimiento'
        ]
        widgets = {
            'origen_deuda': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_estructura_reg-origen_deuda',
                'required': True
            }),
            'frecuencia_de_pago': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
        }
        labels = {
            'origen_deuda': 'Origen de Deuda',
        }

class ReglaMoraForm(forms.ModelForm):
    # Definiciones explícitas para asegurar required=False y usar los choices del modelo

    tipo_de_recargo = forms.ChoiceField(
        # Asume que ReglaMora.TIPO_RECARGO_CHOICES está disponible aquí
        choices=ReglaMora.TIPO_RECARGO_CHOICES,
        required=False, # <--- Es opcional ahora
        label="Tipo de recargo",
        help_text="FIJO (ej: 100pesos) o PORCENTUAL A LA CUOTA (2%)",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'placeholder': 'Seleccione tipo de recargo'
        })
    )

    cantidad_recargo = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        required=False, # <--- Es opcional ahora
        label="Cantidad",
        help_text="Monto fijo o porcentaje según el tipo de recargo seleccionado",
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 10'
        })
    )

    frecuencia_aplicacion = forms.ChoiceField(
        # Asume que ReglaMora.FRECUENCIA_APLICACION_CHOICES está disponible aquí
        choices=ReglaMora.FRECUENCIA_APLICACION_CHOICES,
        required=False, # <--- Es opcional ahora
        label="Frecuencia de aplicación",
        help_text="diaria/semanal/mensual",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'placeholder': 'Seleccione frecuencia'
        })
    )


    # dias_gracia es IntegerField y no necesita definición explícita
    # si no le cambiaste el tipo de widget o required (default=True en forms)
    # PERO, si quieres que los días de gracia sean opcionales y se guarden como NULL si no se llenan:
    dias_gracia = forms.IntegerField(
        required=False,
        label='Días de gracia',
        help_text="cantidad de días antes de que se aplique recargo post vencimiento",
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 5'
        })
    )

    veces_aplicacion = forms.IntegerField(
        required=False,
        label='Veces de Aplicación',
        help_text="Cantidad de veces que se aplicará el recargo por mora",
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 1'
        })
    )
    
    class Meta:
        model = ReglaMora
        # ¡IMPORTANTE! Lista solo los campos que existen en el modelo (sin aplica_reglas_mora)
        fields = [
            'tipo_de_recargo',
            'cantidad_recargo',
            'frecuencia_aplicacion',
            'dias_gracia',
            'veces_aplicacion'
        ]
        
    def clean(self):
        # NOTA: Debes ELIMINAR CUALQUIER LÓGICA DE VALIDACIÓN (clean)
        # que dependiera del checkbox 'aplica_reglas_mora' o de campos obligatorios.
        # Si tenías un método 'clean', asegúrate de que esté ajustado a la nueva lógica opcional.
        return super().clean()