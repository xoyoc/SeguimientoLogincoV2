from django import forms
from .models import Department


class DepartmentForm(forms.ModelForm):
    """Formulario para crear/editar departamentos"""

    class Meta:
        model = Department
        fields = ['name', 'code', 'description', 'color', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'placeholder': 'Nombre del departamento'
            }),
            'code': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'placeholder': 'Código corto (ej: OPS)',
                'maxlength': '10'
            }),
            'description': forms.Textarea(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'rows': 3,
                'placeholder': 'Descripción del departamento'
            }),
            'color': forms.TextInput(attrs={
                'class': 'mt-1 block w-20 h-10 rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 cursor-pointer',
                'type': 'color'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-indigo-600 shadow-sm focus:border-indigo-500 focus:ring-indigo-500'
            }),
        }
        labels = {
            'name': 'Nombre',
            'code': 'Código',
            'description': 'Descripción',
            'color': 'Color',
            'is_active': 'Activo',
        }
