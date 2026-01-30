from django.db import models


class Department(models.Model):
    """Departamento organizacional para agrupar usuarios y steps"""

    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Nombre'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Descripción'
    )
    code = models.CharField(
        max_length=10,
        unique=True,
        blank=True,
        null=True,
        verbose_name='Código',
        help_text='Código corto del departamento (ej: OPS, DOC)'
    )
    color = models.CharField(
        max_length=7,
        default='#6366F1',
        verbose_name='Color',
        help_text='Color hexadecimal para gráficos'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Activo'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'departments'
        verbose_name = 'Departamento'
        verbose_name_plural = 'Departamentos'
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def users_count(self):
        # Usar el valor anotado si existe, sino calcular
        if hasattr(self, '_users_count'):
            return self._users_count
        return self.users.count()

    @users_count.setter
    def users_count(self, value):
        self._users_count = value

    @property
    def steps_count(self):
        # Usar el valor anotado si existe, sino calcular
        if hasattr(self, '_steps_count'):
            return self._steps_count
        return self.steps.count()

    @steps_count.setter
    def steps_count(self, value):
        self._steps_count = value
