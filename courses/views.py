from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django_filters.rest_framework import DjangoFilterBackend
from accounts.permissions import IsTeacher, IsOwnerTeacherOrReadOnly
from .models import Category, Course, Section, Lesson
from .serializers import (
    CategorySerializer, CourseListSerializer, CourseDetailSerializer,
    SectionSerializer, LessonSerializer,
)


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]


class CourseViewSet(viewsets.ModelViewSet):
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['category', 'difficulty', 'language', 'status']
    search_fields = ['title', 'description']

    def get_queryset(self):
        qs = Course.objects.select_related('teacher', 'category')
        user = self.request.user
        if self.request.query_params.get('mine') == 'true' and user.is_authenticated:
            return qs.filter(teacher=user)
        if user.is_authenticated and getattr(user, 'is_teacher', False):
            # Teachers see their own courses (any status) + everyone else's published ones
            from django.db.models import Q
            return qs.filter(Q(status=Course.Status.PUBLISHED) | Q(teacher=user))
        return qs.filter(status=Course.Status.PUBLISHED)

    def get_serializer_class(self):
        if self.action == 'list':
            return CourseListSerializer
        return CourseDetailSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        obj = getattr(self, '_current_obj', None)
        user = self.request.user
        if obj is not None and user.is_authenticated:
            context['is_owner'] = (obj.teacher_id == user.id)
            if getattr(user, 'is_student', False):
                from enrollments.models import Enrollment
                context['is_enrolled'] = Enrollment.objects.filter(
                    student=user, course=obj, status=Enrollment.Status.ACTIVE
                ).exists()
        return context

    def retrieve(self, request, *args, **kwargs):
        self._current_obj = self.get_object()
        return super().retrieve(request, *args, **kwargs)

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [permissions.AllowAny()]
        if self.action == 'create':
            return [permissions.IsAuthenticated(), IsTeacher()]
        return [permissions.IsAuthenticated(), IsTeacher(), IsOwnerTeacherOrReadOnly()]

    def perform_create(self, serializer):
        serializer.save(teacher=self.request.user)

    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated, IsTeacher])
    def roster(self, request, pk=None):
        course = self.get_object()
        if course.teacher_id != request.user.id:
            raise PermissionDenied("You can only view the roster for your own courses.")
        from enrollments.models import Enrollment
        enrollments = Enrollment.objects.filter(course=course).select_related('student')
        data = [
            {
                'student_id': e.student_id,
                'username': e.student.username,
                'email': e.student.email,
                'status': e.status,
                'progress_percentage': e.progress_percentage,
                'enrolled_at': e.enrolled_at,
            }
            for e in enrollments
        ]
        return Response(data)


class SectionViewSet(viewsets.ModelViewSet):
    serializer_class = SectionSerializer
    queryset = Section.objects.all()

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated(), IsTeacher()]

    def perform_create(self, serializer):
        course = serializer.validated_data['course']
        if course.teacher_id != self.request.user.id:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You can only add sections to your own courses.")
        serializer.save()


class LessonViewSet(viewsets.ModelViewSet):
    serializer_class = LessonSerializer
    queryset = Lesson.objects.all()

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated(), IsTeacher()]

    def perform_create(self, serializer):
        section = serializer.validated_data['section']
        if section.course.teacher_id != self.request.user.id:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You can only add lessons to your own courses.")
        serializer.save()
