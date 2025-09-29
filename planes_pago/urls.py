from django.urls import path
from . import views

urlpatterns = [
    # Landing page protegida
    path("", views.home, name="home"),

    # CRUD de planes
    path("planes/", views.planes_list, name="planes_list"),
    path("planes/data/", views.planes_data, name="planes_data"),
    path("planes/guardar/", views.plan_guardar, name="plan_guardar"),
    path("planes/eliminar/<int:pk>/", views.plan_borrar, name="plan_borrar"),

    # CRUD de cuotas
    path("cuotas/", views.cuotas_list, name="cuotas_list"),
    path("cuotas/data/", views.cuotas_data, name="cuotas_data"),
    path("cuotas/guardar/", views.cuota_guardar, name="cuota_guardar"),
    path("cuotas/eliminar/<int:pk>/", views.cuota_borrar, name="cuota_borrar"),

    # Exportar Planes
    path("planes/exportar/pdf/", views.exportar_planes_pdf, name="exportar_planes_pdf"),
    path("planes/exportar/csv/", views.exportar_planes_csv, name="exportar_planes_csv"),
    path("planes/exportar/excel/", views.exportar_planes_excel, name="exportar_planes_excel"),
    path("planes/imprimir/", views.imprimir_planes, name="imprimir_planes"),

    # Exportar Cuotas
    path("cuotas/exportar/pdf/", views.exportar_cuotas_pdf, name="exportar_cuotas_pdf"),
    path("cuotas/exportar/csv/", views.exportar_cuotas_csv, name="exportar_cuotas_csv"),
    path("cuotas/exportar/excel/", views.exportar_cuotas_excel, name="exportar_cuotas_excel"),
    path("cuotas/imprimir/", views.imprimir_cuotas, name="imprimir_cuotas"),
]
