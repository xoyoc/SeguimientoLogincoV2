from django.db import models


class Regimen(models.Model):
    """Régimen aduanal"""

    text = models.CharField(max_length=255, verbose_name='Nombre')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'regimens'
        verbose_name = 'Régimen'
        verbose_name_plural = 'Regímenes'
        ordering = ['text']

    def __str__(self):
        return self.text
