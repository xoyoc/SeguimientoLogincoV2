from django.db import models
from shipments.models import Shipment

class Tracking(models.Model):
    """Seguimiento de envío"""

    STATUS_CHOICES = [
        ('PENDING', 'Pendiente'),
        ('IN_PROGRESS', 'En Progreso'),
        ('COMPLETED', 'Completado'),
        ('CANCELLED', 'Cancelado'),
    ]

    shipment = models.ForeignKey(
        Shipment,
        on_delete=models.CASCADE,
        related_name='trackings'
    )
    step = models.IntegerField()
    assigned_to = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, blank=True)
    finish_date = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'trackings'
        verbose_name = 'Tracking'
        verbose_name_plural = 'Trackings'
        ordering = ['shipment', 'step']

    def __str__(self):
        return f"Tracking {self.id} - Shipment {self.shipment_id} - Step {self.step}"