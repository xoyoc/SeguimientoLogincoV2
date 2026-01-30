from django.db import models

class Step(models.Model):
    """Paso del proceso de tracking"""

    number = models.IntegerField(blank=True, null=True, unique=True)
    description = models.CharField(max_length=255, blank=True)
    etapa = models.IntegerField(blank=True, null=True)  # O ForeignKey si hay una tabla Etapa
    department = models.ForeignKey(
        'departments.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='steps',
        verbose_name='Departamento'
    )
    directory = models.CharField(max_length=255, blank=True)
    imp = models.BooleanField(default=False)  # Importación
    exp = models.BooleanField(default=False)  # Exportación
    button = models.BooleanField(default=False)
    is_fixed = models.BooleanField(default=False)  # Paso obligatorio que no se puede remover

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'steps'
        verbose_name = 'Paso'
        verbose_name_plural = 'Pasos'
        ordering = ['number']

    def __str__(self):
        return f"Paso {self.number}: {self.description}"