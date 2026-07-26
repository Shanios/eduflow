"""
Seed EduFlow with demo data: categories, teacher/student accounts, courses,
sections, lessons, and an enrollment or two — so the dashboard has something
to show immediately.

Usage:
    python manage.py seed_demo

Safe to run more than once (uses get_or_create throughout).
"""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import TeacherProfile, StudentProfile
from courses.models import Category, Course, Section, Lesson
from enrollments.models import Enrollment

User = get_user_model()


class Command(BaseCommand):
    help = "Seed demo data for the EduFlow dashboard"

    @transaction.atomic
    def handle(self, *args, **options):
        # --- Admin (for /admin/) ---
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser("admin", "admin@eduflow.local", "admin12345")
            self.stdout.write(self.style.SUCCESS("Created superuser: admin / admin12345"))
        else:
            self.stdout.write("Superuser 'admin' already exists.")

        # --- Teacher ---
        teacher, created = User.objects.get_or_create(
            username="demo_teacher",
            defaults=dict(email="teacher@eduflow.local", role=User.Role.TEACHER),
        )
        if created:
            teacher.set_password("demo12345")
            teacher.save()
            TeacherProfile.objects.get_or_create(user=teacher)
        self.stdout.write(self.style.SUCCESS(
            f"Teacher account: demo_teacher / demo12345 {'(created)' if created else '(already existed)'}"
        ))

        # --- Student ---
        student, created = User.objects.get_or_create(
            username="demo_student",
            defaults=dict(email="student@eduflow.local", role=User.Role.STUDENT),
        )
        if created:
            student.set_password("demo12345")
            student.save()
            StudentProfile.objects.get_or_create(user=student)
        self.stdout.write(self.style.SUCCESS(
            f"Student account: demo_student / demo12345 {'(created)' if created else '(already existed)'}"
        ))

        # --- Categories ---
        category_names = ["Programming", "Data Science", "Web Development"]
        categories = {}
        for name in category_names:
            cat, _ = Category.objects.get_or_create(name=name, defaults={"slug": name.lower().replace(" ", "-")})
            categories[name] = cat

        # --- Courses ---
        courses_data = [
            {
                "title": "Python for Beginners",
                "slug": "python-for-beginners",
                "category": categories["Programming"],
                "description": "A friendly introduction to Python syntax, data types, and control flow.",
                "price": 0,
                "difficulty": Course.Difficulty.BEGINNER,
                "duration_hours": 12,
                "status": Course.Status.PUBLISHED,
                "sections": [
                    {
                        "title": "Getting Started",
                        "lessons": [
                            {"title": "Installing Python", "video_url": "https://example.com/py-install",
                             "duration_minutes": 8, "preview_available": True},
                            {"title": "Your First Script", "video_url": "https://example.com/py-first-script",
                             "duration_minutes": 12, "preview_available": False},
                        ],
                    },
                    {
                        "title": "Core Syntax",
                        "lessons": [
                            {"title": "Variables and Types", "video_url": "https://example.com/py-vars",
                             "duration_minutes": 15, "preview_available": False},
                            {"title": "Control Flow", "video_url": "https://example.com/py-control-flow",
                             "duration_minutes": 18, "preview_available": False},
                        ],
                    },
                ],
            },
            {
                "title": "Django REST Framework Crash Course",
                "slug": "drf-crash-course",
                "category": categories["Web Development"],
                "description": "Build a JWT-authenticated REST API with Django and DRF.",
                "price": 499,
                "difficulty": Course.Difficulty.INTERMEDIATE,
                "duration_hours": 8,
                "status": Course.Status.PUBLISHED,
                "sections": [
                    {
                        "title": "Foundations",
                        "lessons": [
                            {"title": "Serializers 101", "video_url": "https://example.com/drf-serializers",
                             "duration_minutes": 14, "preview_available": True},
                            {"title": "ViewSets and Routers", "video_url": "https://example.com/drf-viewsets",
                             "duration_minutes": 20, "preview_available": False},
                        ],
                    },
                ],
            },
            {
                "title": "Intro to Data Analysis with Pandas",
                "slug": "pandas-intro",
                "category": categories["Data Science"],
                "description": "Load, clean, and analyze tabular data using pandas.",
                "price": 299,
                "difficulty": Course.Difficulty.BEGINNER,
                "duration_hours": 6,
                "status": Course.Status.DRAFT,  # deliberately unpublished, to demo draft vs published
                "sections": [
                    {
                        "title": "Pandas Basics",
                        "lessons": [
                            {"title": "DataFrames and Series", "video_url": "https://example.com/pandas-df",
                             "duration_minutes": 10, "preview_available": True},
                        ],
                    },
                ],
            },
        ]

        created_courses = []
        for c in courses_data:
            sections_data = c.pop("sections")
            course, created = Course.objects.get_or_create(
                slug=c["slug"],
                defaults={**c, "teacher": teacher},
            )
            created_courses.append(course)
            if created:
                for order, sec in enumerate(sections_data, start=1):
                    section, _ = Section.objects.get_or_create(
                        course=course, title=sec["title"], defaults={"order": order}
                    )
                    for l_order, lesson in enumerate(sec["lessons"], start=1):
                        Lesson.objects.get_or_create(
                            section=section, title=lesson["title"],
                            defaults={**lesson, "order": l_order},
                        )
                self.stdout.write(self.style.SUCCESS(f"Created course: {course.title}"))
            else:
                self.stdout.write(f"Course already existed: {course.title}")

        # --- Enroll the demo student in the first published course ---
        published = [c for c in created_courses if c.status == Course.Status.PUBLISHED]
        if published:
            target = published[0]
            enrollment, created = Enrollment.objects.get_or_create(
                student=student, course=target,
                defaults={"progress_percentage": 35},
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Enrolled demo_student in: {target.title} (35% progress)"))
            else:
                self.stdout.write(f"demo_student already enrolled in: {target.title}")

        self.stdout.write(self.style.SUCCESS(
            "\nSeed complete. Log into the dashboard with:\n"
            "  Teacher -> demo_teacher / demo12345\n"
            "  Student -> demo_student / demo12345\n"
            "  Django admin -> admin / admin12345 (at /admin/)"
        ))
