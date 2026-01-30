from django.contrib import admin
from django.utils.html import format_html
from .models import Shipment, Container


class ContainerInline(admin.TabularInline):
    """Inline para contenedores"""
    model = Container
    extra = 1
    fields = ('number', 'size')


@admin.register(Container)
class ContainerAdmin(admin.ModelAdmin):
    """Administración de Contenedores"""
    list_display = ('number', 'size', 'shipment', 'created_at')
    list_filter = ('size', 'created_at')
    search_fields = ('number', 'shipment__reference')
    raw_id_fields = ('shipment',)


@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    """Administración de Envíos"""

    inlines = [ContainerInline]

    list_display = (
        'id',
        'reference',
        'reference_client',
        'client_name',
        'type_badge',
        'arrival_date',
        'assigned_to',
        'merchandise',
        'transport',
        'regimen',
        'containers_count',
        'created_at',
    )
    
    list_filter = (
        'type',
        'arrival_date',
        'transport',
        'regimen',
        'cr_checked',
        'created_at',
        'assigned_to',
    )
    
    search_fields = (
        'reference',
        'reference_client',
        'client__company',
        'merchandise',
        'vessel',
        'notes',
        'id',
    )
    
    list_per_page = 50
    
    date_hierarchy = 'arrival_date'
    
    readonly_fields = (
        'created_at',
        'updated_at',
        'containers_display',
        'executive_display',
    )
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'reference',
                'reference_client',
                'client',
                'assigned_to',
            )
        }),
        ('Detalles del Envío', {
            'fields': (
                'type',
                'merchandise',
                'transport',
                'regimen',
                'cr_checked',
            )
        }),
        ('Fecha y Hora', {
            'fields': (
                'arrival_date',
                'arrival_time',
            )
        }),
        ('Transporte', {
            'fields': (
                'terminal',
                'line',
                'vessel',
                'time',
            )
        }),
        ('Contenedores (JSONField - Legacy)', {
            'fields': (
                'containers_display',
                'containers',
            ),
            'classes': ('collapse',),
            'description': 'Datos heredados del JSONField. Los nuevos contenedores se gestionan desde el inline arriba.',
        }),
        ('Información Adicional', {
            'fields': (
                'executive_display',
                'executive',
                'client_data',
                'notes',
            ),
            'classes': ('collapse',),
        }),
        ('Metadatos', {
            'fields': (
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',),
        }),
    )
    
    autocomplete_fields = ['client', 'assigned_to']
    
    def client_name(self, obj):
        """Nombre del cliente"""
        return obj.client.company if obj.client else '-'
    client_name.short_description = 'Cliente'
    
    def type_badge(self, obj):
        """Badge colorido para el tipo de envío"""
        if obj.type == 'IMP':
            color = '#10B981'
            text = 'IMPORTACIÓN'
        else:
            color = '#8B5CF6'
            text = 'EXPORTACIÓN'
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 4px; font-size: 11px; font-weight: bold;">{}</span>',
            color, text
        )
    type_badge.short_description = 'Tipo'
    
    def containers_count(self, obj):
        """Número de contenedores"""
        return obj.container_set.count()
    containers_count.short_description = 'Contenedores'
    
    def containers_display(self, obj):
        """Mostrar contenedores legacy (JSONField) en formato legible"""
        if not obj.containers:
            return 'Sin contenedores en JSONField (legacy)'

        html = '<ul>'
        for container in obj.containers:
            name = container.get('name', 'N/A')
            size = container.get('size', 'N/A')
            html += f'<li><strong>{name}</strong> - {size}</li>'
        html += '</ul>'
        return format_html('{}', html)
    containers_display.short_description = 'Contenedores (Legacy)'
    
    def executive_display(self, obj):
        """Mostrar información del ejecutivo"""
        if not obj.executive:
            return 'Sin ejecutivo asignado'
        
        first_name = obj.executive.get('firstName', '')
        last_name = obj.executive.get('lastName', '')
        email = obj.executive.get('email', '')
        
        return format_html(
            '<strong>{} {}</strong><br><small>{}</small>',
            first_name, last_name, email
        )
    executive_display.short_description = 'Ejecutivo'
    
    def get_queryset(self, request):
        """Optimizar consultas"""
        qs = super().get_queryset(request)
        return qs.select_related('client', 'assigned_to', 'terminal', 'line')
    
    actions = ['mark_as_cr_checked', 'unmark_as_cr_checked']
    
    def mark_as_cr_checked(self, request, queryset):
        """Marcar como CR verificado"""
        updated = queryset.update(cr_checked=True)
        self.message_user(request, f'{updated} envío(s) marcado(s) como CR verificado.')
    mark_as_cr_checked.short_description = 'Marcar como CR verificado'
    
    def unmark_as_cr_checked(self, request, queryset):
        """Desmarcar CR verificado"""
        updated = queryset.update(cr_checked=False)
        self.message_user(request, f'{updated} envío(s) desmarcado(s) de CR verificado.')
    unmark_as_cr_checked.short_description = 'Desmarcar CR verificado'
