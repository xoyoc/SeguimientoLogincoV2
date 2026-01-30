from django.contrib import admin
from .models import Line


@admin.register(Line)
class LineAdmin(admin.ModelAdmin):
    """Configuración del admin para el modelo Line"""
    
    list_display = ('id', 'text', 'created_at', 'updated_at')
    search_fields = ('text',)
    ordering = ('text',)
    
    fieldsets = (
        ('Información', {
            'fields': ('text',)
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
