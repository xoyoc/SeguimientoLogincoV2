"""
Celery configuration for seguimiento project.

This module configures Celery for periodic tasks like:
- Document expiration checking
- Expediente completeness updates
- SAT verification scheduling
"""

import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'seguimiento.settings')

app = Celery('seguimiento')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery Beat Schedule - Periodic Tasks
app.conf.beat_schedule = {
    # Check document expiration every day at 6:00 AM
    'check-document-expiration-daily': {
        'task': 'clients.tasks.check_document_expiration',
        'schedule': crontab(hour=6, minute=0),
    },
    # Update expediente completeness every day at 6:30 AM
    'update-expediente-completeness-daily': {
        'task': 'clients.tasks.update_expediente_completeness',
        'schedule': crontab(hour=6, minute=30),
    },
    # Verify SAT status weekly on Mondays at 7:00 AM
    'verify-sat-status-weekly': {
        'task': 'clients.tasks.verify_clients_sat_status',
        'schedule': crontab(hour=7, minute=0, day_of_week=1),
    },
}

app.conf.timezone = 'America/Mexico_City'


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
