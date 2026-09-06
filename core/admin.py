from django.contrib import admin

from . import models


@admin.register(models.Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ("id_usuario", "nombre_usuario", "nombre", "apellido", "dni", "rol")
    list_filter = ("rol",)
    search_fields = ("nombre_usuario", "nombre", "apellido", "dni")


@admin.register(models.Alumno)
class AlumnoAdmin(admin.ModelAdmin):
    list_display = ("id_alumno", "nombre", "apellido", "dni", "grado", "division", "turno", "estado")
    list_filter = ("grado", "division", "turno", "estado")
    search_fields = ("nombre", "apellido", "dni")


@admin.register(models.Informe)
class InformeAdmin(admin.ModelAdmin):
    list_display = ("id_informe", "alumno", "padre", "tipo", "fecha", "estado")
    list_filter = ("estado", "tipo")


admin.site.register(models.Directivo)
admin.site.register(models.Supervisor)
admin.site.register(models.Docente)
admin.site.register(models.Padre)
admin.site.register(models.Grado)
admin.site.register(models.Division)
admin.site.register(models.Turno)
admin.site.register(models.AsignacionDocente)
admin.site.register(models.PadreAlumno)
admin.site.register(models.InformacionMedica)
admin.site.register(models.PersonaRetiro)
admin.site.register(models.AdaptacionAlumno)
admin.site.register(models.SituacionAsistencia)
admin.site.register(models.Notificacion)
