from django import forms
from django.core.validators import FileExtensionValidator
from .models import (
    Client, ClientStep, DocumentCategory, ClientDocument,
    ClientManifest, ClientPhoto, SATVerification
)
from steps.models import Step


# Estilos comunes de Tailwind CSS
INPUT_CLASS = 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500'
CHECKBOX_CLASS = 'rounded border-gray-300 text-indigo-600 shadow-sm focus:border-indigo-500 focus:ring-indigo-500'
SELECT_CLASS = 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500'
TEXTAREA_CLASS = 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500'


class ClientForm(forms.ModelForm):
    """Formulario para crear/editar clientes"""

    class Meta:
        model = Client
        fields = [
            'company', 'rfc', 'phone', 'street', 'ext_number', 'int_number',
            'suburb', 'zip_code', 'locality', 'city', 'state', 'notes', 'show', 'user'
        ]
        widgets = {
            'company': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'placeholder': 'Nombre de la empresa'
            }),
            'rfc': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'placeholder': 'RFC (13 caracteres)',
                'maxlength': '13'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'placeholder': 'Telefono'
            }),
            'street': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'placeholder': 'Calle'
            }),
            'ext_number': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'placeholder': 'No. Exterior'
            }),
            'int_number': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'placeholder': 'No. Interior'
            }),
            'suburb': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'placeholder': 'Colonia'
            }),
            'zip_code': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'placeholder': 'Codigo Postal'
            }),
            'locality': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'placeholder': 'Localidad'
            }),
            'city': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'placeholder': 'Ciudad'
            }),
            'state': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'placeholder': 'Estado'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'rows': 3,
                'placeholder': 'Notas adicionales'
            }),
            'show': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-indigo-600 shadow-sm focus:border-indigo-500 focus:ring-indigo-500'
            }),
            'user': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar usuarios para mostrar solo los que no son staff ni superusuarios
        from users.models import User
        self.fields['user'].queryset = User.objects.filter(
            is_staff=False,
            is_superuser=False
        ).order_by('first_name', 'last_name', 'username')
        self.fields['user'].label_from_instance = lambda obj: (
            f"{obj.first_name} {obj.last_name}" if obj.first_name else obj.username
        )


class ClientStepForm(forms.ModelForm):
    """Formulario para asignar pasos a un cliente"""

    class Meta:
        model = ClientStep
        fields = ['step', 'order', 'is_active']
        widgets = {
            'step': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'min': 0
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-indigo-600 shadow-sm focus:border-indigo-500 focus:ring-indigo-500'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['step'].queryset = Step.objects.all().order_by('number')
        self.fields['step'].label_from_instance = lambda obj: f"{obj.number} - {obj.description}"


class ClientComplianceForm(forms.ModelForm):
    """Formulario para datos de cumplimiento RGCE 1.4.14"""

    class Meta:
        model = Client
        fields = [
            'razon_social', 'regimen_fiscal',
            'representante_legal_nombre', 'representante_legal_rfc', 'representante_legal_curp',
            'domicilio_operaciones_calle', 'domicilio_operaciones_numero_ext',
            'domicilio_operaciones_numero_int', 'domicilio_operaciones_colonia',
            'domicilio_operaciones_cp', 'domicilio_operaciones_ciudad',
            'domicilio_operaciones_estado',
        ]
        widgets = {
            'razon_social': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Razón social completa'
            }),
            'regimen_fiscal': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Ej: Régimen General de Ley Personas Morales'
            }),
            'representante_legal_nombre': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Nombre completo del representante legal'
            }),
            'representante_legal_rfc': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'RFC del representante (13 caracteres)',
                'maxlength': '13'
            }),
            'representante_legal_curp': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'CURP del representante (18 caracteres)',
                'maxlength': '18'
            }),
            'domicilio_operaciones_calle': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Calle del domicilio de operaciones'
            }),
            'domicilio_operaciones_numero_ext': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'No. Exterior'
            }),
            'domicilio_operaciones_numero_int': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'No. Interior'
            }),
            'domicilio_operaciones_colonia': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Colonia'
            }),
            'domicilio_operaciones_cp': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Código Postal'
            }),
            'domicilio_operaciones_ciudad': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Ciudad'
            }),
            'domicilio_operaciones_estado': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Estado'
            }),
        }


class ClientDocumentForm(forms.ModelForm):
    """Formulario para subir documentos del expediente"""

    class Meta:
        model = ClientDocument
        fields = ['category', 'name', 'description', 'file', 'document_date', 'expiration_date']
        widgets = {
            'category': forms.Select(attrs={'class': SELECT_CLASS}),
            'name': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Nombre descriptivo del documento'
            }),
            'description': forms.Textarea(attrs={
                'class': TEXTAREA_CLASS,
                'rows': 2,
                'placeholder': 'Descripción adicional (opcional)'
            }),
            'file': forms.FileInput(attrs={
                'class': 'mt-1 block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100',
                'accept': '.pdf,.jpg,.jpeg,.png,.tiff,.tif'
            }),
            'document_date': forms.DateInput(attrs={
                'class': INPUT_CLASS,
                'type': 'date'
            }),
            'expiration_date': forms.DateInput(attrs={
                'class': INPUT_CLASS,
                'type': 'date'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = DocumentCategory.objects.all().order_by('order')
        self.fields['description'].required = False
        self.fields['document_date'].required = False
        self.fields['expiration_date'].required = False

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Validar tamaño (máx 10MB)
            if file.size > 10 * 1024 * 1024:
                raise forms.ValidationError('El archivo no puede exceder 10MB')
            # Validar tipos permitidos
            allowed_types = [
                'application/pdf',
                'image/jpeg',
                'image/png',
                'image/tiff'
            ]
            if hasattr(file, 'content_type') and file.content_type not in allowed_types:
                raise forms.ValidationError('Solo se permiten archivos PDF, JPG, PNG o TIFF')
        return file


class ClientDocumentReviewForm(forms.ModelForm):
    """Formulario para revisar/aprobar documentos"""

    class Meta:
        model = ClientDocument
        fields = ['status', 'review_notes']
        widgets = {
            'status': forms.Select(attrs={'class': SELECT_CLASS}),
            'review_notes': forms.Textarea(attrs={
                'class': TEXTAREA_CLASS,
                'rows': 3,
                'placeholder': 'Notas de la revisión (motivo de rechazo, observaciones, etc.)'
            }),
        }


class ClientManifestForm(forms.ModelForm):
    """Formulario para crear manifestaciones del cliente"""

    class Meta:
        model = ClientManifest
        fields = [
            'manifest_type', 'content', 'signed_by_name',
            'signed_by_position', 'signature_date', 'signature_place',
            'signed_document'
        ]
        widgets = {
            'manifest_type': forms.Select(attrs={'class': SELECT_CLASS}),
            'content': forms.Textarea(attrs={
                'class': TEXTAREA_CLASS,
                'rows': 6,
                'placeholder': 'Texto completo de la manifestación bajo protesta de decir verdad...'
            }),
            'signed_by_name': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Nombre completo del firmante'
            }),
            'signed_by_position': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Cargo o puesto (Ej: Representante Legal)'
            }),
            'signature_date': forms.DateInput(attrs={
                'class': INPUT_CLASS,
                'type': 'date'
            }),
            'signature_place': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Ciudad donde se firma'
            }),
            'signed_document': forms.FileInput(attrs={
                'class': 'mt-1 block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100',
                'accept': '.pdf,.jpg,.jpeg,.png'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['signed_by_position'].required = False
        self.fields['signature_place'].required = False
        self.fields['signed_document'].required = False

    def clean_signed_document(self):
        file = self.cleaned_data.get('signed_document')
        if file:
            if file.size > 10 * 1024 * 1024:
                raise forms.ValidationError('El archivo no puede exceder 10MB')
        return file


class ClientPhotoForm(forms.ModelForm):
    """Formulario para subir fotografías del lugar de operaciones"""

    class Meta:
        model = ClientPhoto
        fields = ['photo_type', 'image', 'caption', 'taken_date', 'location_description']
        widgets = {
            'photo_type': forms.Select(attrs={'class': SELECT_CLASS}),
            'image': forms.FileInput(attrs={
                'class': 'mt-1 block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100',
                'accept': 'image/*'
            }),
            'caption': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Descripción breve de la foto'
            }),
            'taken_date': forms.DateInput(attrs={
                'class': INPUT_CLASS,
                'type': 'date'
            }),
            'location_description': forms.TextInput(attrs={
                'class': INPUT_CLASS,
                'placeholder': 'Ubicación (Ej: Almacén principal, Oficinas)'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['caption'].required = False
        self.fields['taken_date'].required = False
        self.fields['location_description'].required = False

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image:
            # Validar tamaño (máx 5MB para fotos)
            if image.size > 5 * 1024 * 1024:
                raise forms.ValidationError('La imagen no puede exceder 5MB')
        return image


class SATVerificationForm(forms.ModelForm):
    """Formulario para registrar verificaciones manuales del SAT"""

    class Meta:
        model = SATVerification
        fields = ['is_in_efos', 'is_in_edos', 'status', 'notes']
        widgets = {
            'is_in_efos': forms.CheckboxInput(attrs={'class': CHECKBOX_CLASS}),
            'is_in_edos': forms.CheckboxInput(attrs={'class': CHECKBOX_CLASS}),
            'status': forms.Select(attrs={'class': SELECT_CLASS}),
            'notes': forms.Textarea(attrs={
                'class': TEXTAREA_CLASS,
                'rows': 3,
                'placeholder': 'Observaciones de la verificación'
            }),
        }


# Plantillas de texto para manifestaciones
MANIFEST_TEMPLATES = {
    'EFOS_EDOS': """Bajo protesta de decir verdad, manifiesto que la empresa {company} con RFC {rfc},
no se encuentra publicada en la lista a que se refiere el artículo 69-B del Código Fiscal de la Federación,
ni en calidad de contribuyente que presuntamente realiza operaciones inexistentes (EDOS),
ni en calidad de contribuyente definitivo (EFOS).

Asimismo, declaro que no tengo conocimiento de haber realizado operaciones con empresas que se encuentren
en dichas listas y que todos los comprobantes fiscales digitales (CFDI) utilizados en mis operaciones
de comercio exterior amparan operaciones reales y legítimas.

Me comprometo a informar de inmediato al agente aduanal si llegara a tener conocimiento de cualquier
circunstancia que pudiera modificar esta declaración.""",

    'DATOS_VERIDICOS': """Bajo protesta de decir verdad, manifiesto que todos los datos, documentos e
información proporcionados para la integración de mi expediente electrónico son verídicos,
actuales y corresponden fielmente a la situación real de la empresa {company} con RFC {rfc}.

Acepto que cualquier falsedad u omisión en esta información puede dar lugar a las responsabilidades
legales correspondientes y a la cancelación de los servicios de comercio exterior.""",
}
