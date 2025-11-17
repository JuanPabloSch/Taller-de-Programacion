from django.db import models

class PlanPago(models.Model):
    tipo = models.CharField(default="Plan normal", max_length=20)
    nombre = models.CharField(max_length=100)
    carrera = models.CharField(max_length=100)
    cohorte = models.CharField(max_length=10)
    modalidad = models.CharField(max_length=50)
    iEstado = models.BooleanField(default=True)
    estado = models.CharField(
        max_length=1,
        choices=[
            ('A', 'Activo'),
            ('S', 'Suspendido'),
            ('D', 'Desactivado')
        ],
        default='A'
    )

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
    
                                        #regularizaciones (crear)
class Regularizacion(models.Model):
    tipo = models.CharField(default="Regularización", max_length=20)
    nombre = models.CharField(max_length=100)
    CARRERA_CHOICES = (
        ('INICIAL', 'Meestra nivel inicial'),
        ('ASI', 'Analisis de Sistemas'),
        ('INGLES', 'Profesorado de Ingles'),
        ('Psic', 'Psicopedagogia'),
    )
    # El campo se define como un CharField, pero con el argumento 'choices'
    carrera = models.CharField(
        max_length=20,
        choices=CARRERA_CHOICES,
        default='ASI',
        verbose_name='Carrera Seleccionada'
    )
    MODALIDAD_CHOICES = (
        ('PRESENCIAL', 'Presencial'),
        ('VIRTUAL', 'Virtual'),
        ('MIXTA', 'Mixta'),
    )
    modalidad = models.CharField(
        max_length=20,
        choices=MODALIDAD_CHOICES,
        default='PRESENCIAL',
        verbose_name='Modalidad de Cursada'
    )
    cohorte = models.CharField(max_length=15)
    ESTADO_CHOICES = [
        ('A', 'Activa'),
        ('S', 'Suspendida'),
        ('D', 'Desactivada'),
    ]
    estado = models.CharField(
        max_length=1,
        choices=ESTADO_CHOICES,
        default='S'
    )
    def __str__(self):
         return f"{self.nombre} - {self.get_estado_display()}"

                                    #estructura de la regularizacion
class ReglaEstructura(models.Model):
    regularizacion = models.ForeignKey(
        Regularizacion, 
        on_delete=models.CASCADE,
        related_name='reglas_estructura', # Nombre para acceder desde Regularizacion
        verbose_name='Regularización asociada'
    )
                                #Campos de la pestaña "Estructura"
    
    # Origen de la Deuda
    ORIGEN_CHOICES = (
        ('FIJO', 'Monto Fijo'),
        ('TOTAL', 'Total de Deuda'),
    )
    origen_deuda = models.CharField(max_length=10, choices=ORIGEN_CHOICES) 
    valor = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Tasa (se ve como un porcentaje)
    tasa = models.DecimalField(max_digits=5, decimal_places=2, help_text="Tasa en porcentaje (ej. 10.5)")
  
    # Cuotas
    pago_incial = models.DecimalField(max_digits=10, decimal_places=2)
    cantidad_de_cuotas = models.IntegerField(default=1)
    
    FRECUENCIA_CHOICES = (
        ('MENSUAL', 'Mensual'),
        ('BIMESTRAL', 'Bimestral'),
        ('TRIMESTRAL', 'Trimestral'),
        ('SEMESTRAL', 'Semestral'),
    )
    frecuencia_de_pago = models.CharField(max_length=10, choices=FRECUENCIA_CHOICES)
    dia_vencimiento = models.IntegerField(
        verbose_name='Día de Vencimiento',
        help_text='Día del mes (1 al 31) en que vencerá la cuota.',
        # El valor por defecto podría ser 1 (el primer día del mes) o el que decidas.
        default=1, 
        # Asegura que el valor esté presente
        null=False, 
        blank=False
    )
    def __str__(self):
        return f"Estructura para {self.regularizacion.nombre}"
    
                                                        #REGLAS DE MORA 
class ReglaMora(models.Model):
    regularizacion = models.ForeignKey(
        Regularizacion, 
        on_delete=models.CASCADE,
        related_name='reglas_mora',
        verbose_name='Regularización asociada'
    )
    
    # Campo ELIMINADO: Ya no existe el checkbox de control
    # aplica_reglas_mora = models.BooleanField(...) 
    
    TIPO_RECARGO_CHOICES = (
        ('PORCENTUAL', 'Un porcentaje  respecto a la cuota vencida'),
        ('FIJO', 'Monto Fijo de Multa'),
    )
    tipo_de_recargo = models.CharField(
        max_length=10, 
        choices=TIPO_RECARGO_CHOICES,
        # Mantener null=True y blank=True para que sean opcionales
        null=True,     
        blank=True,     
        verbose_name='Tipo de Recargo'
    )
    
    cantidad_recargo = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True,
        blank=True,
        default=0,
        verbose_name='Tasa/Monto de Recargo'
    )

    
    FRECUENCIA_APLICACION_CHOICES = (
        ('UNA_VEZ', 'Una Sola Vez'),
        ('QUINCENAL', 'Cada 15 días'),
        ('DIARIA', 'Diaria'),
    )
    frecuencia_aplicacion = models.CharField(
        max_length=10, 
        choices=FRECUENCIA_APLICACION_CHOICES,
        null=True,
        blank=True, 
        # Mantener null=True y blank=True
            
        verbose_name='Frecuencia de aplicación'
    )
    veces_aplicacion=models.IntegerField(
        default=0,
        verbose_name='Veces de Aplicación',
        help_text='Veces que se aplicará el recargo según la frecuencia seleccionada'
    )
    
    # Días de gracia puede permanecer con default=0 si quieres que siempre tenga un valor
    dias_gracia = models.IntegerField(
        default=3,
        verbose_name='Días de Gracia',
        help_text='Cantidad de días antes de que se aplique recargo post vencimiento'
    )
    
    def __str__(self):
        return f"Reglas de Mora para {self.regularizacion.nombre}"


# Modelo de Cuota para Regularizaciones
class CuotaRegularizacion(models.Model):
    regularizacion = models.ForeignKey(
        Regularizacion,
        on_delete=models.CASCADE,
        related_name='cuotas',
        verbose_name='Regularización asociada'
    )
    numero_cuota = models.IntegerField(verbose_name='Número de Cuota')
    fecha_vencimiento = models.DateField(null=True, blank=True, verbose_name='Fecha de Vencimiento')
    monto_base = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Monto Base')
    monto_interes = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Interés')
    monto_cuota = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Monto de la Cuota')
    monto_mora = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Recargo por Mora')
    ESTADO_CHOICES = (
        ('P', 'Pendiente'),
        ('PA', 'Pagada'),
        ('V', 'Vencida'),
    )
    estado = models.CharField(max_length=2, choices=ESTADO_CHOICES, default='P', verbose_name='Estado')

    class Meta:
        ordering = ['numero_cuota']
        verbose_name = 'Cuota de Regularización'
        verbose_name_plural = 'Cuotas de Regularización'

    def __str__(self):
        return f"Cuota {self.numero_cuota} - {self.regularizacion.nombre}"

# ------------------------------------
# MODELO DE HISTORIAL DE ACCIONES
# ------------------------------------
from django.contrib.auth.models import User

class HistorialAccion(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    accion = models.CharField(max_length=200)
    plan = models.ForeignKey('PlanPago', on_delete=models.SET_NULL, null=True, blank=True)
    descripcion = models.TextField(blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.fecha} - {self.accion}"
