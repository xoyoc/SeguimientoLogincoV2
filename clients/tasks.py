"""
Celery tasks for clients app.

Periodic tasks for:
- Document expiration monitoring
- Expediente completeness updates
- SAT verification scheduling
"""

from celery import shared_task
from django.utils import timezone
from django.db.models import Count, Q
from django.core.mail import send_mail
from django.conf import settings
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def check_document_expiration(self):
    """
    Check for documents that are expired or about to expire.
    Marks expired documents and creates notifications.
    Runs daily at 6:00 AM.
    """
    from .models import ClientDocument, Client
    from notifications.models import Notification

    today = timezone.now().date()
    expiration_warning_days = 30

    try:
        # Mark expired documents
        expired_docs = ClientDocument.objects.filter(
            expiration_date__lt=today,
            status__in=['PENDIENTE', 'APROBADO']
        )
        expired_count = expired_docs.update(status='VENCIDO')
        logger.info(f"Marked {expired_count} documents as expired")

        # Find documents expiring soon (within 30 days)
        expiring_soon = ClientDocument.objects.filter(
            expiration_date__gte=today,
            expiration_date__lte=today + timedelta(days=expiration_warning_days),
            status='APROBADO'
        ).select_related('client', 'category')

        # Create notifications for expiring documents
        for doc in expiring_soon:
            days_until = (doc.expiration_date - today).days

            # Create notification if not already exists for this document
            notification, created = Notification.objects.get_or_create(
                notification_type='DOCUMENT_EXPIRING',
                content_type__model='clientdocument',
                object_id=doc.pk,
                defaults={
                    'title': f'Documento por vencer: {doc.name}',
                    'message': f'El documento "{doc.name}" del cliente {doc.client.company} '
                               f'vencerá en {days_until} días ({doc.expiration_date}).',
                    'priority': 'HIGH' if days_until <= 7 else 'MEDIUM',
                    'related_client': doc.client,
                }
            )

            if created:
                logger.info(f"Created expiration notification for document {doc.pk}")

        # Create notifications for already expired documents
        expired_docs_list = ClientDocument.objects.filter(
            status='VENCIDO'
        ).select_related('client', 'category')

        for doc in expired_docs_list:
            notification, created = Notification.objects.get_or_create(
                notification_type='DOCUMENT_EXPIRED',
                content_type__model='clientdocument',
                object_id=doc.pk,
                defaults={
                    'title': f'Documento vencido: {doc.name}',
                    'message': f'El documento "{doc.name}" del cliente {doc.client.company} '
                               f'ha vencido ({doc.expiration_date}).',
                    'priority': 'URGENT',
                    'related_client': doc.client,
                }
            )

        return {
            'expired_marked': expired_count,
            'expiring_soon': expiring_soon.count(),
        }

    except Exception as exc:
        logger.error(f"Error in check_document_expiration: {exc}")
        raise self.retry(exc=exc, countdown=60 * 5)  # Retry in 5 minutes


@shared_task(bind=True, max_retries=3)
def update_expediente_completeness(self):
    """
    Update the expediente_completo status for all clients.
    Runs daily at 6:30 AM.
    """
    from .models import Client, DocumentCategory, ClientDocument

    try:
        clients = Client.objects.filter(show=True)
        required_categories = DocumentCategory.objects.filter(is_required=True)
        required_count = required_categories.count()

        updated_complete = 0
        updated_incomplete = 0

        for client in clients:
            # Check if client has all required documents approved
            approved_required = ClientDocument.objects.filter(
                client=client,
                category__is_required=True,
                status='APROBADO'
            ).values('category').distinct().count()

            is_complete = approved_required >= required_count

            if client.expediente_completo != is_complete:
                client.expediente_completo = is_complete
                client.ultima_verificacion_expediente = timezone.now()
                client.save(update_fields=['expediente_completo', 'ultima_verificacion_expediente'])

                if is_complete:
                    updated_complete += 1
                else:
                    updated_incomplete += 1

        logger.info(f"Updated expediente status: {updated_complete} complete, {updated_incomplete} incomplete")

        return {
            'updated_complete': updated_complete,
            'updated_incomplete': updated_incomplete,
            'total_clients': clients.count(),
        }

    except Exception as exc:
        logger.error(f"Error in update_expediente_completeness: {exc}")
        raise self.retry(exc=exc, countdown=60 * 5)


@shared_task(bind=True, max_retries=3)
def verify_clients_sat_status(self):
    """
    Verify all active clients against SAT EFOS/EDOS lists.
    Runs weekly on Mondays at 7:00 AM.
    """
    from .models import Client, SATVerification
    from .services.sat_service import SATVerificationService

    try:
        service = SATVerificationService()
        clients = Client.objects.filter(show=True).exclude(rfc__isnull=True).exclude(rfc='')

        results = {
            'verified': 0,
            'in_efos': 0,
            'in_edos': 0,
            'errors': 0,
        }

        for client in clients:
            try:
                result = service.verify_rfc(client.rfc)

                # Create verification record
                SATVerification.objects.create(
                    client=client,
                    is_in_efos=result.get('is_in_efos', False),
                    is_in_edos=result.get('is_in_edos', False),
                    sat_response=result.get('raw_response', {}),
                    verification_method='AUTOMATIC',
                    status=result.get('status', 'ERROR'),
                    notes=f"Verificación automática semanal - {timezone.now().strftime('%Y-%m-%d %H:%M')}"
                )

                results['verified'] += 1
                if result.get('is_in_efos'):
                    results['in_efos'] += 1
                if result.get('is_in_edos'):
                    results['in_edos'] += 1

            except Exception as e:
                logger.error(f"Error verifying client {client.pk} ({client.rfc}): {e}")
                results['errors'] += 1

        logger.info(f"SAT verification complete: {results}")
        return results

    except Exception as exc:
        logger.error(f"Error in verify_clients_sat_status: {exc}")
        raise self.retry(exc=exc, countdown=60 * 30)  # Retry in 30 minutes


@shared_task
def send_expiration_alert_email(document_id):
    """
    Send email alert for a document about to expire.
    """
    from .models import ClientDocument

    try:
        doc = ClientDocument.objects.select_related('client', 'category').get(pk=document_id)

        if not doc.expiration_date:
            return {'status': 'skipped', 'reason': 'no expiration date'}

        days_until = (doc.expiration_date - timezone.now().date()).days

        subject = f'[ALERTA] Documento por vencer - {doc.client.company}'
        message = f"""
        Estimado usuario,

        El siguiente documento está próximo a vencer:

        Cliente: {doc.client.company}
        RFC: {doc.client.rfc or 'No especificado'}
        Documento: {doc.name}
        Categoría: {doc.category.name}
        Fecha de vencimiento: {doc.expiration_date.strftime('%d/%m/%Y')}
        Días restantes: {days_until}

        Por favor, solicite al cliente la actualización de este documento.

        ---
        Sistema de Seguimiento RGCE 1.4.14
        """

        # Get admin emails (superusers)
        from django.contrib.auth import get_user_model
        User = get_user_model()
        admin_emails = list(User.objects.filter(
            is_superuser=True,
            is_active=True
        ).values_list('email', flat=True))

        if admin_emails:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=admin_emails,
                fail_silently=False,
            )
            logger.info(f"Sent expiration alert for document {document_id} to {len(admin_emails)} admins")
            return {'status': 'sent', 'recipients': len(admin_emails)}

        return {'status': 'skipped', 'reason': 'no admin emails'}

    except ClientDocument.DoesNotExist:
        logger.warning(f"Document {document_id} not found for email alert")
        return {'status': 'error', 'reason': 'document not found'}
    except Exception as e:
        logger.error(f"Error sending expiration alert email: {e}")
        return {'status': 'error', 'reason': str(e)}
