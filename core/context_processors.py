from .models import Usuario, Docente, Notificacion


def usuario_actual(request):
    """Inyecta el usuario logueado (y sus notificaciones si es docente) en cada template."""
    uid = request.session.get("usuario_id")
    if not uid:
        return {}
    usuario = Usuario.objects.filter(pk=uid).first()
    if not usuario:
        return {}
    ctx = {"usuario_actual": usuario}
    if usuario.rol == Usuario.ROL_DOCENTE:
        docente = Docente.objects.filter(usuario=usuario).first()
        if docente:
            notifs = Notificacion.objects.filter(docente=docente).select_related("alumno")
            ctx["notificaciones"] = notifs[:12]
            ctx["notificaciones_no_leidas"] = notifs.filter(leido=False).count()
    return ctx
