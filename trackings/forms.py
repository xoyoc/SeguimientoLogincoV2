from django import forms
from .models import Tracking
from shipments.models import Shipment


class TrackingForm(forms.ModelForm):
    """Formulario para crear/editar seguimientos"""
    
    class Meta:
        model = Tracking
        fields = ['shipment', 'step', 'assigned_to', 'status', 'finish_date']
        
        widgets = {
            'shipment': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
            }),
            'step': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'min': '1',
                'placeholder': 'Número de paso'
            }),
            'assigned_to': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
                'placeholder': 'ID del usuario asignado'
            }),
            'status': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
            }),
            'finish_date': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
            }),
        }
        
        labels = {
            'shipment': 'Envío',
            'step': 'Paso',
            'assigned_to': 'Asignado a',
            'status': 'Estado',
            'finish_date': 'Fecha de Finalización',
        }
