import streamlit as st
from api_client import ApiError


def render(client):
    tab_mine, tab_browse = st.tabs(["🎒 My Courses", "🔍 Browse Courses"])

    with tab_mine:
        render_my_enrollments(client)

    with tab_browse:
        render_browse(client)


def render_my_enrollments(client):
    try:
        enrollments = client.my_enrollments()
    except ApiError as e:
        st.error(str(e))
        return

    if not enrollments:
        st.info("You're not enrolled in anything yet — check the 'Browse Courses' tab.")
        return

    for e in enrollments:
        st.markdown(f"**{e['course_title']}**  ·  {e['status']}")
        st.progress(min(e["progress_percentage"], 100) / 100, text=f"{e['progress_percentage']}% complete")
        with st.expander("View lessons"):
            render_course_content(client, e["course"])
        st.divider()


def render_browse(client):
    col1, col2 = st.columns([3, 1])
    with col1:
        search = st.text_input("Search courses", placeholder="e.g. python")
    with col2:
        difficulty = st.selectbox("Difficulty", ["Any", "BEGINNER", "INTERMEDIATE", "ADVANCED"])

    try:
        courses = client.list_courses(
            search=search or None,
            difficulty=None if difficulty == "Any" else difficulty,
        )
    except ApiError as e:
        st.error(str(e))
        return

    if not courses:
        st.info("No courses found.")
        return

    already_enrolled = set()
    try:
        already_enrolled = {e["course"] for e in client.my_enrollments()}
    except ApiError:
        pass

    for c in courses:
        with st.container(border=True):
            col_a, col_b = st.columns([4, 1])
            with col_a:
                st.markdown(f"**{c['title']}**")
                st.caption(
                    f"{c.get('category_name') or 'Uncategorized'} · {c['difficulty']} · "
                    f"{c['duration_hours']}h · by {c['teacher_name']} · ₹{c['price']}"
                )
            with col_b:
                if c["id"] in already_enrolled:
                    st.success("Enrolled")
                else:
                    if st.button("Enroll", key=f"enroll_{c['id']}", use_container_width=True):
                        try:
                            client.enroll(c["id"])
                            st.success("Enrolled!")
                            st.rerun()
                        except ApiError as e:
                            st.error(str(e))
            with st.expander("Preview content"):
                render_course_content(client, c["id"])


def render_course_content(client, course_id):
    try:
        detail = client.get_course(course_id)
    except ApiError as e:
        st.error(str(e))
        return

    sections = detail.get("sections", [])
    if not sections:
        st.caption("No content added yet.")
        return

    for s in sections:
        st.markdown(f"**{s['title']}**")
        for lesson in s.get("lessons", []):
            locked = lesson.get("locked", False)
            icon = "🔒" if locked else "▶️"
            duration = lesson.get("duration_minutes", 0)
            st.write(f"{icon} {lesson['title']} ({duration} min)")
            if not locked and lesson.get("video_url"):
                st.caption(f"Video: {lesson['video_url']}")
            if not locked and lesson.get("notes"):
                st.caption(f"Notes: {lesson['notes']}")
