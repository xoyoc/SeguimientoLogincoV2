from django.db import models

class Line(models.Model):
    """Línea naviera o compañía de transporte"""

    text = models.CharField(max_length=255)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'lines'
        verbose_name = 'Línea'
        verbose_name_plural = 'Líneas'

    def __str__(self):
        return self.text