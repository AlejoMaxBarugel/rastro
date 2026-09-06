from datetime import date

from django.core.management.base import BaseCommand
from django.db import transaction

from core.models import (
    AdaptacionAlumno, Alumno, AsignacionDocente, Directivo, Division, Docente,
    Grado, Informe, InformacionMedica, Padre, PadreAlumno, PersonaRetiro,
    SituacionAsistencia, Supervisor, Turno, Usuario,
)


class Command(BaseCommand):
    help = "Carga los datos de prueba de Rastro (equivalente a los scripts sqlite3 originales)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset", action="store_true",
            help="Borra todos los datos existentes antes de volver a cargarlos.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["reset"]:
            self.stdout.write("Borrando datos existentes...")
            for model in [
                AdaptacionAlumno, SituacionAsistencia, PersonaRetiro, InformacionMedica,
                Informe, PadreAlumno, AsignacionDocente, Alumno, Turno, Division, Grado,
                Docente, Supervisor, Directivo, Padre, Usuario,
            ]:
                model.objects.all().delete()

        if Usuario.objects.exists():
            self.stdout.write(self.style.WARNING(
                "Ya hay datos cargados. Usá 'python manage.py seed_data --reset' para reiniciar."
            ))
            return

        # 1. USUARIOS
        u_juan = Usuario.objects.create(nombre_usuario="juan_perez", contrasena="pass123", nombre="Juan", apellido="Pérez", dni="30111222", telefono="1144445555", email="juan.perez@email.com", rol=Usuario.ROL_DIRECTIVO)
        u_maria = Usuario.objects.create(nombre_usuario="maria_gomez", contrasena="pass123", nombre="María", apellido="Gómez", dni="31222333", telefono="1144446666", email="maria.gomez@email.com", rol=Usuario.ROL_SUPERVISOR)
        u_carlos = Usuario.objects.create(nombre_usuario="carlos_lopez", contrasena="pass123", nombre="Carlos", apellido="López", dni="32333444", telefono="1144447777", email="carlos.lopez@email.com", rol=Usuario.ROL_DOCENTE)
        u_ana = Usuario.objects.create(nombre_usuario="ana_martinez", contrasena="pass123", nombre="Ana", apellido="Martínez", dni="33444555", telefono="1144448888", email="ana.martinez@email.com", rol=Usuario.ROL_DOCENTE)
        u_roberto = Usuario.objects.create(nombre_usuario="roberto_rodriguez", contrasena="pass123", nombre="Roberto", apellido="Rodríguez", dni="28555666", telefono="1144449999", email="roberto.r@email.com", rol=Usuario.ROL_PADRE)
        u_laura = Usuario.objects.create(nombre_usuario="laura_sanchez", contrasena="pass123", nombre="Laura", apellido="Sánchez", dni="29666777", telefono="1155550000", email="laura.s@email.com", rol=Usuario.ROL_PADRE)

        # 2. ROLES ESPECÍFICOS
        Directivo.objects.create(usuario=u_juan)
        Supervisor.objects.create(usuario=u_maria)
        d_carlos = Docente.objects.create(usuario=u_carlos, especialidad="Matemáticas")
        d_ana = Docente.objects.create(usuario=u_ana, especialidad="Lengua y Literatura")
        p_roberto = Padre.objects.create(usuario=u_roberto)
        p_laura = Padre.objects.create(usuario=u_laura)

        # 3. ESTRUCTURA ESCOLAR
        g1 = Grado.objects.create(nombre_grado="1° Año")
        g2 = Grado.objects.create(nombre_grado="2° Año")
        Grado.objects.create(nombre_grado="3° Año")

        d1a = Division.objects.create(nombre_division="A", grado=g1)
        Division.objects.create(nombre_division="B", grado=g1)
        d2a = Division.objects.create(nombre_division="A", grado=g2)
        Division.objects.create(nombre_division="B", grado=g2)

        t_manana = Turno.objects.create(nombre_turno="Mañana")
        t_tarde = Turno.objects.create(nombre_turno="Tarde")

        # 4. ASIGNACIÓN DOCENTE
        AsignacionDocente.objects.create(docente=d_carlos, grado=g1, division=d1a, turno=t_manana)
        AsignacionDocente.objects.create(docente=d_ana, grado=g2, division=d2a, turno=t_tarde)

        # 5. ALUMNOS
        lucas = Alumno.objects.create(nombre="Lucas", apellido="Rodríguez", dni="50111222", foto="foto_lucas.png", grado=g1, division=d1a, turno=t_manana, estado=Alumno.ESTADO_ACTIVO)
        sofia = Alumno.objects.create(nombre="Sofia", apellido="Rodríguez", dni="51222333", foto="foto_sofia.png", grado=g2, division=d2a, turno=t_tarde, estado=Alumno.ESTADO_ACTIVO)
        mateo = Alumno.objects.create(nombre="Mateo", apellido="Sánchez", dni="52333444", foto="foto_mateo.png", grado=g1, division=d1a, turno=t_manana, estado=Alumno.ESTADO_ACTIVO)

        # 6. RELACIÓN PADRE_ALUMNO (N:M)
        PadreAlumno.objects.create(padre=p_roberto, alumno=lucas)
        PadreAlumno.objects.create(padre=p_roberto, alumno=sofia)
        PadreAlumno.objects.create(padre=p_laura, alumno=mateo)

        # 7. INFORMACIÓN MÉDICA
        InformacionMedica.objects.create(alumno=lucas, alergias="Polen, Penicilina", celiaquia=False, diabetes=False, medicacion_necesaria="Ventolín en caso de crisis", medicacion_emergencia="Llamar a la madre", informacion_medica_emergencia="Ninguna", restricciones_educacion_fisica="Sin restricción")
        InformacionMedica.objects.create(alumno=sofia, alergias="Ninguna", celiaquia=True, diabetes=False, medicacion_necesaria="No consume gluten", medicacion_emergencia="N/A", informacion_medica_emergencia="Avisar si ingiere TACC", restricciones_educacion_fisica="Sin restricción")

        # 8. PERSONAS DE RETIRO
        PersonaRetiro.objects.create(alumno=lucas, nombre="Marta", apellido="Gómez", dni="18111222", telefono="1166667777", vinculo="Abuela", autorizado=True)
        PersonaRetiro.objects.create(alumno=mateo, nombre="Jorge", apellido="Sánchez", dni="17222333", telefono="1177778888", vinculo="Tío", autorizado=True)

        # 9. INFORMES, ADAPTACIONES Y ASISTENCIA
        Informe.objects.create(
            padre=p_roberto, alumno=lucas, tipo="Situación médica",
            mensaje="Lucas no puede hacer educación física hoy: el cardiólogo le detectó un soplo y le indicó reposo hasta la próxima consulta.",
            fecha=date(2026, 3, 10), estado=Informe.ESTADO_ENVIADO,
        )
        AdaptacionAlumno.objects.create(alumno=mateo, adaptaciones_necesarias="Uso de tipografía más grande en exámenes", estrategias_funcionales="Ubicación en primera fila", observaciones="Requiere pausa de 5 min en evaluaciones largas")
        SituacionAsistencia.objects.create(alumno=lucas, tipo="Licencia Médica", descripcion="Cuadro gripal con reposo indicado", fecha_inicio=date(2026, 3, 15), fecha_fin=date(2026, 3, 18), observaciones="Presentó certificado")

        self.stdout.write(self.style.SUCCESS("Datos de prueba cargados con éxito."))
        self.stdout.write("")
        self.stdout.write("Usuarios de ejemplo (usuario / contraseña):")
        for u in [u_roberto, u_juan, u_carlos, u_maria]:
            self.stdout.write(f"  {u.rol:<11} {u.nombre_usuario} / pass123")
