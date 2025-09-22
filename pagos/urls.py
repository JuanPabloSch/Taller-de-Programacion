from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # Autenticación (login/logout/registro)
    path("accounts/", include("accounts.urls")),

    # Home, planes y cuotas
    path("", include("planes_pago.urls")),

    # Admin de Django
    path("admin/", admin.site.urls),
]
