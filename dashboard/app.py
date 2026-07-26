"""
EduFlow Dashboard — Streamlit frontend for the Django/DRF EduFlow API.

Run:
    streamlit run dashboard/app.py

Assumes the Django API is running at API_BASE (default http://127.0.0.1:8000).
"""
import streamlit as st
from api_client import ApiClient, ApiError
import teacher_view
import student_view

st.set_page_config(page_title="EduFlow Dashboard", page_icon="🎓", layout="wide")

if "access_token" not in st.session_state:
    st.session_state.access_token = None
    st.session_state.refresh_token = None
    st.session_state.user = None

with st.sidebar:
    st.title("🎓 EduFlow")
    api_base = st.text_input("API base URL", value="http://127.0.0.1:8000", key="api_base")

client = ApiClient(base_url=st.session_state.api_base)


def do_logout():
    st.session_state.access_token = None
    st.session_state.refresh_token = None
    st.session_state.user = None


def login_form():
    st.subheader("Log in")
    tab_login, tab_register = st.tabs(["Log in", "Register"])

    with tab_login:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Log in", use_container_width=True)
        if submitted:
            try:
                tokens = client.login(username, password)
                st.session_state.access_token = tokens["access"]
                st.session_state.refresh_token = tokens["refresh"]
                client.token = tokens["access"]
                st.session_state.user = client.me()
                st.rerun()
            except ApiError as e:
                st.error(f"Login failed: {e}")

    with tab_register:
        with st.form("register_form"):
            r_username = st.text_input("Username", key="r_username")
            r_email = st.text_input("Email", key="r_email")
            r_password = st.text_input("Password", type="password", key="r_password")
            r_role = st.selectbox("Role", ["STUDENT", "TEACHER"], key="r_role")
            r_submitted = st.form_submit_button("Create account", use_container_width=True)
        if r_submitted:
            try:
                client.register(r_username, r_email, r_password, r_role)
                st.success("Account created — switch to the Log in tab.")
            except ApiError as e:
                st.error(f"Registration failed: {e}")


if not st.session_state.access_token:
    st.title("Welcome to EduFlow")
    st.caption("Log in as a teacher to manage courses, or as a student to browse and enroll.")
    login_form()
else:
    client.token = st.session_state.access_token
    user = st.session_state.user

    with st.sidebar:
        st.markdown(f"**{user['username']}**")
        st.caption(f"Role: {user['role']}")
        if st.button("Log out", use_container_width=True):
            do_logout()
            st.rerun()

    st.title(f"Welcome, {user['username']} 👋")

    if user["role"] == "TEACHER":
        teacher_view.render(client)
    elif user["role"] == "STUDENT":
        student_view.render(client)
    else:
        st.info("Admin accounts should use the Django admin site (/admin/) for now.")
