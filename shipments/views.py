from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Shipment
from .forms import ShipmentForm, ContainerFormSet, get_next_consecutive
from steps.models import Step
from clients.models import ClientStep
from seguimiento.mixins import StaffRequiredMixin


class ShipmentListView(StaffRequiredMixin, ListView):
    """Vista para listar envíos"""
    model = Shipment
    template_name = 'shipments/shipment_list.html'
    context_object_name = 'shipments'
    paginate_by = 20

    def get_queryset(self):
        from trackings.models import Tracking
        from django.db.models import Exists, OuterRef

        # Subquery para verificar si el shipment está finalizado
        finished_subquery = Tracking.objects.filter(
            shipment=OuterRef('pk'),
            step=14,
            status='COMPLETED'
        )

        queryset = Shipment.objects.select_related(
            'client', 'assigned_to', 'terminal', 'line'
        ).annotate(
            is_finished=Exists(finished_subquery)
        ).order_by('-arrival_date', '-created_at')

        # Staff solo ve shipments en proceso (no finalizados) por defecto
        user = self.request.user
        show_finished = self.request.GET.get('finished', '')

        if not user.is_superuser and show_finished != 'all':
            # Excluir shipments finalizados
            queryset = queryset.filter(is_finished=False)

            # También filtrar solo clientes activos para staff
            queryset = queryset.filter(client__show=True)

        # Filtro por búsqueda
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(reference__icontains=search) |
                Q(reference_client__icontains=search) |
                Q(client__company__icontains=search) |
                Q(merchandise__icontains=search)
            )

        # Filtro por tipo
        ship_type = self.request.GET.get('type')
        if ship_type:
            queryset = queryset.filter(type=ship_type)

        # Filtro por año
        year = self.request.GET.get('year')
        if year:
            queryset = queryset.filter(arrival_date__year=year)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['selected_type'] = self.request.GET.get('type', '')
        context['selected_year'] = self.request.GET.get('year', '')
        context['show_finished'] = self.request.GET.get('finished', '')
        context['is_superuser'] = self.request.user.is_superuser
        return context


class ShipmentDetailView(StaffRequiredMixin, DetailView):
    """Vista para ver detalle de un envío"""
    model = Shipment
    template_name = 'shipments/shipment_detail.html'
    context_object_name = 'shipment'

    def get_context_data(self, **kwargs):
        from revisions.models import Revision

        context = super().get_context_data(**kwargs)
        shipment = self.object

        # Obtener trackings relacionados
        trackings_qs = shipment.trackings.all().order_by('step')

        # Obtener steps del cliente (si tiene configurados) o steps generales
        client_steps = ClientStep.objects.filter(
            client=shipment.client,
            is_active=True
        ).select_related('step').order_by('order', 'step__number')

        if client_steps.exists():
            # Usar pasos personalizados del cliente
            steps_list = [cs.step for cs in client_steps]
        else:
            # Usar pasos generales filtrados por tipo de envio
            if shipment.type == 'IMP':
                steps_list = list(Step.objects.filter(imp=True).order_by('number'))
            else:
                steps_list = list(Step.objects.filter(exp=True).order_by('number'))

        # Crear diccionario de trackings por step number
        trackings_dict = {t.step: t for t in trackings_qs}

        # Obtener todas las revisiones de los trackings de este shipment
        tracking_ids = [t.id for t in trackings_qs]
        all_revisions = Revision.objects.filter(
            tracking_id__in=tracking_ids
        ).select_related('assigned_to').order_by('-created_at')

        # Crear diccionario de revisiones por step number
        revisions_by_step = {}
        for revision in all_revisions:
            step_num = revision.step
            if step_num not in revisions_by_step:
                revisions_by_step[step_num] = []
            revisions_by_step[step_num].append(revision)

        # Enriquecer los steps con información del tracking y revisiones
        timeline_steps = []
        for step in steps_list:
            tracking = trackings_dict.get(step.number)
            revisions = revisions_by_step.get(step.number, [])
            timeline_steps.append({
                'step': step,
                'tracking': tracking,
                'status': tracking.status if tracking else 'NOT_STARTED',
                'has_tracking': tracking is not None,
                'revisions': revisions,
                'revisions_count': len(revisions),
            })

        # Calcular progreso
        total_steps = len(timeline_steps)
        completed_steps = sum(1 for ts in timeline_steps if ts['status'] == 'COMPLETED')
        progress_percent = int((completed_steps / total_steps) * 100) if total_steps > 0 else 0

        context['trackings'] = trackings_qs
        context['timeline_steps'] = timeline_steps
        context['progress_percent'] = progress_percent
        context['completed_steps'] = completed_steps
        context['total_steps'] = total_steps

        return context


class ShipmentCreateView(StaffRequiredMixin, CreateView):
    """Vista para crear un nuevo envío"""
    model = Shipment
    form_class = ShipmentForm
    template_name = 'shipments/shipment_form.html'
    success_url = reverse_lazy('shipment-list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['container_formset'] = ContainerFormSet(self.request.POST)
        else:
            context['container_formset'] = ContainerFormSet()
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        container_formset = context['container_formset']
        if container_formset.is_valid():
            self.object = form.save()
            container_formset.instance = self.object
            container_formset.save()
            messages.success(self.request, 'Envío creado exitosamente.')
            return super().form_valid(form)
        else:
            return self.render_to_response(self.get_context_data(form=form))


class ShipmentUpdateView(StaffRequiredMixin, UpdateView):
    """Vista para editar un envío"""
    model = Shipment
    form_class = ShipmentForm
    template_name = 'shipments/shipment_form.html'
    success_url = reverse_lazy('shipment-list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['container_formset'] = ContainerFormSet(self.request.POST, instance=self.object)
        else:
            context['container_formset'] = ContainerFormSet(instance=self.object)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        container_formset = context['container_formset']
        if container_formset.is_valid():
            self.object = form.save()
            container_formset.instance = self.object
            container_formset.save()
            messages.success(self.request, 'Envío actualizado exitosamente.')
            return super().form_valid(form)
        else:
            return self.render_to_response(self.get_context_data(form=form))


class ShipmentDeleteView(StaffRequiredMixin, DeleteView):
    """Vista para eliminar un envío"""
    model = Shipment
    template_name = 'shipments/shipment_confirm_delete.html'
    success_url = reverse_lazy('shipment-list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Envío eliminado exitosamente.')
        return super().delete(request, *args, **kwargs)


@login_required
def get_next_consecutive_view(request):
    """API endpoint para obtener el siguiente consecutivo sugerido"""
    from datetime import datetime
    year = datetime.now().year
    year_suffix = str(year)[-2:]
    next_consecutive = get_next_consecutive(year)
    return JsonResponse({
        'consecutive': next_consecutive,
        'year_suffix': year_suffix,
        'preview': f'LC___{next_consecutive}/{year_suffix}'
    })
