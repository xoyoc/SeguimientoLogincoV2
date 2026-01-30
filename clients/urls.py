from django.urls import path
from .views import (
    # Vistas existentes
    ClientListView, ClientDetailView, ClientCreateView,
    ClientUpdateView, ClientDeleteView, client_steps_view,
    toggle_client_step, update_client_step, bulk_assign_steps,
    reorder_client_steps,
    # Vistas de expediente electrónico
    client_expediente_view, client_compliance_edit,
    # Vistas de documentos
    client_document_upload, client_document_detail,
    client_document_review, client_document_download, client_document_delete,
    # Vistas de manifestaciones
    client_manifest_create, client_manifest_detail,
    # Vistas de fotografías
    client_photo_upload, client_photo_delete,
    # Vistas de verificación SAT
    client_sat_verification, client_sat_verification_create,
    # Dashboard de cumplimiento
    compliance_dashboard_view,
)

urlpatterns = [
    # CRUD de clientes
    path('', ClientListView.as_view(), name='client-list'),
    path('create/', ClientCreateView.as_view(), name='client-create'),
    path('<int:pk>/', ClientDetailView.as_view(), name='client-detail'),
    path('<int:pk>/edit/', ClientUpdateView.as_view(), name='client-edit'),
    path('<int:pk>/delete/', ClientDeleteView.as_view(), name='client-delete'),

    # Pasos del cliente
    path('<int:pk>/steps/', client_steps_view, name='client-steps'),
    path('<int:pk>/steps/<int:step_id>/toggle/', toggle_client_step, name='client-step-toggle'),
    path('<int:pk>/steps/<int:step_id>/update/', update_client_step, name='client-step-update'),
    path('<int:pk>/steps/bulk/', bulk_assign_steps, name='client-steps-bulk'),
    path('<int:pk>/steps/reorder/', reorder_client_steps, name='client-steps-reorder'),

    # Expediente electrónico RGCE 1.4.14
    path('<int:pk>/expediente/', client_expediente_view, name='client-expediente'),
    path('<int:pk>/expediente/compliance/', client_compliance_edit, name='client-compliance-edit'),

    # Documentos del expediente
    path('<int:pk>/documentos/upload/', client_document_upload, name='client-document-upload'),
    path('<int:pk>/documentos/<int:doc_pk>/', client_document_detail, name='client-document-detail'),
    path('<int:pk>/documentos/<int:doc_pk>/review/', client_document_review, name='client-document-review'),
    path('<int:pk>/documentos/<int:doc_pk>/download/', client_document_download, name='client-document-download'),
    path('<int:pk>/documentos/<int:doc_pk>/delete/', client_document_delete, name='client-document-delete'),

    # Manifestaciones
    path('<int:pk>/manifestaciones/create/', client_manifest_create, name='client-manifest-create'),
    path('<int:pk>/manifestaciones/<int:manifest_pk>/', client_manifest_detail, name='client-manifest-detail'),

    # Fotografías
    path('<int:pk>/fotos/upload/', client_photo_upload, name='client-photo-upload'),
    path('<int:pk>/fotos/<int:photo_pk>/delete/', client_photo_delete, name='client-photo-delete'),

    # Verificación SAT
    path('<int:pk>/sat-verificacion/', client_sat_verification, name='client-sat-verification'),
    path('<int:pk>/sat-verificacion/create/', client_sat_verification_create, name='client-sat-verification-create'),

    # Dashboard de cumplimiento
    path('cumplimiento/', compliance_dashboard_view, name='compliance-dashboard'),
]
