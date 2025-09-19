from django.contrib import admin
from .models import PlanPago, Cuota

@admin.register(PlanPago)
class PlanPagoAdmin(admin.ModelAdmin):
    list_display = ["id", "nombre", "carrera", "cohorte", "modalidad", "iEstado"]
    list_filter = ["carrera", "cohorte", "modalidad", "iEstado"]
    search_fields = ["nombre", "carrera"]

@admin.register(Cuota)
class CuotaAdmin(admin.ModelAdmin):
    list_display = ["id", "plan", "numero", "vencimiento", "monto", "iEstado"]
    list_filter = ["plan", "iEstado"]
    search_fields = ["plan__nombre"]
