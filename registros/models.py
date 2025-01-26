from django.db import models

CATEGORIAS = [
    ('ACTIVO', 'Activo'),
    ('PASIVO', 'Pasivo'),
    ('PATRIMONIO', 'Patrimonio'),  # Cambiado de 'CAPITAL CONTABLE DEL PROPIETARIO'
    ('INGRESOS', 'Ingresos'),
    ('COSTOS_GASTOS', 'Costos/Gastos'),  # Cambiado de 'GASTOS'
]

class Categoria_ecuacion_contable(models.Model):
    id_categoria = models.AutoField(primary_key=True)  # AutoField para un ID autoincremental
    nombre_categoria = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre_categoria  # Representación legible de la categoría

class Cuenta(models.Model):
    id_cuenta = models.IntegerField(primary_key=True)
    nombre_cuenta = models.CharField(max_length=100)
    id_categoria = models.ForeignKey(Categoria_ecuacion_contable, on_delete=models.CASCADE)
    activo = models.BooleanField(default=True)  # Nuevo campo para marcar si la cuenta está activa

    def __str__(self):
        return self.nombre_cuenta  # Representación legible de la cuenta

class Transaccion(models.Model):
    id_transaccion = models.AutoField(primary_key=True)  # AutoField para un ID autoincremental
    monto_transaccion = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_transaccion = models.DateField()
    id_cuenta_cargo = models.ForeignKey(Cuenta, related_name='debe', on_delete=models.CASCADE)
    id_cuenta_abono = models.ForeignKey(Cuenta, related_name='haber', on_delete=models.CASCADE)
    # If 'descripcion_transaccion' is needed, uncomment the following line
    # descripcion_transaccion = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Transacción {self.id_transaccion} - {self.monto_transaccion}"
