# accounts/urls.py
from django.urls import path
from . import views
from . import views_admin

urlpatterns = [
    # Login propio (usa tu login_view + accounts/login.html)
    path("login/", views.login_view, name="login"),

    # Logout con confirmación (usa accounts/confirm_logout.html)
    path("logout/", views.logout_view, name="logout"),

    # Registro opcional
    path("registro/", views.register_view, name="registro"),

    # Home (vista protegida)
    path("", views.home, name="home"),

    # Administración de usuarios y roles (solo Administradores)
    path("gestionar-usuarios/", views_admin.gestionar_usuarios, name="gestionar_usuarios"),
    path("asignar-rol/<int:user_id>/", views_admin.asignar_rol, name="asignar_rol"),
]

