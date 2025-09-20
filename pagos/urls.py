from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('', include('planes_pago.urls')),  # usa las rutas de la app (home, planes, cuotas)
    path('admin/', admin.site.urls),
]
