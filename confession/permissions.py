from rest_framework.permissions import SAFE_METHODS

from djangoProject.common import BasePermission
from member.models import Session


class ConfessionPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.method in SAFE_METHODS or \
               obj.author == request.user and not obj.is_approved or \
               request.user.is_authenticated and (request.user.role == 'admin' or
                                                  request.method != 'DELETE' and request.user.role == 'moderator')


class CommentReactionPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.method in SAFE_METHODS or \
               Session.objects.get(ip_address=request.META['REMOTE_ADDR']) == obj.sender or \
               request.method == 'DELETE' and request.user.is_authenticated and request.user.role == 'admin'

