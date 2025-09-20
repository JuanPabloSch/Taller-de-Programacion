from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import PlanPago, Cuota

# -------------------------------
# Vistas de Planes
# -------------------------------

def planes_list(request):
    return render(request, "planes_list.html")   # ya no usa prefijo

def planes_data(request):
    data = [
        {
            "id": p.id,
            "nombre": p.nombre,
            "carrera": p.carrera,
            "cohorte": p.cohorte,
            "modalidad": p.modalidad,
        }
        for p in PlanPago.objects.filter(iEstado=True)
    ]
    return JsonResponse({"data": data})

@require_POST
def plan_guardar(request):
    datos = request.POST
    plan_id = datos.get("id")

    if plan_id:  # Actualizar plan existente
        try:
            plan = PlanPago.objects.get(pk=plan_id)
            plan.nombre = datos["nombre"]
            plan.carrera = datos["carrera"]
            plan.cohorte = datos["cohorte"]
            plan.modalidad = datos["modalidad"]
            plan.save()
            return JsonResponse({"ok": True, "msg": "Plan actualizado"})
        except PlanPago.DoesNotExist:
            return JsonResponse({"ok": False, "msg": "Plan no encontrado"}, status=404)
    else:  # Crear nuevo plan
        PlanPago.objects.create(
            nombre=datos["nombre"],
            carrera=datos["carrera"],
            cohorte=datos["cohorte"],
            modalidad=datos["modalidad"],
        )
        return JsonResponse({"ok": True, "msg": "Plan creado"})

@require_POST
def plan_borrar(request, pk):
    try:
        plan = PlanPago.objects.get(pk=pk)
        plan.iEstado = False  # borrado lógico
        plan.save()
        return JsonResponse({"ok": True, "msg": "Plan eliminado"})
    except PlanPago.DoesNotExist:
        return JsonResponse({"ok": False, "msg": "Plan no encontrado"}, status=404)

# -------------------------------
# Vistas de Cuotas
# -------------------------------

def cuotas_list(request):
    plans = PlanPago.objects.filter(iEstado=True)  # solo planes activos
    return render(request, "cuotas_list.html", {"plans": plans})   # ya no usa prefijo

def cuotas_data(request):
    data = [
        {
            "id": c.id,
            "plan": c.plan.nombre,
            "numero": c.numero,
            "vencimiento": c.vencimiento.strftime("%Y-%m-%d"),
            "monto": str(c.monto),
        }
        for c in Cuota.objects.filter(iEstado=True)
    ]
    return JsonResponse({"data": data})

@require_POST
def cuota_guardar(request):
    datos = request.POST
    cuota_id = datos.get("id")

    if cuota_id:  # Actualizar
        try:
            cuota = Cuota.objects.get(pk=cuota_id)
            cuota.plan_id = datos["plan"]
            cuota.numero = datos["numero"]
            cuota.vencimiento = datos["vencimiento"]
            cuota.monto = datos["monto"]
            cuota.save()
            return JsonResponse({"ok": True, "msg": "Cuota actualizada"})
        except Cuota.DoesNotExist:
            return JsonResponse({"ok": False, "msg": "Cuota no encontrada"}, status=404)
    else:  # Crear
        Cuota.objects.create(
            plan_id=datos["plan"],
            numero=datos["numero"],
            vencimiento=datos["vencimiento"],
            monto=datos["monto"],
        )
        return JsonResponse({"ok": True, "msg": "Cuota creada"})

@require_POST
def cuota_borrar(request, pk):
    try:
        cuota = Cuota.objects.get(pk=pk)
        cuota.iEstado = False
        cuota.save()
        return JsonResponse({"ok": True, "msg": "Cuota eliminada"})
    except Cuota.DoesNotExist:
        return JsonResponse({"ok": False, "msg": "Cuota no encontrada"}, status=404)

# -------------------------------
# Página de inicio
# -------------------------------

def home(request):
    return render(request, "index.html")
