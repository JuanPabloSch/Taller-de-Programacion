from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from .models import PlanPago, Cuota, Regularizacion, ReglaEstructura, ReglaMora
from fpdf import FPDF
from datetime import datetime
from .forms import PlanPagoForm
from .forms import RegularizacionForm, ReglaEstructuraForm, ReglaMoraForm
import csv
import openpyxl
from django.db import transaction
from openpyxl.utils import get_column_letter
import os
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from decimal import Decimal, ROUND_HALF_UP
from datetime import date, timedelta

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
    
    # Instanciar los TRES formularios con prefijos únicos
    # (El prefijo es opcional, pero ALTAMENTE recomendado)
    regularizacion_form = RegularizacionForm(prefix='regularizacion') 
    estructura_form = ReglaEstructuraForm(prefix='estructura') 
    mora_form = ReglaMoraForm(prefix='mora') # <-- ¡Añadido el formulario de Mora!
    
    # Instancia de los planes existentes (asumiendo que los listaras)
    # planes = PlanPago.objects.all() 
    
    # Pasar los TRES formularios al contexto
    context = {
        # 'planes': planes, # Si los estás listando
        'regularizacion_form': regularizacion_form,
        'estructura_form': estructura_form,
        'mora_form': mora_form, # <-- Añadido al contexto
    }
    
    return render(request, "planes_list.html", context)



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
# FORMULARIOS DE PLANES (páginas separadas)
# -------------------------------
from .forms import PlanPagoForm  # asegúrate de tener esto entre los imports

# -------------------------------
# FORMULARIOS DE PLANES (modal AJAX)
# -------------------------------
@login_required
def plan_crear(request):
    if request.method == "POST":
        form = PlanPagoForm(request.POST)
        if form.is_valid():
            form.save()
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({"success": True})
            return redirect("planes_list")
    else:
        form = PlanPagoForm()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, "planes/plan_form.html", {"form": form})
    return render(request, "planes/plan_form.html", {"form": form})


                                                    #regularizaciones
@require_http_methods(["POST"])
def regularizacion_crear(request):
    # 1. Instanciar los formularios con los datos POST
    regularizacion_form = RegularizacionForm(request.POST, prefix='regularizacion')
    estructura_form = ReglaEstructuraForm(request.POST, prefix='estructura')
    mora_form = ReglaMoraForm(request.POST, prefix='mora')

    # 2. Validar todos los formularios
    if regularizacion_form.is_valid() and estructura_form.is_valid() and mora_form.is_valid():
        try:
            # Usar transaction.atomic() asegura que si falla el guardado de un formulario, 
            # todos los cambios se revierten y no se guarda nada incompleto.
            with transaction.atomic():
                # A. Guardar el formulario padre (Regularizacion)
                regularizacion_instance = regularizacion_form.save()

                # B. Guardar los formularios hijos, enlazándolos a la instancia padre.
                # Nota: Necesitas el campo ForeignKey (regularizacion) en ReglaEstructura y ReglaMora.

                # Guardar Estructura
                estructura_instance = estructura_form.save(commit=False)
                estructura_instance.regularizacion = regularizacion_instance
                estructura_instance.save()
                
                # Guardar Mora
                mora_instance = mora_form.save(commit=False)
                mora_instance.regularizacion = regularizacion_instance
                mora_instance.save()

            messages.success(request, 'La regularización fue creada exitosamente.')
            return redirect('nombre_de_la_lista_de_planes') # Redirige al listado

        except Exception as e:
            messages.error(request, f'Ocurrió un error al guardar: {e}')
            # Si hay error, necesitamos volver a mostrar el modal con los datos y errores.
            
    # Si la validación falla (o si hubo un error al guardar)
    # Debes renderizar la plantilla de nuevo, pasando todos los formularios con sus errores.
    # Nota: Si esta vista es solo POST, la redirección es más limpia. Si manejas GET aquí, 
    # la lógica se vuelve más compleja. Por simplicidad, asumo que fallas y re-renderizas.
    
    # Aquí deberías tener una función que muestre el modal de nuevo, con los formularios
    # que contienen los errores de validación.

    # Esto es una simplificación; la lógica real de cómo volver a mostrar el modal 
    # en la página de listado depende de cómo manejas el GET y el POST en tu vista principal.

    # Por ahora, volvamos al listado (el usuario verá el mensaje de error si falla el guardado)
    return redirect('nombre_de_la_lista_de_planes') 

                                #calculo visualizacion
@require_http_methods(["POST"])
def regla_estructura_calculos(request):
    # Usamos el prefijo 'estructura' para recibir solo los datos relevantes
    estructura_form = ReglaEstructuraForm(request.POST, prefix='estructura') 
    
    if estructura_form.is_valid():
        datos = estructura_form.cleaned_data
        
        try:
            # Llama a tu función de cálculo (PENDIENTE DE IMPLEMENTAR)
            plan_pagos = generar_plan_regularizacion(datos) 
            
            # Devuelve el plan de pagos en formato JSON
            return JsonResponse({
                'success': True,
                'plan_pagos': plan_pagos # Lista de diccionarios (cuotas)
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Error al calcular: {e}'}, status=400)
    
    # Si falla la validación del formulario de Estructura
    else:
        return JsonResponse({'success': False, 'errors': estructura_form.errors}, status=400)
@require_http_methods(["POST"])
def regla_estructura_calculos(request):
    # ... (código para instanciar y validar estructura_form) ...
    estructura_form = ReglaEstructuraForm(request.POST, prefix='estructura') 
    
    if estructura_form.is_valid():
        datos = estructura_form.cleaned_data
        
        try:
            # Llama a la función de cálculo con los datos limpios
            plan_pagos = generar_plan_pagos(datos) 
            
            return JsonResponse({
                'success': True,
                'plan_pagos': plan_pagos 
            })
            
        except Exception as e:
            # Captura errores como división por cero o datos inválidos
            return JsonResponse({'success': False, 'message': f'Error al calcular: {e}'}, status=400)
    
    else:
        # Devuelve errores de validación
        return JsonResponse({'success': False, 'errors': estructura_form.errors}, status=400)


# ----------------------------------------------------------------------
# LÓGICA DE CÁLCULO DE AMORTIZACIÓN
# ----------------------------------------------------------------------

def generar_plan_pagos(datos):
    # 1. Extracción y Conversión de Parámetros
    
    # Usamos Decimal para evitar errores de coma flotante en montos monetarios
    monto_capital = datos.get('valor', Decimal(0)) - datos.get('pago_incial', Decimal(0))
    tasa_anual = datos.get('tasa', Decimal(0)) # Tasa porcentual, ej. 12
    cantidad_cuotas = datos.get('cantidad_de_cuotas', 1)
    frecuencia_pago = datos.get('frecuencia_de_pago') # Ej. 'MENSUAL'
    dia_vencimiento = datos.get('dia_vencimiento') # El día del mes de vencimiento
    
    # 2. Conversión de Tasa y Frecuencia
    
    # Convertir la tasa anual (ej. 12%) a una tasa por período (mensual, quincenal, etc.)
    # tasa_periodica (ej. 0.01 para 1% mensual)
    # Asumimos una capitalización simple mensual (12 períodos) para fines de ejemplo.
    if tasa_anual > 0 and cantidad_cuotas > 0:
        # Tasa nominal (ej. 0.12) / Frecuencia (ej. 12 meses)
        tasa_mensual_decimal = (tasa_anual / Decimal(100)) / Decimal(12)
        
        # Ajustar la tasa según la frecuencia de pago si es necesario
        # Esto es muy específico de cada cálculo. Aquí usamos la mensual como base.
        if frecuencia_pago == 'MENSUAL':
             tasa_aplicable = tasa_mensual_decimal
        elif frecuencia_pago == 'QUINCENAL':
             tasa_aplicable = tasa_mensual_decimal / Decimal(2) # Simplificación
        # ... añadir otras frecuencias ...
        else:
            tasa_aplicable = tasa_mensual_decimal # Usar mensual si no está definida
            
    else:
        tasa_aplicable = Decimal(0)
        
    # 3. Cálculo de Cuota Fija (Método Francés/Amortización Fija)
    # Fórmula: Cuota = Capital * [ i / (1 - (1 + i)^-n) ]
    
    cuotas = []
    capital_pendiente = monto_capital
    
    if cantidad_cuotas > 0 and capital_pendiente > 0:
        if tasa_aplicable > 0:
            # Denominador de la fórmula: 1 - (1 + i)^-n
            denominador = Decimal(1) - (Decimal(1) + tasa_aplicable)**(-cantidad_cuotas)
            if denominador == 0:
                raise ValueError("No se puede calcular la cuota (denominador cero).")
                
            cuota_fija = capital_pendiente * (tasa_aplicable / denominador)
            
        else:
            # Sin interés (cuota es solo capital)
            cuota_fija = capital_pendiente / cantidad_cuotas

        # 4. Cálculo de Fechas de Vencimiento
        # Usaremos el primer día hábil del próximo mes si no se especifica una fecha de inicio
        fecha_actual = date.today()
        # Puedes añadir lógica aquí para definir la fecha inicial (ej. hoy + 30 días)
        
        # Iterar para generar cada cuota
        for i in range(1, cantidad_cuotas + 1):
            
            # Cálculo de interés y capital
            interes = capital_pendiente * tasa_aplicable
            capital = cuota_fija - interes
            
            # Ajuste de la última cuota para evitar residuos por redondeo
            if i == cantidad_cuotas:
                capital = capital_pendiente
                interes = cuota_fija - capital # Recalcula el interés con el capital ajustado
                monto_cuota = capital + interes
            else:
                monto_cuota = cuota_fija
            
            # Cálculo de la próxima fecha de vencimiento (simplificación: +30 días)
            # NOTA: La lógica de fechas puede ser compleja por meses de 30/31 días.
            # Aquí se requiere una librería como dateutil para un cálculo preciso de meses.
            fecha_vencimiento = fecha_actual + timedelta(days=30 * i)
            
            # 5. Agregar la cuota al plan
            cuotas.append({
                'vencimiento': fecha_vencimiento.strftime('%Y-%m-%d'),
                'monto_cuota': monto_cuota.quantize(Decimal('.01'), rounding=ROUND_HALF_UP),
                'capital': capital.quantize(Decimal('.01'), rounding=ROUND_HALF_UP),
                'interes': interes.quantize(Decimal('.01'), rounding=ROUND_HALF_UP),
            })
            
            # Actualizar el capital pendiente
            capital_pendiente -= capital
            
    return cuotas
# --- FUNCIÓN PENDIENTE ---
def generar_plan_regularizacion(datos):
    """Aquí va la lógica para calcular la amortización (tasa, cuotas, fechas)."""
    # Ejemplo de un resultado esperado (DEBES REEMPLAZAR ESTO CON TU CÁLCULO)
    return [
        {'vencimiento': '2025-12-10', 'monto_cuota': 1050.00, 'capital': 1000.00, 'interes': 50.00},
        # ... más cuotas
    ]


@login_required
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

# Planes suspendidos
@login_required
def planes_suspendidos(request):
    suspendidos = PlanPago.objects.filter(iEstado=False)
    desactivados = []  # Más adelante los filtramos distinto
    return render(request, "planes_suspendidos.html", {
        "suspendidos": suspendidos,
        "desactivados": desactivados
    })
    
    # Suspender plan (desde la vista principal)
# Suspender plan (desde la vista principal)
@require_POST
@login_required
def plan_suspendido(request, pk):
    try:
        plan = PlanPago.objects.get(pk=pk)
        plan.iEstado = False  # Marcamos el plan como suspendido
        plan.save()
        return JsonResponse({"ok": True, "msg": "Plan suspendido correctamente"})
    except PlanPago.DoesNotExist:
        return JsonResponse({"ok": False, "msg": "Plan no encontrado"}, status=404)

# -------------------------------
# DESACTIVAR / REACTIVAR PLANES
# -------------------------------

@login_required
def planes_suspendidos(request):
    """
    Vista de planes suspendidos y desactivados.
    Muestra dos listas separadas: suspendidos (estado='S') y desactivados (estado='D').
    """
    suspendidos = PlanPago.objects.filter(estado='S')
    desactivados = PlanPago.objects.filter(estado='D')
    return render(request, "planes_suspendidos.html", {
        "suspendidos": suspendidos,
        "desactivados": desactivados
    })


@require_POST
@login_required
def plan_suspender(request, pk):
    """
    Marca un plan como suspendido (estado='S').
    """
    try:
        plan = PlanPago.objects.get(pk=pk)
        plan.estado = 'S'
        plan.save()
        return JsonResponse({"ok": True, "msg": "Plan suspendido correctamente"})
    except PlanPago.DoesNotExist:
        return JsonResponse({"ok": False, "msg": "Plan no encontrado"}, status=404)


@require_POST
@login_required
def plan_desactivar(request, pk):
    """
    Desactiva un plan (estado='D' y iEstado=False).
    No se elimina, simplemente deja de estar disponible.
    """
    try:
        plan = PlanPago.objects.get(pk=pk)
        plan.estado = 'D'
        plan.iEstado = False
        plan.save()
        return JsonResponse({"ok": True, "msg": "Plan desactivado correctamente"})
    except PlanPago.DoesNotExist:
        return JsonResponse({"ok": False, "msg": "Plan no encontrado"}, status=404)


@require_POST
@login_required
def plan_reactivar(request, pk):
    """
    Reactiva un plan desactivado o suspendido (estado='A' y iEstado=True).
    """
    try:
        plan = PlanPago.objects.get(pk=pk)
        plan.estado = 'A'
        plan.iEstado = True
        plan.save()
        return JsonResponse({"ok": True, "msg": "Plan reactivado correctamente"})
    except PlanPago.DoesNotExist:
        return JsonResponse({"ok": False, "msg": "Plan no encontrado"}, status=404)
