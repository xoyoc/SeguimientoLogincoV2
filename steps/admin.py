from django.contrib import admin
from .models import Step


@admin.register(Step)
class StepAdmin(admin.ModelAdmin):
    """Configuración del admin para el modelo Step"""
    
    list_display = ('number', 'description', 'etapa', 'department', 'imp', 'exp', 'button', 'created_at')
    list_filter = ('etapa', 'department', 'imp', 'exp', 'button')
    search_fields = ('description', 'directory')
    ordering = ('number',)
    
    fieldsets = (
        ('Información General', {
            'fields': ('number', 'description', 'etapa', 'directory')
        }),
        ('Configuración', {
            'fields': ('department', 'imp', 'exp', 'button', 'is_fixed')
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
