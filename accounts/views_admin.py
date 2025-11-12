from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from planes_pago.decorators import group_required


@login_required
@group_required('Administrador')
def gestionar_usuarios(request):
    """
    Vista para que los administradores gestionen usuarios y sus roles.
    """
    usuarios = User.objects.all().order_by('username')
    grupos = Group.objects.all().order_by('name')

    context = {
        'usuarios': usuarios,
        'grupos': grupos,
    }
    return render(request, 'accounts/gestionar_usuarios.html', context)


@login_required
@group_required('Administrador')
def asignar_rol(request, user_id):
    """
    Asigna o cambia el rol de un usuario.
    """
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'msg': 'Método no permitido'}, status=405)

    usuario = get_object_or_404(User, pk=user_id)
    grupo_nombre = request.POST.get('grupo')

    if not grupo_nombre:
        return JsonResponse({'ok': False, 'msg': 'Debe seleccionar un grupo'}, status=400)

    try:
        # Remover todos los grupos actuales
        usuario.groups.clear()

        # Asignar el nuevo grupo
        if grupo_nombre != 'ninguno':
            grupo = Group.objects.get(name=grupo_nombre)
            usuario.groups.add(grupo)

        return JsonResponse({
            'ok': True,
            'msg': f'Rol actualizado para {usuario.username}'
        })
    except Group.DoesNotExist:
        return JsonResponse({'ok': False, 'msg': 'Grupo no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'ok': False, 'msg': str(e)}, status=500)
