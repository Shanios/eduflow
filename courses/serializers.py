from rest_framework import serializers
from .models import Category, Course, Section, Lesson


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = '__all__'
        read_only_fields = ('id',)


class LessonPreviewSerializer(serializers.ModelSerializer):
    """Used for non-enrolled students: locks content, shows metadata only."""
    locked = serializers.SerializerMethodField()
    video_url = serializers.SerializerMethodField()
    notes = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = ('id', 'title', 'description', 'duration_minutes', 'order',
                  'preview_available', 'locked', 'video_url', 'notes')

    def get_locked(self, obj):
        return not obj.preview_available

    def get_video_url(self, obj):
        return obj.video_url if obj.preview_available else None

    def get_notes(self, obj):
        return obj.notes if obj.preview_available else None


class SectionSerializer(serializers.ModelSerializer):
    lessons = serializers.SerializerMethodField()

    class Meta:
        model = Section
        fields = ('id', 'course', 'title', 'order', 'lessons')

    def get_lessons(self, obj):
        request = self.context.get('request')
        enrolled = self.context.get('is_enrolled', False)
        is_owner = self.context.get('is_owner', False)
        if enrolled or is_owner:
            return LessonSerializer(obj.lessons.all(), many=True).data
        return LessonPreviewSerializer(obj.lessons.all(), many=True).data


class CourseListSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source='teacher.username', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Course
        fields = ('id', 'title', 'slug', 'teacher', 'teacher_name', 'category', 'category_name',
                  'thumbnail', 'price', 'difficulty', 'language', 'duration_hours', 'status')


class CourseDetailSerializer(serializers.ModelSerializer):
    sections = serializers.SerializerMethodField()
    teacher_name = serializers.CharField(source='teacher.username', read_only=True)

    class Meta:
        model = Course
        fields = ('id', 'title', 'slug', 'teacher', 'teacher_name', 'category', 'description',
                  'thumbnail', 'price', 'difficulty', 'language', 'duration_hours', 'requirements',
                  'objectives', 'status', 'created_at', 'sections')
        read_only_fields = ('teacher',)

    def get_sections(self, obj):
        request = self.context.get('request')
        context = dict(self.context)
        return SectionSerializer(obj.sections.all(), many=True, context=context).data
