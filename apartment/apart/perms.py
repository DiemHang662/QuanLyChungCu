from rest_framework import permissions
class ResidentAuthenticated(permissions.IsAuthenticated):
    def has_permission(self, request, view):
        return request.user.role_user == "Resident"

class OwnerAuthenticated(permissions.IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view) and request.user == obj.resident

