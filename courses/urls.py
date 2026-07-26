from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, CourseViewSet, SectionViewSet, LessonViewSet

router = DefaultRouter()
router.register('categories', CategoryViewSet)
router.register('courses', CourseViewSet, basename='course')
router.register('sections', SectionViewSet)
router.register('lessons', LessonViewSet)

urlpatterns = router.urls
