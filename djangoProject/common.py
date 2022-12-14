import re
from django.utils import timezone
from django.db.models import Q
from rest_framework.permissions import BasePermission as RestFrameworkBasePermission, SAFE_METHODS
from rest_framework.viewsets import ViewSet
from rest_framework.pagination import CursorPagination
from rest_framework.serializers import ModelSerializer, ValidationError

from member.models import Session, Blocklist


EMOJI_PATTERN = re.compile(
    "(["
    "\U0001F1E0-\U0001F1FF"  # flags (iOS)
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F680-\U0001F6FF"  # transport & map symbols
    "\U0001F700-\U0001F77F"  # alchemical symbols
    "\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
    "\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
    "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
    "\U0001FA00-\U0001FA6F"  # Chess Symbols
    "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
    "\U00002702-\U000027B0"  # Dingbats
    "])"
)


def is_string_truthy(value):
    return value in ["1", "true", "TRUE", "True"]


class PermissionsPerMethodMixin(ViewSet):
    def get_permissions(self):
        """
        Allows overriding default permissions with @permission_classes_decorator
        """
        if self.action:
            view = getattr(self, self.action)
            if hasattr(view, 'permission_classes'):
                return [permission_class() for permission_class in view.permission_classes]
        return super().get_permissions()


def get_current_session(request):
    return Session.objects.get(ip_address=request.META['REMOTE_ADDR'])


class BasePermission(RestFrameworkBasePermission):
    def has_permission(self, request, view):
        if not getattr(self, 'no_safe_methods', None) and request.method in SAFE_METHODS:
            return True
        expires_query = Q(expires=None) | Q(expires__gt=timezone.now())
        session_query = Q(session=get_current_session(request))
        if request.user.is_authenticated:
            session_query |= Q(user=request.user)
        return not Blocklist.objects.filter(expires_query, session_query).exists()


class IsAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        return super().has_permission(request, view) or \
               request.user.is_authenticated and request.user.role == 'admin'


# class IsStaffOrReadOnly(BasePermission):
#     no_safe_methods = True
#
#     def has_permission(self, request, view):
#         return request.user.is_authenticated and (request.user.role == 'admin' or
#                                                   request.user.role == 'moderator' and request.method != 'DELETE')


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin'


class IsStaff(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['admin', 'moderator']


class DefaultCursorPagination(CursorPagination):
    page_size = 20


class ConfessionOrCommentInSerializerUnique(ModelSerializer):
    def create(self, validated_data):
        if bool(validated_data.get('confession', False)) == bool(validated_data.get('comment', False)):
            raise ValidationError({"error": "There must be either one confession or one comment specified."})
        if self.Meta.model.objects.filter(**validated_data).exists():
            raise ValidationError({"error": self._duplicate_error})
        return super().create(validated_data)

