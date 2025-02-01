from rest_framework import permissions

class IsDoctor(permissions.BasePermission):
    """
    Custom permission to only allow doctors to access the view.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_doctor()

class IsPatient(permissions.BasePermission):
    """
    Custom permission to only allow patients to access the view.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_patient()

class IsDoctorOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow doctors to create/edit objects.
    Patients can only read.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated and request.user.is_doctor()

class IsOwnerOrDoctor(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object or doctors to access it.
    """
    def has_object_permission(self, request, view, obj):
        # Doctors can access any object
        if request.user.is_doctor():
            return True
            
        # Check if the object has a patient or user field
        if hasattr(obj, 'patient'):
            return obj.patient == request.user
        elif hasattr(obj, 'user'):
            return obj.user == request.user
            
        return False 