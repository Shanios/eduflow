# EduFlow — LMS Backend (Django + DRF)

A role-based Learning Management System backend built with Django REST Framework and JWT auth.

## What's actually built and tested (as of this commit)

- **Custom user model** with `ADMIN` / `TEACHER` / `STUDENT` roles, plus separate
  `TeacherProfile` / `StudentProfile` models.
- **JWT auth**: register, login, token refresh, `/me` profile endpoint.
- **Role-based permissions**: only teachers can create courses/sections/lessons and
  only for courses they own; only admins manage categories; students are read-only
  on course content.
- **Course catalog**: categories, courses (with difficulty/price/language/status),
  sections, lessons.
- **Enrollment-gated content**: non-enrolled students see locked lesson previews
  (title/duration only, or full content if `preview_available=True`); enrolled
  students see full lesson content (video URL, notes, PDF). This was verified with
  an end-to-end test: same course, same lesson, different response before vs. after
  enrollment.
- **Filtering & search** on courses (category, difficulty, language, status, text search).
- Django admin wired up for all models.

All of the above was migrated and smoke-tested against a live SQLite DB
(register → login → create course as teacher → attempt as student, correctly
rejected → enroll → content unlocks). It's not just written, it runs.

## Explicitly NOT built yet (do not claim these in an interview)

These are in the original spec but out of scope for this pass — don't represent
them as done:

- Assignments (submission + grading)
- Quizzes
- Progress tracking / certificates
- Reviews, wishlist, notifications
- Payments (Stripe/Razorpay)
- Celery/Redis background tasks (email reminders)
- Cloud file storage (S3/Cloudinary) — currently local `MEDIA_ROOT`
- Analytics/reporting dashboards
- API docs (drf-spectacular)
- Automated test suite (the verification above was manual/interactive, not
  committed as `pytest`/`unittest` files — if you have any time left, this is the
  single highest-value thing to add before an interview, since "I tested it
  manually" is a weaker claim than "here's the test suite")

If asked in an interview what's next, this list is your honest answer.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

python manage.py migrate
python manage.py seed_demo       # populates demo accounts + sample courses (safe to re-run)
python manage.py runserver
```

`seed_demo` creates:
- Superuser `admin` / `admin12345` (for `/admin/`)
- Teacher `demo_teacher` / `demo12345` — owns 3 sample courses (2 published, 1 draft)
- Student `demo_student` / `demo12345` — already enrolled in one course at 35% progress
- Categories, sections, lessons with a mix of locked/free-preview content, so you
  can immediately see the enrollment-gating behavior without manually creating anything

If you don't want the demo data, just skip that command — an empty DB works fine too.

## Dashboard (Streamlit)

A role-aware dashboard on top of the API — teachers manage courses/content/roster,
students browse, enroll, and track progress. It's a thin client: all state lives in
the Django API, the dashboard just calls it with `requests`.

**Run both (two terminals):**

```bash
# Terminal 1 — API
python manage.py runserver

# Terminal 2 — dashboard
streamlit run dashboard/app.py
```

Then open the Streamlit URL it prints (usually http://localhost:8501). The sidebar
lets you point it at a different API base URL if needed.

**What it does:**
- Login/register (calls `/api/auth/login/` and `/api/auth/register/`, stores JWT
  in `st.session_state`)
- **Teacher**: overview metrics + enrollment-by-course chart (Plotly), per-course
  roster table, inline forms to add sections/lessons, a "New Course" form
- **Student**: enrolled courses with progress bars and a lesson viewer that
  respects the same locked/unlocked logic as the API (🔒 vs ▶️), a browse/search
  tab with one-click enroll

**What it doesn't do** (be honest about this in an interview): no grading UI (no
assignments module yet), progress bars reflect `progress_percentage` but nothing
currently updates that field automatically (there's no lesson-completion tracking
wired up) — it's there as a schema field, ready for that logic, not a finished
feature. Say that plainly if asked.

Tested by running the Django server and the dashboard's `api_client.py` against
it directly (register → login → create category as admin → create course →
add section/lesson → browse/search as student → enroll → verify roster and
lesson-lock state) — every call in the dashboard has been exercised against a
live server, and the Streamlit app was booted headlessly to confirm it starts
without import/runtime errors. It has not been clicked through in an actual
browser session, so give the UI a once-over yourself before demoing it live.

## API overview

| Endpoint | Method | Who |
|---|---|---|
| `/api/auth/register/` | POST | anyone |
| `/api/auth/login/` | POST | anyone |
| `/api/auth/login/refresh/` | POST | anyone (with refresh token) |
| `/api/auth/me/` | GET/PATCH | authenticated |
| `/api/categories/` | GET | anyone; POST/PUT/DELETE admin only |
| `/api/courses/` | GET | anyone (published only, unless owner/teacher); POST teacher only |
| `/api/courses/{id}/` | GET | anyone — response shape changes based on enrollment |
| `/api/sections/` | POST/PUT/DELETE | course owner (teacher) only |
| `/api/lessons/` | POST/PUT/DELETE | course owner (teacher) only |
| `/api/enrollments/` | GET/POST | student only, scoped to own enrollments |

## Project layout

```
config/          settings, root urls
accounts/        custom User, TeacherProfile, StudentProfile, JWT auth endpoints
courses/         Category, Course, Section, Lesson + enrollment-aware serializers
enrollments/     Enrollment model + student-facing viewset
```
