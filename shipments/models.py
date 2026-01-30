from django.db import models
from users.models import User
from clients.models import Client
from terminals.models import Terminal
from lines.models import Line
from regimens.models import Regimen

class Shipment(models.Model):
    """Envío de mercancía"""

    # Tipos de envío
    TYPE_CHOICES = [
        ('IMP', 'Importación'),
        ('EXP', 'Exportación'),
    ]

    # Tipos de transporte
    TRANSPORT_CHOICES = [
        ('CAMION', 'Camión'),
        ('FERROCARRIL', 'Ferrocarril'),
        ('PENDIENTE', 'Pendiente'),
    ]

    assigned_to = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='shipments'
    )
    client = models.ForeignKey(
        Client,
        on_delete=models.PROTECT,
        related_name='shipments'
    )
    client_data = models.JSONField(blank=True, null=True)  # Datos desnormalizados del cliente

    reference = models.CharField(max_length=100, blank=True)
    reference_client = models.CharField(max_length=100, blank=True)

    arrival_date = models.DateField(blank=True, null=True)
    arrival_time = models.TimeField(blank=True, null=True)

    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    merchandise = models.CharField(max_length=255, blank=True)
    transport = models.CharField(max_length=20, choices=TRANSPORT_CHOICES, default='PENDIENTE')
    regimen = models.ForeignKey(
        Regimen,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='shipments',
        verbose_name='Régimen'
    )
    cr_checked = models.BooleanField(default=False)

    terminal = models.ForeignKey(
        Terminal,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='shipments'
    )
    line = models.ForeignKey(
        Line,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='shipments'
    )

    vessel = models.CharField(max_length=100, blank=True)
    time = models.CharField(max_length=50, blank=True)
    executive = models.JSONField(blank=True, null=True)
    notes = models.TextField(blank=True)
    containers = models.JSONField(default=list, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'shipments'
        verbose_name = 'Envío'
        verbose_name_plural = 'Envíos'
        ordering = ['-created_at']

    def __str__(self):
        return f"Shipment {self.id} - {self.reference}"


class Container(models.Model):
    """Contenedor de un envío"""
    shipment = models.ForeignKey(
        Shipment,
        on_delete=models.CASCADE,
        related_name='container_set'
    )
    number = models.CharField(max_length=50, verbose_name='# Contenedor')
    size = models.CharField(max_length=20, verbose_name='Tamaño')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'containers'
        verbose_name = 'Contenedor'
        verbose_name_plural = 'Contenedores'
        ordering = ['id']

    def __str__(self):
        return f"{self.number} - {self.size}"