from django import forms
from .models import PlanPago
from .models import Regularizacion
from .models import ReglaEstructura
from .models import ReglaMora
import datetime

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
                'required': True
            }),
            'modalidad': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'cohorte': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 2025',
                'required': True
            }),
        }

        error_messages = {
            'nombre': {
                'required': '*Debe ingresar un nombre.',
                'max_length': '*El nombre es demasiado largo.',
            },
            'carrera': {
                'required': '*Debe seleccionar una carrera.',
            },
            'modalidad': {
                'required': '*Debe seleccionar una modalidad.',
            },
            'cohorte': {
                'required': '*Debe ingresar un cohorte.',
                'invalid': '*Debe ser un número válido.'
            },
        }

    # -------- VALIDACIONES PERSONALIZADAS -------- #

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre')
        if nombre and len(nombre.strip()) < 3:
            raise forms.ValidationError("*El nombre es demasiado corto.")
        return nombre

    def clean_cohorte(self):
        cohorte = self.cleaned_data.get('cohorte')

        if cohorte:
            if not cohorte.isdigit():
                raise forms.ValidationError("*El cohorte debe ser un año válido.")
            if len(cohorte) != 4:
                raise forms.ValidationError("*El cohorte debe tener 4 dígitos.")
        return cohorte



    # VALIDACIONES PERSONALIZADAS


    def clean_cohorte(self):
        cohorte = self.cleaned_data.get("cohorte")

        if not cohorte:
            raise forms.ValidationError("*Debe ingresar un cohorte.")

        if not str(cohorte).isdigit():
            raise forms.ValidationError("*El cohorte debe ser un número (ej: 2025).")

        cohorte = int(cohorte)
        current_year = datetime.date.today().year

        if cohorte < 2023 or cohorte > 2040:
            raise forms.ValidationError("*El cohorte debe estar entre 2023 y 2040.")

        if cohorte < current_year - 5:
            raise forms.ValidationError(
                f"*El cohorte no puede ser menor a {current_year - 5}."
            )

        if cohorte > current_year + 2 :
            raise forms.ValidationError(
                f"*El cohorte no puede ser mayor a {current_year + 2}."
            )

        return cohorte

    def clean(self):
        cleaned_data = super().clean()

        carrera = cleaned_data.get("carrera")
        modalidad = cleaned_data.get("modalidad")

        # Validación de selects vacíos (cuando el value es "")


        if carrera in (None, "", " "):
            self.add_error("carrera", "Debe seleccionar una carrera válida.")

        if modalidad in (None, "", " "):
            self.add_error("modalidad", "Debe seleccionar una modalidad válida.")

        return cleaned_data
    
class ReglaEstructuraForm(forms.ModelForm):

    valor = forms.DecimalField(
        label='Precio Base',
        max_digits=10,
        decimal_places=2,
        min_value=0,
        error_messages={
            'required': '*Debe ingresar el precio base.',
            'min_value': '*El precio base no puede ser negativo.',
            'invalid': '*Debe ingresar un número válido.',
            'max_digits': 'El número es demasiado grande, máximo 8 dígitos antes del decimal.',
            'max_decimal_places': 'Solo se permiten 2 decimales.',
        },
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 88000.00 (monto total del año)',
        })
    )

    tasa = forms.DecimalField(
        label='Tasa de Interés (%)',
        max_digits=5,
        decimal_places=2,
        min_value=0,
        error_messages={
            'required': '*Debe ingresar la tasa.',
            'min_value': '*La tasa no puede ser negativa.',
            'invalid': '*Debe ingresar un número válido.'
        },
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 10.5',
        })
    )

    pago_incial = forms.DecimalField(
        label='Matrícula / Pago Inicial',
        max_digits=10,
        decimal_places=2,
        min_value=0,
        error_messages={
            'required': '*Debe ingresar el pago inicial.',
            'min_value': '*El pago inicial no puede ser negativo.',
            'invalid': '*Debe ingresar un número válido.'
        },
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 2000.00',
        })
    )

    cantidad_de_cuotas = forms.IntegerField(
        label='Cantidad de Cuotas',
        min_value=1,
        max_value=12,
        error_messages={
            'required': '*Debe ingresar la cantidad de cuotas.',
            'min_value': '*Debe haber al menos 1 cuota.',
            'invalid': '*Debe ingresar una cantidad de cuotas válido.'
        },
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 12',
        })
    )

    dia_vencimiento = forms.IntegerField(
        label='Día de Vencimiento',
        min_value=1,
        max_value=31,
        error_messages={
            'required': '*Debe ingresar un día.',
            'min_value': '*El día debe ser entre 1 y 31.',
            'max_value': '*El día debe ser entre 1 y 31.',
            'invalid': '*Debe ingresar un número válido.'
        },
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 15',
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
            }),
        }
        error_messages = {
            'frecuencia_de_pago': {
                'required': '*Debe seleccionar una frecuencia de pago.',
            }
        }

    def clean(self):
        cleaned_data = super().clean()

        valor = cleaned_data.get('valor')
        pago = cleaned_data.get('pago_incial')
        cuotas = cleaned_data.get('cantidad_de_cuotas')
        tasa = cleaned_data.get('tasa')

        # Pago inicial no debe superar el valor total
        if valor and pago and pago > valor:
            self.add_error('pago_incial', '*El pago inicial no puede ser mayor al precio base.')

        # Cuotas no deben ser excesivamente grandes o absurdas
        if cuotas and cuotas > 12:
            self.add_error('cantidad_de_cuotas', '*La cantidad de cuotas no puede ser mayor a 12.')

        # Tasa extrema
        if tasa and tasa > 100:
            self.add_error('tasa', 'La tasa no puede superar el 100%.')

        return cleaned_data


class ReglaEstructuraRegularizacionForm(forms.ModelForm):

    valor = forms.DecimalField(
        label='Monto',
        max_digits=10,
        decimal_places=2,
        min_value=0,
        required=False,   # Solo obligatorio si origen_deuda = MONTO_FIJO
        error_messages={
            'min_value': '*El monto no puede ser negativo.',
            'invalid': '*Debe ingresar un número válido.',
        },
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
        error_messages={
            'required': '*Debe ingresar una tasa de interés.',
            'min_value': '*La tasa no puede ser negativa.',
            'invalid': '*Debe ingresar un número válido.',
        },
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 10.5',
        })
    )

    pago_incial = forms.DecimalField(
        label='Pago Inicial',
        max_digits=10,
        decimal_places=2,
        min_value=0,
        error_messages={
            'required': '*Debe ingresar el pago inicial.',
            'min_value': '*El pago inicial no puede ser negativo.',
            'invalid': '*Debe ingresar un número válido.',
        },
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 2000.00',
        })
    )

    cantidad_de_cuotas = forms.IntegerField(
        label='Cantidad de Cuotas',
        min_value=1,
        error_messages={
            'required': '*Debe ingresar la cantidad de cuotas.',
            'min_value': '*Debe existir al menos 1 cuota.',
            'invalid': '*Debe ingresar un número válido.',
        },
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 12',
        })
    )

    dia_vencimiento = forms.IntegerField(
        label='Día de Vencimiento',
        min_value=1,
        max_value=31,
        error_messages={
            'required': '*Debe ingresar un día de vencimiento.',
            'min_value': '*El día no puede ser menor a 1.',
            'max_value': '*El día no puede ser mayor a 31.',
            'invalid': '*Debe ingresar un número válido.',
        },
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 15',
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
            }),
            'frecuencia_de_pago': forms.Select(attrs={
                'class': 'form-select',
            }),
        }

        labels = {
            'origen_deuda': 'Origen de Deuda',
        }

        error_messages = {
            'origen_deuda': {
                'required': '*Debe seleccionar un origen de deuda.',
            },
            'frecuencia_de_pago': {
                'required': '*Debe seleccionar una frecuencia de pago.',
            },
        }
    # VALIDACIÓN 

    def clean(self):
        cleaned_data = super().clean()

        origen = cleaned_data.get('origen_deuda')
        valor = cleaned_data.get('valor')

        # Si el origen es MONTO FIJO → valor debe ser obligatorio
        if origen == 'FIJO' and (valor is None or valor == ''):
            self.add_error('valor', "*Debe ingresar el monto fijo.")

        return cleaned_data


class ReglaMoraForm(forms.ModelForm):

    tipo_de_recargo = forms.ChoiceField(
        choices=ReglaMora.TIPO_RECARGO_CHOICES,
        required=True,
        label="Tipo de recargo",
        help_text="FIJO (ej: 100 pesos) o PORCENTUAL (ej: 2%)",
        error_messages={
            "required": "Debe seleccionar un tipo de recargo."
        },
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    cantidad_recargo = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        required=True,
        label="Cantidad",
        min_value=0,
        help_text="Monto fijo o porcentaje según el tipo seleccionado",
        error_messages={
            "required": "Debe ingresar un recargo. El minimo es 0.",
            "min_value": "La cantidad no puede ser menor que 0."
        },
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )

    frecuencia_aplicacion = forms.ChoiceField(
        choices=ReglaMora.FRECUENCIA_APLICACION_CHOICES,
        required=True,
        label="Frecuencia de aplicación",
        help_text="diaria / semanal / mensual",
        error_messages={
            "required": "Debe seleccionar una frecuencia de aplicación de mora."
        },
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    dias_gracia = forms.IntegerField(
        required=True,
        min_value=0,
        label="Días de gracia",
        help_text="Cantidad de días antes de comenzar a aplicar recargo",
        error_messages={
            "required": "Debe ingresar un valor en días de gracia. El mínimo es 0.",
            "min_value": "Los días de gracia no pueden ser negativos."
        },
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )

    veces_aplicacion = forms.IntegerField(
        required=True,
        min_value=0,
        label="Veces de aplicación",
        help_text="Cantidad de veces que se aplicará la mora",
        error_messages={
            "required": "Debe ingresar cuantas veces se aplicará la mora.",
            "min_value": "La cantidad de aplicaciones de mora no puede ser negativa."
        },
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = ReglaMora
        fields = [
            'tipo_de_recargo',
            'cantidad_recargo',
            'frecuencia_aplicacion',
            'dias_gracia',
            'veces_aplicacion',
        ]

    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get("tipo_de_recargo")
        cantidad = cleaned_data.get("cantidad_recargo")


        # Validar FIJO 
        if tipo == "FIJO" and cantidad is None:
            self.add_error("cantidad_recargo", "Debe ingresar un monto fijo.")

        # Validar PORCENTUAL
        if tipo == "PORC":
            if cantidad is None:
                self.add_error("cantidad_recargo", "Debe ingresar un porcentaje.")
            elif cantidad > 100:
                self.add_error("cantidad_recargo", "El porcentaje no puede superar 100%.")

        return cleaned_data
