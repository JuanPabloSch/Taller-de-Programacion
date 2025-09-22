# accounts/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Login propio (usa tu login_view + accounts/login.html)
    path("login/", views.login_view, name="login"),

    # Logout con confirmación (usa accounts/confirm_logout.html)
    path("logout/", views.logout_view, name="logout"),

    # Registro opcional
    path("registro/", views.register_view, name="registro"),

    # Home (vista protegida)
    path("", views.home, name="home"),
]

