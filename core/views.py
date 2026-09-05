from functools import wraps

from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .models import (
    Alumno, AsignacionDocente, Division, Docente, Grado, Informe, Padre,
    Turno, Usuario,
)


# ---------- Autenticación y permisos ----------

def home_url_for(usuario):
    return {
        "PADRE": "padre_hijos",
        "DIRECTIVO": "directivo_alumnos",
        "DOCENTE": "docente_alumnos",
        "SUPERVISOR": "supervisor_alumnos",
    }.get(usuario.rol, "login")


def login_required_custom(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        usuario_id = request.session.get("usuario_id")
        if not usuario_id:
            return redirect("login")
        usuario = Usuario.objects.filter(pk=usuario_id).first()
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


# ---------- Login / logout ----------

def login_view(request):
    if request.method == "POST":
        nombre_usuario = request.POST.get("nombre_usuario", "").strip()
        contrasena = request.POST.get("contrasena", "")
        usuario = Usuario.objects.filter(nombre_usuario=nombre_usuario).first()
        if usuario and usuario.contrasena == contrasena:
            request.session["usuario_id"] = usuario.id_usuario
            return redirect(home_url_for(usuario))
        messages.error(request, "Usuario o contraseña incorrectos.")
    return render(request, "core/login.html")


def logout_view(request):
    request.session.flush()
    return redirect("login")


# ---------- PADRE ----------

@role_required("PADRE")
def padre_hijos(request):
    padre = Padre.objects.get(usuario=request.usuario)
    hijos = Alumno.objects.filter(vinculos__padre=padre).select_related("grado", "division", "turno")
    return render(request, "core/padre_hijos.html", {"usuario": request.usuario, "hijos": hijos})


# ---------- FICHA DE ALUMNO (compartida por los 4 roles) ----------

@login_required_custom
def alumno_detail(request, id_alumno):
    usuario = request.usuario
    alumno = get_object_or_404(Alumno.objects.select_related("grado", "division", "turno"), pk=id_alumno)

    puede_informar = False

    if usuario.rol == "PADRE":
        padre = Padre.objects.get(usuario=usuario)
        if not alumno.vinculos.filter(padre=padre).exists():
            messages.error(request, "Ese alumno no está asociado a tu cuenta.")
            return redirect("padre_hijos")
        puede_informar = True

    elif usuario.rol == "DOCENTE":
        docente = Docente.objects.get(usuario=usuario)
        en_asignacion = AsignacionDocente.objects.filter(
            docente=docente, grado=alumno.grado, division=alumno.division, turno=alumno.turno
        ).exists()
        if not en_asignacion:
            messages.error(request, "Ese alumno no corresponde a tus asignaciones.")
            return redirect("docente_alumnos")

    # DIRECTIVO y SUPERVISOR entran sin restricción adicional

    if request.method == "POST" and puede_informar:
        mensaje = request.POST.get("mensaje", "").strip()
        if mensaje:
            padre = Padre.objects.get(usuario=usuario)
            Informe.objects.create(
                padre=padre, alumno=alumno, mensaje=mensaje,
                fecha=timezone.localdate(), estado="ENVIADO",
            )
            messages.success(request, "Informe enviado al directivo.")
            return redirect("alumno_detail", id_alumno=alumno.id_alumno)
        messages.error(request, "Escribí un mensaje antes de enviar.")

    return render(request, "core/alumno_detail.html", {
        "usuario": usuario, "alumno": alumno, "puede_informar": puede_informar,
    })


# ---------- DIRECTIVO ----------

@role_required("DIRECTIVO")
def directivo_alumnos(request):
    qs = Alumno.objects.select_related("grado", "division", "turno")
    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(Q(nombre__icontains=q) | Q(apellido__icontains=q) | Q(dni__icontains=q))
    return render(request, "core/directivo_alumnos.html", {"usuario": request.usuario, "alumnos": qs, "q": q})


@role_required("DIRECTIVO")
def alumno_form(request, id_alumno=None):
    alumno = get_object_or_404(Alumno, pk=id_alumno) if id_alumno else None
    grados = Grado.objects.all()
    turnos = Turno.objects.all()
    grado_sel = request.POST.get("id_grado") or (alumno.grado_id if alumno else None)
    divisiones = Division.objects.filter(grado_id=grado_sel) if grado_sel else Division.objects.none()

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
                estado=request.POST.get("estado", "ACTIVO"),
            )
            if alumno:
                for k, v in data.items():
                    setattr(alumno, k, v)
                alumno.save()
                messages.success(request, "Alumno actualizado.")
            else:
                Alumno.objects.create(**data)
                messages.success(request, "Alumno creado.")
            return redirect("directivo_alumnos")

    return render(request, "core/alumno_form.html", {
        "usuario": request.usuario, "alumno": alumno, "grados": grados,
        "turnos": turnos, "divisiones": divisiones,
        "grado_sel": int(grado_sel) if grado_sel else None,
    })


@role_required("DIRECTIVO")
def alumno_eliminar(request, id_alumno):
    alumno = get_object_or_404(Alumno, pk=id_alumno)
    if request.method == "POST":
        alumno.delete()
        messages.success(request, "Alumno eliminado.")
        return redirect("directivo_alumnos")
    return render(request, "core/alumno_eliminar.html", {"usuario": request.usuario, "alumno": alumno})


@role_required("DIRECTIVO")
def directivo_informes(request):
    informes = Informe.objects.select_related("alumno", "padre__usuario").order_by("-fecha")
    return render(request, "core/directivo_informes.html", {"usuario": request.usuario, "informes": informes})


@role_required("DIRECTIVO")
def informe_cambiar_estado(request, id_informe):
    informe = get_object_or_404(Informe, pk=id_informe)
    if request.method == "POST":
        nuevo_estado = request.POST.get("estado")
        if nuevo_estado in ("ENVIADO", "REVISADO", "RESUELTO"):
            informe.estado = nuevo_estado
            informe.save()
            messages.success(request, f"Estado actualizado a {nuevo_estado}.")
    return redirect("directivo_informes")


# ---------- DOCENTE ----------

@role_required("DOCENTE")
def docente_alumnos(request):
    docente = Docente.objects.get(usuario=request.usuario)
    asignaciones = AsignacionDocente.objects.filter(docente=docente).select_related("grado", "division", "turno")
    filtros = Q()
    for a in asignaciones:
        filtros |= Q(grado=a.grado, division=a.division, turno=a.turno)
    alumnos = Alumno.objects.filter(filtros).select_related("grado", "division", "turno") if asignaciones else Alumno.objects.none()
    return render(request, "core/docente_alumnos.html", {
        "usuario": request.usuario, "docente": docente, "asignaciones": asignaciones, "alumnos": alumnos,
    })


# ---------- SUPERVISOR ----------

@role_required("SUPERVISOR")
def supervisor_alumnos(request):
    qs = Alumno.objects.select_related("grado", "division", "turno")
    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(Q(nombre__icontains=q) | Q(apellido__icontains=q) | Q(dni__icontains=q))
    return render(request, "core/supervisor_alumnos.html", {"usuario": request.usuario, "alumnos": qs, "q": q})