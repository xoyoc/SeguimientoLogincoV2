"""
Notification models for RGCE 1.4.14 compliance alerts.

Handles notifications for:
- Document expiration warnings
- Expired documents
- Incomplete expedientes
- SAT verification alerts
"""

from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class Notification(models.Model):
    """
    System notification for compliance alerts.
    Uses GenericForeignKey to link to any model (ClientDocument, Client, etc.)
    """

    NOTIFICATION_TYPES = [
        ('DOCUMENT_EXPIRING', 'Documento por vencer'),
        ('DOCUMENT_EXPIRED', 'Documento vencido'),
        ('DOCUMENT_REJECTED', 'Documento rechazado'),
        ('EXPEDIENTE_INCOMPLETE', 'Expediente incompleto'),
        ('SAT_ALERT', 'Alerta SAT (EFOS/EDOS)'),
        ('SAT_VERIFICATION', 'Verificación SAT completada'),
        ('GENERAL', 'Notificación general'),
    ]

    PRIORITY_CHOICES = [
        ('LOW', 'Baja'),
        ('MEDIUM', 'Media'),
        ('HIGH', 'Alta'),
        ('URGENT', 'Urgente'),
    ]

    # Basic notification info
    notification_type = models.CharField(
        max_length=30,
        choices=NOTIFICATION_TYPES,
        default='GENERAL',
        verbose_name='Tipo'
    )
    title = models.CharField(max_length=255, verbose_name='Título')
    message = models.TextField(verbose_name='Mensaje')
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='MEDIUM',
        verbose_name='Prioridad'
    )

    # Generic relation to any object
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name='Tipo de contenido'
    )
    object_id = models.PositiveIntegerField(null=True, blank=True, verbose_name='ID del objeto')
    content_object = GenericForeignKey('content_type', 'object_id')

    # Direct relation to client for easier filtering
    related_client = models.ForeignKey(
        'clients.Client',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications',
        verbose_name='Cliente relacionado'
    )

    # Recipients and read status
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications',
        verbose_name='Destinatario'
    )
    is_read = models.BooleanField(default=False, verbose_name='Leída')
    read_at = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de lectura')

    # Email notification tracking
    email_sent = models.BooleanField(default=False, verbose_name='Email enviado')
    email_sent_at = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de envío de email')

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Última actualización')

    class Meta:
        verbose_name = 'Notificación'
        verbose_name_plural = 'Notificaciones'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['notification_type', 'is_read']),
            models.Index(fields=['related_client', 'is_read']),
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['priority', 'is_read']),
        ]

    def __str__(self):
        return f"{self.get_notification_type_display()}: {self.title}"

    def mark_as_read(self):
        """Mark the notification as read."""
        from django.utils import timezone
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])

    @property
    def priority_color(self):
        """Return CSS color class based on priority."""
        colors = {
            'LOW': 'gray',
            'MEDIUM': 'blue',
            'HIGH': 'yellow',
            'URGENT': 'red',
        }
        return colors.get(self.priority, 'gray')

    @property
    def type_icon(self):
        """Return icon name based on notification type."""
        icons = {
            'DOCUMENT_EXPIRING': 'clock',
            'DOCUMENT_EXPIRED': 'exclamation-circle',
            'DOCUMENT_REJECTED': 'x-circle',
            'EXPEDIENTE_INCOMPLETE': 'folder-open',
            'SAT_ALERT': 'shield-exclamation',
            'SAT_VERIFICATION': 'check-circle',
            'GENERAL': 'bell',
        }
        return icons.get(self.notification_type, 'bell')


class NotificationPreference(models.Model):
    """
    User preferences for notifications.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_preferences',
        verbose_name='Usuario'
    )

    # Email preferences
    email_document_expiring = models.BooleanField(
        default=True,
        verbose_name='Email: documentos por vencer'
    )
    email_document_expired = models.BooleanField(
        default=True,
        verbose_name='Email: documentos vencidos'
    )
    email_sat_alerts = models.BooleanField(
        default=True,
        verbose_name='Email: alertas SAT'
    )
    email_expediente_incomplete = models.BooleanField(
        default=False,
        verbose_name='Email: expedientes incompletos'
    )

    # Days before expiration to notify
    expiration_warning_days = models.PositiveIntegerField(
        default=30,
        verbose_name='Días de anticipación para alertas de vencimiento'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Preferencia de notificación'
        verbose_name_plural = 'Preferencias de notificación'

    def __str__(self):
        return f"Preferencias de {self.user}"
