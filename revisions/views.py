from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse_lazy
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from .models import Revision
from .forms import RevisionForm
from trackings.models import Tracking
from seguimiento.mixins import StaffRequiredMixin


def is_staff_user(user):
    """Verifica si el usuario es staff o superusuario"""
    return user.is_staff or user.is_superuser


class RevisionListView(StaffRequiredMixin, ListView):
    model = Revision
    template_name = 'revisions/revision_list.html'
    context_object_name = 'revisions'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Revision.objects.select_related('tracking', 'tracking__shipment', 'assigned_to').order_by('-date', '-time')
        
        # Búsqueda
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(tracking__shipment__reference__icontains=search) |
                Q(client__icontains=search) |
                Q(assigned_to__username__icontains=search) |
                Q(status__icontains=search)
            )
        
        # Filtro por estado
        status_filter = self.request.GET.get('status')
        if status_filter:
            queryset = queryset.filter(status__icontains=status_filter)
        
        # Filtro por paso
        step_filter = self.request.GET.get('step')
        if step_filter:
            queryset = queryset.filter(step=step_filter)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['status_filter'] = self.request.GET.get('status', '')
        context['step_filter'] = self.request.GET.get('step', '')
        return context


class RevisionDetailView(StaffRequiredMixin, DetailView):
    model = Revision
    template_name = 'revisions/revision_detail.html'
    context_object_name = 'revision'

    def get_queryset(self):
        return Revision.objects.select_related('tracking', 'tracking__shipment', 'assigned_to')


class RevisionCreateView(StaffRequiredMixin, CreateView):
    model = Revision
    form_class = RevisionForm
    template_name = 'revisions/revision_form.html'
    success_url = reverse_lazy('revision-list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class RevisionUpdateView(StaffRequiredMixin, UpdateView):
    model = Revision
    form_class = RevisionForm
    template_name = 'revisions/revision_form.html'
    success_url = reverse_lazy('revision-list')


class RevisionDeleteView(StaffRequiredMixin, DeleteView):
    model = Revision
    template_name = 'revisions/revision_confirm_delete.html'
    success_url = reverse_lazy('revision-list')
    context_object_name = 'revision'


@login_required
@user_passes_test(is_staff_user)
@require_POST
def quick_add_revision(request):
    """Endpoint AJAX para agregar comentarios rapidos desde el dashboard"""
    try:
        tracking_id = request.POST.get('tracking_id')
        notes = request.POST.get('notes', '').strip()
        new_status = request.POST.get('status', '').strip()

        if not tracking_id:
            return JsonResponse({'error': 'Tracking ID requerido'}, status=400)

        if not notes:
            return JsonResponse({'error': 'El comentario no puede estar vacio'}, status=400)

        # Obtener el tracking
        try:
            tracking = Tracking.objects.select_related('shipment', 'shipment__client').get(id=tracking_id)
        except Tracking.DoesNotExist:
            return JsonResponse({'error': 'Tracking no encontrado'}, status=404)

        # Crear la revision
        now = timezone.now()
        revision = Revision.objects.create(
            tracking=tracking,
            assigned_to=request.user,
            step=tracking.step,
            client=tracking.shipment.client.company if tracking.shipment.client else '',
            date=now.date(),
            time=now.time(),
            notes=notes,
            status=new_status or tracking.status,
        )

        # Actualizar el status del tracking si se proporciono uno nuevo
        if new_status and new_status != tracking.status:
            tracking.status = new_status
            if new_status == 'COMPLETED':
                tracking.finish_date = now
            tracking.save()

        return JsonResponse({
            'success': True,
            'message': 'Comentario guardado correctamente',
            'revision_id': revision.id,
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
