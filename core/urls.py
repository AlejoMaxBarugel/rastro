from django.urls import path
from . import views

urlpatterns = [
    path("", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    path("padre/hijos/", views.padre_hijos, name="padre_hijos"),
    path("alumno/<int:id_alumno>/", views.alumno_detail, name="alumno_detail"),

    path("directivo/alumnos/", views.directivo_alumnos, name="directivo_alumnos"),
    path("directivo/alumnos/nuevo/", views.alumno_form, name="alumno_nuevo"),
    path("directivo/alumnos/<int:id_alumno>/editar/", views.alumno_form, name="alumno_editar"),
    path("directivo/alumnos/<int:id_alumno>/eliminar/", views.alumno_eliminar, name="alumno_eliminar"),
    path("directivo/informes/", views.directivo_informes, name="directivo_informes"),
    path("directivo/informes/<int:id_informe>/estado/", views.informe_cambiar_estado, name="informe_cambiar_estado"),

    path("docente/alumnos/", views.docente_alumnos, name="docente_alumnos"),

    path("supervisor/alumnos/", views.supervisor_alumnos, name="supervisor_alumnos"),
]