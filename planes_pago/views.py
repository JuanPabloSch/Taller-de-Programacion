# views.py (fusionado y limpio)
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST, require_http_methods
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from decimal import Decimal, ROUND_HALF_UP
import csv, os, openpyxl
from openpyxl.utils import get_column_letter
from fpdf import FPDF

from .models import PlanPago, Cuota, Regularizacion, ReglaEstructura, ReglaMora
from .forms import (PlanPagoForm, RegularizacionForm,
                    ReglaEstructuraForm, ReglaMoraForm)
from .decorators import group_required, can_delete, can_modify


# -------------------------------
# Clase PDF personalizada
# -------------------------------
class PDF(FPDF):
    def header(self):
        logo_path = os.path.join("static", "img", "logo.png")
        if os.path.exists(logo_path):
            try:
                self.image(logo_path, 10, 8, 20)  # (x, y, ancho)
            except Exception:
                # si hay problemas con la imagen, no rompe el PDF
                pass
        self.set_font("Arial", "B", 14)
        self.cell(0, 10, "ISDM - Sistema de Pagos", border=False, ln=1, align="C")
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 10, f"Página {self.page_no()}/{{nb}}", align="C")


# -------------------------------
# Página de inicio
# -------------------------------
@login_required
def home(request):
    return render(request, "index.html")


# -------------------------------
# CRUD Planes (lista principal)
# -------------------------------
@login_required
def planes_list(request):
    # Instanciar los TRES formularios con prefijos únicos
    regularizacion_form = RegularizacionForm(prefix='regularizacion')
    estructura_form = ReglaEstructuraForm(prefix='estructura')
    mora_form = ReglaMoraForm(prefix='mora')

    context = {
        'regularizacion_form': regularizacion_form,
        'estructura_form': estructura_form,
        'mora_form': mora_form,
    }

    return render(request, "planes_list.html", context)


# views.py

# ... (código previo)

@login_required
def planes_data(request):
    """
    Endpoint JSON para datatables / fetch de planes activos.
    Combina PlanPago y Regularizacion activos.
    """
    
    # 1. Obtener Planes de Pago activos
    planes = PlanPago.objects.filter(estado='A').values(
        'id', 'tipo', 'nombre', 'carrera', 'cohorte', 'modalidad'
    )
    
    # 2. Obtener Regularizaciones activas
    # NOTA: Asumimos que Regularizacion tiene 'nombre', 'carrera', 'cohorte', 'modalidad'.
    # Si no los tiene, usa .annotate() para mapear campos.
    regularizaciones = Regularizacion.objects.filter(estado='A').values(
        'id', 'tipo', 'nombre', 'carrera', 'cohorte', 'modalidad'
    )
    
    # 3. Combinar y formatear
    combined_data = list(planes) + list(regularizaciones)

    data = [
        {
            "id": p['id'],
            # Si el modelo tiene un campo 'tipo', úsalo. Si no, forzamos un valor por defecto.
            "tipo": p.get('tipo', 'plan') if 'cohorte' in p else p.get('tipo', 'regularizacion'), 
            "nombre": p['nombre'],
            "carrera": p['carrera'],
            "cohorte": p['cohorte'],
            "modalidad": p['modalidad'],
        }
        for p in combined_data
    ]
    return JsonResponse({"data": data})

# ... (código posterior)

@require_POST
@login_required
def plan_guardar(request):
    """
    Crear o actualizar plan vía POST (AJAX u ordinario).
    """
    if not can_modify(request.user):
        return JsonResponse({"ok": False, "msg": "No tienes permisos para realizar esta acción"}, status=403)

    datos = request.POST
    plan_id = datos.get("id")

    if plan_id:
        try:
            plan = PlanPago.objects.get(pk=plan_id)
            plan.nombre = datos.get("nombre", plan.nombre)
            plan.carrera = datos.get("carrera", plan.carrera)
            plan.cohorte = datos.get("cohorte", plan.cohorte)
            plan.modalidad = datos.get("modalidad", plan.modalidad)
            plan.save()
            return JsonResponse({"ok": True, "msg": "Plan actualizado"})
        except PlanPago.DoesNotExist:
            return JsonResponse({"ok": False, "msg": "Plan no encontrado"}, status=404)
    else:
        PlanPago.objects.create(
            nombre=datos.get("nombre", ""),
            carrera=datos.get("carrera", ""),
            cohorte=datos.get("cohorte", ""),
            modalidad=datos.get("modalidad", ""),
            estado='S'  # por defecto guardamos como suspendido para revisión del admin
        )
        return JsonResponse({"ok": True, "msg": "Plan creado"})


@require_POST
@login_required
def plan_borrar(request, pk):
    """
    Marcar plan como inactivo (iEstado=False) - borrado lógico.
    """
    if not can_delete(request.user):
        return JsonResponse({"ok": False, "msg": "No tienes permisos para eliminar planes"}, status=403)

    try:
        plan = PlanPago.objects.get(pk=pk)
        plan.iEstado = False
        plan.save()
        return JsonResponse({"ok": True, "msg": "Plan eliminado"})
    except PlanPago.DoesNotExist:
        return JsonResponse({"ok": False, "msg": "Plan no encontrado"}, status=404)


# -------------------------------
# FORMULARIOS DE PLANES (modal AJAX)
# -------------------------------
@login_required
@group_required('Administrador', 'Tesorero')
def plan_crear(request):
    if request.method == "POST":
        form = PlanPagoForm(request.POST)
        if form.is_valid():
            plan = form.save(commit=False)
            # Si el flujo requiere que nuevos planes queden en 'S' (suspendidos) para validacion:
            plan.estado = 'S'
            plan.save()
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({"success": True})
            return redirect("planes_suspendidos")
    else:
        form = PlanPagoForm()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, "planes/plan_form.html", {"form": form})
    return render(request, "planes/plan_form.html", {"form": form})


# Regularizaciones (combinado con reglas)
@require_http_methods(["POST"])
def regularizacion_crear(request):
    if request.method == 'POST':
        regularizacion_form = RegularizacionForm(request.POST, prefix='regularizacion')
        estructura_form = ReglaEstructuraForm(request.POST, prefix='estructura')
        mora_form = ReglaMoraForm(request.POST, prefix='mora')

        if all([regularizacion_form.is_valid(), estructura_form.is_valid(), mora_form.is_valid()]):
            try:
                with transaction.atomic():
                    regularizacion = regularizacion_form.save(commit=False)
                    regularizacion.estado = 'S'  # Se marca como suspendido
                    regularizacion.save()

                    estructura = estructura_form.save(commit=False)
                    estructura.regularizacion = regularizacion
                    estructura.save()

                    mora = mora_form.save(commit=False)
                    mora.regularizacion = regularizacion
                    mora.save()

                    # Guardar las cuotas si fueron enviadas
                    cuotas_json = request.POST.get('cuotas_json')
                    if cuotas_json:
                        import json
                        from .models import CuotaRegularizacion
                        from datetime import datetime
                        try:
                            cuotas_data = json.loads(cuotas_json)
                            for cuota in cuotas_data:
                                # Parsear la fecha de vencimiento
                                fecha_vto = None
                                if cuota.get('vto'):
                                    try:
                                        # Intentar formato DD/MM/YYYY
                                        fecha_vto = datetime.strptime(cuota['vto'], '%d/%m/%Y').date()
                                    except:
                                        pass

                                CuotaRegularizacion.objects.create(
                                    regularizacion=regularizacion,
                                    numero_cuota=cuota.get('nro', 0),
                                    fecha_vencimiento=fecha_vto,
                                    monto_base=cuota.get('base', 0),
                                    monto_interes=cuota.get('interes', 0),
                                    monto_cuota=cuota.get('monto_total', 0),
                                    monto_mora=cuota.get('mora', 0),
                                    estado='P'  # Pendiente por defecto
                                )
                        except Exception as e:
                            # Si hay error al guardar cuotas, log pero no falla la transacción
                            print(f"Error al guardar cuotas: {e}")

                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'success': True, 'message': 'Regularización creada correctamente.'})

                messages.success(request, 'La regularización fue creada exitosamente.')
                return redirect('planes_suspendidos')

            except Exception as e:
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': str(e)}, status=500)
                messages.error(request, f'Ocurrió un error al guardar: {e}')

        else:
            # Responder errores (AJAX o normal)
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'errors': {
                        'regularizacion': regularizacion_form.errors,
                        'estructura': estructura_form.errors,
                        'mora': mora_form.errors
                    }
                }, status=400)

            messages.error(request, 'Hay errores en los formularios.')
            # No guardamos parcialmente en este flujo; redirigimos
    return redirect('planes_list')


@login_required
@group_required('Administrador', 'Tesorero')
def plan_editar(request, pk):
    plan = get_object_or_404(PlanPago, pk=pk)
    if request.method == "POST":
        form = PlanPagoForm(request.POST, instance=plan)
        if form.is_valid():
            form.save()
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({"success": True})
            return redirect("planes_list")
    else:
        form = PlanPagoForm(instance=plan)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, "planes/plan_form.html", {"form": form})
    return render(request, "planes/plan_form.html", {"form": form})


@login_required
def plan_clonar(request, pk):
    original = get_object_or_404(PlanPago, pk=pk)
    if request.method == "POST":
        form = PlanPagoForm(request.POST)
        if form.is_valid():
            form.save()
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({"success": True})
            return redirect("planes_list")
    else:
        data_inicial = {
            "nombre": f"{original.nombre} (Copia)",
            "carrera": original.carrera,
            "cohorte": original.cohorte,
            "modalidad": original.modalidad,
            "iEstado": True,
            "estado": "S",
        }
        form = PlanPagoForm(initial=data_inicial)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, "planes/plan_form.html", {"form": form})
    return render(request, "planes/plan_form.html", {"form": form})


# -------------------------------
# CRUD Cuotas
# -------------------------------
@login_required
def cuotas_list(request):
    plans = PlanPago.objects.filter(estado='A')  # solo planes activos
    return render(request, "cuotas_list.html", {"plans": plans})


@login_required
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
@login_required
def cuota_guardar(request):
    if not can_modify(request.user):
        return JsonResponse({"ok": False, "msg": "No tienes permisos para realizar esta acción"}, status=403)

    datos = request.POST
    cuota_id = datos.get("id")

    if cuota_id:
        try:
            cuota = Cuota.objects.get(pk=cuota_id)
            cuota.plan_id = datos.get("plan", cuota.plan_id)
            cuota.numero = datos.get("numero", cuota.numero)
            cuota.vencimiento = datos.get("vencimiento", cuota.vencimiento)
            cuota.monto = datos.get("monto", cuota.monto)
            cuota.save()
            return JsonResponse({"ok": True, "msg": "Cuota actualizada"})
        except Cuota.DoesNotExist:
            return JsonResponse({"ok": False, "msg": "Cuota no encontrada"}, status=404)
    else:
        Cuota.objects.create(
            plan_id=datos.get("plan"),
            numero=datos.get("numero"),
            vencimiento=datos.get("vencimiento"),
            monto=datos.get("monto"),
        )
        return JsonResponse({"ok": True, "msg": "Cuota creada"})


@require_POST
@login_required
def cuota_borrar(request, pk):
    if not can_delete(request.user):
        return JsonResponse({"ok": False, "msg": "No tienes permisos para eliminar cuotas"}, status=403)

    try:
        cuota = Cuota.objects.get(pk=pk)
        cuota.iEstado = False
        cuota.save()
        return JsonResponse({"ok": True, "msg": "Cuota eliminada"})
    except Cuota.DoesNotExist:
        return JsonResponse({"ok": False, "msg": "Cuota no encontrada"}, status=404)


# -------------------------------
# EXPORTAR PLANES
# -------------------------------
@login_required
def exportar_planes_pdf(request):
    pdf = PDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
    usuario = request.user.username
    pdf.cell(0, 10, f"Listado de Planes de Pago", ln=True, align="C")
    pdf.set_font("Arial", "I", 10)
    pdf.cell(0, 10, f"Generado por: {usuario} - Fecha: {fecha}", ln=True, align="C")
    pdf.ln(10)

    pdf.set_font("Arial", "B", 10)
    pdf.cell(40, 10, "Nombre", 1, 0, "C")
    pdf.cell(40, 10, "Carrera", 1, 0, "C")
    pdf.cell(40, 10, "Cohorte", 1, 0, "C")
    pdf.cell(40, 10, "Modalidad", 1, 1, "C")

    pdf.set_font("Arial", size=10)
    for p in PlanPago.objects.filter(estado='A'):
        pdf.cell(40, 10, str(p.nombre), 1)
        pdf.cell(40, 10, str(p.carrera), 1)
        pdf.cell(40, 10, str(p.cohorte), 1)
        pdf.cell(40, 10, str(p.modalidad), 1)
        pdf.ln()

    pdf_bytes = pdf.output(dest="S")
    response = HttpResponse(bytes(pdf_bytes), content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="planes_pago.pdf"'
    return response


@login_required
def exportar_planes_csv(request):
    response = HttpResponse(content_type="text/csv; charset=utf-8-sig")
    response["Content-Disposition"] = 'attachment; filename="planes_pago.csv"'

    writer = csv.writer(response, delimiter=";")
    writer.writerow(["Nombre del Plan", "Carrera", "Cohorte", "Modalidad"])

    for p in PlanPago.objects.filter(estado='A'):
        writer.writerow([p.nombre, p.carrera, p.cohorte, p.modalidad])

    return response


@login_required
def exportar_planes_excel(request):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Planes de Pago"

    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

    bold_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="4F81BD", end_color="4F81BD", fill_type="solid")
    center_align = Alignment(horizontal="center", vertical="center")
    thin_border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin"),
    )

    headers = ["Nombre", "Carrera", "Cohorte", "Modalidad"]
    ws.append(headers)

    for col, header in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = bold_font
        cell.fill = header_fill
        cell.alignment = center_align
        cell.border = thin_border

    for p in PlanPago.objects.filter(estado='A'):
        ws.append([p.nombre, p.carrera, p.cohorte, p.modalidad])

    for col in ws.columns:
        max_length = 0
        col_letter = col[0].column_letter
        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = (max_length + 2)
        ws.column_dimensions[col_letter].width = adjusted_width

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="planes_pago.xlsx"'
    wb.save(response)
    return response


@login_required
def imprimir_planes(request):
    planes = PlanPago.objects.filter(estado='A')
    return render(request, "imprimir_planes.html", {"planes": planes})


# -------------------------------
# EXPORTAR CUOTAS
# -------------------------------
@login_required
def exportar_cuotas_pdf(request):
    pdf = PDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
    usuario = request.user.username
    pdf.cell(0, 10, "Listado de Cuotas", ln=True, align="C")
    pdf.set_font("Arial", "I", 10)
    pdf.cell(0, 10, f"Generado por: {usuario} - Fecha: {fecha}", ln=True, align="C")
    pdf.ln(10)

    pdf.set_font("Arial", "B", 10)
    pdf.cell(30, 10, "Plan", 1, 0, "C")
    pdf.cell(30, 10, "Número", 1, 0, "C")
    pdf.cell(40, 10, "Vencimiento", 1, 0, "C")
    pdf.cell(40, 10, "Monto", 1, 1, "C")

    pdf.set_font("Arial", size=10)
    for c in Cuota.objects.filter(iEstado=True):
        pdf.cell(30, 10, str(c.plan.nombre), 1)
        pdf.cell(30, 10, str(c.numero), 1)
        pdf.cell(40, 10, c.vencimiento.strftime("%Y-%m-%d"), 1)
        pdf.cell(40, 10, str(c.monto), 1)
        pdf.ln()

    pdf_bytes = pdf.output(dest="S")
    response = HttpResponse(bytes(pdf_bytes), content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="cuotas.pdf"'
    return response


@login_required
def exportar_cuotas_csv(request):
    response = HttpResponse(content_type="text/csv; charset=utf-8-sig")
    response["Content-Disposition"] = 'attachment; filename="cuotas.csv"'

    writer = csv.writer(response, delimiter=";")
    writer.writerow(["Plan", "Número de Cuota", "Fecha de Vencimiento", "Monto ($)"])

    for c in Cuota.objects.filter(iEstado=True):
        writer.writerow([c.plan.nombre, c.numero, c.vencimiento.strftime("%d/%m/%Y"), c.monto])

    return response


@login_required
def exportar_cuotas_excel(request):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Cuotas"

    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

    bold_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="9BBB59", end_color="9BBB59", fill_type="solid")
    center_align = Alignment(horizontal="center", vertical="center")
    thin_border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin"),
    )

    headers = ["Plan", "Número", "Vencimiento", "Monto"]
    ws.append(headers)

    for col, header in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = bold_font
        cell.fill = header_fill
        cell.alignment = center_align
        cell.border = thin_border

    for c in Cuota.objects.filter(iEstado=True):
        ws.append([c.plan.nombre, c.numero, c.vencimiento.strftime("%d/%m/%Y"), float(c.monto)])

    for col in ws.columns:
        max_length = 0
        col_letter = col[0].column_letter
        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        ws.column_dimensions[col_letter].width = max_length + 2

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="cuotas.xlsx"'
    wb.save(response)
    return response


@login_required
def imprimir_cuotas(request):
    cuotas = Cuota.objects.filter(iEstado=True)
    return render(request, "imprimir_cuotas.html", {"cuotas": cuotas})


# -------------------------------
# Planes suspendidos
# -------------------------------
@login_required
def planes_suspendidos(request):

    # --- Planes ---
    suspendidos_planes = PlanPago.objects.filter(estado='S')
    desactivados_planes = PlanPago.objects.filter(estado='D')

    # --- Regularizaciones ---
    suspendidos_regularizaciones = Regularizacion.objects.filter(estado='S')
    desactivados_regularizaciones = Regularizacion.objects.filter(estado='D')

    # --- Marcar cada objeto con su tipo ---
    for p in suspendidos_planes:
        p.tipo_backend = "plan"
    for p in desactivados_planes:
        p.tipo_backend = "plan"

    for r in suspendidos_regularizaciones:
        r.tipo_backend = "regularizacion"
    for r in desactivados_regularizaciones:
        r.tipo_backend = "regularizacion"

    # --- Combinar ---
    suspendidos = list(suspendidos_planes) + list(suspendidos_regularizaciones)
    desactivados = list(desactivados_planes) + list(desactivados_regularizaciones)

    return render(request, "planes_suspendidos.html", {
        "suspendidos": suspendidos,
        "desactivados": desactivados
    })


@login_required
def plan_ver_detalle(request, pk):
    """
    Vista para ver los detalles de un plan o regularización en formato JSON
    """
    tipo = request.GET.get('tipo', 'plan')

    try:
        if tipo == 'regularizacion':
            obj = Regularizacion.objects.get(pk=pk)
            plan_data = {
                'id': obj.id,
                'nombre': obj.nombre,
                'carrera': obj.carrera,
                'cohorte': obj.cohorte,
                'modalidad': obj.modalidad,
                'estado': obj.estado,
                'fecha_creacion': obj.fecha_creacion.strftime('%d/%m/%Y %H:%M') if hasattr(obj, 'fecha_creacion') and obj.fecha_creacion else 'N/A',
            }

            # Buscar estructura asociada
            try:
                estructura = ReglaEstructura.objects.filter(regularizacion=obj).first()
                if estructura:
                    plan_data['estructura'] = {
                        'origen_deuda': estructura.get_origen_deuda_display() if estructura.origen_deuda else 'N/A',
                        'valor': str(estructura.valor),
                        'tasa': str(estructura.tasa),
                        'pago_inicial': str(estructura.pago_incial),
                        'cantidad_cuotas': estructura.cantidad_de_cuotas,
                        'frecuencia': estructura.get_frecuencia_de_pago_display(),
                        'dia_vencimiento': estructura.dia_vencimiento,
                    }
            except:
                pass

            # Buscar reglas de mora asociadas
            try:
                mora = ReglaMora.objects.filter(regularizacion=obj).first()
                if mora:
                    plan_data['mora'] = {
                        'tipo': mora.get_tipo_de_recargo_display() if mora.tipo_de_recargo else 'N/A',
                        'cantidad': str(mora.cantidad_recargo) if mora.cantidad_recargo else 'N/A',
                        'frecuencia': mora.get_frecuencia_aplicacion_display() if mora.frecuencia_aplicacion else 'N/A',
                        'dias_gracia': mora.dias_gracia if mora.dias_gracia else 0,
                        'veces_aplicacion': mora.veces_aplicacion if mora.veces_aplicacion else 0,
                    }
            except:
                pass

            # Buscar cuotas asociadas
            try:
                from .models import CuotaRegularizacion
                cuotas = CuotaRegularizacion.objects.filter(regularizacion=obj).order_by('numero_cuota')
                if cuotas.exists():
                    plan_data['cuotas'] = [
                        {
                            'numero': c.numero_cuota,
                            'fecha_vencimiento': c.fecha_vencimiento.strftime('%d/%m/%Y') if c.fecha_vencimiento else 'N/A',
                            'base': str(c.monto_base),
                            'interes': str(c.monto_interes),
                            'monto': str(c.monto_cuota),
                            'mora': str(c.monto_mora),
                            'estado': c.get_estado_display(),
                        }
                        for c in cuotas
                    ]
            except Exception as e:
                print(f"Error al obtener cuotas: {e}")

        else:  # plan
            obj = PlanPago.objects.get(pk=pk)
            plan_data = {
                'id': obj.id,
                'nombre': obj.nombre,
                'carrera': obj.carrera,
                'cohorte': obj.cohorte,
                'modalidad': obj.modalidad,
                'estado': obj.estado,
                'fecha_creacion': obj.fecha_creacion.strftime('%d/%m/%Y %H:%M') if hasattr(obj, 'fecha_creacion') and obj.fecha_creacion else 'N/A',
            }

        return JsonResponse({'ok': True, 'plan': plan_data})

    except (PlanPago.DoesNotExist, Regularizacion.DoesNotExist):
        return JsonResponse({'ok': False, 'msg': f'{tipo.capitalize()} no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'ok': False, 'msg': f'Error al obtener detalles: {str(e)}'}, status=500)


@require_POST
@login_required
def plan_suspendido(request, pk):
    """
    Acción que marca iEstado=False (uso legacy). Dejéla si alguna parte del sistema la llama.
    """
    try:
        plan = PlanPago.objects.get(pk=pk)
        plan.iEstado = False
        plan.save()
        return JsonResponse({"ok": True, "msg": "Plan suspendido correctamente"})
    except PlanPago.DoesNotExist:
        return JsonResponse({"ok": False, "msg": "Plan no encontrado"}, status=404)


# -------------------------------
# DESACTIVAR / REACTIVAR PLANES
# -------------------------------

@require_POST
@login_required
def plan_suspender(request, pk):
    if not can_delete(request.user):
        return JsonResponse({"ok": False, "msg": "No tienes permisos para suspender planes"}, status=403)

    # 1. Intentar suspender un PlanPago
    try:
        plan = PlanPago.objects.get(pk=pk)
        plan.estado = 'S'
        plan.iEstado = False
        plan.save()
        return JsonResponse({"ok": True, "msg": "Plan suspendido correctamente"})
    except PlanPago.DoesNotExist:
        pass

    # 2. Intentar suspender una Regularización
    try:
        reg = Regularizacion.objects.get(pk=pk)
        reg.estado = 'S'
        reg.save()
        return JsonResponse({"ok": True, "msg": "Regularización suspendida correctamente"})
    except Regularizacion.DoesNotExist:
        pass

    # 3. Si no existe en ninguna tabla
    return JsonResponse({"ok": False, "msg": "Objeto no encontrado"}, status=404)


@require_POST
@login_required
def desactivar_objeto(request):
    tipo = request.POST.get("tipo")
    pk = request.POST.get("id")

    print("DEBUG tipo recibido:", repr(tipo))
    print("DEBUG id recibido:", repr(pk))

    if tipo not in ["plan", "regularizacion"]:
        return JsonResponse({"ok": False, "msg": f"Tipo inválido: {tipo}"}, status=400)

    Model = PlanPago if tipo == "plan" else Regularizacion

    try:
        obj = Model.objects.get(pk=pk)
        obj.estado = "D"
        obj.save()
        return JsonResponse({"ok": True, "msg": f"{tipo.capitalize()} desactivado correctamente"})
    
    except Model.DoesNotExist:
        return JsonResponse({"ok": False, "msg": "Objeto no encontrado"}, status=404)

    except Exception as e:
        # CAPTURA CUALQUIER OTRO ERROR 
        print("ERROR inesperado:", e)
        return JsonResponse({"ok": False, "msg": f"Error inesperado: {str(e)}"}, status=500)

# @require_POST -------ESTE ES EL REACTIVAR VIEJO, LO DEJO COMENTADO POR LAS DUDAS-------
# @login_required
# def plan_reactivar(request, pk):
#     """
#     Reactiva un plan desactivado o suspendido (estado='A' y iEstado=True).
#     """
#     if not can_delete(request.user):
#         return JsonResponse({"ok": False, "msg": "No tienes permisos para reactivar planes"}, status=403)

#     try:
#         plan = PlanPago.objects.get(pk=pk)
#         plan.estado = 'A'
#         plan.iEstado = True
#         plan.save()
#         return JsonResponse({"ok": True, "msg": "Plan reactivado correctamente"})
#     except PlanPago.DoesNotExist:
#         return JsonResponse({"ok": False, "msg": "Plan no encontrado"}, status=404)
@require_POST
@login_required
def reactivar_objeto(request):
    tipo = request.POST.get("tipo")
    pk = request.POST.get("id")

    if tipo not in ["plan", "regularizacion"]:
        return JsonResponse({"ok": False, "msg": "Tipo inválido"}, status=400)

    Model = PlanPago if tipo == "plan" else Regularizacion

    try:
        obj = Model.objects.get(pk=pk)
        obj.estado = "A"
        obj.save()
        return JsonResponse({"ok": True, "msg": f"{tipo.capitalize()} reactivado correctamente"})
    except Model.DoesNotExist:
        return JsonResponse({"ok": False, "msg": "Objeto no encontrado"}, status=404)

@login_required
def historial(request):
    return render(request, "historial.html")


# -------------------------------
# Gestión de Usuarios y Roles
# -------------------------------
@login_required
@group_required('Administrador')
def usuarios_list(request):
    """Vista principal de gestión de usuarios (solo para administradores)"""
    from django.contrib.auth.models import User, Group

    return render(request, "usuarios_list.html")


@login_required
@group_required('Administrador')
def usuarios_data(request):
    """Endpoint JSON para datatables de usuarios"""
    from django.contrib.auth.models import User

    usuarios = User.objects.all().prefetch_related('groups')

    data = []
    for user in usuarios:
        grupos_list = list(user.groups.all())
        grupos_nombres = ", ".join([g.name for g in grupos_list]) or "Sin rol"
        grupo_id = grupos_list[0].id if grupos_list else None

        data.append({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "is_active": user.is_active,
            "grupos": grupos_nombres,
            "grupo_id": grupo_id,
        })

    return JsonResponse({"data": data})


@login_required
@group_required('Administrador')
def grupos_data(request):
    """Endpoint JSON para obtener grupos/roles disponibles"""
    from django.contrib.auth.models import Group

    print("=== DEBUG grupos_data ===")
    print(f"Usuario: {request.user.username}")
    print(f"Es superuser: {request.user.is_superuser}")
    print(f"Grupos del usuario: {list(request.user.groups.values_list('name', flat=True))}")

    grupos = Group.objects.all().values('id', 'name')
    grupos_list = list(grupos)

    print(f"Grupos disponibles en DB: {grupos_list}")
    print(f"Cantidad de grupos: {len(grupos_list)}")

    return JsonResponse({"grupos": grupos_list})


@require_POST
@login_required
@group_required('Administrador')
def usuario_crear(request):
    """Crear nuevo usuario con rol asignado"""
    from django.contrib.auth.models import User, Group

    try:
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        password = request.POST.get('password', '').strip()
        password_confirm = request.POST.get('password_confirm', '').strip()
        grupo_id = request.POST.get('grupo')

        # Validaciones
        if not username:
            return JsonResponse({"ok": False, "msg": "El nombre de usuario es obligatorio"}, status=400)

        if User.objects.filter(username=username).exists():
            return JsonResponse({"ok": False, "msg": "El nombre de usuario ya existe"}, status=400)

        if email and User.objects.filter(email=email).exists():
            return JsonResponse({"ok": False, "msg": "El email ya está registrado"}, status=400)

        if not password:
            return JsonResponse({"ok": False, "msg": "La contraseña es obligatoria"}, status=400)

        if password != password_confirm:
            return JsonResponse({"ok": False, "msg": "Las contraseñas no coinciden"}, status=400)

        if len(password) < 6:
            return JsonResponse({"ok": False, "msg": "La contraseña debe tener al menos 6 caracteres"}, status=400)

        # Crear usuario
        with transaction.atomic():
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )

            # Asignar grupo/rol si fue seleccionado
            if grupo_id:
                try:
                    grupo = Group.objects.get(id=grupo_id)
                    user.groups.add(grupo)
                except Group.DoesNotExist:
                    pass

        return JsonResponse({
            "ok": True,
            "msg": f"Usuario '{username}' creado correctamente"
        })

    except Exception as e:
        return JsonResponse({
            "ok": False,
            "msg": f"Error al crear usuario: {str(e)}"
        }, status=500)


@require_POST
@login_required
@group_required('Administrador')
def usuario_editar(request, pk):
    """Editar usuario existente"""
    from django.contrib.auth.models import User, Group

    try:
        user = get_object_or_404(User, pk=pk)

        email = request.POST.get('email', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        is_active = request.POST.get('is_active') == 'true'
        grupo_id = request.POST.get('grupo')

        # Validar email único (excepto el actual)
        if email and User.objects.filter(email=email).exclude(pk=pk).exists():
            return JsonResponse({"ok": False, "msg": "El email ya está registrado"}, status=400)

        # Actualizar datos
        with transaction.atomic():
            user.email = email
            user.first_name = first_name
            user.last_name = last_name
            user.is_active = is_active
            user.save()

            # Actualizar grupo
            user.groups.clear()
            if grupo_id:
                try:
                    grupo = Group.objects.get(id=grupo_id)
                    user.groups.add(grupo)
                except Group.DoesNotExist:
                    pass

        return JsonResponse({
            "ok": True,
            "msg": f"Usuario '{user.username}' actualizado correctamente"
        })

    except Exception as e:
        return JsonResponse({
            "ok": False,
            "msg": f"Error al actualizar usuario: {str(e)}"
        }, status=500)


@require_POST
@login_required
@group_required('Administrador')
def usuario_eliminar(request, pk):
    """Desactivar usuario (no se elimina físicamente)"""
    from django.contrib.auth.models import User

    try:
        user = get_object_or_404(User, pk=pk)

        # No permitir desactivar el propio usuario
        if user.id == request.user.id:
            return JsonResponse({
                "ok": False,
                "msg": "No puedes desactivar tu propio usuario"
            }, status=400)

        user.is_active = False
        user.save()

        return JsonResponse({
            "ok": True,
            "msg": f"Usuario '{user.username}' desactivado correctamente"
        })

    except Exception as e:
        return JsonResponse({
            "ok": False,
            "msg": f"Error al desactivar usuario: {str(e)}"
        }, status=500)
