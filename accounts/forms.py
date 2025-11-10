from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class RegistroFormulario(UserCreationForm):
    """
    Formulario de registro personalizado con mensajes en español
    """
    username = forms.CharField(
        label='Nombre de usuario',
        max_length=150,
        required=True,
        error_messages={
            'required': 'Este campo es obligatorio.',
            'max_length': 'El nombre de usuario no puede tener más de 150 caracteres.',
        },
        help_text='Requerido. 150 caracteres o menos. Letras, dígitos y @/./+/-/_ solamente.',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Elegí tu nombre de usuario'
        })
    )

    password1 = forms.CharField(
        label='Contraseña',
        required=True,
        error_messages={
            'required': 'Este campo es obligatorio.',
        },
        help_text=(
            '<ul class="mb-0">'
            '<li>Tu contraseña no puede ser muy similar a tu otra información personal.</li>'
            '<li>Tu contraseña debe contener al menos 8 caracteres.</li>'
            '<li>Tu contraseña no puede ser una contraseña común.</li>'
            '<li>Tu contraseña no puede ser completamente numérica.</li>'
            '</ul>'
        ),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Elegí una contraseña segura'
        })
    )

    password2 = forms.CharField(
        label='Confirmación de contraseña',
        required=True,
        error_messages={
            'required': 'Este campo es obligatorio.',
        },
        help_text='Ingresá la misma contraseña que antes, para verificación.',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirmá tu contraseña'
        })
    )

    class Meta:
        model = User
        fields = ('username', 'password1', 'password2')

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError("Las contraseñas no coinciden.")
        return password2

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError("Este nombre de usuario ya está en uso.")
        return username

    # Sobrescribir mensajes de error predeterminados
    error_messages = {
        'password_mismatch': 'Las dos contraseñas no coinciden.',
    }
