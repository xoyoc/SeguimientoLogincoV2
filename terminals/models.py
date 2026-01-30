from django.db import models

class Terminal(models.Model):
    """Terminal portuaria"""

    text = models.CharField(max_length=255)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'terminals'
        verbose_name = 'Terminal'
        verbose_name_plural = 'Terminales'

    def __str__(self):
        return self.text