from django import forms
from .models import Proveedor

class LoginForm(forms.Form):
    correo = forms.EmailField(label="Correo electrónico", widget=forms.EmailInput(attrs={'placeholder': 'correo@ejemplo.com'}))
    contraseña = forms.CharField(label="Contraseña", widget=forms.PasswordInput(attrs={'placeholder': '********'}))

class RegistroForm(forms.Form):
    nombre = forms.CharField(
        label="Nombre",
        max_length=100,
        widget=forms.TextInput(attrs={'placeholder': 'Tu nombre'})
    )
    apellido = forms.CharField(
        label="Apellido",
        max_length=100,
        widget=forms.TextInput(attrs={'placeholder': 'Tu apellido'})
    )
    correo = forms.EmailField(
        label="Correo electrónico",
        widget=forms.EmailInput(attrs={'placeholder': 'correo@ejemplo.com'})
    )
    celular = forms.CharField(
        label="Celular",
        max_length=20,
        widget=forms.TextInput(attrs={'placeholder': '+56 9 1234 5678'})
    )
    direccion = forms.CharField(
        label="Dirección",
        widget=forms.Textarea(attrs={'placeholder': 'Calle, número, ciudad', 'rows': 3})
    )
    contraseña = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={'placeholder': '********'})
    )
    confirmar_contraseña = forms.CharField(
        label="Confirmar contraseña",
        widget=forms.PasswordInput(attrs={'placeholder': '********'})
    )

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("contraseña")
        confirm = cleaned_data.get("confirmar_contraseña")

        if password != confirm:
            raise forms.ValidationError("Las contraseñas no coinciden.")

class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = ['nombre', 'correo', 'celular', 'direccion']
        widgets = {
            'nombre': forms.TextInput(attrs={'placeholder': 'Nombre del proveedor'}),
            'correo': forms.EmailInput(attrs={'placeholder': 'correo@ejemplo.com'}),
            'celular': forms.TextInput(attrs={'placeholder': '+57 300 123 4567'}),
            'direccion': forms.Textarea(attrs={
                'placeholder': 'Dirección del proveedor',
                'rows': 3
            }),
        }
        labels = {
            'nombre': 'Nombre',
            'correo': 'Correo electrónico',
            'celular': 'Celular',
            'direccion': 'Dirección',
        }