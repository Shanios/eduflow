from rest_framework import viewsets, permissions
from rest_framework.exceptions import ValidationError
from accounts.permissions import IsStudent
from courses.models import Course
from .models import Enrollment
from .serializers import EnrollmentSerializer


class EnrollmentViewSet(viewsets.ModelViewSet):
    serializer_class = EnrollmentSerializer
    permission_classes = [permissions.IsAuthenticated, IsStudent]
    http_method_names = ['get', 'post', 'delete', 'head', 'options']

    def get_queryset(self):
        return Enrollment.objects.filter(student=self.request.user).select_related('course')

    def perform_create(self, serializer):
        course = serializer.validated_data['course']
        if course.status != Course.Status.PUBLISHED:
            raise ValidationError("Cannot enroll in an unpublished course.")
        if Enrollment.objects.filter(student=self.request.user, course=course).exists():
            raise ValidationError("Already enrolled in this course.")
        serializer.save(student=self.request.user)
