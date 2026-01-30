from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """Usuario del sistema con autenticación"""

    # Los campos username, password, email ya vienen de AbstractUser
    # Sobreescribir email para hacerlo opcional si es necesario
    email = models.EmailField(blank=True, null=True)
    
    # Evitar clashes con el modelo User de Django
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='custom_user_set',
        related_query_name='custom_user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='custom_user_set',
        related_query_name='custom_user',
    )

    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    company = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    flex = models.JSONField(default=list, blank=True)
    department = models.ForeignKey(
        'departments.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
        verbose_name='Departamento'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def __str__(self):
        return f"{self.first_name} {self.last_name}" if self.first_name else self.username

    @property
    def is_client_user(self):
        """Verifica si el usuario es un usuario de cliente (no staff ni superuser)"""
        if self.is_staff or self.is_superuser:
            return False
        return self.clients.exists()

    @property
    def get_client(self):
        """Obtiene el cliente asociado al usuario (si existe)"""
        return self.clients.first()

    @property
    def is_agency_user(self):
        """Verifica si el usuario es de la agencia aduanal (staff pero no superuser)"""
        return self.is_staff and not self.is_superuser