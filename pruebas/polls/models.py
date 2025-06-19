from django.db import models

class Celular(models.Model):
    id_celular = models.IntegerField(primary_key=True)
    marca = models.CharField(max_length=100)
    modelo = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.marca} {self.modelo}"
    class Meta:
        db_table = 'celulares'

class Pedido(models.Model):
    tipo = models.CharField(max_length=50)
    color = models.CharField(max_length=50)
    modelo = models.ForeignKey(Celular, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)
