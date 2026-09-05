import random
from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction

from core.models import (
    AdaptacionAlumno, Alumno, AsignacionDocente, Directivo, Division, Docente,
    Grado, Informe, InformacionMedica, Padre, PadreAlumno, PersonaRetiro,
    SituacionAsistencia, Supervisor, Turno, Usuario,
)

NOMBRES = ["Juan", "María", "Carlos", "Ana", "Roberto", "Laura", "Pedro", "Sofía",
           "Diego", "Valentina", "Martín", "Camila", "Lucas", "Julieta", "Nicolás",
           "Agustina", "Franco", "Renata", "Tomás", "Bianca", "Federico", "Milagros",
           "Ignacio", "Delfina", "Santiago", "Catalina", "Joaquín", "Martina",
           "Emiliano", "Victoria"]

APELLIDOS = ["Pérez", "Gómez", "López", "Martínez", "Rodríguez", "Sánchez",
             "Fernández", "Díaz", "Álvarez", "Romero", "Torres", "Flores",
             "Acosta", "Benítez", "Suárez", "Molina", "Ortiz", "Silva",
             "Núñez", "Rojas", "Medina", "Herrera", "Aguirre", "Cabrera"]

ESPECIALIDADES = ["Matemáticas", "Lengua y Literatura", "Educación Física",
                   "Música", "Inglés", "Arte", "Ciencias Naturales", "Historia"]

VINCULOS = ["Madre", "Padre", "Abuela", "Abuelo", "Tío", "Tía", "Hermano/a mayor"]

TIPOS_SITUACION = ["Enfermedad del alumno", "Enfermedad familiar", "Situación familiar",
                    "Problema de transporte", "Otro"]

ESTADOS_ALUMNO = ["ACTIVO", "ACTIVO", "ACTIVO", "INACTIVO", "EGRESADO", "BAJA"]
ESTADOS_INFORME = ["ENVIADO", "REVISADO", "RESUELTO"]


def nombre_random():
    return random.choice(NOMBRES), random.choice(APELLIDOS)


def fecha_random(desde, hasta):
    delta = (hasta - desde).days
    return desde + timedelta(days=random.randint(0, delta))


class Command(BaseCommand):
    help = "Carga ~20 registros de ejemplo en cada tabla de Rastro."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true",
                             help="Borra todos los datos antes de cargar de nuevo.")

    @transaction.atomic
    def handle(self, *args, **options):
        if options["reset"]:
            for modelo in [AdaptacionAlumno, SituacionAsistencia, PersonaRetiro,
                           InformacionMedica, Informe, PadreAlumno, AsignacionDocente,
                           Alumno, Division, Grado, Turno, Docente, Supervisor,
                           Directivo, Padre, Usuario]:
                modelo.objects.all().delete()

        if Usuario.objects.exists():
            self.stdout.write(self.style.WARNING(
                "Ya hay datos cargados. Usá --reset para borrar todo y recargar."))
            return

        dni_usuario = 20000000
        dni_alumno = 50000000

        def crear_usuario(rol):
            nonlocal dni_usuario
            nombre, apellido = nombre_random()
            dni_usuario += random.randint(1, 5)
            n_usuario = f"{nombre.lower()}.{apellido.lower()}{dni_usuario % 1000}"
            u = Usuario.objects.create(
                nombre_usuario=n_usuario, contrasena="pass123",
                nombre=nombre, apellido=apellido, dni=str(dni_usuario),
                telefono=f"261-{random.randint(4000000,4999999)}",
                email=f"{n_usuario}@email.com", rol=rol,
            )
            return u

        # 1-4. USUARIO + roles (20 de cada uno)
        directivos = [Directivo.objects.create(usuario=crear_usuario("DIRECTIVO")) for _ in range(20)]
        supervisores = [Supervisor.objects.create(usuario=crear_usuario("SUPERVISOR")) for _ in range(20)]
        docentes = [Docente.objects.create(usuario=crear_usuario("DOCENTE"),
                                            especialidad=random.choice(ESPECIALIDADES))
                    for _ in range(20)]
        padres = [Padre.objects.create(usuario=crear_usuario("PADRE")) for _ in range(20)]

        # 5. GRADO (20)
        grados = [Grado.objects.create(nombre_grado=f"{i}° Grado") for i in range(1, 21)]

        # 6. TURNO (20, con nombres repetidos a propósito)
        nombres_turno = ["Mañana", "Tarde", "Vespertino", "Doble Jornada"]
        turnos = [Turno.objects.create(nombre_turno=random.choice(nombres_turno)) for _ in range(20)]

        # 7. DIVISION (20, cada una asociada a un grado al azar)
        letras = ["A", "B", "C", "D"]
        divisiones = [Division.objects.create(nombre_division=random.choice(letras),
                                               grado=random.choice(grados))
                      for _ in range(20)]

        # 8. ASIGNACION_DOCENTE (20)
        asignaciones = []
        for _ in range(20):
            division = random.choice(divisiones)
            asignaciones.append(AsignacionDocente.objects.create(
                docente=random.choice(docentes), grado=division.grado,
                division=division, turno=random.choice(turnos),
            ))

        # 9. ALUMNO (20)
        alumnos = []
        for _ in range(20):
            nombre, apellido = nombre_random()
            dni_alumno += random.randint(1, 5)
            division = random.choice(divisiones)
            alumnos.append(Alumno.objects.create(
                nombre=nombre, apellido=apellido, dni=str(dni_alumno),
                grado=division.grado, division=division,
                turno=random.choice(turnos), estado=random.choice(ESTADOS_ALUMNO),
            ))

        # 10. PADRE_ALUMNO (20 vínculos únicos)
        vinculos_creados = set()
        intentos = 0
        while len(vinculos_creados) < 20 and intentos < 200:
            intentos += 1
            padre = random.choice(padres)
            alumno = random.choice(alumnos)
            if (padre.id_padre, alumno.id_alumno) in vinculos_creados:
                continue
            PadreAlumno.objects.create(padre=padre, alumno=alumno)
            vinculos_creados.add((padre.id_padre, alumno.id_alumno))

        vinculos = list(PadreAlumno.objects.select_related("padre", "alumno"))

        # 11. INFORME (20) — siempre entre un padre y un hijo real suyo
        for _ in range(20):
            v = random.choice(vinculos)
            Informe.objects.create(
                padre=v.padre, alumno=v.alumno,
                mensaje=f"Novedad sobre {v.alumno.nombre}: seguimiento de rutina.",
                fecha=fecha_random(date(2026, 3, 1), date(2026, 8, 1)),
                estado=random.choice(ESTADOS_INFORME),
            )

        # 12. INFORMACION_MEDICA (una por alumno, hasta 20)
        for alumno in alumnos:
            InformacionMedica.objects.create(
                alumno=alumno,
                alergias=random.choice(["Ninguna", "Polen", "Penicilina", "Frutos secos"]),
                celiaquia=random.random() < 0.15,
                diabetes=random.random() < 0.08,
                medicacion_necesaria=random.choice(["—", "Ventolín si hace falta", "Antihistamínico"]),
                medicacion_emergencia=random.choice(["—", "Llamar a la familia", "Glucagón en botiquín"]),
                informacion_medica_emergencia="Contactar a la familia ante cualquier síntoma.",
                restricciones_educacion_fisica=random.choice(["Sin restricción", "Evitar esfuerzo intenso"]),
            )

        # 13. PERSONA_RETIRO (20)
        for _ in range(20):
            nombre, apellido = nombre_random()
            PersonaRetiro.objects.create(
                alumno=random.choice(alumnos), nombre=nombre, apellido=apellido,
                dni=str(random.randint(10000000, 45000000)),
                telefono=f"261-{random.randint(4000000,4999999)}",
                vinculo=random.choice(VINCULOS),
                autorizado=random.random() < 0.85,
            )

        # 14. ADAPTACION_ALUMNO (20)
        for _ in range(20):
            AdaptacionAlumno.objects.create(
                alumno=random.choice(alumnos),
                adaptaciones_necesarias="Apoyo visual y consignas simplificadas.",
                estrategias_funcionales="Ubicación cercana al pizarrón, pausas breves.",
                observaciones="Revisar avances cada trimestre.",
            )

        # 15. SITUACION_ASISTENCIA (20)
        for _ in range(20):
            inicio = fecha_random(date(2026, 3, 1), date(2026, 7, 1))
            SituacionAsistencia.objects.create(
                alumno=random.choice(alumnos),
                tipo=random.choice(TIPOS_SITUACION),
                descripcion="Situación registrada por el directivo.",
                fecha_inicio=inicio, fecha_fin=inicio + timedelta(days=random.randint(1, 10)),
                observaciones="Sin observaciones adicionales.",
            )

        self.stdout.write(self.style.SUCCESS(
            f"Listo: {Usuario.objects.count()} usuarios, {Alumno.objects.count()} alumnos, "
            f"{Informe.objects.count()} informes y el resto de las tablas cargadas."
        ))