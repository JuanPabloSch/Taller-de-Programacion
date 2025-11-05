from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from planes_pago.models import PlanPago, Cuota


class Command(BaseCommand):
    help = 'Crea los grupos de usuarios con sus permisos correspondientes'

    def handle(self, *args, **kwargs):
        # Obtener los content types
        plan_ct = ContentType.objects.get_for_model(PlanPago)
        cuota_ct = ContentType.objects.get_for_model(Cuota)

        # Obtener todos los permisos
        permisos_plan = Permission.objects.filter(content_type=plan_ct)
        permisos_cuota = Permission.objects.filter(content_type=cuota_ct)

        # ========================
        # GRUPO: ADMINISTRADOR
        # ========================
        admin_group, created = Group.objects.get_or_create(name='Administrador')
        if created:
            self.stdout.write(self.style.SUCCESS('Grupo "Administrador" creado'))

        # Administrador tiene todos los permisos
        admin_group.permissions.set(list(permisos_plan) + list(permisos_cuota))
        self.stdout.write(self.style.SUCCESS('Permisos asignados a Administrador: TODOS'))

        # ========================
        # GRUPO: TESORERO
        # ========================
        tesorero_group, created = Group.objects.get_or_create(name='Tesorero')
        if created:
            self.stdout.write(self.style.SUCCESS('Grupo "Tesorero" creado'))

        # Tesorero puede ver, agregar y modificar (NO eliminar)
        permisos_tesorero = Permission.objects.filter(
            content_type__in=[plan_ct, cuota_ct],
            codename__in=[
                'view_planpago', 'add_planpago', 'change_planpago',
                'view_cuota', 'add_cuota', 'change_cuota'
            ]
        )
        tesorero_group.permissions.set(permisos_tesorero)
        self.stdout.write(self.style.SUCCESS('Permisos asignados a Tesorero: Ver, Agregar, Modificar'))

        # ========================
        # GRUPO: CONSULTA
        # ========================
        consulta_group, created = Group.objects.get_or_create(name='Consulta')
        if created:
            self.stdout.write(self.style.SUCCESS('Grupo "Consulta" creado'))

        # Consulta solo puede ver
        permisos_consulta = Permission.objects.filter(
            content_type__in=[plan_ct, cuota_ct],
            codename__in=['view_planpago', 'view_cuota']
        )
        consulta_group.permissions.set(permisos_consulta)
        self.stdout.write(self.style.SUCCESS('Permisos asignados a Consulta: Solo Ver'))

        self.stdout.write(self.style.SUCCESS('\n=== Grupos configurados exitosamente ==='))
        self.stdout.write('- Administrador: Acceso completo')
        self.stdout.write('- Tesorero: Ver, Crear, Editar (sin eliminar)')
        self.stdout.write('- Consulta: Solo ver')
