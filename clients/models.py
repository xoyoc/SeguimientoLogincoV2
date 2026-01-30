import os
from datetime import datetime, timedelta
from django.db import models
from django.utils import timezone
from users.models import User
from steps.models import Step
from seguimiento.storage_backends import SecureMediaStorage


def client_document_path(instance, filename):
    """Genera ruta segura para documentos de cliente"""
    client_id = instance.client_id
    category = instance.category.code if instance.category else 'otros'
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    name, ext = os.path.splitext(filename)
    safe_name = ''.join(c for c in name if c.isalnum() or c in '-_')[:50]
    return f"expedientes/{client_id}/{category}/{safe_name}_{timestamp}{ext}"


def client_photo_path(instance, filename):
    """Genera ruta para fotografías de cliente"""
    client_id = instance.client_id
    photo_type = instance.photo_type.lower() if instance.photo_type else 'otros'
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    name, ext = os.path.splitext(filename)
    return f"expedientes/{client_id}/fotos/{photo_type}/{timestamp}{ext}"


def client_manifest_path(instance, filename):
    """Genera ruta para manifestaciones firmadas"""
    client_id = instance.client_id
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    name, ext = os.path.splitext(filename)
    return f"expedientes/{client_id}/manifestaciones/{timestamp}{ext}"


class Client(models.Model):
    """Cliente del sistema"""

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='clients'
    )

    # Información de la empresa
    company = models.CharField(max_length=255, blank=True)
    rfc = models.CharField(max_length=13, blank=True, unique=True, null=True, verbose_name='RFC')
    phone = models.CharField(max_length=50, blank=True)

    # Datos complementarios RGCE 1.4.14
    razon_social = models.CharField(max_length=255, blank=True, verbose_name='Razón Social')
    regimen_fiscal = models.CharField(max_length=100, blank=True, verbose_name='Régimen Fiscal')

    # Representante Legal
    representante_legal_nombre = models.CharField(
        max_length=255, blank=True, verbose_name='Nombre del Representante Legal'
    )
    representante_legal_rfc = models.CharField(
        max_length=13, blank=True, verbose_name='RFC del Representante Legal'
    )
    representante_legal_curp = models.CharField(
        max_length=18, blank=True, verbose_name='CURP del Representante Legal'
    )

    # Dirección Fiscal
    street = models.CharField(max_length=255, blank=True, verbose_name='Calle')
    ext_number = models.CharField(max_length=50, blank=True, verbose_name='Número Exterior')
    int_number = models.CharField(max_length=50, blank=True, verbose_name='Número Interior')
    suburb = models.CharField(max_length=255, blank=True, verbose_name='Colonia')
    zip_code = models.CharField(max_length=20, blank=True, verbose_name='Código Postal')
    locality = models.CharField(max_length=255, blank=True, verbose_name='Localidad')
    city = models.CharField(max_length=255, blank=True, verbose_name='Ciudad')
    state = models.CharField(max_length=255, blank=True, verbose_name='Estado')

    # Domicilio de Operaciones (puede diferir del fiscal)
    domicilio_operaciones_calle = models.CharField(
        max_length=255, blank=True, verbose_name='Calle (Operaciones)'
    )
    domicilio_operaciones_numero_ext = models.CharField(
        max_length=50, blank=True, verbose_name='Número Exterior (Operaciones)'
    )
    domicilio_operaciones_numero_int = models.CharField(
        max_length=50, blank=True, verbose_name='Número Interior (Operaciones)'
    )
    domicilio_operaciones_colonia = models.CharField(
        max_length=255, blank=True, verbose_name='Colonia (Operaciones)'
    )
    domicilio_operaciones_cp = models.CharField(
        max_length=20, blank=True, verbose_name='Código Postal (Operaciones)'
    )
    domicilio_operaciones_ciudad = models.CharField(
        max_length=255, blank=True, verbose_name='Ciudad (Operaciones)'
    )
    domicilio_operaciones_estado = models.CharField(
        max_length=255, blank=True, verbose_name='Estado (Operaciones)'
    )

    # Información adicional
    notes = models.TextField(blank=True)
    flex = models.JSONField(default=list, blank=True)
    show = models.BooleanField(default=True)

    # Estado del expediente RGCE 1.4.14
    expediente_completo = models.BooleanField(
        default=False, verbose_name='Expediente Completo'
    )
    ultima_verificacion_expediente = models.DateTimeField(
        null=True, blank=True, verbose_name='Última Verificación del Expediente'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'clients'
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'

    def __str__(self):
        return f"{self.company}" if self.company else f"Cliente {self.id}"

    @property
    def domicilio_fiscal_completo(self):
        """Retorna la dirección fiscal completa"""
        partes = [
            self.street,
            f"#{self.ext_number}" if self.ext_number else "",
            f"Int. {self.int_number}" if self.int_number else "",
            self.suburb,
            f"C.P. {self.zip_code}" if self.zip_code else "",
            self.city,
            self.state,
        ]
        return ", ".join(p for p in partes if p)

    @property
    def domicilio_operaciones_completo(self):
        """Retorna la dirección de operaciones completa"""
        partes = [
            self.domicilio_operaciones_calle,
            f"#{self.domicilio_operaciones_numero_ext}" if self.domicilio_operaciones_numero_ext else "",
            f"Int. {self.domicilio_operaciones_numero_int}" if self.domicilio_operaciones_numero_int else "",
            self.domicilio_operaciones_colonia,
            f"C.P. {self.domicilio_operaciones_cp}" if self.domicilio_operaciones_cp else "",
            self.domicilio_operaciones_ciudad,
            self.domicilio_operaciones_estado,
        ]
        return ", ".join(p for p in partes if p)

    def calcular_completitud_expediente(self):
        """Calcula el porcentaje de completitud del expediente"""
        categorias_requeridas = DocumentCategory.objects.filter(is_required=True)
        total = categorias_requeridas.count()
        if total == 0:
            return 100

        completadas = 0
        for cat in categorias_requeridas:
            if self.documents.filter(category=cat, status='APROBADO').exists():
                completadas += 1

        return int((completadas / total) * 100)


class ClientStep(models.Model):
    """Pasos personalizados por cliente - el admin selecciona qué pasos aplican"""

    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='client_steps',
        verbose_name='Cliente'
    )
    step = models.ForeignKey(
        Step,
        on_delete=models.CASCADE,
        related_name='client_steps',
        verbose_name='Paso'
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name='Orden',
        help_text='Orden personalizado del paso para este cliente'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Activo',
        help_text='Si el paso está activo para este cliente'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'client_steps'
        verbose_name = 'Paso del Cliente'
        verbose_name_plural = 'Pasos del Cliente'
        unique_together = ['client', 'step']
        ordering = ['order', 'step__number']

    def __str__(self):
        return f"{self.client.company} - Paso {self.step.number}: {self.step.description}"


class DocumentCategory(models.Model):
    """Categoría de documentos según RGCE 1.4.14"""

    code = models.CharField(max_length=30, unique=True, verbose_name='Código')
    name = models.CharField(max_length=100, verbose_name='Nombre de Categoría')
    description = models.TextField(blank=True, verbose_name='Descripción')
    is_required = models.BooleanField(default=True, verbose_name='Obligatorio')
    validity_months = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name='Vigencia en Meses',
        help_text='Dejar vacío si no tiene vigencia'
    )
    order = models.PositiveIntegerField(default=0, verbose_name='Orden')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'document_categories'
        verbose_name = 'Categoría de Documento'
        verbose_name_plural = 'Categorías de Documentos'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class ClientDocument(models.Model):
    """Documento del expediente electrónico del cliente - RGCE 1.4.14"""

    STATUS_CHOICES = [
        ('PENDIENTE', 'Pendiente de Revisión'),
        ('APROBADO', 'Aprobado'),
        ('RECHAZADO', 'Rechazado'),
        ('VENCIDO', 'Vencido'),
    ]

    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='documents',
        verbose_name='Cliente'
    )
    category = models.ForeignKey(
        DocumentCategory,
        on_delete=models.PROTECT,
        related_name='documents',
        verbose_name='Categoría'
    )

    # Archivo
    file = models.FileField(
        upload_to=client_document_path,
        storage=SecureMediaStorage(),
        verbose_name='Archivo'
    )
    original_filename = models.CharField(max_length=255, verbose_name='Nombre Original')
    file_size = models.PositiveIntegerField(default=0, verbose_name='Tamaño (bytes)')
    mime_type = models.CharField(max_length=100, blank=True)

    # Metadatos del documento
    name = models.CharField(max_length=255, verbose_name='Nombre del Documento')
    description = models.TextField(blank=True, verbose_name='Descripción')
    document_date = models.DateField(
        null=True, blank=True,
        verbose_name='Fecha del Documento'
    )
    expiration_date = models.DateField(
        null=True, blank=True,
        verbose_name='Fecha de Vencimiento'
    )

    # Estado y revisión
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDIENTE',
        verbose_name='Estado'
    )
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='reviewed_documents',
        verbose_name='Revisado Por'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de Revisión')
    review_notes = models.TextField(blank=True, verbose_name='Notas de Revisión')

    # Quién subió el documento
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_documents',
        verbose_name='Subido Por'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'client_documents'
        verbose_name = 'Documento del Cliente'
        verbose_name_plural = 'Documentos de Clientes'
        ordering = ['category__order', '-created_at']

    def __str__(self):
        return f"{self.client.company} - {self.name}"

    @property
    def is_expired(self):
        """Verifica si el documento está vencido"""
        if self.expiration_date:
            return self.expiration_date < timezone.now().date()
        return False

    @property
    def days_until_expiration(self):
        """Días hasta el vencimiento (negativo si ya venció)"""
        if self.expiration_date:
            delta = self.expiration_date - timezone.now().date()
            return delta.days
        return None

    def save(self, *args, **kwargs):
        # Calcular fecha de vencimiento automática si la categoría tiene vigencia
        if not self.expiration_date and self.category and self.category.validity_months:
            base_date = self.document_date or timezone.now().date()
            self.expiration_date = base_date + timedelta(days=self.category.validity_months * 30)

        # Actualizar estado si está vencido
        if self.is_expired and self.status == 'APROBADO':
            self.status = 'VENCIDO'

        super().save(*args, **kwargs)


class ClientManifest(models.Model):
    """Manifestación del cliente - Declaraciones obligatorias EFOS/EDOS"""

    MANIFEST_TYPES = [
        ('EFOS', 'No aparecer en lista de EFOS'),
        ('EDOS', 'No aparecer en lista de EDOS'),
        ('EFOS_EDOS', 'No aparecer en listas EFOS/EDOS'),
        ('OPERACIONES_INEXISTENTES', 'No realizar operaciones inexistentes'),
        ('DATOS_VERIDICOS', 'Datos proporcionados son verídicos'),
        ('CONOCIMIENTO_OBLIGACIONES', 'Conocimiento de obligaciones fiscales'),
        ('OTRO', 'Otra manifestación'),
    ]

    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='manifests',
        verbose_name='Cliente'
    )
    manifest_type = models.CharField(
        max_length=30,
        choices=MANIFEST_TYPES,
        verbose_name='Tipo de Manifestación'
    )

    # Contenido de la manifestación
    content = models.TextField(verbose_name='Texto de la Manifestación')

    # Firma
    signed_by_name = models.CharField(max_length=255, verbose_name='Nombre del Firmante')
    signed_by_position = models.CharField(max_length=100, blank=True, verbose_name='Cargo')
    signature_date = models.DateField(verbose_name='Fecha de Firma')
    signature_place = models.CharField(max_length=255, blank=True, verbose_name='Lugar de Firma')

    # Documento escaneado de la manifestación firmada
    signed_document = models.FileField(
        upload_to=client_manifest_path,
        storage=SecureMediaStorage(),
        null=True, blank=True,
        verbose_name='Documento Firmado'
    )

    # Vigencia
    is_active = models.BooleanField(default=True, verbose_name='Vigente')
    superseded_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='supersedes',
        verbose_name='Reemplazada por'
    )

    # Quién registró
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_manifests',
        verbose_name='Creado Por'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'client_manifests'
        verbose_name = 'Manifestación del Cliente'
        verbose_name_plural = 'Manifestaciones de Clientes'
        ordering = ['-signature_date', '-created_at']

    def __str__(self):
        return f"{self.client.company} - {self.get_manifest_type_display()}"


class ClientPhoto(models.Model):
    """Fotografías del lugar de operaciones del cliente - RGCE 1.4.14"""

    PHOTO_TYPES = [
        ('FACHADA', 'Fachada del Inmueble'),
        ('INTERIOR', 'Interior'),
        ('MAQUINARIA', 'Maquinaria y Equipo'),
        ('ALMACEN', 'Almacén'),
        ('PERSONAL', 'Personal Trabajando'),
        ('VEHICULOS', 'Vehículos'),
        ('OTRO', 'Otro'),
    ]

    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='photos',
        verbose_name='Cliente'
    )
    photo_type = models.CharField(
        max_length=20,
        choices=PHOTO_TYPES,
        verbose_name='Tipo de Fotografía'
    )

    # Imagen
    image = models.ImageField(
        upload_to=client_photo_path,
        storage=SecureMediaStorage(),
        verbose_name='Fotografía'
    )

    # Metadatos
    caption = models.CharField(max_length=255, blank=True, verbose_name='Descripción')
    taken_date = models.DateField(null=True, blank=True, verbose_name='Fecha de la Foto')
    location_description = models.CharField(
        max_length=255, blank=True, verbose_name='Ubicación'
    )

    # Geolocalización (opcional)
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True, verbose_name='Latitud'
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True, verbose_name='Longitud'
    )

    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_photos',
        verbose_name='Subido Por'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'client_photos'
        verbose_name = 'Fotografía del Cliente'
        verbose_name_plural = 'Fotografías de Clientes'
        ordering = ['photo_type', '-created_at']

    def __str__(self):
        return f"{self.client.company} - {self.get_photo_type_display()}"


class SATVerification(models.Model):
    """Registro de verificaciones en listas del SAT (69-B EFOS/EDOS)"""

    STATUS_CHOICES = [
        ('LIMPIO', 'Sin irregularidades'),
        ('PRESUNTO', 'En lista de presuntos (EDOS)'),
        ('DEFINITIVO', 'En lista definitiva (EFOS)'),
        ('ERROR', 'Error en consulta'),
    ]

    VERIFICATION_METHOD_CHOICES = [
        ('AUTOMATIC', 'Automática'),
        ('MANUAL', 'Manual'),
    ]

    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='sat_verifications',
        verbose_name='Cliente'
    )

    # Resultado de verificación
    is_in_efos = models.BooleanField(default=False, verbose_name='En lista EFOS')
    is_in_edos = models.BooleanField(default=False, verbose_name='En lista EDOS')

    # Datos de la consulta
    sat_response = models.JSONField(default=dict, blank=True, verbose_name='Respuesta del SAT')
    verification_method = models.CharField(
        max_length=20,
        choices=VERIFICATION_METHOD_CHOICES,
        default='MANUAL',
        verbose_name='Método de Verificación'
    )

    # Estado
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='LIMPIO',
        verbose_name='Estado'
    )

    verified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='sat_verifications',
        verbose_name='Verificado Por'
    )
    notes = models.TextField(blank=True, verbose_name='Notas')

    verification_date = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Verificación')

    class Meta:
        db_table = 'sat_verifications'
        verbose_name = 'Verificación SAT'
        verbose_name_plural = 'Verificaciones SAT'
        ordering = ['-verification_date']

    def __str__(self):
        return f"{self.client.company} - {self.get_status_display()} ({self.verification_date.strftime('%Y-%m-%d')})"
