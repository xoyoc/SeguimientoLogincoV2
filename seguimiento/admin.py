"""
Custom Django Admin Site Configuration.

Organizes the admin interface into logical groups:
- Operaciones: Shipments, Trackings, Revisions
- Clientes y Cumplimiento: Clients, Documents, Compliance
- Configuración: Steps, Terminals, Lines, Departments
- Sistema: Users, Groups, Notifications
"""

from django.contrib import admin
from django.contrib.admin.apps import AdminConfig


class SeguimientoAdminSite(admin.AdminSite):
    """Custom admin site with improved organization."""

    site_header = "Sistema de Seguimiento - Administración"
    site_title = "Seguimiento Admin"
    index_title = "Panel de Administración"

    def get_app_list(self, request, app_label=None):
        """
        Override to group apps into logical sections.
        """
        app_list = super().get_app_list(request, app_label)

        # Define custom grouping
        groups = {
            'Operaciones': {
                'icon': '📦',
                'apps': ['shipments', 'trackings', 'revisions'],
                'models': []
            },
            'Clientes y Cumplimiento RGCE': {
                'icon': '👥',
                'apps': ['clients'],
                'models': []
            },
            'Configuración': {
                'icon': '⚙️',
                'apps': ['steps', 'terminals', 'lines', 'departments'],
                'models': []
            },
            'Sistema': {
                'icon': '🔧',
                'apps': ['users', 'auth', 'notifications', 'django_celery_beat'],
                'models': []
            },
        }

        # If a specific app is requested, return standard behavior
        if app_label:
            return app_list

        # Reorganize apps into groups
        grouped_list = []
        processed_apps = set()

        for group_name, group_config in groups.items():
            group_models = []

            for app in app_list:
                app_name = app.get('app_label', '')

                if app_name in group_config['apps']:
                    processed_apps.add(app_name)
                    group_models.extend(app.get('models', []))

            if group_models:
                # Sort models alphabetically within each group
                group_models.sort(key=lambda x: x.get('name', ''))

                grouped_list.append({
                    'name': f"{group_config['icon']} {group_name}",
                    'app_label': group_name.lower().replace(' ', '_'),
                    'app_url': '',
                    'has_module_perms': True,
                    'models': group_models,
                })

        # Add any remaining apps not in our groups
        for app in app_list:
            if app.get('app_label', '') not in processed_apps:
                grouped_list.append(app)

        return grouped_list


class SeguimientoAdminConfig(AdminConfig):
    """Admin config to use custom admin site."""
    default_site = 'seguimiento.admin.SeguimientoAdminSite'
