from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsTeacher(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_teacher)


class IsStudent(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_student)


class IsOwnerTeacherOrReadOnly(BasePermission):
    """Object-level: only the teacher who owns a course can edit/delete it."""

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return getattr(obj, 'teacher_id', None) == request.user.id
