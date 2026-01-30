from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q
from .models import Regimen
from seguimiento.mixins import SuperuserRequiredMixin


class RegimenListView(SuperuserRequiredMixin, ListView):
    """Lista de regímenes aduanales (solo superusuarios)"""
    model = Regimen
    template_name = 'regimens/regimen_list.html'
    context_object_name = 'regimens'
    paginate_by = 20

    def get_queryset(self):
        queryset = Regimen.objects.all()

        # Búsqueda
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(text__icontains=search)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        return context


class RegimenCreateView(SuperuserRequiredMixin, CreateView):
    """Crear nuevo régimen (solo superusuarios)"""
    model = Regimen
    template_name = 'regimens/regimen_form.html'
    fields = ['text']
    success_url = reverse_lazy('regimen-list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['text'].widget.attrs.update({
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
            'placeholder': 'Nombre del régimen aduanal'
        })
        return form

    def form_valid(self, form):
        messages.success(self.request, 'Régimen creado exitosamente.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Nuevo Régimen'
        context['button_text'] = 'Crear Régimen'
        return context


class RegimenUpdateView(SuperuserRequiredMixin, UpdateView):
    """Editar régimen existente (solo superusuarios)"""
    model = Regimen
    template_name = 'regimens/regimen_form.html'
    fields = ['text']
    success_url = reverse_lazy('regimen-list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['text'].widget.attrs.update({
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
            'placeholder': 'Nombre del régimen aduanal'
        })
        return form

    def form_valid(self, form):
        messages.success(self.request, 'Régimen actualizado exitosamente.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Editar: {self.object.text}'
        context['button_text'] = 'Guardar Cambios'
        return context


class RegimenDeleteView(SuperuserRequiredMixin, DeleteView):
    """Eliminar régimen (solo superusuarios)"""
    model = Regimen
    template_name = 'regimens/regimen_confirm_delete.html'
    success_url = reverse_lazy('regimen-list')
    context_object_name = 'regimen'

    def form_valid(self, form):
        messages.success(self.request, 'Régimen eliminado exitosamente.')
        return super().form_valid(form)
