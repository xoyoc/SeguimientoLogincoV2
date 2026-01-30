from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.http import JsonResponse, FileResponse, Http404
from django.views.decorators.http import require_POST
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta
from .models import (
    Client, ClientStep, DocumentCategory, ClientDocument,
    ClientManifest, ClientPhoto, SATVerification
)
from .forms import (
    ClientForm, ClientStepForm, ClientComplianceForm, ClientDocumentForm,
    ClientDocumentReviewForm, ClientManifestForm, ClientPhotoForm,
    SATVerificationForm, MANIFEST_TEMPLATES
)
from steps.models import Step
from seguimiento.mixins import SuperuserRequiredMixin


def is_superuser(user):
    """Verifica si el usuario es superusuario"""
    return user.is_authenticated and user.is_superuser


class ClientListView(SuperuserRequiredMixin, ListView):
    """Lista de clientes para administradores"""
    model = Client
    template_name = 'clients/client_list.html'
    context_object_name = 'clients'
    paginate_by = 20

    def get_queryset(self):
        queryset = Client.objects.annotate(
            steps_count=Count('client_steps', filter=Q(client_steps__is_active=True)),
            shipments_count=Count('shipments')
        ).order_by('company')

        # Busqueda
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(company__icontains=search) |
                Q(rfc__icontains=search) |
                Q(phone__icontains=search) |
                Q(city__icontains=search) |
                Q(state__icontains=search)
            )

        # Filtro por estado geografico
        state_filter = self.request.GET.get('state')
        if state_filter:
            queryset = queryset.filter(state=state_filter)

        # Filtro por visibilidad
        show_filter = self.request.GET.get('show')
        if show_filter == 'active':
            queryset = queryset.filter(show=True)
        elif show_filter == 'inactive':
            queryset = queryset.filter(show=False)

        # Filtro por estado de expediente
        expediente_filter = self.request.GET.get('expediente')
        if expediente_filter == 'complete':
            queryset = queryset.filter(expediente_completo=True)
        elif expediente_filter == 'incomplete':
            queryset = queryset.filter(expediente_completo=False)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['state_filter'] = self.request.GET.get('state', '')
        context['show_filter'] = self.request.GET.get('show', '')
        context['expediente_filter'] = self.request.GET.get('expediente', '')

        # Obtener estados unicos para el filtro
        context['states'] = Client.objects.exclude(
            state=''
        ).values_list('state', flat=True).distinct().order_by('state')

        # Calcular porcentaje de expediente para cada cliente en la pagina
        clients = context.get('clients', context.get('object_list', []))
        for client in clients:
            client.expediente_percentage = client.calcular_completitud_expediente()

        return context


class ClientDetailView(SuperuserRequiredMixin, DetailView):
    """Detalle de un cliente con informacion de cumplimiento RGCE 1.4.14"""
    model = Client
    template_name = 'clients/client_detail.html'
    context_object_name = 'client'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        client = self.object

        # Pasos asignados al cliente
        context['client_steps'] = ClientStep.objects.filter(
            client=client
        ).select_related('step').order_by('order', 'step__number')

        # Embarques del cliente
        context['shipments'] = client.shipments.all().order_by('-arrival_date')[:10]
        context['shipments_count'] = client.shipments.count()

        # === Informacion de Cumplimiento RGCE 1.4.14 ===
        # Porcentaje de completitud del expediente
        context['expediente_percentage'] = client.calcular_completitud_expediente()

        # Documentos por categoria
        from .models import DocumentCategory, ClientDocument, SATVerification
        categories = DocumentCategory.objects.all().order_by('order')
        docs_by_category = []
        for cat in categories:
            docs = ClientDocument.objects.filter(client=client, category=cat)
            approved = docs.filter(status='APROBADO').exists()
            pending = docs.filter(status='PENDIENTE').exists()
            docs_by_category.append({
                'category': cat,
                'documents': docs,
                'has_approved': approved,
                'has_pending': pending,
                'is_complete': approved,
            })
        context['docs_by_category'] = docs_by_category

        # Resumen de documentos
        all_docs = ClientDocument.objects.filter(client=client)
        context['docs_total'] = all_docs.count()
        context['docs_approved'] = all_docs.filter(status='APROBADO').count()
        context['docs_pending'] = all_docs.filter(status='PENDIENTE').count()
        context['docs_rejected'] = all_docs.filter(status='RECHAZADO').count()
        context['docs_expired'] = all_docs.filter(status='VENCIDO').count()

        # Documentos por vencer (proximos 30 dias)
        from django.utils import timezone
        from datetime import timedelta
        today = timezone.now().date()
        context['docs_expiring_soon'] = all_docs.filter(
            expiration_date__gte=today,
            expiration_date__lte=today + timedelta(days=30),
            status='APROBADO'
        ).count()

        # Ultima verificacion SAT
        context['last_sat_verification'] = SATVerification.objects.filter(
            client=client
        ).order_by('-verification_date').first()

        # Fotografias
        context['photos_count'] = client.photos.count()

        # Manifestaciones activas
        context['active_manifests'] = client.manifests.filter(is_active=True).count()

        return context


class ClientCreateView(SuperuserRequiredMixin, CreateView):
    """Crear nuevo cliente"""
    model = Client
    form_class = ClientForm
    template_name = 'clients/client_form.html'
    success_url = reverse_lazy('client-list')

    def form_valid(self, form):
        messages.success(self.request, 'Cliente creado exitosamente.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Nuevo Cliente'
        context['button_text'] = 'Crear Cliente'
        return context


class ClientUpdateView(SuperuserRequiredMixin, UpdateView):
    """Editar cliente existente"""
    model = Client
    form_class = ClientForm
    template_name = 'clients/client_form.html'

    def get_success_url(self):
        return reverse('client-detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Cliente actualizado exitosamente.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Editar: {self.object.company}'
        context['button_text'] = 'Guardar Cambios'
        return context


class ClientDeleteView(SuperuserRequiredMixin, DeleteView):
    """Eliminar cliente"""
    model = Client
    template_name = 'clients/client_confirm_delete.html'
    success_url = reverse_lazy('client-list')
    context_object_name = 'client'

    def form_valid(self, form):
        messages.success(self.request, 'Cliente eliminado exitosamente.')
        return super().form_valid(form)


@login_required
@user_passes_test(is_superuser)
def client_steps_view(request, pk):
    """Vista para personalizar los pasos de un cliente con drag & drop"""
    client = get_object_or_404(Client, pk=pk)

    # Obtener todos los pasos disponibles
    all_steps = Step.objects.all().order_by('number')

    # Obtener pasos ya asignados al cliente
    assigned_steps = ClientStep.objects.filter(client=client).select_related('step')
    assigned_step_ids = set(cs.step_id for cs in assigned_steps)

    # Crear diccionario de pasos asignados para acceso rapido
    assigned_dict = {cs.step_id: cs for cs in assigned_steps}

    # Separar pasos fijos (primero y ultimo) de pasos opcionales
    fixed_first = None  # Paso 1: Recepcion de documentos
    fixed_last = None   # Paso 14: Comprobante de Pago/Devolucion
    optional_steps = []

    for step in all_steps:
        if step.is_fixed:
            if step.number == 1:
                fixed_first = step
            elif step.number == 14:
                fixed_last = step
        else:
            optional_steps.append(step)

    # Asegurar que los pasos fijos esten asignados automaticamente
    if fixed_first and fixed_first.id not in assigned_step_ids:
        ClientStep.objects.create(
            client=client,
            step=fixed_first,
            order=0,  # Siempre primero
            is_active=True
        )
        assigned_step_ids.add(fixed_first.id)

    if fixed_last and fixed_last.id not in assigned_step_ids:
        ClientStep.objects.create(
            client=client,
            step=fixed_last,
            order=9999,  # Siempre ultimo
            is_active=True
        )
        assigned_step_ids.add(fixed_last.id)

    # Actualizar diccionario con los pasos fijos recien creados
    assigned_steps = ClientStep.objects.filter(client=client).select_related('step')
    assigned_dict = {cs.step_id: cs for cs in assigned_steps}

    # Preparar pasos seleccionados (ordenados por order) - excluyendo fijos
    selected_steps = []
    for cs in sorted(assigned_steps, key=lambda x: (x.order, x.step.number)):
        if not cs.step.is_fixed:
            selected_steps.append({
                'step': cs.step,
                'client_step': cs,
                'order': cs.order,
            })

    # Preparar pasos disponibles (no asignados y no fijos)
    available_steps = []
    for step in optional_steps:
        if step.id not in assigned_step_ids:
            available_steps.append(step)

    context = {
        'client': client,
        'fixed_first': fixed_first,
        'fixed_last': fixed_last,
        'selected_steps': selected_steps,
        'available_steps': available_steps,
        'assigned_count': len(assigned_step_ids),
        'total_steps': all_steps.count(),
    }

    return render(request, 'clients/client_steps.html', context)


@login_required
@user_passes_test(is_superuser)
@require_POST
def toggle_client_step(request, pk, step_id):
    """Endpoint AJAX para agregar/quitar un paso de un cliente"""
    client = get_object_or_404(Client, pk=pk)
    step = get_object_or_404(Step, pk=step_id)

    # No permitir remover pasos fijos
    if step.is_fixed:
        return JsonResponse({
            'success': False,
            'error': 'Los pasos obligatorios no se pueden remover'
        }, status=400)

    client_step, created = ClientStep.objects.get_or_create(
        client=client,
        step=step,
        defaults={'order': step.number, 'is_active': True}
    )

    if not created:
        # Si ya existia, lo eliminamos
        client_step.delete()
        return JsonResponse({
            'success': True,
            'action': 'removed',
            'message': f'Paso {step.number} removido del cliente'
        })

    return JsonResponse({
        'success': True,
        'action': 'added',
        'message': f'Paso {step.number} agregado al cliente'
    })


@login_required
@user_passes_test(is_superuser)
@require_POST
def update_client_step(request, pk, step_id):
    """Endpoint AJAX para actualizar orden y estado de un paso"""
    client = get_object_or_404(Client, pk=pk)
    step = get_object_or_404(Step, pk=step_id)

    try:
        client_step = ClientStep.objects.get(client=client, step=step)
    except ClientStep.DoesNotExist:
        return JsonResponse({'error': 'Paso no asignado'}, status=404)

    order = request.POST.get('order')
    is_active = request.POST.get('is_active')

    if order is not None:
        try:
            client_step.order = int(order)
        except ValueError:
            return JsonResponse({'error': 'Orden invalido'}, status=400)

    if is_active is not None:
        client_step.is_active = is_active.lower() == 'true'

    client_step.save()

    return JsonResponse({
        'success': True,
        'message': 'Paso actualizado correctamente'
    })


@login_required
@user_passes_test(is_superuser)
@require_POST
def bulk_assign_steps(request, pk):
    """Asignar multiples pasos a un cliente de una vez"""
    client = get_object_or_404(Client, pk=pk)

    step_type = request.POST.get('type')  # 'imp', 'exp', 'all', 'none'

    # Obtener pasos fijos (siempre se mantienen)
    fixed_steps = Step.objects.filter(is_fixed=True)

    if step_type == 'none':
        # Eliminar solo pasos opcionales (mantener fijos)
        ClientStep.objects.filter(client=client, step__is_fixed=False).delete()
        messages.success(request, 'Pasos opcionales removidos. Los pasos obligatorios se mantienen.')

    elif step_type in ['imp', 'exp', 'all']:
        # Obtener pasos segun el tipo (excluyendo fijos)
        if step_type == 'imp':
            steps = Step.objects.filter(imp=True, is_fixed=False)
        elif step_type == 'exp':
            steps = Step.objects.filter(exp=True, is_fixed=False)
        else:  # all
            steps = Step.objects.filter(is_fixed=False)

        # Eliminar pasos opcionales existentes
        ClientStep.objects.filter(client=client, step__is_fixed=False).delete()

        # Crear pasos opcionales
        order = 1
        for step in steps.order_by('number'):
            ClientStep.objects.create(
                client=client,
                step=step,
                order=order,
                is_active=True
            )
            order += 1

        # Asegurar que pasos fijos existan
        for fixed_step in fixed_steps:
            ClientStep.objects.get_or_create(
                client=client,
                step=fixed_step,
                defaults={
                    'order': 0 if fixed_step.number == 1 else 9999,
                    'is_active': True
                }
            )

        messages.success(request, f'Se asignaron {steps.count()} pasos opcionales al cliente.')

    return redirect('client-steps', pk=pk)


@login_required
@user_passes_test(is_superuser)
@require_POST
def reorder_client_steps(request, pk):
    """Endpoint AJAX para reordenar pasos via drag & drop"""
    import json

    client = get_object_or_404(Client, pk=pk)

    try:
        data = json.loads(request.body)
        step_ids = data.get('step_ids', [])
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON invalido'}, status=400)

    if not step_ids:
        return JsonResponse({'error': 'No se recibieron pasos'}, status=400)

    # Actualizar orden de cada paso (empezando en 1, dejando 0 para el fijo inicial)
    for order, step_id in enumerate(step_ids, start=1):
        try:
            client_step = ClientStep.objects.get(client=client, step_id=step_id)
            # No modificar orden de pasos fijos
            if not client_step.step.is_fixed:
                client_step.order = order
                client_step.save()
        except ClientStep.DoesNotExist:
            continue

    return JsonResponse({
        'success': True,
        'message': 'Orden actualizado correctamente'
    })


# ============================================
# VISTAS DE EXPEDIENTE ELECTRÓNICO RGCE 1.4.14
# ============================================

@login_required
@user_passes_test(is_superuser)
def client_expediente_view(request, pk):
    """Vista principal del expediente electrónico del cliente"""
    client = get_object_or_404(Client, pk=pk)

    # Obtener todas las categorías de documentos
    categories = DocumentCategory.objects.all().order_by('order')

    # Documentos por categoría
    documents_by_category = {}
    for cat in categories:
        docs = client.documents.filter(category=cat).order_by('-created_at')
        documents_by_category[cat] = {
            'documents': docs,
            'has_approved': docs.filter(status='APROBADO').exists(),
            'latest': docs.first(),
        }

    # Calcular completitud del expediente
    total_required = categories.filter(is_required=True).count()
    completed = 0
    for cat in categories.filter(is_required=True):
        if client.documents.filter(category=cat, status='APROBADO').exists():
            completed += 1

    completeness_percentage = int((completed / total_required * 100)) if total_required > 0 else 0

    # Documentos por vencer (próximos 30 días)
    thirty_days = timezone.now().date() + timedelta(days=30)
    expiring_docs = client.documents.filter(
        expiration_date__lte=thirty_days,
        expiration_date__gt=timezone.now().date(),
        status='APROBADO'
    ).select_related('category').order_by('expiration_date')

    # Documentos vencidos
    expired_docs = client.documents.filter(
        expiration_date__lt=timezone.now().date()
    ).select_related('category')

    # Documentos pendientes de revisión
    pending_docs = client.documents.filter(status='PENDIENTE').select_related('category')

    # Manifestaciones activas
    manifests = client.manifests.filter(is_active=True).order_by('-signature_date')

    # Fotografías agrupadas por tipo
    photos = client.photos.all()
    photos_by_type = {}
    for photo_type, label in ClientPhoto.PHOTO_TYPES:
        photos_by_type[photo_type] = {
            'label': label,
            'photos': photos.filter(photo_type=photo_type)
        }

    # Última verificación SAT
    last_sat_verification = client.sat_verifications.first()

    context = {
        'client': client,
        'categories': categories,
        'documents_by_category': documents_by_category,
        'completeness_percentage': completeness_percentage,
        'completed_categories': completed,
        'total_required': total_required,
        'expiring_docs': expiring_docs,
        'expired_docs': expired_docs,
        'pending_docs': pending_docs,
        'manifests': manifests,
        'photos_by_type': photos_by_type,
        'last_sat_verification': last_sat_verification,
    }

    return render(request, 'clients/expediente/expediente_detail.html', context)


@login_required
@user_passes_test(is_superuser)
def client_compliance_edit(request, pk):
    """Editar datos de cumplimiento del cliente"""
    client = get_object_or_404(Client, pk=pk)

    if request.method == 'POST':
        form = ClientComplianceForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            messages.success(request, 'Datos de cumplimiento actualizados correctamente.')
            return redirect('client-expediente', pk=pk)
    else:
        form = ClientComplianceForm(instance=client)

    context = {
        'client': client,
        'form': form,
        'title': 'Editar Datos de Cumplimiento',
    }

    return render(request, 'clients/expediente/compliance_form.html', context)


# --- Vistas de Documentos ---

@login_required
@user_passes_test(is_superuser)
def client_document_upload(request, pk):
    """Subir un nuevo documento al expediente"""
    client = get_object_or_404(Client, pk=pk)

    if request.method == 'POST':
        form = ClientDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.client = client
            document.uploaded_by = request.user

            # Guardar metadatos del archivo
            uploaded_file = request.FILES.get('file')
            if uploaded_file:
                document.original_filename = uploaded_file.name
                document.file_size = uploaded_file.size
                document.mime_type = getattr(uploaded_file, 'content_type', '')

            document.save()
            messages.success(request, f'Documento "{document.name}" subido correctamente.')
            return redirect('client-expediente', pk=pk)
    else:
        # Pre-seleccionar categoría si viene en URL
        initial = {}
        category_id = request.GET.get('category')
        if category_id:
            initial['category'] = category_id
        form = ClientDocumentForm(initial=initial)

    # Obtener categorias para el JavaScript
    categories = DocumentCategory.objects.all().order_by('order')

    context = {
        'client': client,
        'form': form,
        'title': 'Subir Documento',
        'categories': categories,
    }

    return render(request, 'clients/documents/document_form.html', context)


@login_required
@user_passes_test(is_superuser)
def client_document_detail(request, pk, doc_pk):
    """Ver detalle de un documento"""
    client = get_object_or_404(Client, pk=pk)
    document = get_object_or_404(ClientDocument, pk=doc_pk, client=client)

    context = {
        'client': client,
        'document': document,
    }

    return render(request, 'clients/documents/document_detail.html', context)


@login_required
@user_passes_test(is_superuser)
def client_document_review(request, pk, doc_pk):
    """Revisar/aprobar un documento"""
    client = get_object_or_404(Client, pk=pk)
    document = get_object_or_404(ClientDocument, pk=doc_pk, client=client)

    if request.method == 'POST':
        form = ClientDocumentReviewForm(request.POST, instance=document)
        if form.is_valid():
            document = form.save(commit=False)
            document.reviewed_by = request.user
            document.reviewed_at = timezone.now()
            document.save()

            status_msg = dict(ClientDocument.STATUS_CHOICES).get(document.status, document.status)
            messages.success(request, f'Documento marcado como: {status_msg}')
            return redirect('client-expediente', pk=pk)
    else:
        form = ClientDocumentReviewForm(instance=document)

    context = {
        'client': client,
        'document': document,
        'form': form,
        'title': 'Revisar Documento',
    }

    return render(request, 'clients/documents/document_review.html', context)


@login_required
@user_passes_test(is_superuser)
def client_document_download(request, pk, doc_pk):
    """Descargar un documento"""
    client = get_object_or_404(Client, pk=pk)
    document = get_object_or_404(ClientDocument, pk=doc_pk, client=client)

    if not document.file:
        raise Http404("Archivo no encontrado")

    # Usar la URL firmada del storage seguro
    return redirect(document.file.url)


@login_required
@user_passes_test(is_superuser)
@require_POST
def client_document_delete(request, pk, doc_pk):
    """Eliminar un documento"""
    client = get_object_or_404(Client, pk=pk)
    document = get_object_or_404(ClientDocument, pk=doc_pk, client=client)

    doc_name = document.name
    document.delete()
    messages.success(request, f'Documento "{doc_name}" eliminado correctamente.')

    return redirect('client-expediente', pk=pk)


# --- Vistas de Manifestaciones ---

@login_required
@user_passes_test(is_superuser)
def client_manifest_create(request, pk):
    """Crear una nueva manifestación"""
    client = get_object_or_404(Client, pk=pk)

    if request.method == 'POST':
        form = ClientManifestForm(request.POST, request.FILES)
        if form.is_valid():
            manifest = form.save(commit=False)
            manifest.client = client
            manifest.created_by = request.user

            # Desactivar manifestaciones anteriores del mismo tipo
            ClientManifest.objects.filter(
                client=client,
                manifest_type=manifest.manifest_type,
                is_active=True
            ).update(is_active=False, superseded_by=None)

            manifest.save()

            # Actualizar superseded_by de las anteriores
            ClientManifest.objects.filter(
                client=client,
                manifest_type=manifest.manifest_type,
                is_active=False,
                superseded_by__isnull=True
            ).exclude(pk=manifest.pk).update(superseded_by=manifest)

            messages.success(request, 'Manifestación registrada correctamente.')
            return redirect('client-expediente', pk=pk)
    else:
        # Pre-llenar con plantilla si se especifica tipo
        initial = {}
        manifest_type = request.GET.get('type')
        if manifest_type and manifest_type in MANIFEST_TEMPLATES:
            initial['manifest_type'] = manifest_type
            initial['content'] = MANIFEST_TEMPLATES[manifest_type].format(
                company=client.company,
                rfc=client.rfc or '[RFC]'
            )
        form = ClientManifestForm(initial=initial)

    context = {
        'client': client,
        'form': form,
        'title': 'Nueva Manifestación',
        'templates': MANIFEST_TEMPLATES,
    }

    return render(request, 'clients/manifests/manifest_form.html', context)


@login_required
@user_passes_test(is_superuser)
def client_manifest_detail(request, pk, manifest_pk):
    """Ver detalle de una manifestación"""
    client = get_object_or_404(Client, pk=pk)
    manifest = get_object_or_404(ClientManifest, pk=manifest_pk, client=client)

    # Historial de manifestaciones del mismo tipo
    history = ClientManifest.objects.filter(
        client=client,
        manifest_type=manifest.manifest_type
    ).exclude(pk=manifest.pk).order_by('-signature_date')

    context = {
        'client': client,
        'manifest': manifest,
        'history': history,
    }

    return render(request, 'clients/manifests/manifest_detail.html', context)


# --- Vistas de Fotografías ---

@login_required
@user_passes_test(is_superuser)
def client_photo_upload(request, pk):
    """Subir una fotografía"""
    client = get_object_or_404(Client, pk=pk)

    if request.method == 'POST':
        form = ClientPhotoForm(request.POST, request.FILES)
        if form.is_valid():
            photo = form.save(commit=False)
            photo.client = client
            photo.uploaded_by = request.user
            photo.save()
            messages.success(request, 'Fotografía subida correctamente.')
            return redirect('client-expediente', pk=pk)
    else:
        initial = {}
        photo_type = request.GET.get('type')
        if photo_type:
            initial['photo_type'] = photo_type
        form = ClientPhotoForm(initial=initial)

    context = {
        'client': client,
        'form': form,
        'title': 'Subir Fotografía',
    }

    return render(request, 'clients/photos/photo_form.html', context)


@login_required
@user_passes_test(is_superuser)
@require_POST
def client_photo_delete(request, pk, photo_pk):
    """Eliminar una fotografía"""
    client = get_object_or_404(Client, pk=pk)
    photo = get_object_or_404(ClientPhoto, pk=photo_pk, client=client)

    photo.delete()
    messages.success(request, 'Fotografía eliminada correctamente.')

    return redirect('client-expediente', pk=pk)


# --- Vistas de Verificación SAT ---

@login_required
@user_passes_test(is_superuser)
def client_sat_verification(request, pk):
    """Ver historial de verificaciones SAT"""
    client = get_object_or_404(Client, pk=pk)

    verifications = client.sat_verifications.all().order_by('-verification_date')

    context = {
        'client': client,
        'verifications': verifications,
    }

    return render(request, 'clients/sat/verification_list.html', context)


@login_required
@user_passes_test(is_superuser)
def client_sat_verification_create(request, pk):
    """Crear verificación manual del SAT"""
    client = get_object_or_404(Client, pk=pk)

    if request.method == 'POST':
        form = SATVerificationForm(request.POST)
        if form.is_valid():
            verification = form.save(commit=False)
            verification.client = client
            verification.verified_by = request.user
            verification.verification_method = 'MANUAL'

            # Determinar estado basado en checkboxes
            if verification.is_in_efos:
                verification.status = 'DEFINITIVO'
            elif verification.is_in_edos:
                verification.status = 'PRESUNTO'
            else:
                verification.status = 'LIMPIO'

            verification.save()
            messages.success(request, 'Verificación SAT registrada correctamente.')
            return redirect('client-expediente', pk=pk)
    else:
        form = SATVerificationForm()

    context = {
        'client': client,
        'form': form,
        'title': 'Nueva Verificación SAT',
    }

    return render(request, 'clients/sat/verification_form.html', context)


# --- Dashboard de Cumplimiento ---

@login_required
@user_passes_test(is_superuser)
def compliance_dashboard_view(request):
    """Dashboard general de cumplimiento de todos los clientes"""
    # Clientes activos con anotaciones
    clients = Client.objects.filter(show=True).annotate(
        total_docs=Count('documents'),
        approved_docs=Count('documents', filter=Q(documents__status='APROBADO')),
        pending_docs=Count('documents', filter=Q(documents__status='PENDIENTE')),
        expired_docs=Count('documents', filter=Q(documents__status='VENCIDO')),
    ).order_by('company')

    # Estadísticas generales
    thirty_days = timezone.now().date() + timedelta(days=30)

    stats = {
        'total_clients': clients.count(),
        'complete_expedientes': clients.filter(expediente_completo=True).count(),
        'incomplete_expedientes': clients.filter(expediente_completo=False).count(),
        'docs_expiring_soon': ClientDocument.objects.filter(
            expiration_date__lte=thirty_days,
            expiration_date__gt=timezone.now().date(),
            status='APROBADO'
        ).count(),
        'docs_pending_review': ClientDocument.objects.filter(status='PENDIENTE').count(),
        'docs_expired': ClientDocument.objects.filter(status='VENCIDO').count(),
    }

    # Clientes con expedientes incompletos
    incomplete_clients = clients.filter(expediente_completo=False)[:10]

    # Documentos por vencer pronto
    expiring_soon = ClientDocument.objects.filter(
        expiration_date__lte=thirty_days,
        expiration_date__gt=timezone.now().date(),
        status='APROBADO'
    ).select_related('client', 'category').order_by('expiration_date')[:20]

    # Documentos pendientes de revisión
    pending_review = ClientDocument.objects.filter(
        status='PENDIENTE'
    ).select_related('client', 'category').order_by('-created_at')[:20]

    context = {
        'stats': stats,
        'clients': clients,
        'incomplete_clients': incomplete_clients,
        'expiring_soon': expiring_soon,
        'pending_review': pending_review,
    }

    return render(request, 'clients/compliance/dashboard.html', context)
