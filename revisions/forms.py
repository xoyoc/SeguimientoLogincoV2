from django import forms
from .models import Revision


class RevisionForm(forms.ModelForm):
    """Formulario para crear/editar revisiones"""
    
    class Meta:
        model = Revision
        fields = ['tracking', 'assigned_to', 'step', 'client', 'date', 'time', 'status', 'notes']
        
        widgets = {
            'tracking': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
            }),
            'assigned_to': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
            }),
            'step': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'min': '1'
            }),
            'client': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
            }),
            'date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
            }),
            'time': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
            }),
            'status': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'rows': 4
            }),
        }
        
        labels = {
            'tracking': 'Seguimiento',
            'assigned_to': 'Asignado a',
            'step': 'Paso',
            'client': 'Cliente',
            'date': 'Fecha',
            'time': 'Hora',
            'status': 'Estado',
            'notes': 'Notas',
        }
