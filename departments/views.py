import json
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.db.models import Count, Q
from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone

from .models import Department
from .forms import DepartmentForm
from seguimiento.mixins import SuperuserRequiredMixin
from users.models import User
from shipments.models import Shipment
from trackings.models import Tracking
from steps.models import Step


class DepartmentListView(SuperuserRequiredMixin, ListView):
    """Lista de departamentos"""
    model = Department
    template_name = 'departments/department_list.html'
    context_object_name = 'departments'
    paginate_by = 20

    def get_queryset(self):
        queryset = Department.objects.annotate(
            users_count=Count('users', distinct=True),
            steps_count=Count('steps', distinct=True)
        ).order_by('name')

        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(code__icontains=search) |
                Q(description__icontains=search)
            )

        status = self.request.GET.get('status')
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['status'] = self.request.GET.get('status', '')
        return context


class DepartmentDetailView(SuperuserRequiredMixin, DetailView):
    """Detalle de un departamento"""
    model = Department
    template_name = 'departments/department_detail.html'
    context_object_name = 'department'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        dept = self.object

        # Usuarios del departamento
        context['users'] = dept.users.all().order_by('first_name', 'last_name')

        # Steps asignados al departamento
        context['steps'] = dept.steps.all().order_by('number')

        # Estadísticas rápidas
        user_ids = list(dept.users.values_list('id', flat=True))
        context['shipments_count'] = Shipment.objects.filter(assigned_to_id__in=user_ids).count()
        context['trackings_completed'] = Tracking.objects.filter(
            shipment__assigned_to_id__in=user_ids,
            status='COMPLETED'
        ).count()
        context['trackings_pending'] = Tracking.objects.filter(
            shipment__assigned_to_id__in=user_ids,
            status='PENDING'
        ).count()

        return context


class DepartmentCreateView(SuperuserRequiredMixin, CreateView):
    """Crear nuevo departamento"""
    model = Department
    form_class = DepartmentForm
    template_name = 'departments/department_form.html'
    success_url = reverse_lazy('department-list')

    def form_valid(self, form):
        messages.success(self.request, 'Departamento creado exitosamente.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Nuevo Departamento'
        context['button_text'] = 'Crear Departamento'
        return context


class DepartmentUpdateView(SuperuserRequiredMixin, UpdateView):
    """Editar departamento"""
    model = Department
    form_class = DepartmentForm
    template_name = 'departments/department_form.html'

    def get_success_url(self):
        return reverse('department-detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Departamento actualizado exitosamente.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Editar: {self.object.name}'
        context['button_text'] = 'Guardar Cambios'
        return context


class DepartmentDeleteView(SuperuserRequiredMixin, DeleteView):
    """Eliminar departamento"""
    model = Department
    template_name = 'departments/department_confirm_delete.html'
    success_url = reverse_lazy('department-list')
    context_object_name = 'department'

    def form_valid(self, form):
        messages.success(self.request, 'Departamento eliminado exitosamente.')
        return super().form_valid(form)


def is_superuser(user):
    return user.is_authenticated and user.is_superuser


@login_required
@user_passes_test(is_superuser)
def department_analytics_view(request):
    """Dashboard de estadísticas por departamento"""

    now = timezone.now()
    current_year = now.year
    current_month = now.month

    departments = Department.objects.filter(is_active=True)

    # Stats per department
    department_stats = []
    for dept in departments:
        user_ids = list(dept.users.values_list('id', flat=True))

        # Shipments asignados a miembros del departamento
        dept_shipments = Shipment.objects.filter(
            assigned_to_id__in=user_ids,
            arrival_date__year=current_year
        )

        # Trackings para los steps del departamento
        step_numbers = list(dept.steps.values_list('number', flat=True))
        dept_trackings = Tracking.objects.filter(
            step__in=step_numbers,
            shipment__arrival_date__year=current_year
        )

        # Calcular tiempo promedio de respuesta
        completed_trackings = dept_trackings.filter(
            status='COMPLETED',
            finish_date__isnull=False
        )

        total_hours = 0
        count = 0
        for t in completed_trackings:
            if t.finish_date and t.created_at:
                delta = t.finish_date - t.created_at
                total_hours += delta.total_seconds() / 3600
                count += 1

        avg_response_hours = round(total_hours / count, 1) if count > 0 else 0

        department_stats.append({
            'department': dept,
            'shipments_count': dept_shipments.count(),
            'shipments_imp': dept_shipments.filter(type='IMP').count(),
            'shipments_exp': dept_shipments.filter(type='EXP').count(),
            'trackings_total': dept_trackings.count(),
            'trackings_completed': completed_trackings.count(),
            'trackings_pending': dept_trackings.filter(status='PENDING').count(),
            'trackings_in_progress': dept_trackings.filter(status='IN_PROGRESS').count(),
            'avg_response_hours': avg_response_hours,
            'users_count': len(user_ids),
            'steps_count': len(step_numbers),
        })

    # Datos para gráficos de comparación
    dept_names = [d['department'].name for d in department_stats]
    dept_colors = [d['department'].color for d in department_stats]
    shipments_data = [d['shipments_count'] for d in department_stats]
    completed_data = [d['trackings_completed'] for d in department_stats]
    response_times = [d['avg_response_hours'] for d in department_stats]

    # Comparativa mensual por departamento (últimos 6 meses)
    months_labels = []
    monthly_by_dept = {dept.name: [] for dept in departments}

    for i in range(5, -1, -1):
        month = current_month - i
        year = current_year
        if month <= 0:
            month += 12
            year -= 1

        month_name = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun',
                      'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'][month - 1]
        months_labels.append(month_name)

        for dept in departments:
            user_ids = list(dept.users.values_list('id', flat=True))
            count = Shipment.objects.filter(
                assigned_to_id__in=user_ids,
                arrival_date__year=year,
                arrival_date__month=month
            ).count()
            monthly_by_dept[dept.name].append(count)

    context = {
        'now': now,
        'current_year': current_year,
        'department_stats': department_stats,
        'dept_names': json.dumps(dept_names),
        'dept_colors': json.dumps(dept_colors),
        'shipments_data': json.dumps(shipments_data),
        'completed_data': json.dumps(completed_data),
        'response_times': json.dumps(response_times),
        'months_labels': json.dumps(months_labels),
        'monthly_by_dept': json.dumps(monthly_by_dept),
    }

    return render(request, 'departments/department_analytics.html', context)
