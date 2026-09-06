from functools import wraps

from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .models import (
    AdaptacionAlumno, Alumno, AsignacionDocente, Directivo, Division, Docente,
    Grado, Informe, InformacionMedica, Notificacion, Padre, PadreAlumno,
    PersonaRetiro, SituacionAsistencia, Supervisor, Turno, Usuario,
)

# Usuarios "de ejemplo" ofrecidos en la pantalla de login (uno por rol)
LOGIN_ROSTER = ["roberto_rodriguez", "juan_perez", "carlos_lopez", "maria_gomez"]


# ---------------------------------------------------------------------------
# Autenticación (propia, contra la tabla USUARIO) y control de acceso por rol
# ---------------------------------------------------------------------------
def get_current_usuario(request):
    uid = request.session.get("usuario_id")
    if not uid:
        return None
    return Usuario.objects.filter(pk=uid).first()


def login_required_custom(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        usuario = get_current_usuario(request)
        if not usuario:
            return redirect("login")
        request.usuario = usuario
        return view_func(request, *args, **kwargs)
    return wrapper


def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        @login_required_custom
        def wrapper(request, *args, **kwargs):
            if request.usuario.rol not in roles:
                messages.error(request, "No tenés permiso para acceder a esa sección.")
                return redirect(home_url_for(request.usuario))
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def home_url_for(usuario):
    return {
        Usuario.ROL_PADRE: "padre_hijos",
        Usuario.ROL_DIRECTIVO: "directivo_alumnos",
        Usuario.ROL_DOCENTE: "docente_alumnos",
        Usuario.ROL_SUPERVISOR: "supervisor_alumnos",
    }.get(usuario.rol, "login")


# ---------------------------------------------------------------------------
# Login / logout
# ---------------------------------------------------------------------------
def login_view(request):
    if get_current_usuario(request):
        return redirect(home_url_for(get_current_usuario(request)))

    roster = list(Usuario.objects.filter(nombre_usuario__in=LOGIN_ROSTER))
    roster.sort(key=lambda u: LOGIN_ROSTER.index(u.nombre_usuario))

    if request.method == "POST":
        nombre_usuario = request.POST.get("nombre_usuario", "").strip()
        contrasena = request.POST.get("contrasena", "")
        usuario = Usuario.objects.filter(nombre_usuario=nombre_usuario).first()
        if usuario and usuario.contrasena == contrasena:
            request.session["usuario_id"] = usuario.id_usuario
            return redirect(home_url_for(usuario))
        messages.error(request, "Usuario o contraseña incorrectos.")

    return render(request, "core/login.html", {"roster": roster})


def logout_view(request):
    request.session.flush()
    return redirect("login")


def registro_padre(request):
    errores = []
    if request.method == "POST":
        nombre = request.POST.get("nombre", "").strip()
        apellido = request.POST.get("apellido", "").strip()
        dni = request.POST.get("dni", "").strip()
        telefono = request.POST.get("telefono", "").strip()
        email = request.POST.get("email", "").strip()
        nombre_usuario = request.POST.get("nombre_usuario", "").strip()
        contrasena = request.POST.get("contrasena", "")
        contrasena2 = request.POST.get("contrasena2", "")
        dni_hijo = request.POST.get("dni_hijo", "").strip()

        if not (nombre and apellido and dni and nombre_usuario and contrasena):
            errores.append("Completá todos los campos obligatorios.")
        if contrasena != contrasena2:
            errores.append("Las contraseñas no coinciden.")
        if Usuario.objects.filter(nombre_usuario=nombre_usuario).exists():
            errores.append("Ese nombre de usuario ya está en uso.")
        if Usuario.objects.filter(dni=dni).exists():
            errores.append("Ya existe un usuario registrado con ese DNI.")

        alumno_a_vincular = None
        if dni_hijo:
            alumno_a_vincular = Alumno.objects.filter(dni=dni_hijo).first()
            if not alumno_a_vincular:
                errores.append("No se encontró ningún alumno con ese DNI. Podés dejarlo en blanco y pedirle al directivo que te vincule después.")

        if not errores:
            with transaction.atomic():
                usuario = Usuario.objects.create(
                    nombre_usuario=nombre_usuario, contrasena=contrasena,
                    nombre=nombre, apellido=apellido, dni=dni,
                    telefono=telefono, email=email, rol=Usuario.ROL_PADRE,
                )
                padre = Padre.objects.create(usuario=usuario)
                if alumno_a_vincular:
                    PadreAlumno.objects.create(padre=padre, alumno=alumno_a_vincular)

            request.session["usuario_id"] = usuario.id_usuario
            messages.success(request, "Cuenta creada correctamente. ¡Bienvenido/a a Rastro!")
            return redirect("padre_hijos")

    return render(request, "core/registro_padre.html", {"errores": errores})


# ---------------------------------------------------------------------------
# Notificaciones a docentes (cuando el directivo actualiza datos de un alumno)
# ---------------------------------------------------------------------------
def notificar_docentes_de_alumno(alumno, mensaje):
    asignaciones = AsignacionDocente.objects.filter(
        grado=alumno.grado, division=alumno.division, turno=alumno.turno
    ).select_related("docente")
    docentes_ids = {a.docente_id for a in asignaciones}
    for docente_id in docentes_ids:
        Notificacion.objects.create(docente_id=docente_id, alumno=alumno, mensaje=mensaje)
    return len(docentes_ids)


@login_required_custom
def notificacion_marcar_leida(request, id_notif):
    notif = get_object_or_404(Notificacion, pk=id_notif)
    docente = Docente.objects.filter(usuario=request.usuario).first()
    if docente and notif.docente_id == docente.id_docente:
        notif.leido = True
        notif.save()
    return redirect(request.META.get("HTTP_REFERER", "docente_alumnos"))


@role_required(Usuario.ROL_DOCENTE)
def notificaciones_marcar_todas(request):
    docente = Docente.objects.get(usuario=request.usuario)
    Notificacion.objects.filter(docente=docente, leido=False).update(leido=True)
    return redirect(request.META.get("HTTP_REFERER", "docente_alumnos"))


# ---------------------------------------------------------------------------
# PADRE
# ---------------------------------------------------------------------------
@role_required(Usuario.ROL_PADRE)
def padre_hijos(request):
    padre = get_object_or_404(Padre, usuario=request.usuario)
    hijos = Alumno.objects.filter(vinculos__padre=padre).select_related("grado", "division", "turno")
    return render(request, "core/padre_hijos.html", {"hijos": hijos})


# ---------------------------------------------------------------------------
# FICHA DE ALUMNO (compartida entre PADRE, DIRECTIVO, DOCENTE, SUPERVISOR)
# ---------------------------------------------------------------------------
@login_required_custom
def alumno_detail(request, id_alumno):
    usuario = request.usuario
    alumno = get_object_or_404(Alumno.objects.select_related("grado", "division", "turno"), pk=id_alumno)

    # --- control de acceso según el rol ---
    if usuario.rol == Usuario.ROL_PADRE:
        padre = get_object_or_404(Padre, usuario=usuario)
        if not PadreAlumno.objects.filter(padre=padre, alumno=alumno).exists():
            messages.error(request, "Ese alumno no está asociado a tu cuenta.")
            return redirect("padre_hijos")
    elif usuario.rol == Usuario.ROL_DOCENTE:
        docente = get_object_or_404(Docente, usuario=usuario)
        en_asignacion = AsignacionDocente.objects.filter(
            docente=docente, grado=alumno.grado, division=alumno.division, turno=alumno.turno
        ).exists()
        if not en_asignacion:
            messages.error(request, "Ese alumno no corresponde a tus asignaciones.")
            return redirect("docente_alumnos")
    # DIRECTIVO y SUPERVISOR tienen acceso completo de lectura

    puede_editar = usuario.rol == Usuario.ROL_DIRECTIVO
    puede_informar = usuario.rol == Usuario.ROL_PADRE

    # --- acciones POST ---
    if request.method == "POST":
        accion = request.POST.get("accion")

        if accion == "enviar_informe" and puede_informar:
            mensaje = request.POST.get("mensaje", "").strip()
            tipo = request.POST.get("tipo", "")
            if mensaje:
                padre = Padre.objects.get(usuario=usuario)
                Informe.objects.create(
                    padre=padre, alumno=alumno, tipo=tipo, mensaje=mensaje,
                    fecha=timezone.localdate(), estado=Informe.ESTADO_ENVIADO,
                )
                messages.success(request, "Informe enviado al directivo.")
            else:
                messages.error(request, "Escribí un mensaje antes de enviar.")
            return redirect("alumno_detail", id_alumno=alumno.id_alumno)

        if accion == "guardar_medica" and puede_editar:
            im, _ = InformacionMedica.objects.get_or_create(alumno=alumno)
            im.alergias = request.POST.get("alergias", "").strip()
            im.celiaquia = request.POST.get("celiaquia") == "on"
            im.diabetes = request.POST.get("diabetes") == "on"
            im.medicacion_necesaria = request.POST.get("medicacion_necesaria", "").strip()
            im.medicacion_emergencia = request.POST.get("medicacion_emergencia", "").strip()
            im.informacion_medica_emergencia = request.POST.get("informacion_medica_emergencia", "").strip()
            im.restricciones_educacion_fisica = request.POST.get("restricciones_educacion_fisica", "").strip()
            im.save()
            notificar_docentes_de_alumno(alumno, f"Se actualizó la información médica de {alumno.nombre} {alumno.apellido}.")
            messages.success(request, "Información médica actualizada.")
            return redirect("alumno_detail", id_alumno=alumno.id_alumno)

        if accion == "agregar_adaptacion" and puede_editar:
            nec = request.POST.get("adaptaciones_necesarias", "").strip()
            if nec:
                AdaptacionAlumno.objects.create(
                    alumno=alumno, adaptaciones_necesarias=nec,
                    estrategias_funcionales=request.POST.get("estrategias_funcionales", "").strip(),
                    observaciones=request.POST.get("observaciones", "").strip(),
                )
                notificar_docentes_de_alumno(alumno, f"Se agregó una nueva adaptación para {alumno.nombre} {alumno.apellido}.")
                messages.success(request, "Adaptación registrada.")
            else:
                messages.error(request, "Describí la adaptación necesaria.")
            return redirect("alumno_detail", id_alumno=alumno.id_alumno)

        if accion == "agregar_situacion" and puede_editar:
            desc = request.POST.get("descripcion", "").strip()
            if desc:
                SituacionAsistencia.objects.create(
                    alumno=alumno, tipo=request.POST.get("tipo", ""), descripcion=desc,
                    fecha_inicio=request.POST.get("fecha_inicio") or None,
                    fecha_fin=request.POST.get("fecha_fin") or None,
                    observaciones=request.POST.get("observaciones", "").strip(),
                )
                notificar_docentes_de_alumno(alumno, f"Nueva situación de asistencia registrada para {alumno.nombre} {alumno.apellido}.")
                messages.success(request, "Situación registrada.")
            else:
                messages.error(request, "Agregá una descripción.")
            return redirect("alumno_detail", id_alumno=alumno.id_alumno)

        if accion == "agregar_retiro" and puede_editar:
            nombre = request.POST.get("nombre", "").strip()
            apellido = request.POST.get("apellido", "").strip()
            if nombre and apellido:
                PersonaRetiro.objects.create(
                    alumno=alumno, nombre=nombre, apellido=apellido,
                    dni=request.POST.get("dni", "").strip(),
                    telefono=request.POST.get("telefono", "").strip(),
                    vinculo=request.POST.get("vinculo", "").strip(),
                    autorizado=request.POST.get("autorizado") == "on",
                )
                messages.success(request, "Persona agregada.")
            else:
                messages.error(request, "Completá nombre y apellido.")
            return redirect("alumno_detail", id_alumno=alumno.id_alumno)

    context = {
        "alumno": alumno,
        "info_medica": getattr(alumno, "informacion_medica", None),
        "retiros": alumno.personas_retiro.all(),
        "adaptaciones": alumno.adaptaciones.all(),
        "situaciones": alumno.situaciones.all(),
        "puede_editar": puede_editar,
        "puede_informar": puede_informar,
        "tipos_informe": Informe.TIPO_CHOICES,
        "tipos_situacion": SituacionAsistencia.TIPO_CHOICES,
    }
    if puede_editar or usuario.rol == Usuario.ROL_PADRE:
        context["informes"] = alumno.informes.select_related("padre__usuario")
    return render(request, "core/alumno_detail.html", context)


# ---------------------------------------------------------------------------
# DIRECTIVO
# ---------------------------------------------------------------------------
@role_required(Usuario.ROL_DIRECTIVO)
def directivo_alumnos(request):
    qs = Alumno.objects.select_related("grado", "division", "turno")
    q = request.GET.get("q", "").strip()
    estado = request.GET.get("estado", "").strip()
    if q:
        qs = qs.filter(Q(nombre__icontains=q) | Q(apellido__icontains=q) | Q(dni__icontains=q))
    if estado:
        qs = qs.filter(estado=estado)
    return render(request, "core/directivo_alumnos.html", {
        "alumnos": qs, "q": q, "estado": estado, "estados": Alumno.ESTADO_CHOICES,
    })


@role_required(Usuario.ROL_DIRECTIVO)
def alumno_form(request, id_alumno=None):
    alumno = get_object_or_404(Alumno, pk=id_alumno) if id_alumno else None
    grados = Grado.objects.all()
    turnos = Turno.objects.all()
    grado_sel = request.POST.get("id_grado") or (alumno.grado_id if alumno else (grados.first().id_grado if grados else None))
    divisiones = Division.objects.filter(grado_id=grado_sel)

    if request.method == "POST" and not request.POST.get("solo_refrescar"):
        nombre = request.POST.get("nombre", "").strip()
        apellido = request.POST.get("apellido", "").strip()
        dni = request.POST.get("dni", "").strip()
        if not (nombre and apellido and dni):
            messages.error(request, "Completá nombre, apellido y DNI.")
        else:
            data = dict(
                nombre=nombre, apellido=apellido, dni=dni,
                grado_id=request.POST.get("id_grado"),
                division_id=request.POST.get("id_division"),
                turno_id=request.POST.get("id_turno"),
                estado=request.POST.get("estado", Alumno.ESTADO_ACTIVO),
            )
            if alumno:
                for k, v in data.items():
                    setattr(alumno, k, v)
                alumno.save()
                messages.success(request, "Alumno actualizado.")
            else:
                alumno = Alumno.objects.create(**data)
                messages.success(request, "Alumno creado.")
            return redirect("directivo_alumnos")

    return render(request, "core/alumno_form.html", {
        "alumno": alumno, "grados": grados, "turnos": turnos, "divisiones": divisiones,
        "grado_sel": int(grado_sel) if grado_sel else None,
        "estados": Alumno.ESTADO_CHOICES,
    })


@role_required(Usuario.ROL_DIRECTIVO)
def divisiones_por_grado(request):
    """Repobla el <select> de división al cambiar el grado (recarga liviana, sin JS de más)."""
    id_grado = request.GET.get("id_grado")
    divisiones = Division.objects.filter(grado_id=id_grado)
    return render(request, "core/_opciones_division.html", {"divisiones": divisiones})


@role_required(Usuario.ROL_DIRECTIVO)
def alumno_eliminar(request, id_alumno):
    alumno = get_object_or_404(Alumno, pk=id_alumno)
    if request.method == "POST":
        alumno.delete()
        messages.success(request, "Alumno eliminado.")
        return redirect("directivo_alumnos")
    return render(request, "core/alumno_eliminar.html", {"alumno": alumno})


@role_required(Usuario.ROL_DIRECTIVO)
def directivo_informes(request):
    informes = Informe.objects.select_related("alumno", "padre__usuario")
    return render(request, "core/directivo_informes.html", {"informes": informes})


@role_required(Usuario.ROL_DIRECTIVO)
def informe_cambiar_estado(request, id_informe):
    informe = get_object_or_404(Informe, pk=id_informe)
    if request.method == "POST":
        nuevo_estado = request.POST.get("estado")
        if nuevo_estado in dict(Informe.ESTADO_CHOICES):
            informe.estado = nuevo_estado
            informe.save()
            messages.success(request, f"Estado del informe actualizado a {nuevo_estado}.")
    return redirect("directivo_informes")


# ---------------------------------------------------------------------------
# DOCENTE
# ---------------------------------------------------------------------------
@role_required(Usuario.ROL_DOCENTE)
def docente_alumnos(request):
    docente = get_object_or_404(Docente, usuario=request.usuario)
    asignaciones = docente.asignaciones.select_related("grado", "division", "turno")
    filtros = Q()
    for a in asignaciones:
        filtros |= Q(grado=a.grado, division=a.division, turno=a.turno)
    alumnos = Alumno.objects.filter(filtros).select_related("grado", "division", "turno") if asignaciones else Alumno.objects.none()

    no_leidas_por_alumno = set(
        Notificacion.objects.filter(docente=docente, leido=False).values_list("alumno_id", flat=True)
    )
    return render(request, "core/docente_alumnos.html", {
        "docente": docente, "asignaciones": asignaciones, "alumnos": alumnos,
        "no_leidas_por_alumno": no_leidas_por_alumno,
    })


# ---------------------------------------------------------------------------
# SUPERVISOR
# ---------------------------------------------------------------------------
@role_required(Usuario.ROL_SUPERVISOR)
def supervisor_alumnos(request):
    qs = Alumno.objects.select_related("grado", "division", "turno")
    q = request.GET.get("q", "").strip()
    estado = request.GET.get("estado", "").strip()
    if q:
        qs = qs.filter(Q(nombre__icontains=q) | Q(apellido__icontains=q) | Q(dni__icontains=q))
    if estado:
        qs = qs.filter(estado=estado)
    return render(request, "core/supervisor_alumnos.html", {
        "alumnos": qs, "q": q, "estado": estado, "estados": Alumno.ESTADO_CHOICES,
    })


@role_required(Usuario.ROL_SUPERVISOR)
def supervisor_panorama(request):
    grados = Grado.objects.all()
    por_grado = [{"grado": g, "n": Alumno.objects.filter(grado=g).count()} for g in grados]
    context = {
        "total": Alumno.objects.count(),
        "activos": Alumno.objects.filter(estado=Alumno.ESTADO_ACTIVO).count(),
        "n_grados": grados.count(),
        "n_docentes": Docente.objects.count(),
        "por_grado": por_grado,
    }
    return render(request, "core/supervisor_panorama.html", context)