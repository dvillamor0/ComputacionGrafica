from django.db import models

class Celular(models.Model):
    id_celular = models.IntegerField(primary_key=True)
    marca = models.CharField(max_length=100)
    modelo = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.marca} {self.modelo}"
    class Meta:
        db_table = 'celulares'


class Cliente(models.Model):
    id_cliente = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    correo = models.EmailField(unique=True)
    celular = models.CharField(max_length=20)
    direccion = models.TextField()
    contraseña = models.CharField(max_length=100)  # ¡Veremos seguridad abajo!

    class Meta:
        db_table = 'clientes'  # Usa la tabla existente en PostgreSQL

    def __str__(self):
        return f'{self.nombre} {self.apellido}'

from django.db import models

class Pedido(models.Model):
    id_pedido = models.AutoField(primary_key=True)
    id_cliente = models.IntegerField()
    id_celular = models.IntegerField()
    color = models.CharField(max_length=50)
    aro_dedo = models.BooleanField(default=False)
    fecha = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=15, default='pendiente')
    cantidad = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = 'pedidos'

class Proveedor(models.Model):
    id_proveedor = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    correo = models.EmailField(unique=True)
    celular = models.CharField(max_length=20)
    direccion = models.TextField()

    class Meta:
        db_table = 'proveedores'

    def __str__(self):
        return self.nombre