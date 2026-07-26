# 🎓 EduFlow

A role-based Learning Management System — Django REST Framework API + a Streamlit dashboard on top of it. Teachers create and manage courses, students browse, enroll, and learn. Lesson content is gated by enrollment, not just by the UI.

![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![Django](https://img.shields.io/badge/Django-4.2-092E20?logo=django)
![DRF](https://img.shields.io/badge/DRF-3.15-red)
![Streamlit](https://img.shields.io/badge/Streamlit-dashboard-FF4B4B?logo=streamlit)

---

## Contents

- [Features](#features)
- [Tech stack](#tech-stack)
- [Quickstart](#quickstart)
- [Demo accounts](#demo-accounts)
- [Dashboard](#dashboard-streamlit)
- [API reference](#api-reference)
- [Project structure](#project-structure)
- [Roadmap](#roadmap)

---

## Features

- **Role-based accounts** — `ADMIN` / `TEACHER` / `STUDENT`, with separate teacher and student profile models
- **JWT authentication** — register, login, token refresh, `/me` profile endpoint
- **Course catalog** — categories, courses, sections, lessons, with filtering and search (category, difficulty, language, status, free-text)
- **Ownership-enforced permissions** — teachers can only edit their own courses/sections/lessons; only admins manage categories; students are read-only on content
- **Enrollment-gated lessons** — a lesson marked `preview_available=False` is locked (title/duration only) until the student enrolls, then unlocks fully. This is enforced server-side, verified end-to-end, not just hidden in the UI
- **Streamlit dashboard** — a full front end on top of the API: teachers manage courses/content/roster, students browse and enroll, with live publish/unpublish and lesson-lock toggles
- **One-command demo data** — `python manage.py seed_demo` populates realistic sample accounts, courses, and content

## Tech stack

| Layer | Tech |
|---|---|
| API | Django 4.2, Django REST Framework |
| Auth | `djangorestframework-simplejwt` (JWT) |
| Filtering | `django-filter` |
| Database | SQLite (dev) — swap `DATABASES` in `settings.py` for Postgres in production |
| Dashboard | Streamlit, Plotly, pandas, `requests` |

## Quickstart

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt

python manage.py migrate
python manage.py seed_demo       # optional but recommended — see below
python manage.py runserver
```

The API is now live at `http://127.0.0.1:8000/`. Try `http://127.0.0.1:8000/api/categories/` in a browser — DRF's browsable API will render the response.

### Environment variables (optional)

The app runs out of the box with safe local-dev defaults. For anything beyond local use, set:

```bash
export DJANGO_SECRET_KEY="your-own-secret-key"
export DJANGO_DEBUG="False"
export DJANGO_ALLOWED_HOSTS="yourdomain.com"
```

## Demo accounts

Running `python manage.py seed_demo` creates (idempotent — safe to re-run):

| Role | Username | Password | Notes |
|---|---|---|---|
| Admin | `admin` | `admin12345` | Django admin at `/admin/` |
| Teacher | `demo_teacher` | `demo12345` | Owns 3 sample courses (2 published, 1 draft) |
| Student | `demo_student` | `demo12345` | Already enrolled in one course at 35% progress |

## Dashboard (Streamlit)

A thin client on top of the API — all state lives in Django, the dashboard just calls it over HTTP.

```bash
# Terminal 1
python manage.py runserver

# Terminal 2
streamlit run dashboard/app.py
```

Open the URL Streamlit prints (usually `http://localhost:8501`).

**Teacher view**
- Overview metrics + enrollment-by-course chart
- Per-course roster table
- One-click publish/unpublish
- Editable course details (title, price, difficulty, duration)
- Add sections/lessons, with a lock/unlock toggle per lesson
- New-course form

**Student view**
- Enrolled courses with progress bars
- Lesson viewer that respects the same lock/unlock state as the API (🔒 vs ▶️)
- Browse/search catalog with one-click enroll

## API reference

| Endpoint | Method | Access |
|---|---|---|
| `/api/auth/register/` | POST | anyone |
| `/api/auth/login/` | POST | anyone |
| `/api/auth/login/refresh/` | POST | anyone (with refresh token) |
| `/api/auth/me/` | GET / PATCH | authenticated |
| `/api/categories/` | GET | anyone · POST/PUT/DELETE admin only |
| `/api/courses/` | GET | anyone (published only, unless owner) · POST teacher only |
| `/api/courses/{id}/` | GET / PATCH | anyone to view · owner-teacher to edit — response shape changes based on enrollment |
| `/api/courses/{id}/roster/` | GET | course owner (teacher) only |
| `/api/sections/` | POST / PUT / DELETE | course owner (teacher) only |
| `/api/lessons/` | POST / PUT / DELETE | course owner (teacher) only |
| `/api/enrollments/` | GET / POST | student only, scoped to own enrollments |

## Project structure

```
config/          settings, root URLs
accounts/        custom User, TeacherProfile, StudentProfile, JWT auth endpoints
courses/         Category, Course, Section, Lesson + enrollment-aware serializers
                 courses/management/commands/seed_demo.py — demo data seeder
enrollments/     Enrollment model + student-facing viewset
dashboard/       Streamlit app (app.py, api_client.py, teacher_view.py, student_view.py)
```

## Roadmap

Not built yet — tracked here rather than left ambiguous:

- Assignments (submission + grading)
- Quizzes
- Automated lesson-completion → progress tracking, and certificates
- Reviews, wishlist, notifications
- Payments (Stripe/Razorpay)
- Background tasks (Celery/Redis) for reminder emails
- Cloud file storage (S3/Cloudinary) — currently local `MEDIA_ROOT`
- Analytics/reporting dashboards
- OpenAPI/Swagger docs (`drf-spectacular`)
- Automated test suite (`pytest`) — currently verified via manual/scripted smoke tests, not committed test files

---

Built as a portfolio project to demonstrate role-based auth, REST API design, and a full-stack thin-client dashboard on top of it.
