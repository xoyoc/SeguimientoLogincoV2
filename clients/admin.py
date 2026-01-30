from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Client, ClientStep, DocumentCategory, ClientDocument,
    ClientManifest, ClientPhoto, SATVerification
)


class ClientStepInline(admin.TabularInline):
    """Inline para configurar los pasos del cliente"""
    model = ClientStep
    extra = 1
    autocomplete_fields = ['step']
    fields = ('step', 'order', 'is_active')
    ordering = ('order', 'step__number')

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('step')


class ClientDocumentInline(admin.TabularInline):
    """Inline para ver documentos del cliente"""
    model = ClientDocument
    extra = 0
    fields = ('category', 'name', 'status', 'expiration_date', 'uploaded_by')
    readonly_fields = ('uploaded_by',)
    ordering = ('category__order', '-created_at')

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('category', 'uploaded_by')


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    """Configuracion del admin para el modelo Client"""

    list_display = (
        'company', 'rfc', 'city', 'state', 'phone', 'user',
        'expediente_status', 'show', 'steps_count', 'created_at'
    )
    list_filter = ('show', 'expediente_completo', 'state', 'city')
    search_fields = ('company', 'rfc', 'phone', 'street', 'city', 'state', 'notes', 'razon_social')
    ordering = ('company',)
    inlines = [ClientStepInline, ClientDocumentInline]

    fieldsets = (
        ('Informacion de la Empresa', {
            'fields': ('user', 'company', 'rfc', 'phone')
        }),
        ('Datos de Cumplimiento RGCE 1.4.14', {
            'fields': (
                'razon_social', 'regimen_fiscal',
                'representante_legal_nombre', 'representante_legal_rfc', 'representante_legal_curp'
            ),
            'classes': ('collapse',)
        }),
        ('Direccion Fiscal', {
            'fields': ('street', 'ext_number', 'int_number', 'suburb', 'zip_code', 'locality', 'city', 'state')
        }),
        ('Domicilio de Operaciones', {
            'fields': (
                'domicilio_operaciones_calle', 'domicilio_operaciones_numero_ext',
                'domicilio_operaciones_numero_int', 'domicilio_operaciones_colonia',
                'domicilio_operaciones_cp', 'domicilio_operaciones_ciudad',
                'domicilio_operaciones_estado'
            ),
            'classes': ('collapse',)
        }),
        ('Estado del Expediente', {
            'fields': ('expediente_completo', 'ultima_verificacion_expediente'),
            'classes': ('collapse',)
        }),
        ('Informacion Adicional', {
            'fields': ('notes', 'flex', 'show')
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ('created_at', 'updated_at', 'ultima_verificacion_expediente')

    def steps_count(self, obj):
        """Muestra el numero de pasos configurados para el cliente"""
        return obj.client_steps.filter(is_active=True).count()
    steps_count.short_description = 'Pasos'

    def expediente_status(self, obj):
        """Muestra el estado del expediente"""
        if obj.expediente_completo:
            return format_html('<span style="color: green;">Completo</span>')
        else:
            percentage = obj.calcular_completitud_expediente()
            return format_html('<span style="color: orange;">{}%</span>', percentage)
    expediente_status.short_description = 'Expediente'


@admin.register(ClientStep)
class ClientStepAdmin(admin.ModelAdmin):
    """Admin independiente para ClientStep"""
    list_display = ('client', 'step', 'order', 'is_active', 'created_at')
    list_filter = ('is_active', 'client', 'step__imp', 'step__exp')
    search_fields = ('client__company', 'step__description')
    autocomplete_fields = ['client', 'step']
    ordering = ('client', 'order', 'step__number')


@admin.register(DocumentCategory)
class DocumentCategoryAdmin(admin.ModelAdmin):
    """Admin para categorias de documentos"""
    list_display = ('name', 'code', 'is_required', 'validity_months', 'order', 'documents_count')
    list_filter = ('is_required',)
    search_fields = ('name', 'code', 'description')
    ordering = ('order', 'name')

    def documents_count(self, obj):
        return obj.documents.count()
    documents_count.short_description = 'Documentos'


@admin.register(ClientDocument)
class ClientDocumentAdmin(admin.ModelAdmin):
    """Admin para documentos de clientes"""
    list_display = (
        'client', 'category', 'name', 'status_badge', 'expiration_badge',
        'uploaded_by', 'created_at'
    )
    list_filter = ('status', 'category', 'client')
    search_fields = ('client__company', 'name', 'description', 'original_filename')
    autocomplete_fields = ['client', 'category', 'uploaded_by', 'reviewed_by']
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)

    fieldsets = (
        ('Documento', {
            'fields': ('client', 'category', 'name', 'description', 'file')
        }),
        ('Metadatos del Archivo', {
            'fields': ('original_filename', 'file_size', 'mime_type'),
            'classes': ('collapse',)
        }),
        ('Fechas', {
            'fields': ('document_date', 'expiration_date')
        }),
        ('Estado y Revision', {
            'fields': ('status', 'reviewed_by', 'reviewed_at', 'review_notes')
        }),
        ('Auditoria', {
            'fields': ('uploaded_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ('original_filename', 'file_size', 'mime_type', 'created_at', 'updated_at')

    def status_badge(self, obj):
        colors = {
            'PENDIENTE': 'orange',
            'APROBADO': 'green',
            'RECHAZADO': 'red',
            'VENCIDO': 'gray',
        }
        return format_html(
            '<span style="color: {};">{}</span>',
            colors.get(obj.status, 'black'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Estado'

    def expiration_badge(self, obj):
        if not obj.expiration_date:
            return '-'
        if obj.is_expired:
            return format_html('<span style="color: red;">Vencido</span>')
        days = obj.days_until_expiration
        if days <= 30:
            return format_html('<span style="color: orange;">{} dias</span>', days)
        return format_html('{} dias', days)
    expiration_badge.short_description = 'Vencimiento'


@admin.register(ClientManifest)
class ClientManifestAdmin(admin.ModelAdmin):
    """Admin para manifestaciones de clientes"""
    list_display = (
        'client', 'manifest_type', 'signed_by_name', 'signature_date',
        'is_active', 'created_by'
    )
    list_filter = ('manifest_type', 'is_active')
    search_fields = ('client__company', 'signed_by_name', 'content')
    autocomplete_fields = ['client', 'created_by']
    ordering = ('-signature_date',)


@admin.register(ClientPhoto)
class ClientPhotoAdmin(admin.ModelAdmin):
    """Admin para fotografias de clientes"""
    list_display = ('client', 'photo_type', 'caption', 'taken_date', 'uploaded_by', 'created_at')
    list_filter = ('photo_type', 'client')
    search_fields = ('client__company', 'caption', 'location_description')
    autocomplete_fields = ['client', 'uploaded_by']
    ordering = ('-created_at',)


@admin.register(SATVerification)
class SATVerificationAdmin(admin.ModelAdmin):
    """Admin para verificaciones SAT"""
    list_display = (
        'client', 'status_badge', 'is_in_efos', 'is_in_edos',
        'verification_method', 'verified_by', 'verification_date'
    )
    list_filter = ('status', 'verification_method', 'is_in_efos', 'is_in_edos')
    search_fields = ('client__company', 'client__rfc', 'notes')
    autocomplete_fields = ['client', 'verified_by']
    ordering = ('-verification_date',)

    def status_badge(self, obj):
        colors = {
            'LIMPIO': 'green',
            'PRESUNTO': 'orange',
            'DEFINITIVO': 'red',
            'ERROR': 'gray',
        }
        return format_html(
            '<span style="color: {};">{}</span>',
            colors.get(obj.status, 'black'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Estado'
