from django.db import models

class PlanPago(models.Model):
    nombre = models.CharField(max_length=100)
    carrera = models.CharField(max_length=100)
    cohorte = models.CharField(max_length=20)
    modalidad = models.CharField(max_length=50)
    iEstado = models.BooleanField(default=True)  # borrado lógico

    def __str__(self):
        return f"{self.nombre} - {self.carrera} ({self.cohorte})"


class Cuota(models.Model):
    plan = models.ForeignKey(PlanPago, on_delete=models.CASCADE)
    numero = models.IntegerField()
    vencimiento = models.DateField()
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    iEstado = models.BooleanField(default=True)

    def __str__(self):
        return f"Cuota {self.numero} - {self.plan.nombre}"
