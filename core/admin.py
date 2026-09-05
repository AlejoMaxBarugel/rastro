from django.contrib import admin
from . import models

admin.site.register(models.Usuario)
admin.site.register(models.Directivo)
admin.site.register(models.Supervisor)
admin.site.register(models.Docente)
admin.site.register(models.Padre)
admin.site.register(models.Grado)
admin.site.register(models.Division)
admin.site.register(models.Turno)
admin.site.register(models.AsignacionDocente)
admin.site.register(models.Alumno)
admin.site.register(models.PadreAlumno)
admin.site.register(models.Informe)
admin.site.register(models.InformacionMedica)
admin.site.register(models.PersonaRetiro)
admin.site.register(models.AdaptacionAlumno)
admin.site.register(models.SituacionAsistencia)