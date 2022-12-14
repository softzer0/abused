from djangoProject.common import BasePermission


class ReportPermission(BasePermission):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.is_authenticated and request.user.role \
               or request.method == 'POST' or request.user.role == 'admin'

