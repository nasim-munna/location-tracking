from rest_framework.permissions import BasePermission

class IsSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.role == 'SUPERADMIN'


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.role == 'ADMIN'


class IsEmployee(BasePermission):
    def has_permission(self, request, view):
        return request.user.role == 'EMPLOYEE'
