from django.urls import path
from . import views

urlpatterns = [
    path('planes/', views.planes_list, name='planes_list'),
    path('planes/data/', views.planes_data, name='planes_data'),
    path('planes/guardar/', views.plan_guardar, name='plan_guardar'),
    path('planes/eliminar/<int:pk>/', views.plan_borrar, name='plan_borrar'),
    # CRUD de cuotas
    path('cuotas/', views.cuotas_list, name='cuotas_list'),
    path('cuotas/data/', views.cuotas_data, name='cuotas_data'),
    path('cuotas/guardar/', views.cuota_guardar, name='cuota_guardar'),
    path('cuotas/eliminar/<int:pk>/', views.cuota_borrar, name='cuota_borrar'),

]
