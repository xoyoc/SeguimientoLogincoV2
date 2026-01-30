from django.contrib import admin
from .models import Terminal


@admin.register(Terminal)
class TerminalAdmin(admin.ModelAdmin):
    """Configuración del admin para el modelo Terminal"""
    
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
