from django.db import models
from trackings.models import Tracking
from users.models import User
from steps.models import Step

class Revision(models.Model):
    """Revisión de tracking"""

    tracking = models.ForeignKey(
        Tracking,
        on_delete=models.CASCADE,
        related_name='revisions'
    )
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='revisions'
    )
    step = models.IntegerField()

    client = models.CharField(max_length=255, blank=True)
    date = models.DateField(blank=True, null=True)
    time = models.TimeField()
    notes = models.TextField(blank=True)
    files = models.JSONField(default=list, blank=True)
    responsable = models.JSONField(blank=True, null=True)
    status = models.CharField(max_length=50, blank=True)
    documents = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'revisions'
        verbose_name = 'Revisión'
        verbose_name_plural = 'Revisiones'
        ordering = ['-created_at']

    def __str__(self):
        return f"Revision {self.id} - Tracking {self.tracking_id}"

    @property
    def step_info(self):
        """Propiedad que simula el virtual de Mongoose"""
        try:
            return Step.objects.get(number=self.step)
        except Step.DoesNotExist:
            return None