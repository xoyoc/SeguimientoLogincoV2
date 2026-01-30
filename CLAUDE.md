# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LogincoSeguimientoV2 is a Django 6.0-based shipping tracking and management system for logistics operations. The application tracks shipments through various stages, manages clients, and provides analytics dashboards. The system was migrated from MongoDB/Mongoose to Django/SQLite.

## Technology Stack

- **Backend**: Django 6.0, Django REST Framework 3.16.1
- **Task Queue**: Celery 5.6.2 with Redis
- **WebSockets**: Django Channels 4.3.2
- **Frontend**: Tailwind CSS (django-tailwind), Chart.js
- **Database**: SQLite3 (development), PostgreSQL (production via psycopg2-binary)
- **Authentication**: Custom User model with JWT support (djangorestframework_simplejwt)

## Common Commands

```bash
# Development server
python manage.py runserver

# Database operations
python manage.py makemigrations
python manage.py migrate

# Load fixture data
python manage.py loaddata django_fixtures/users_fixture.json
python manage.py loaddata django_fixtures/clients_fixture.json
python manage.py loaddata django_fixtures/terminals_fixture.json
python manage.py loaddata django_fixtures/lines_fixture.json
python manage.py loaddata django_fixtures/steps_fixture.json

# Create admin user
python manage.py createsuperuser

# Django shell
python manage.py shell
```

## Architecture

### Django Apps (in project root)

| App | Purpose |
|-----|---------|
| `users` | Custom User model extending AbstractUser |
| `shipments` | Core shipment management with CRUD views |
| `trackings` | Tracking status management for shipment stages |
| `revisions` | Revision history and audit trail |
| `clients` | Client/customer management |
| `terminals` | Port terminal lookup table |
| `lines` | Shipping line/carrier lookup table |
| `steps` | Tracking stages definition (numbered steps with import/export flags) |
| `notifications` | Notification system (placeholder) |

### Key Model Relationships

```
User ←─────────────────────────────────┐
  │                                    │
  ↓                                    │
Client ←──── Shipment ────────────────→│
               │    ↘                  │
               │     Terminal, Line    │
               ↓                       │
            Tracking ─────────────────→│
               │                       │
               ↓                       │
            Revision ─────────────────→┘
```

- **Shipment**: Central entity with FKs to User (assigned_to), Client, Terminal, Line
- **Tracking**: Links to Shipment, tracks step number and status
- **Revision**: Links to Tracking, stores audit history with file attachments (JSONField)
- **ClientStep**: Links Client to Step, allows per-client process customization

### URL Structure

- `/` - Dashboard view (general statistics)
- `/mi-dashboard/` - Personal dashboard (user's assigned shipments, requires login)
- `/analytics/` - Analytics view with charts
- `/shipments/` - Shipment CRUD (list, detail with timeline, create, edit, delete)
- `/trackings/` - Tracking CRUD
- `/revisions/` - Revision CRUD (requires login)
- `/revisions/quick-add/` - AJAX endpoint for quick comments
- `/clients/` - Client management (admin only)
- `/clients/<id>/steps/` - Configure client process steps
- `/login/` - Login page
- `/logout/` - Logout (redirects to login)
- `/admin/` - Django admin interface

### Main Views Location

- Dashboard and analytics: `seguimiento/views.py`
- App-specific views: `<app_name>/views.py`

## Data Migration Context

The `db_exports/` directory contains migration utilities from the original MongoDB system:
- `transform_to_django.py` - Transforms MongoDB exports to Django fixtures
- `mongoose_exports/` - Original MongoDB JSON exports
- `django_fixtures/` - Generated Django fixtures for data loading

## Key Features

### Client Management Module (`/clients/`)
- Full CRUD for clients (admin/staff only)
- Views: `clients/views.py`, Templates: `clients/templates/clients/`
- Features: search, filter by state, filter by visibility status

### Client Process Customization (`/clients/<id>/steps/`)
- Interactive UI for assigning steps to clients
- Toggle switches for each step assignment
- Bulk actions: assign all IMP steps, EXP steps, or all steps
- Order and active status customization per step
- Shipment detail view shows timeline based on client's configured steps

### Personal Dashboard (`/mi-dashboard/`)
- Shows only shipments assigned to the logged-in user
- Quick comment feature via modal (AJAX)
- Statistics: pending/in-progress trackings, completed today

### Shipment Timeline
- Visual progress bar showing completion percentage
- Step-by-step timeline with status indicators (completed/in-progress/pending/not started)
- Uses client's custom steps if configured, otherwise falls back to IMP/EXP steps

## Configuration Notes

- **Language**: Spanish (es-mx)
- **Timezone**: America/Mexico_City
- **Custom User Model**: `users.User` (defined in AUTH_USER_MODEL)
- Settings file: `seguimiento/settings.py`
- Environment variables loaded from `.env` (contains SECRET_KEY)
- **Virtual Environment**: `.venvLogincoSeguimiento/` (activate before running commands)
