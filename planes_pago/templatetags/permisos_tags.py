from django import template

register = template.Library()


@register.filter(name='has_group')
def has_group(user, group_name):
    """
    Verifica si un usuario pertenece a un grupo específico.
    Uso en template: {% if request.user|has_group:"Administrador" %}
    """
    if user.is_superuser:
        return True
    return user.groups.filter(name=group_name).exists()


@register.filter(name='is_in_groups')
def is_in_groups(user, group_names):
    """
    Verifica si un usuario pertenece a alguno de los grupos (separados por coma).
    Uso en template: {% if request.user|is_in_groups:"Administrador,Tesorero" %}
    """
    if user.is_superuser:
        return True
    groups = [g.strip() for g in group_names.split(',')]
    return user.groups.filter(name__in=groups).exists()


@register.simple_tag
def can_delete_items(user):
    """
    Verifica si el usuario puede eliminar elementos.
    Uso en template: {% can_delete_items request.user as puede_eliminar %}
    """
    return user.is_superuser or user.groups.filter(name='Administrador').exists()


@register.simple_tag
def can_modify_items(user):
    """
    Verifica si el usuario puede modificar elementos.
    Uso en template: {% can_modify_items request.user as puede_modificar %}
    """
    return user.is_superuser or user.groups.filter(name__in=['Administrador', 'Tesorero']).exists()


@register.simple_tag
def user_role(user):
    """
    Retorna el rol del usuario.
    Uso en template: {% user_role request.user as rol %}
    """
    if user.is_superuser:
        return "Superusuario"

    groups = user.groups.values_list('name', flat=True)
    if 'Administrador' in groups:
        return "Administrador"
    elif 'Tesorero' in groups:
        return "Tesorero"
    elif 'Consulta' in groups:
        return "Consulta"
    else:
        return "Sin rol asignado"
