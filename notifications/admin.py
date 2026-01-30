from django.contrib import admin
from django.utils.html import format_html
from .models import Notification, NotificationPreference


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Admin configuration for Notification model."""

    list_display = (
        'title', 'notification_type', 'priority_badge', 'related_client',
        'recipient', 'is_read', 'email_sent', 'created_at'
    )
    list_filter = ('notification_type', 'priority', 'is_read', 'email_sent')
    search_fields = ('title', 'message', 'related_client__company')
    readonly_fields = ('created_at', 'updated_at', 'read_at', 'email_sent_at')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)

    fieldsets = (
        ('Notificación', {
            'fields': ('notification_type', 'title', 'message', 'priority')
        }),
        ('Relaciones', {
            'fields': ('related_client', 'recipient', 'content_type', 'object_id')
        }),
        ('Estado', {
            'fields': ('is_read', 'read_at', 'email_sent', 'email_sent_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def priority_badge(self, obj):
        colors = {
            'LOW': 'gray',
            'MEDIUM': 'blue',
            'HIGH': 'orange',
            'URGENT': 'red',
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.priority, 'black'),
            obj.get_priority_display()
        )
    priority_badge.short_description = 'Prioridad'

    actions = ['mark_as_read', 'mark_as_unread']

    @admin.action(description='Marcar como leídas')
    def mark_as_read(self, request, queryset):
        from django.utils import timezone
        queryset.update(is_read=True, read_at=timezone.now())

    @admin.action(description='Marcar como no leídas')
    def mark_as_unread(self, request, queryset):
        queryset.update(is_read=False, read_at=None)


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    """Admin configuration for NotificationPreference model."""

    list_display = (
        'user', 'email_document_expiring', 'email_document_expired',
        'email_sat_alerts', 'expiration_warning_days'
    )
    list_filter = ('email_document_expiring', 'email_sat_alerts')
    search_fields = ('user__username', 'user__email')
