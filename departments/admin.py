from django.contrib import admin
from .models import Department


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    """Configuración del admin para Department"""

    list_display = ('name', 'code', 'users_count', 'steps_count', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'code', 'description')
    ordering = ('name',)

    fieldsets = (
        ('Información General', {
            'fields': ('name', 'code', 'description')
        }),
        ('Apariencia', {
            'fields': ('color',)
        }),
        ('Estado', {
            'fields': ('is_active',)
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ('created_at', 'updated_at')

    def users_count(self, obj):
        return obj.users.count()
    users_count.short_description = 'Usuarios'

    def steps_count(self, obj):
        return obj.steps.count()
    steps_count.short_description = 'Pasos'
