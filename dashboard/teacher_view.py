import streamlit as st
import pandas as pd
import plotly.express as px
from api_client import ApiError


def render(client):
    tab_overview, tab_courses, tab_create = st.tabs(["📊 Overview", "📚 My Courses", "➕ New Course"])

    try:
        my_courses = client.list_courses(mine=True)
    except ApiError as e:
        st.error(str(e))
        return

    with tab_overview:
        render_overview(client, my_courses)

    with tab_courses:
        render_my_courses(client, my_courses)

    with tab_create:
        render_create_course(client)


def render_overview(client, my_courses):
    if not my_courses:
        st.info("You haven't created any courses yet — head to the 'New Course' tab.")
        return

    col1, col2, col3 = st.columns(3)
    col1.metric("Your courses", len(my_courses))
    published = sum(1 for c in my_courses if c["status"] == "PUBLISHED")
    col2.metric("Published", published)

    total_students = 0
    rows = []
    for c in my_courses:
        try:
            roster = client.get_roster(c["id"])
        except ApiError:
            roster = []
        total_students += len(roster)
        rows.append({"Course": c["title"], "Enrolled students": len(roster)})

    col3.metric("Total enrolled students", total_students)

    if rows:
        df = pd.DataFrame(rows)
        fig = px.bar(df, x="Course", y="Enrolled students", title="Enrollment by course")
        st.plotly_chart(fig, use_container_width=True)


def render_my_courses(client, my_courses):
    if not my_courses:
        st.info("No courses yet.")
        return

    for c in my_courses:
        with st.expander(f"**{c['title']}**  ·  {c['status']}  ·  ₹{c['price']}"):
            st.write(f"Category: {c.get('category_name') or '—'}  |  Difficulty: {c['difficulty']}  |  "
                     f"Language: {c['language']}  |  Duration: {c['duration_hours']}h")

            # --- Quick publish/unpublish toggle ---
            col_pub, col_edit_toggle = st.columns([1, 3])
            with col_pub:
                if c["status"] == "PUBLISHED":
                    if st.button("⏸ Unpublish", key=f"unpub_{c['id']}", use_container_width=True):
                        try:
                            client.update_course(c["id"], status="DRAFT")
                            st.rerun()
                        except ApiError as e:
                            st.error(str(e))
                else:
                    if st.button("🚀 Publish", key=f"pub_{c['id']}", use_container_width=True):
                        try:
                            client.update_course(c["id"], status="PUBLISHED")
                            st.rerun()
                        except ApiError as e:
                            st.error(str(e))

            # --- Edit course details ---
            with st.expander("✏️ Edit course details"):
                with st.form(f"edit_course_form_{c['id']}"):
                    e_title = st.text_input("Title", value=c["title"], key=f"et_{c['id']}")
                    e_price = st.number_input("Price", min_value=0.0, value=float(c["price"]),
                                               step=100.0, key=f"ep_{c['id']}")
                    e_difficulty = st.selectbox(
                        "Difficulty", ["BEGINNER", "INTERMEDIATE", "ADVANCED"],
                        index=["BEGINNER", "INTERMEDIATE", "ADVANCED"].index(c["difficulty"]),
                        key=f"ed_{c['id']}",
                    )
                    e_duration = st.number_input("Duration (hours)", min_value=0,
                                                  value=c["duration_hours"], key=f"edur_{c['id']}")
                    e_submit = st.form_submit_button("Save changes")
                if e_submit:
                    try:
                        client.update_course(
                            c["id"], title=e_title, price=e_price,
                            difficulty=e_difficulty, duration_hours=e_duration,
                        )
                        st.success("Course updated.")
                        st.rerun()
                    except ApiError as ex:
                        st.error(str(ex))

            col_a, col_b = st.columns(2)

            with col_a:
                st.markdown("**Roster**")
                try:
                    roster = client.get_roster(c["id"])
                except ApiError as e:
                    st.error(str(e))
                    roster = []
                if roster:
                    df = pd.DataFrame(roster)[["username", "email", "status", "progress_percentage"]]
                    df.columns = ["Student", "Email", "Status", "Progress %"]
                    st.dataframe(df, use_container_width=True, hide_index=True)
                else:
                    st.caption("No students enrolled yet.")

                st.markdown("**Lessons**")
                detail = client.get_course(c["id"])
                any_lessons = False
                for s in detail.get("sections", []):
                    for lesson in s.get("lessons", []):
                        any_lessons = True
                        is_preview = lesson.get("preview_available", False)
                        lc1, lc2 = st.columns([4, 1])
                        lc1.write(f"{'🔓' if is_preview else '🔒'} {lesson['title']}  _(section: {s['title']})_")
                        toggle_label = "Lock" if is_preview else "Make free preview"
                        if lc2.button(toggle_label, key=f"tp_{lesson['id']}"):
                            try:
                                client.update_lesson(lesson["id"], preview_available=not is_preview)
                                st.rerun()
                            except ApiError as e:
                                st.error(str(e))
                if not any_lessons:
                    st.caption("No lessons yet.")

            with col_b:
                st.markdown("**Add a section**")
                with st.form(f"section_form_{c['id']}"):
                    section_title = st.text_input("Section title", key=f"sec_title_{c['id']}")
                    section_order = st.number_input("Order", min_value=1, value=1, key=f"sec_order_{c['id']}")
                    add_section = st.form_submit_button("Add section")
                if add_section and section_title:
                    try:
                        client.create_section(c["id"], section_title, section_order)
                        st.success("Section added.")
                        st.rerun()
                    except ApiError as e:
                        st.error(str(e))

                st.markdown("**Add a lesson**")
                with st.form(f"lesson_form_{c['id']}"):
                    detail = client.get_course(c["id"])
                    section_options = {s["title"]: s["id"] for s in detail.get("sections", [])}
                    if section_options:
                        sec_choice = st.selectbox("Section", list(section_options.keys()), key=f"lsec_{c['id']}")
                        lesson_title = st.text_input("Lesson title", key=f"lt_{c['id']}")
                        video_url = st.text_input("Video URL", key=f"lv_{c['id']}")
                        preview = st.checkbox("Free preview (visible before enrollment)", key=f"lp_{c['id']}")
                        add_lesson = st.form_submit_button("Add lesson")
                    else:
                        st.caption("Add a section first.")
                        add_lesson = False
                if section_options and add_lesson and lesson_title:
                    try:
                        client.create_lesson(
                            section_options[sec_choice], lesson_title,
                            video_url=video_url, preview_available=preview,
                        )
                        st.success("Lesson added.")
                        st.rerun()
                    except ApiError as e:
                        st.error(str(e))


def render_create_course(client):
    st.subheader("Create a new course")
    try:
        categories = client.list_categories()
    except ApiError as e:
        st.error(str(e))
        categories = []

    cat_options = {c["name"]: c["id"] for c in categories} if categories else {}

    with st.form("create_course_form"):
        title = st.text_input("Title")
        slug = st.text_input("Slug (unique, url-friendly)", help="e.g. python-for-beginners")
        description = st.text_area("Description")
        if cat_options:
            category_name = st.selectbox("Category", list(cat_options.keys()))
        else:
            st.caption("No categories yet — ask an admin to create one, or use Django admin.")
            category_name = None
        col1, col2, col3 = st.columns(3)
        with col1:
            price = st.number_input("Price", min_value=0.0, value=0.0, step=100.0)
        with col2:
            difficulty = st.selectbox("Difficulty", ["BEGINNER", "INTERMEDIATE", "ADVANCED"])
        with col3:
            duration_hours = st.number_input("Duration (hours)", min_value=0, value=0)
        status = st.selectbox("Status", ["PUBLISHED", "DRAFT"],
                               help="Published courses are visible to students immediately.")
        submitted = st.form_submit_button("Create course", use_container_width=True)

    if submitted:
        if not title or not slug:
            st.error("Title and slug are required.")
            return
        try:
            client.create_course(
                title=title, slug=slug, description=description,
                category=cat_options.get(category_name) if category_name else None,
                price=price, difficulty=difficulty, duration_hours=duration_hours, status=status,
            )
            st.success(f"Course '{title}' created.")
            st.rerun()
        except ApiError as e:
            st.error(str(e))
