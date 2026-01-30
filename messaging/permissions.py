from rest_framework.permissions import BasePermission

class CanSendMessage(BasePermission):
    def has_permission(self, request, view):
        user = request.user

        if user.role == "SUPERADMIN":
            return True

        if user.role == "ADMIN":
            return True

        if user.role == "EMPLOYEE":
            return True  # validated later (receiver check)

        return False
