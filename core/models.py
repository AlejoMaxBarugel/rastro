from django.db import models


class Usuario(models.Model):
    ROL_DIRECTIVO = "DIRECTIVO"
    ROL_SUPERVISOR = "SUPERVISOR"
    ROL_DOCENTE = "DOCENTE"
    ROL_PADRE = "PADRE"
    ROL_CHOICES = [
        (ROL_DIRECTIVO, "Directivo"),
        (ROL_SUPERVISOR, "Supervisor"),
        (ROL_DOCENTE, "Docente"),
        (ROL_PADRE, "Padre/Tutor"),
    ]

    id_usuario = models.AutoField(primary_key=True)
    nombre_usuario = models.CharField(max_length=100, unique=True)
    contrasena = models.CharField(max_length=255)
    nombre = models.CharField(max_length=100, blank=True, null=True)
    apellido = models.CharField(max_length=100, blank=True, null=True)
    dni = models.CharField(max_length=20, unique=True)
    telefono = models.CharField(max_length=30, blank=True, null=True)
    email = models.CharField(max_length=150, blank=True, null=True)
    rol = models.CharField(max_length=20, choices=ROL_CHOICES)

    class Meta:
        db_table = "USUARIO"

    def __str__(self):
        return f"{self.nombre} {self.apellido} ({self.rol})"

    @property
    def nombre_completo(self):
        return f"{self.nombre or ''} {self.apellido or ''}".strip()

    def iniciales(self):
        n = (self.nombre or "?")[:1]
        a = (self.apellido or "?")[:1]
        return (n + a).upper()


class Directivo(models.Model):
    id_directivo = models.AutoField(primary_key=True)
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, db_column="id_usuario")

    class Meta:
        db_table = "DIRECTIVO"

    def __str__(self):
        return str(self.usuario)


class Supervisor(models.Model):
    id_supervisor = models.AutoField(primary_key=True)
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, db_column="id_usuario")

    class Meta:
        db_table = "SUPERVISOR"

    def __str__(self):
        return str(self.usuario)


class Docente(models.Model):
    id_docente = models.AutoField(primary_key=True)
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, db_column="id_usuario")
    especialidad = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        db_table = "DOCENTE"

    def __str__(self):
        return str(self.usuario)


class Padre(models.Model):
    id_padre = models.AutoField(primary_key=True)
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, db_column="id_usuario")

    class Meta:
        db_table = "PADRE"

    def __str__(self):
        return str(self.usuario)


class Grado(models.Model):
    id_grado = models.AutoField(primary_key=True)
    nombre_grado = models.CharField(max_length=100)

    class Meta:
        db_table = "GRADO"

    def __str__(self):
        return self.nombre_grado


class Division(models.Model):
    id_division = models.AutoField(primary_key=True)
    nombre_division = models.CharField(max_length=50)
    grado = models.ForeignKey(Grado, on_delete=models.CASCADE, db_column="id_grado", related_name="divisiones")

    class Meta:
        db_table = "DIVISION"

    def __str__(self):
        return f"{self.grado.nombre_grado} - {self.nombre_division}"


class Turno(models.Model):
    id_turno = models.AutoField(primary_key=True)
    nombre_turno = models.CharField(max_length=50)

    class Meta:
        db_table = "TURNO"

    def __str__(self):
        return self.nombre_turno


class AsignacionDocente(models.Model):
    id_asignacion = models.AutoField(primary_key=True)
    docente = models.ForeignKey(Docente, on_delete=models.CASCADE, db_column="id_docente", related_name="asignaciones")
    grado = models.ForeignKey(Grado, on_delete=models.CASCADE, db_column="id_grado")
    division = models.ForeignKey(Division, on_delete=models.CASCADE, db_column="id_division")
    turno = models.ForeignKey(Turno, on_delete=models.CASCADE, db_column="id_turno")

    class Meta:
        db_table = "ASIGNACION_DOCENTE"

    def __str__(self):
        return f"{self.docente} · {self.grado} {self.division.nombre_division} · {self.turno}"


class Alumno(models.Model):
    ESTADO_ACTIVO = "ACTIVO"
    ESTADO_INACTIVO = "INACTIVO"
    ESTADO_EGRESADO = "EGRESADO"
    ESTADO_BAJA = "BAJA"
    ESTADO_CHOICES = [
        (ESTADO_ACTIVO, "Activo"),
        (ESTADO_INACTIVO, "Inactivo"),
        (ESTADO_EGRESADO, "Egresado"),
        (ESTADO_BAJA, "Baja"),
    ]

    id_alumno = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    dni = models.CharField(max_length=20, unique=True)
    foto = models.CharField(max_length=255, blank=True, null=True)
    grado = models.ForeignKey(Grado, on_delete=models.PROTECT, db_column="id_grado")
    division = models.ForeignKey(Division, on_delete=models.PROTECT, db_column="id_division")
    turno = models.ForeignKey(Turno, on_delete=models.PROTECT, db_column="id_turno")
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default=ESTADO_ACTIVO)

    class Meta:
        db_table = "ALUMNO"
        ordering = ["apellido", "nombre"]

    def __str__(self):
        return f"{self.nombre} {self.apellido}"

    def iniciales(self):
        return (self.nombre[:1] + self.apellido[:1]).upper()


class PadreAlumno(models.Model):
    """Tabla pivote N:M entre PADRE y ALUMNO."""
    padre = models.ForeignKey(Padre, on_delete=models.CASCADE, db_column="id_padre", related_name="vinculos")
    alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE, db_column="id_alumno", related_name="vinculos")

    class Meta:
        db_table = "PADRE_ALUMNO"
        unique_together = (("padre", "alumno"),)

    def __str__(self):
        return f"{self.padre} -> {self.alumno}"


class Informe(models.Model):
    ESTADO_ENVIADO = "ENVIADO"
    ESTADO_REVISADO = "REVISADO"
    ESTADO_RESUELTO = "RESUELTO"
    ESTADO_CHOICES = [
        (ESTADO_ENVIADO, "Enviado"),
        (ESTADO_REVISADO, "Revisado"),
        (ESTADO_RESUELTO, "Resuelto"),
    ]
    TIPO_CHOICES = [
        ("Situación médica", "Situación médica"),
        ("Situación familiar", "Situación familiar"),
        ("Adaptación para el alumno", "Adaptación para el alumno"),
        ("Situación de asistencia", "Situación de asistencia"),
    ]

    id_informe = models.AutoField(primary_key=True)
    padre = models.ForeignKey(Padre, on_delete=models.CASCADE, db_column="id_padre", related_name="informes")
    alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE, db_column="id_alumno", related_name="informes")
    # Campo agregado respecto del esquema original para poder categorizar la novedad
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES, blank=True, null=True)
    mensaje = models.TextField()
    fecha = models.DateField()
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default=ESTADO_ENVIADO)

    class Meta:
        db_table = "INFORME"
        ordering = ["-fecha", "-id_informe"]

    def __str__(self):
        return f"Informe #{self.id_informe} - {self.alumno}"


class InformacionMedica(models.Model):
    id_informacion_medica = models.AutoField(primary_key=True)
    alumno = models.OneToOneField(Alumno, on_delete=models.CASCADE, db_column="id_alumno", related_name="informacion_medica")
    alergias = models.TextField(blank=True, null=True)
    celiaquia = models.BooleanField(default=False)
    diabetes = models.BooleanField(default=False)
    medicacion_necesaria = models.TextField(blank=True, null=True)
    medicacion_emergencia = models.TextField(blank=True, null=True)
    informacion_medica_emergencia = models.TextField(blank=True, null=True)
    restricciones_educacion_fisica = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "INFORMACION_MEDICA"

    def __str__(self):
        return f"Info. médica de {self.alumno}"


class PersonaRetiro(models.Model):
    id_persona_retiro = models.AutoField(primary_key=True)
    alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE, db_column="id_alumno", related_name="personas_retiro")
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    dni = models.CharField(max_length=20, blank=True, null=True)
    telefono = models.CharField(max_length=30, blank=True, null=True)
    vinculo = models.CharField(max_length=100, blank=True, null=True)
    autorizado = models.BooleanField(default=True)

    class Meta:
        db_table = "PERSONA_RETIRO"

    def __str__(self):
        return f"{self.nombre} {self.apellido} ({self.alumno})"


class AdaptacionAlumno(models.Model):
    id_adaptacion = models.AutoField(primary_key=True)
    alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE, db_column="id_alumno", related_name="adaptaciones")
    adaptaciones_necesarias = models.TextField()
    estrategias_funcionales = models.TextField(blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "ADAPTACION_ALUMNO"

    def __str__(self):
        return f"Adaptación de {self.alumno}"


class SituacionAsistencia(models.Model):
    TIPO_CHOICES = [
        ("Enfermedad del alumno", "Enfermedad del alumno"),
        ("Enfermedad familiar", "Enfermedad familiar"),
        ("Situación familiar", "Situación familiar"),
        ("Problema de transporte", "Problema de transporte"),
        ("Licencia Médica", "Licencia Médica"),
        ("Otro", "Otro"),
    ]
    id_situacion = models.AutoField(primary_key=True)
    alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE, db_column="id_alumno", related_name="situaciones")
    tipo = models.CharField(max_length=100, choices=TIPO_CHOICES, blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)
    fecha_inicio = models.DateField(blank=True, null=True)
    fecha_fin = models.DateField(blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "SITUACION_ASISTENCIA"
        ordering = ["-fecha_inicio"]

    def __str__(self):
        return f"{self.tipo} - {self.alumno}"


class Notificacion(models.Model):
    """
    Tabla agregada respecto del esquema original: registra los avisos que
    recibe un docente cuando el directivo actualiza datos de uno de sus alumnos.
    """
    id_notif = models.AutoField(primary_key=True)
    docente = models.ForeignKey(Docente, on_delete=models.CASCADE, db_column="id_docente", related_name="notificaciones")
    alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE, db_column="id_alumno")
    mensaje = models.CharField(max_length=255)
    fecha = models.DateField(auto_now_add=True)
    leido = models.BooleanField(default=False)

    class Meta:
        db_table = "NOTIFICACION"
        ordering = ["-id_notif"]

    def __str__(self):
        return self.mensaje
