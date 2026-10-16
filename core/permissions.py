from rest_framework.permissions import BasePermission

class IsDirector(BasePermission):
    """Faqat Direktor yoki Superuser uchun"""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (getattr(request.user, 'role', None) == 'direktor' or request.user.is_superuser)


class IsOmborchi(BasePermission):
    """Omborchi va Direktor uchun"""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (getattr(request.user, 'role', None) in ['omborchi', 'direktor'] or request.user.is_superuser)


class IsTexnolog(BasePermission):
    """Texnolog va Direktor uchun"""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (getattr(request.user, 'role', None) in ['texnolog', 'direktor'] or request.user.is_superuser)