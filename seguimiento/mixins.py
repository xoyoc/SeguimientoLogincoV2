from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.core.exceptions import PermissionDenied


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin que requiere que el usuario sea staff o superusuario"""

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            # Si es usuario de cliente, redirigir a su portal
            if self.request.user.is_client_user:
                return redirect('client-dashboard')
            raise PermissionDenied("No tienes permiso para acceder a esta seccion.")
        return super().handle_no_permission()


class SuperuserRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin que requiere que el usuario sea superusuario"""

    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            if self.request.user.is_client_user:
                return redirect('client-dashboard')
            elif self.request.user.is_staff:
                return redirect('my-dashboard')
            raise PermissionDenied("No tienes permiso para acceder a esta seccion.")
        return super().handle_no_permission()


class ClientUserRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin que requiere que el usuario sea un usuario de cliente"""

    def test_func(self):
        return self.request.user.is_client_user

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            if self.request.user.is_staff:
                return redirect('my-dashboard')
            raise PermissionDenied("No tienes permiso para acceder a esta seccion.")
        return super().handle_no_permission()
