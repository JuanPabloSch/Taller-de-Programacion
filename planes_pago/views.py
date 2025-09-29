from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from .models import PlanPago, Cuota
from fpdf import FPDF
from datetime import datetime
import csv
import openpyxl
from openpyxl.utils import get_column_letter
import os


# -------------------------------
# Clase PDF personalizada
# -------------------------------
class PDF(FPDF):
    def header(self):
        logo_path = os.path.join("static", "img", "logo.png")
        if os.path.exists(logo_path):
            self.image(logo_path, 10, 8, 20)  # (x, y, ancho)
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
# CRUD Planes
# -------------------------------
@login_required
def planes_list(request):
    return render(request, "planes_list.html")


@login_required
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
@login_required
def plan_guardar(request):
    datos = request.POST
    plan_id = datos.get("id")

    if plan_id:
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
    else:
        PlanPago.objects.create(
            nombre=datos["nombre"],
            carrera=datos["carrera"],
            cohorte=datos["cohorte"],
            modalidad=datos["modalidad"],
        )
        return JsonResponse({"ok": True, "msg": "Plan creado"})


@require_POST
@login_required
def plan_borrar(request, pk):
    try:
        plan = PlanPago.objects.get(pk=pk)
        plan.iEstado = False
        plan.save()
        return JsonResponse({"ok": True, "msg": "Plan eliminado"})
    except PlanPago.DoesNotExist:
        return JsonResponse({"ok": False, "msg": "Plan no encontrado"}, status=404)


# -------------------------------
# CRUD Cuotas
# -------------------------------
@login_required
def cuotas_list(request):
    plans = PlanPago.objects.filter(iEstado=True)
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
    datos = request.POST
    cuota_id = datos.get("id")

    if cuota_id:
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
    else:
        Cuota.objects.create(
            plan_id=datos["plan"],
            numero=datos["numero"],
            vencimiento=datos["vencimiento"],
            monto=datos["monto"],
        )
        return JsonResponse({"ok": True, "msg": "Cuota creada"})


@require_POST
@login_required
def cuota_borrar(request, pk):
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
    for p in PlanPago.objects.filter(iEstado=True):
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

    for p in PlanPago.objects.filter(iEstado=True):
        writer.writerow([p.nombre, p.carrera, p.cohorte, p.modalidad])

    return response



@login_required
def exportar_planes_excel(request):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Planes de Pago"

    # Estilos
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

    # Cabecera
    headers = ["Nombre", "Carrera", "Cohorte", "Modalidad"]
    ws.append(headers)

    for col, header in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = bold_font
        cell.fill = header_fill
        cell.alignment = center_align
        cell.border = thin_border

    # Datos
    for p in PlanPago.objects.filter(iEstado=True):
        ws.append([p.nombre, p.carrera, p.cohorte, p.modalidad])

    # Ajustar ancho de columnas
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

    # Descargar
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="planes_pago.xlsx"'
    wb.save(response)
    return response



@login_required
def imprimir_planes(request):
    planes = PlanPago.objects.filter(iEstado=True)
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

    pdf_bytes = pdf.output(dest="S")  # 👈 bytes directos
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

    # Cabecera
    headers = ["Plan", "Número", "Vencimiento", "Monto"]
    ws.append(headers)

    for col, header in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = bold_font
        cell.fill = header_fill
        cell.alignment = center_align
        cell.border = thin_border

    # Datos
    for c in Cuota.objects.filter(iEstado=True):
        ws.append([c.plan.nombre, c.numero, c.vencimiento.strftime("%d/%m/%Y"), float(c.monto)])

    # Ajustar ancho de columnas
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

    # Descargar
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
