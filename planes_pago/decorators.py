from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied
from functools import wraps


def group_required(*group_names):
    """
    Decorador que verifica si el usuario pertenece a alguno de los grupos especificados.
    Uso: @group_required('Administrador', 'Tesorero')
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if request.user.is_authenticated:
                # Superusuarios siempre tienen acceso
                if request.user.is_superuser:
                    return view_func(request, *args, **kwargs)

                # Verificar si el usuario está en alguno de los grupos
                user_groups = request.user.groups.values_list('name', flat=True)
                if any(group in user_groups for group in group_names):
                    return view_func(request, *args, **kwargs)

            raise PermissionDenied
        return wrapper
    return decorator


def is_administrador(user):
    """Verifica si el usuario es Administrador"""
    return user.is_superuser or user.groups.filter(name='Administrador').exists()


def is_tesorero_or_admin(user):
    """Verifica si el usuario es Tesorero o Administrador"""
    return user.is_superuser or user.groups.filter(name__in=['Administrador', 'Tesorero']).exists()


def can_delete(user):
    """Verifica si el usuario puede eliminar (solo Administradores)"""
    return user.is_superuser or user.groups.filter(name='Administrador').exists()


def can_modify(user):
    """Verifica si el usuario puede modificar (Administrador o Tesorero)"""
    return user.is_superuser or user.groups.filter(name__in=['Administrador', 'Tesorero']).exists()
