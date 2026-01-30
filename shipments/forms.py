import re
from datetime import datetime
from django import forms
from django.forms import inlineformset_factory
from django.db.models import Max
from .models import Shipment, Container
from clients.models import Client
from users.models import User
from terminals.models import Terminal
from lines.models import Line


class ShipmentForm(forms.ModelForm):
    """Formulario para crear/editar envíos"""

    # Campos auxiliares para construir la referencia
    ref_initials = forms.CharField(
        max_length=2,
        min_length=2,
        required=True,
        label='Iniciales',
        help_text='2 caracteres después de LC',
        widget=forms.TextInput(attrs={
            'class': 'w-16 py-2 px-2 rounded-r-md border border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 font-mono font-bold text-center',
            'placeholder': 'MJ',
            'maxlength': '2',
            'style': 'text-transform: uppercase;'
        })
    )

    ref_consecutive = forms.CharField(
        max_length=4,
        min_length=1,
        required=True,
        label='Consecutivo',
        help_text='Número consecutivo (se completará con ceros)',
        widget=forms.TextInput(attrs={
            'class': 'w-20 py-2 px-2 rounded-md border border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 font-mono text-center',
            'placeholder': '0001',
            'maxlength': '4',
        })
    )

    def __init__(self, *args, **kwargs):
        # Extraer el usuario del request si se pasa
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Si es edición, extraer valores de la referencia existente y hacer campos solo lectura
        if self.instance and self.instance.pk and self.instance.reference:
            ref = self.instance.reference
            # Patrón: LC + 2 letras + 4 dígitos + / + 2 dígitos
            match = re.match(r'^LC([A-Z]{2})(\d{4})/(\d{2})$', ref.upper())
            if match:
                self.fields['ref_initials'].initial = match.group(1)
                self.fields['ref_consecutive'].initial = match.group(2)

            # Hacer los campos de referencia de solo lectura en edición
            self.fields['ref_initials'].widget.attrs['readonly'] = True
            self.fields['ref_initials'].widget.attrs['class'] = 'w-16 py-2 px-2 rounded-r-md border border-gray-300 shadow-sm font-mono font-bold text-center bg-gray-100 cursor-not-allowed'
            self.fields['ref_consecutive'].widget.attrs['readonly'] = True
            self.fields['ref_consecutive'].widget.attrs['class'] = 'w-20 py-2 px-2 rounded-md border border-gray-300 shadow-sm font-mono text-center bg-gray-100 cursor-not-allowed'
            self.fields['ref_initials'].required = False
            self.fields['ref_consecutive'].required = False

        # Filtrar clientes: staff solo ve activos, superusuarios ven todos
        if self.user and not self.user.is_superuser:
            self.fields['client'].queryset = Client.objects.filter(show=True).order_by('company')
        else:
            self.fields['client'].queryset = Client.objects.all().order_by('company')

    class Meta:
        model = Shipment
        fields = [
            'assigned_to',
            'client',
            'reference_client',
            'arrival_date',
            'arrival_time',
            'type',
            'merchandise',
            'transport',
            'regimen',
            'cr_checked',
            'terminal',
            'line',
            'vessel',
            'notes',
        ]

        widgets = {
            'assigned_to': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
            }),
            'client': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
            }),
            'reference_client': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'placeholder': 'Referencia del cliente'
            }),
            'arrival_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
            }),
            'arrival_time': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
            }),
            'type': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
            }),
            'merchandise': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'placeholder': 'Tipo de mercancía'
            }),
            'transport': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
            }),
            'regimen': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
            }),
            'cr_checked': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
            }),
            'terminal': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
            }),
            'line': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
            }),
            'vessel': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'placeholder': 'Nombre del buque'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'rows': 4,
                'placeholder': 'Notas adicionales...'
            }),
        }
        
        labels = {
            'assigned_to': 'Asignado a',
            'client': 'Cliente',
            'reference_client': 'Referencia Cliente',
            'arrival_date': 'Fecha de Llegada',
            'arrival_time': 'Hora de Llegada',
            'type': 'Tipo de Envío',
            'merchandise': 'Mercancía',
            'transport': 'Transporte',
            'regimen': 'Régimen',
            'cr_checked': 'CR Verificado',
            'terminal': 'Terminal',
            'line': 'Línea',
            'vessel': 'Buque',
            'notes': 'Notas',
        }

    def clean_ref_initials(self):
        """Validar que las iniciales sean solo letras"""
        # Si es edición, no validar (campo de solo lectura)
        if self.instance and self.instance.pk:
            return self.cleaned_data.get('ref_initials', '')
        initials = self.cleaned_data.get('ref_initials', '').upper()
        if not initials.isalpha():
            raise forms.ValidationError('Las iniciales deben ser solo letras.')
        return initials

    def clean_ref_consecutive(self):
        """Validar que el consecutivo sea numérico"""
        # Si es edición, no validar (campo de solo lectura)
        if self.instance and self.instance.pk:
            return self.cleaned_data.get('ref_consecutive', '')
        consecutive = self.cleaned_data.get('ref_consecutive', '')
        if not consecutive.isdigit():
            raise forms.ValidationError('El consecutivo debe ser solo números.')
        # Asegurar 4 dígitos con ceros a la izquierda
        return consecutive.zfill(4)

    def clean(self):
        """Construir y validar la referencia completa"""
        cleaned_data = super().clean()

        # Si es edición, no validar ni construir la referencia (es de solo lectura)
        if self.instance and self.instance.pk:
            return cleaned_data

        initials = cleaned_data.get('ref_initials', '')
        consecutive = cleaned_data.get('ref_consecutive', '')

        if initials and consecutive:
            # Obtener los últimos 2 dígitos del año actual
            year_suffix = datetime.now().strftime('%y')
            # Construir referencia: LC + iniciales + consecutivo + / + año
            reference = f"LC{initials.upper()}{consecutive}/{year_suffix}"

            # Validar unicidad
            existing = Shipment.objects.filter(reference=reference)

            if existing.exists():
                raise forms.ValidationError(
                    f'Ya existe un envío con la referencia {reference}. Por favor usa un consecutivo diferente.'
                )

            cleaned_data['_reference'] = reference

        return cleaned_data

    def save(self, commit=True):
        """Guardar el shipment con la referencia construida"""
        instance = super().save(commit=False)
        # Solo asignar la referencia si es nuevo (no tiene pk aún)
        # En edición, mantener la referencia original
        if not instance.pk:
            if hasattr(self, 'cleaned_data') and '_reference' in self.cleaned_data:
                instance.reference = self.cleaned_data['_reference']
        if commit:
            instance.save()
        return instance


def get_next_consecutive(year=None):
    """Obtener el siguiente consecutivo disponible para el año dado"""
    if year is None:
        year = datetime.now().year
    year_suffix = str(year)[-2:]

    # Buscar referencias del año actual con el patrón LC__####/YY
    pattern = f'%/{year_suffix}'
    last_shipment = Shipment.objects.filter(
        reference__endswith=f'/{year_suffix}'
    ).order_by('-reference').first()

    if last_shipment and last_shipment.reference:
        # Extraer el consecutivo de la referencia
        match = re.match(r'^LC[A-Z]{2}(\d{4})/\d{2}$', last_shipment.reference.upper())
        if match:
            last_consecutive = int(match.group(1))
            return str(last_consecutive + 1).zfill(4)

    return '0001'


class ContainerForm(forms.ModelForm):
    """Formulario para contenedores"""

    class Meta:
        model = Container
        fields = ['number', 'size']
        widgets = {
            'number': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'placeholder': 'Ej: EITU9568530'
            }),
            'size': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'placeholder': 'Ej: 40HC'
            }),
        }
        labels = {
            'number': '# Contenedor',
            'size': 'Tamaño',
        }


ContainerFormSet = inlineformset_factory(
    Shipment,
    Container,
    form=ContainerForm,
    extra=1,
    can_delete=True
)
