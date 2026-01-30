from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q
from .models import Tracking
from .forms import TrackingForm
from seguimiento.mixins import SuperuserRequiredMixin


class TrackingListView(SuperuserRequiredMixin, ListView):
    model = Tracking
    template_name = 'trackings/tracking_list.html'
    context_object_name = 'trackings'
    paginate_by = 20

    def get_queryset(self):
        queryset = Tracking.objects.select_related('shipment', 'shipment__client').order_by('-created_at')

        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(shipment__reference__icontains=search) |
                Q(assigned_to__icontains=search)
            )

        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['selected_status'] = self.request.GET.get('status', '')
        return context


class TrackingDetailView(SuperuserRequiredMixin, DetailView):
    model = Tracking
    template_name = 'trackings/tracking_detail.html'
    context_object_name = 'tracking'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['revisions'] = self.object.revisions.all().order_by('-created_at')
        return context


class TrackingCreateView(SuperuserRequiredMixin, CreateView):
    model = Tracking
    form_class = TrackingForm
    template_name = 'trackings/tracking_form.html'
    success_url = reverse_lazy('tracking-list')

    def form_valid(self, form):
        messages.success(self.request, 'Seguimiento creado exitosamente.')
        return super().form_valid(form)


class TrackingUpdateView(SuperuserRequiredMixin, UpdateView):
    model = Tracking
    form_class = TrackingForm
    template_name = 'trackings/tracking_form.html'
    success_url = reverse_lazy('tracking-list')

    def form_valid(self, form):
        messages.success(self.request, 'Seguimiento actualizado exitosamente.')
        return super().form_valid(form)


class TrackingDeleteView(SuperuserRequiredMixin, DeleteView):
    model = Tracking
    template_name = 'trackings/tracking_confirm_delete.html'
    success_url = reverse_lazy('tracking-list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Seguimiento eliminado exitosamente.')
        return super().delete(request, *args, **kwargs)
