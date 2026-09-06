from django.urls import path

from . import views

urlpatterns = [
    path("", views.login_view, name="login"),
    path("registro/", views.registro_padre, name="registro_padre"),
    path("logout/", views.logout_view, name="logout"),

    # Padre
    path("padre/hijos/", views.padre_hijos, name="padre_hijos"),

    # Ficha de alumno (compartida)
    path("alumno/<int:id_alumno>/", views.alumno_detail, name="alumno_detail"),

    # Directivo
    path("directivo/alumnos/", views.directivo_alumnos, name="directivo_alumnos"),
    path("directivo/alumnos/nuevo/", views.alumno_form, name="alumno_nuevo"),
    path("directivo/alumnos/<int:id_alumno>/editar/", views.alumno_form, name="alumno_editar"),
    path("directivo/alumnos/<int:id_alumno>/eliminar/", views.alumno_eliminar, name="alumno_eliminar"),
    path("directivo/divisiones-por-grado/", views.divisiones_por_grado, name="divisiones_por_grado"),
    path("directivo/informes/", views.directivo_informes, name="directivo_informes"),
    path("directivo/informes/<int:id_informe>/estado/", views.informe_cambiar_estado, name="informe_cambiar_estado"),

    # Docente
    path("docente/alumnos/", views.docente_alumnos, name="docente_alumnos"),
    path("notificaciones/<int:id_notif>/leer/", views.notificacion_marcar_leida, name="notificacion_leer"),
    path("notificaciones/leer-todas/", views.notificaciones_marcar_todas, name="notificaciones_leer_todas"),

    # Supervisor
    path("supervisor/alumnos/", views.supervisor_alumnos, name="supervisor_alumnos"),
    path("supervisor/panorama/", views.supervisor_panorama, name="supervisor_panorama"),
]