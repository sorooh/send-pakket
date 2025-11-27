"""
Custom permissions for the platform
"""

from rest_framework.permissions import BasePermission


class IsCompanyMember(BasePermission):
    """
    Check that the user is a member of the company
    """

    def has_permission(self, request, view):
        """
        Check permission at the view level
        """
        return hasattr(request.user, 'company') and request.user.company is not None

    def has_object_permission(self, request, view, obj):
        """
        Check permission at the object level
        """
        if hasattr(obj, 'company'):
            return obj.company == request.user.company
        return True


class IsCompanyAdmin(BasePermission):
    """
    Check that the user is a company administrator
    """

    def has_permission(self, request, view):
        """
        Check permission at the view level
        """
        # Allow superusers
        if request.user.is_superuser:
            return True

        return (
            hasattr(request.user, 'company') and
            request.user.company is not None and
            getattr(request.user, 'role', None) in ['admin', 'owner']
        )

    def has_object_permission(self, request, view, obj):
        """
        Check permission at the object level
        """
        # Allow superusers
        if request.user.is_superuser:
            return True

        if hasattr(obj, 'company'):
            return (
                obj.company == request.user.company and
                getattr(request.user, 'role', None) in ['admin', 'owner']
            )
        return getattr(request.user, 'role', None) in ['admin', 'owner']


class IsPlatformAdmin(BasePermission):
    """
    Check that the user is a platform administrator
    """

    def has_permission(self, request, view):
        """
        Check permission at the view level
        """
        return (
            request.user.is_staff or
            request.user.is_superuser or
            getattr(request.user, 'role', None) == 'platform_admin'
        )

    def has_object_permission(self, request, view, obj):
        """
        Check permission at the object level
        """
        return (
            request.user.is_staff or
            request.user.is_superuser or
            getattr(request.user, 'role', None) == 'platform_admin'
        )