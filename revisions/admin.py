from django.contrib import admin
from django.utils.html import format_html
from .models import Revision


@admin.register(Revision)
class RevisionAdmin(admin.ModelAdmin):
    """Administración de Revisiones"""
    
    list_display = (
        'id',
        'tracking_info',
        'step',
        'client',
        'assigned_to',
        'status_badge',
        'date',
        'created_at',
    )
    
    list_filter = (
        'status',
        'step',
        'date',
        'created_at',
        'assigned_to',
    )
    
    search_fields = (
        'tracking__shipment__reference',
        'tracking__shipment__reference_client',
        'client',
        'notes',
        'status',
    )
    
    list_per_page = 50
    
    date_hierarchy = 'created_at'
    
    readonly_fields = (
        'created_at',
        'updated_at',
        'tracking_details',
        'files_display',
        'documents_display',
        'responsable_display',
    )
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'tracking',
                'tracking_details',
                'step',
                'assigned_to',
            )
        }),
        ('Detalles de la Revisión', {
            'fields': (
                'client',
                'date',
                'time',
                'status',
            )
        }),
        ('Notas y Archivos', {
            'fields': (
                'notes',
                'files_display',
                'files',
            )
        }),
        ('Documentos', {
            'fields': (
                'documents_display',
                'documents',
            ),
            'classes': ('collapse',),
        }),
        ('Responsable', {
            'fields': (
                'responsable_display',
                'responsable',
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
    
    autocomplete_fields = ['tracking', 'assigned_to']
    
    def tracking_info(self, obj):
        """Información del tracking"""
        if obj.tracking and obj.tracking.shipment:
            ref = obj.tracking.shipment.reference
            return f'{ref} (Step {obj.tracking.step})' if ref else f'ID: {obj.tracking.shipment.id}'
        return '-'
    tracking_info.short_description = 'Tracking'
    
    def status_badge(self, obj):
        """Badge colorido para el estado"""
        if not obj.status:
            return format_html('<span style="color: #9CA3AF;">Sin estado</span>')
        
        # Colores comunes para estados
        if 'finalizado' in obj.status.lower() or 'completado' in obj.status.lower():
            color = '#10B981'
        elif 'proceso' in obj.status.lower() or 'progreso' in obj.status.lower():
            color = '#3B82F6'
        elif 'pendiente' in obj.status.lower():
            color = '#FBBF24'
        elif 'cancelado' in obj.status.lower():
            color = '#EF4444'
        else:
            color = '#6B7280'
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 4px; font-size: 11px; font-weight: bold;">{}</span>',
            color, obj.status.upper()
        )
    status_badge.short_description = 'Estado'
    
    def tracking_details(self, obj):
        """Detalles del tracking"""
        if not obj.tracking:
            return 'Sin tracking asociado'
        
        tracking = obj.tracking
        shipment = tracking.shipment
        
        if not shipment:
            return 'Tracking sin envío asociado'
        
        return format_html(
            '<strong>Envío:</strong> {}<br>'
            '<strong>Cliente:</strong> {}<br>'
            '<strong>Mercancía:</strong> {}<br>'
            '<strong>Paso del Tracking:</strong> {}',
            shipment.reference or f'ID: {shipment.id}',
            shipment.client.company if shipment.client else 'N/A',
            shipment.merchandise or 'N/A',
            tracking.step
        )
    tracking_details.short_description = 'Detalles del Tracking'
    
    def files_display(self, obj):
        """Mostrar archivos en formato legible"""
        if not obj.files or len(obj.files) == 0:
            return 'Sin archivos'
        
        html = '<ul style="margin: 0; padding-left: 20px;">'
        for file_path in obj.files:
            html += f'<li>{file_path}</li>'
        html += '</ul>'
        return format_html('{}', html)
    files_display.short_description = 'Archivos'
    
    def documents_display(self, obj):
        """Mostrar documentos en formato legible"""
        if not obj.documents or len(obj.documents) == 0:
            return 'Sin documentos'
        
        html = '<table style="width: 100%; border-collapse: collapse;">'
        html += '<tr style="background-color: #f3f4f6;"><th style="padding: 8px; text-align: left; border: 1px solid #e5e7eb;">Documento</th><th style="padding: 8px; text-align: left; border: 1px solid #e5e7eb;">Estado</th></tr>'
        
        for doc_name, doc_data in obj.documents.items():
            if isinstance(doc_data, dict):
                state = doc_data.get('state', 'N/A')
            else:
                state = str(doc_data)
            
            # Color según estado
            if 'correct' in state.lower():
                badge_color = '#10B981'
            elif 'incorrect' in state.lower() or 'error' in state.lower():
                badge_color = '#EF4444'
            else:
                badge_color = '#6B7280'
            
            html += f'<tr><td style="padding: 8px; border: 1px solid #e5e7eb;">{doc_name}</td>'
            html += f'<td style="padding: 8px; border: 1px solid #e5e7eb;"><span style="background-color: {badge_color}; color: white; padding: 2px 8px; border-radius: 4px; font-size: 10px;">{state}</span></td></tr>'
        
        html += '</table>'
        return format_html('{}', html)
    documents_display.short_description = 'Documentos'
    
    def responsable_display(self, obj):
        """Mostrar información del responsable"""
        if not obj.responsable:
            return 'Sin responsable asignado'
        
        if isinstance(obj.responsable, dict):
            name = obj.responsable.get('name', 'N/A')
            email = obj.responsable.get('email', '')
            return format_html('<strong>{}</strong><br><small>{}</small>', name, email)
        
        return str(obj.responsable)
    responsable_display.short_description = 'Responsable'
    
    def get_queryset(self, request):
        """Optimizar consultas"""
        qs = super().get_queryset(request)
        return qs.select_related('tracking', 'tracking__shipment', 'tracking__shipment__client', 'assigned_to')
    
    actions = ['export_to_csv']
    
    def export_to_csv(self, request, queryset):
        """Exportar revisiones seleccionadas a CSV"""
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="revisiones.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['ID', 'Tracking', 'Step', 'Cliente', 'Asignado a', 'Estado', 'Fecha', 'Notas'])
        
        for revision in queryset:
            tracking_ref = revision.tracking.shipment.reference if revision.tracking and revision.tracking.shipment else 'N/A'
            writer.writerow([
                revision.id,
                tracking_ref,
                revision.step,
                revision.client,
                str(revision.assigned_to) if revision.assigned_to else 'N/A',
                revision.status,
                revision.date,
                revision.notes[:100] if revision.notes else ''
            ])
        
        return response
    export_to_csv.short_description = 'Exportar a CSV'
