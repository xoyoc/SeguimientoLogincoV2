from django.shortcuts import render, redirect
from django.db.models import Count, Q, Avg
from django.utils import timezone
from django.db.models.functions import TruncMonth, TruncYear
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponseForbidden
from datetime import datetime, timedelta
from shipments.models import Shipment
from trackings.models import Tracking
from revisions.models import Revision
from steps.models import Step
from clients.models import Client, ClientStep
import json


def is_superuser(user):
    """Verifica si el usuario es superusuario"""
    return user.is_superuser


def is_staff_or_superuser(user):
    """Verifica si el usuario es staff o superusuario"""
    return user.is_staff or user.is_superuser


@login_required
def login_redirect_view(request):
    """Vista que redirige al usuario segun su rol despues del login"""
    user = request.user

    if user.is_superuser:
        # Superusuarios van al dashboard general
        return redirect('dashboard')
    elif user.is_staff:
        # Usuarios staff van a mi-dashboard
        return redirect('my-dashboard')
    elif user.is_client_user:
        # Usuarios de cliente van a su portal
        return redirect('client-dashboard')
    else:
        # Por defecto, redirigir al login
        return redirect('login')


@login_required
@user_passes_test(is_superuser, login_url='login-redirect')
def dashboard_view(request):
    """Vista principal del dashboard con estadísticas"""
    
    # Obtener fecha actual
    now = timezone.now()
    today = now.date()
    current_year = now.year
    current_month = now.month
    
    # Filtros para 2026 hasta el mes actual
    year_filter = Q(arrival_date__year=2026)
    month_filter = Q(
        arrival_date__year=2026,
        arrival_date__month__lte=current_month
    )
    
    # Estadísticas de Shipments (2026 hasta mes actual)
    total_shipments = Shipment.objects.filter(month_filter).count()
    shipments_imp = Shipment.objects.filter(month_filter, type='IMP').count()
    shipments_exp = Shipment.objects.filter(month_filter, type='EXP').count()
    
    # Estadísticas del mes actual
    shipments_this_month = Shipment.objects.filter(
        arrival_date__year=2026,
        arrival_date__month=current_month
    ).count()
    
    # Comparación con mes anterior
    if current_month > 1:
        shipments_last_month = Shipment.objects.filter(
            arrival_date__year=2026,
            arrival_date__month=current_month - 1
        ).count()
    else:
        # Si es enero, comparar con diciembre del año anterior
        shipments_last_month = Shipment.objects.filter(
            arrival_date__year=2025,
            arrival_date__month=12
        ).count()
    
    # Calcular variación mensual
    if shipments_last_month > 0:
        month_variation = ((shipments_this_month - shipments_last_month) / shipments_last_month) * 100
    else:
        month_variation = 0
    
    # Estadísticas de Trackings (filtrar por shipments de 2026)
    shipments_2026_ids = Shipment.objects.filter(month_filter).values_list('id', flat=True)
    total_trackings = Tracking.objects.filter(shipment_id__in=shipments_2026_ids).count()
    
    trackings_by_status = {
        'PENDING': Tracking.objects.filter(shipment_id__in=shipments_2026_ids, status='PENDING').count(),
        'IN_PROGRESS': Tracking.objects.filter(shipment_id__in=shipments_2026_ids, status='IN_PROGRESS').count(),
        'COMPLETED': Tracking.objects.filter(shipment_id__in=shipments_2026_ids, status='COMPLETED').count(),
        'CANCELLED': Tracking.objects.filter(shipment_id__in=shipments_2026_ids, status='CANCELLED').count(),
    }
    
    # Promedio de trackings por shipment
    avg_trackings_per_shipment = 0
    if total_shipments > 0:
        avg_trackings_per_shipment = total_trackings / total_shipments
    
    # Estadísticas de Revisiones (solo hoy)
    total_revisions = Revision.objects.filter(
        tracking__shipment_id__in=shipments_2026_ids
    ).count()
    
    revisions_today = Revision.objects.filter(
        created_at__date=today
    ).count()
    
    # Estadísticas de Clientes (activos en 2026)
    total_clients = Client.objects.count()
    active_clients = Client.objects.filter(
        shipments__arrival_date__year=2026,
        shipments__arrival_date__month__lte=current_month
    ).distinct().count()
    
    # Envíos recientes (2026, últimos 10)
    recent_shipments = Shipment.objects.filter(
        month_filter
    ).select_related(
        'client', 'assigned_to'
    ).order_by('-arrival_date', '-created_at')[:10]
    
    # Revisiones recientes (últimas 10)
    recent_revisions = Revision.objects.filter(
        tracking__shipment_id__in=shipments_2026_ids
    ).select_related(
        'tracking', 'assigned_to'
    ).order_by('-created_at')[:10]
    
    # Todos los pasos del proceso
    steps = Step.objects.all().order_by('number')
    
    context = {
        'now': now,
        'current_year': current_year,
        'current_month': current_month,
        'stats': {
            'total_shipments': total_shipments,
            'shipments_imp': shipments_imp,
            'shipments_exp': shipments_exp,
            'shipments_this_month': shipments_this_month,
            'shipments_last_month': shipments_last_month,
            'month_variation': round(month_variation, 2),
            'total_trackings': total_trackings,
            'trackings_by_status': trackings_by_status,
            'avg_trackings_per_shipment': avg_trackings_per_shipment,
            'total_revisions': total_revisions,
            'revisions_today': revisions_today,
            'total_clients': total_clients,
            'active_clients': active_clients,
        },
        'recent_shipments': recent_shipments,
        'recent_revisions': recent_revisions,
        'steps': steps,
    }
    
    return render(request, 'dashboard.html', context)


@login_required
@user_passes_test(is_superuser, login_url='login-redirect')
def analytics_view(request):
    """Vista de análisis y reportes con predicciones"""
    
    now = timezone.now()
    current_year = now.year
    current_month = now.month
    
    # Años a analizar
    years = [2024, 2025, 2026]
    
    # ===== ESTADÍSTICAS POR AÑO =====
    yearly_stats = {}
    for year in years:
        year_start = datetime(year, 1, 1)
        year_end = datetime(year, 12, 31, 23, 59, 59)
        
        shipments_count = Shipment.objects.filter(
            arrival_date__year=year
        ).count()
        
        shipments_imp = Shipment.objects.filter(
            arrival_date__year=year,
            type='IMP'
        ).count()
        
        shipments_exp = Shipment.objects.filter(
            arrival_date__year=year,
            type='EXP'
        ).count()
        
        revisions_count = Revision.objects.filter(
            created_at__year=year
        ).count()
        
        trackings_completed = Tracking.objects.filter(
            created_at__year=year,
            status='COMPLETED'
        ).count()
        
        yearly_stats[year] = {
            'shipments': shipments_count,
            'shipments_imp': shipments_imp,
            'shipments_exp': shipments_exp,
            'revisions': revisions_count,
            'trackings_completed': trackings_completed,
        }
    
    # ===== ESTADÍSTICAS MENSUALES =====
    # Obtener datos mensuales de 2024 y 2025 para análisis
    monthly_data_2024 = Shipment.objects.filter(
        arrival_date__year=2024
    ).annotate(
        month=TruncMonth('arrival_date')
    ).values('month').annotate(
        count=Count('id'),
        imp_count=Count('id', filter=Q(type='IMP')),
        exp_count=Count('id', filter=Q(type='EXP'))
    ).order_by('month')
    
    monthly_data_2025 = Shipment.objects.filter(
        arrival_date__year=2025
    ).annotate(
        month=TruncMonth('arrival_date')
    ).values('month').annotate(
        count=Count('id'),
        imp_count=Count('id', filter=Q(type='IMP')),
        exp_count=Count('id', filter=Q(type='EXP'))
    ).order_by('month')
    
    monthly_data_2026 = Shipment.objects.filter(
        arrival_date__year=2026
    ).annotate(
        month=TruncMonth('arrival_date')
    ).values('month').annotate(
        count=Count('id'),
        imp_count=Count('id', filter=Q(type='IMP')),
        exp_count=Count('id', filter=Q(type='EXP'))
    ).order_by('month')
    
    # Crear arrays para los gráficos
    months_labels = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 
                     'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
    
    # Datos 2024
    monthly_2024 = [0] * 12
    for item in monthly_data_2024:
        month_idx = item['month'].month - 1
        monthly_2024[month_idx] = item['count']
    
    # Datos 2025
    monthly_2025 = [0] * 12
    for item in monthly_data_2025:
        month_idx = item['month'].month - 1
        monthly_2025[month_idx] = item['count']
    
    # Datos 2026 (hasta el mes actual)
    monthly_2026 = [0] * 12
    for item in monthly_data_2026:
        month_idx = item['month'].month - 1
        monthly_2026[month_idx] = item['count']
    
    # ===== CÁLCULO DE PREDICCIONES =====
    # Calcular promedio mensual de 2024 y 2025
    avg_2024 = sum(monthly_2024) / 12 if sum(monthly_2024) > 0 else 0
    avg_2025 = sum(monthly_2025) / 12 if sum(monthly_2025) > 0 else 0
    
    # Calcular tasa de crecimiento
    if avg_2024 > 0:
        growth_rate = ((avg_2025 - avg_2024) / avg_2024) * 100
    else:
        growth_rate = 0
    
    # Predecir meses restantes de 2026 basado en promedio y tendencia
    predicted_avg_2026 = avg_2025 * (1 + (growth_rate / 100))
    
    # Llenar predicciones para meses futuros de 2026
    monthly_2026_predicted = monthly_2026.copy()
    for i in range(current_month, 12):
        # Aplicar estacionalidad basada en patrones de años anteriores
        if sum(monthly_2024) > 0 and sum(monthly_2025) > 0:
            seasonality_factor = (monthly_2024[i] + monthly_2025[i]) / (avg_2024 + avg_2025)
        else:
            seasonality_factor = 1
        
        monthly_2026_predicted[i] = int(predicted_avg_2026 * seasonality_factor)
    
    # Proyección total para 2026
    actual_2026 = sum(monthly_2026[:current_month])
    predicted_remainder = sum(monthly_2026_predicted[current_month:])
    total_projected_2026 = actual_2026 + predicted_remainder
    
    # ===== CLIENTES MÁS ACTIVOS =====
    top_clients = Client.objects.filter(
        shipments__arrival_date__year__gte=2024
    ).annotate(
        shipments_count=Count('shipments')
    ).order_by('-shipments_count')[:10]
    
    # ===== COMPARATIVA POR TIPO =====
    type_comparison = {
        '2024': {
            'IMP': yearly_stats.get(2024, {}).get('shipments_imp', 0),
            'EXP': yearly_stats.get(2024, {}).get('shipments_exp', 0),
        },
        '2025': {
            'IMP': yearly_stats.get(2025, {}).get('shipments_imp', 0),
            'EXP': yearly_stats.get(2025, {}).get('shipments_exp', 0),
        },
        '2026': {
            'IMP': yearly_stats.get(2026, {}).get('shipments_imp', 0),
            'EXP': yearly_stats.get(2026, {}).get('shipments_exp', 0),
        },
    }
    
    # ===== RENDIMIENTO DE TRACKINGS =====
    avg_completion_time = {}
    for year in years:
        completed_trackings = Tracking.objects.filter(
            created_at__year=year,
            status='COMPLETED',
            finish_date__isnull=False
        )
        
        total_days = 0
        count = 0
        for tracking in completed_trackings:
            if tracking.finish_date and tracking.created_at:
                delta = tracking.finish_date - tracking.created_at
                total_days += delta.days
                count += 1
        
        avg_completion_time[year] = round(total_days / count, 1) if count > 0 else 0
    
    context = {
        'now': now,
        'current_year': current_year,
        'yearly_stats': yearly_stats,
        'monthly_labels': json.dumps(months_labels),
        'monthly_2024': json.dumps(monthly_2024),
        'monthly_2025': json.dumps(monthly_2025),
        'monthly_2026': json.dumps(monthly_2026),
        'monthly_2026_predicted': json.dumps(monthly_2026_predicted),
        'growth_rate': round(growth_rate, 2),
        'total_projected_2026': total_projected_2026,
        'actual_2026': actual_2026,
        'predicted_remainder': predicted_remainder,
        'top_clients': top_clients,
        'type_comparison': type_comparison,
        'avg_completion_time': avg_completion_time,
    }
    
    return render(request, 'analytics.html', context)


@login_required
@user_passes_test(is_staff_or_superuser, login_url='login-redirect')
def my_dashboard_view(request):
    """Dashboard personal del usuario - solo sus embarques y pasos asignados"""

    user = request.user
    now = timezone.now()
    today = now.date()

    # Mis embarques asignados
    my_shipments = Shipment.objects.filter(
        assigned_to=user
    ).select_related(
        'client', 'terminal', 'line'
    ).order_by('-arrival_date', '-created_at')

    # Estadísticas de mis embarques
    my_shipments_count = my_shipments.count()
    my_shipments_pending = my_shipments.filter(
        trackings__status='PENDING'
    ).distinct().count()
    my_shipments_in_progress = my_shipments.filter(
        trackings__status='IN_PROGRESS'
    ).distinct().count()

    # Mis trackings (de mis embarques)
    my_trackings = Tracking.objects.filter(
        shipment__assigned_to=user
    ).select_related(
        'shipment', 'shipment__client'
    ).order_by('status', '-created_at')

    my_trackings_pending = my_trackings.filter(status='PENDING').count()
    my_trackings_in_progress = my_trackings.filter(status='IN_PROGRESS').count()
    my_trackings_completed_today = my_trackings.filter(
        status='COMPLETED',
        finish_date__date=today
    ).count()

    # Mis revisiones (donde soy el asignado)
    my_revisions = Revision.objects.filter(
        assigned_to=user
    ).select_related(
        'tracking', 'tracking__shipment', 'tracking__shipment__client'
    ).order_by('-created_at')[:10]

    # Trackings pendientes para comentar (no completados)
    trackings_to_comment_qs = Tracking.objects.filter(
        shipment__assigned_to=user,
        status__in=['PENDING', 'IN_PROGRESS']
    ).select_related(
        'shipment', 'shipment__client'
    ).order_by('shipment__arrival_date', 'step')[:15]

    # Obtener información de steps para los trackings
    step_numbers = list(trackings_to_comment_qs.values_list('step', flat=True))
    steps_dict = {s.number: s for s in Step.objects.filter(number__in=step_numbers)}

    # Agregar step_info a cada tracking
    trackings_to_comment = []
    for tracking in trackings_to_comment_qs:
        tracking.step_info = steps_dict.get(tracking.step)
        trackings_to_comment.append(tracking)

    context = {
        'user': user,
        'now': now,
        'my_shipments': my_shipments[:10],
        'my_shipments_count': my_shipments_count,
        'stats': {
            'shipments_pending': my_shipments_pending,
            'shipments_in_progress': my_shipments_in_progress,
            'trackings_pending': my_trackings_pending,
            'trackings_in_progress': my_trackings_in_progress,
            'completed_today': my_trackings_completed_today,
        },
        'my_revisions': my_revisions,
        'trackings_to_comment': trackings_to_comment,
    }

    return render(request, 'my_dashboard.html', context)


@login_required
def client_dashboard_view(request):
    """Dashboard para usuarios de cliente - solo ven sus despachos por RFC"""

    user = request.user

    # Verificar que es un usuario de cliente
    if not user.is_client_user:
        return HttpResponseForbidden("No tienes acceso a esta vista.")

    client = user.get_client
    if not client:
        return HttpResponseForbidden("No tienes un cliente asociado.")

    now = timezone.now()
    today = now.date()
    current_year = now.year
    current_month = now.month

    # Filtrar despachos del cliente
    client_shipments = Shipment.objects.filter(
        client=client
    ).select_related(
        'assigned_to', 'terminal', 'line'
    ).order_by('-arrival_date', '-created_at')

    # Despachos del mes actual
    shipments_this_month = client_shipments.filter(
        arrival_date__year=current_year,
        arrival_date__month=current_month
    )

    # Estadisticas del mes
    total_month = shipments_this_month.count()
    shipments_imp_month = shipments_this_month.filter(type='IMP').count()
    shipments_exp_month = shipments_this_month.filter(type='EXP').count()

    # Estadisticas de trackings
    client_shipment_ids = client_shipments.values_list('id', flat=True)

    # Trackings pendientes y completados
    trackings_pending = Tracking.objects.filter(
        shipment_id__in=client_shipment_ids,
        status='PENDING'
    ).count()

    trackings_in_progress = Tracking.objects.filter(
        shipment_id__in=client_shipment_ids,
        status='IN_PROGRESS'
    ).count()

    trackings_completed = Tracking.objects.filter(
        shipment_id__in=client_shipment_ids,
        status='COMPLETED'
    ).count()

    # Total de operaciones (despachos) concluidos y pendientes
    # Un despacho se considera concluido cuando todos sus trackings estan COMPLETED
    shipments_with_pending = Shipment.objects.filter(
        id__in=client_shipment_ids,
        trackings__status__in=['PENDING', 'IN_PROGRESS']
    ).distinct().count()

    shipments_completed = Shipment.objects.filter(
        id__in=client_shipment_ids
    ).exclude(
        trackings__status__in=['PENDING', 'IN_PROGRESS']
    ).filter(
        trackings__status='COMPLETED'
    ).distinct().count()

    # 5 despachos pendientes con linea de tiempo
    pending_shipments = Shipment.objects.filter(
        id__in=client_shipment_ids,
        trackings__status__in=['PENDING', 'IN_PROGRESS']
    ).distinct().select_related(
        'assigned_to', 'terminal', 'line'
    ).order_by('-arrival_date')[:5]

    # Preparar timeline para cada despacho pendiente
    pending_shipments_with_timeline = []
    for shipment in pending_shipments:
        # Obtener trackings del despacho
        trackings_qs = shipment.trackings.all().order_by('step')

        # Obtener steps del cliente o generales
        client_steps = ClientStep.objects.filter(
            client=client,
            is_active=True
        ).select_related('step').order_by('order', 'step__number')

        if client_steps.exists():
            steps_list = [cs.step for cs in client_steps]
        else:
            if shipment.type == 'IMP':
                steps_list = list(Step.objects.filter(imp=True).order_by('number'))
            else:
                steps_list = list(Step.objects.filter(exp=True).order_by('number'))

        # Crear diccionario de trackings por step number
        trackings_dict = {t.step: t for t in trackings_qs}

        # Calcular progreso
        total_steps = len(steps_list)
        completed_steps = sum(1 for step in steps_list if trackings_dict.get(step.number) and trackings_dict[step.number].status == 'COMPLETED')
        progress_percent = int((completed_steps / total_steps) * 100) if total_steps > 0 else 0

        # Encontrar el paso actual (primer paso no completado)
        current_step = None
        for step in steps_list:
            tracking = trackings_dict.get(step.number)
            if not tracking or tracking.status in ['PENDING', 'IN_PROGRESS']:
                current_step = step
                break

        pending_shipments_with_timeline.append({
            'shipment': shipment,
            'progress_percent': progress_percent,
            'completed_steps': completed_steps,
            'total_steps': total_steps,
            'current_step': current_step,
        })

    context = {
        'user': user,
        'client': client,
        'now': now,
        'current_month': current_month,
        'current_year': current_year,
        'stats': {
            'total_month': total_month,
            'shipments_imp_month': shipments_imp_month,
            'shipments_exp_month': shipments_exp_month,
            'trackings_pending': trackings_pending,
            'trackings_in_progress': trackings_in_progress,
            'trackings_completed': trackings_completed,
            'shipments_pending': shipments_with_pending,
            'shipments_completed': shipments_completed,
        },
        'pending_shipments': pending_shipments_with_timeline,
    }

    return render(request, 'client_dashboard.html', context)
