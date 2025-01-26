from django import forms
from .models import Cuenta, Transaccion

# Formulario para las cuentas
class CuentaForm(forms.ModelForm):
    class Meta:
        model = Cuenta
        fields = ['id_cuenta', 'nombre_cuenta','id_categoria']

# Formulario para las transacciones
class TransaccionForm(forms.ModelForm):
    class Meta:
        model = Transaccion
        fields = ['monto_transaccion', 'fecha_transaccion', 'id_cuenta_cargo', 'id_cuenta_abono']
        widgets = {
            'fecha_transaccion': forms.DateInput(attrs={'type': 'date'}),  # Aquí especificamos que sea tipo date
        }
