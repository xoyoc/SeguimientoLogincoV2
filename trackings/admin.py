from django.contrib import admin
from django.utils.html import format_html
from .models import Tracking


@admin.register(Tracking)
class TrackingAdmin(admin.ModelAdmin):
    """Administración de Seguimientos"""
    
    list_display = (
        'id',
        'shipment_reference',
        'step',
        'assigned_to',
        'status_badge',
        'finish_date',
        'created_at',
    )
    
    list_filter = (
        'status',
        'step',
        'created_at',
        'finish_date',
    )
    
    search_fields = (
        'shipment__reference',
        'shipment__reference_client',
        'assigned_to',
    )
    
    list_per_page = 50
    
    date_hierarchy = 'created_at'
    
    readonly_fields = (
        'created_at',
        'updated_at',
        'shipment_details',
    )
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'shipment',
                'shipment_details',
                'step',
            )
        }),
        ('Asignación', {
            'fields': (
                'assigned_to',
                'status',
            )
        }),
        ('Fechas', {
            'fields': (
                'finish_date',
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',),
        }),
    )
    
    autocomplete_fields = ['shipment']
    
    def shipment_reference(self, obj):
        """Referencia del envío"""
        if obj.shipment:
            return obj.shipment.reference or f'ID: {obj.shipment.id}'
        return '-'
    shipment_reference.short_description = 'Envío'
    
    def status_badge(self, obj):
        """Badge colorido para el estado"""
        status_colors = {
            'PENDING': ('#FBBF24', 'PENDIENTE'),
            'IN_PROGRESS': ('#3B82F6', 'EN PROGRESO'),
            'COMPLETED': ('#10B981', 'COMPLETADO'),
            'CANCELLED': ('#EF4444', 'CANCELADO'),
        }
        
        color, text = status_colors.get(obj.status, ('#6B7280', obj.status or 'SIN ESTADO'))
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 4px; font-size: 11px; font-weight: bold;">{}</span>',
            color, text
        )
    status_badge.short_description = 'Estado'
    
    def shipment_details(self, obj):
        """Detalles del envío relacionado"""
        if not obj.shipment:
            return 'Sin envío asociado'
        
        ship = obj.shipment
        return format_html(
            '<strong>Referencia:</strong> {}<br>'
            '<strong>Cliente:</strong> {}<br>'
            '<strong>Tipo:</strong> {}<br>'
            '<strong>Mercancía:</strong> {}',
            ship.reference or 'N/A',
            ship.client.company if ship.client else 'N/A',
            ship.get_type_display(),
            ship.merchandise or 'N/A'
        )
    shipment_details.short_description = 'Detalles del Envío'
    
    def get_queryset(self, request):
        """Optimizar consultas"""
        qs = super().get_queryset(request)
        return qs.select_related('shipment', 'shipment__client')
    
    actions = ['mark_as_completed', 'mark_as_in_progress', 'mark_as_cancelled']
    
    def mark_as_completed(self, request, queryset):
        """Marcar como completado"""
        from django.utils import timezone
        updated = queryset.update(status='COMPLETED', finish_date=timezone.now())
        self.message_user(request, f'{updated} seguimiento(s) marcado(s) como completado.')
    mark_as_completed.short_description = 'Marcar como Completado'
    
    def mark_as_in_progress(self, request, queryset):
        """Marcar como en progreso"""
        updated = queryset.update(status='IN_PROGRESS')
        self.message_user(request, f'{updated} seguimiento(s) marcado(s) como en progreso.')
    mark_as_in_progress.short_description = 'Marcar como En Progreso'
    
    def mark_as_cancelled(self, request, queryset):
        """Marcar como cancelado"""
        updated = queryset.update(status='CANCELLED')
        self.message_user(request, f'{updated} seguimiento(s) marcado(s) como cancelado.')
    mark_as_cancelled.short_description = 'Marcar como Cancelado'
