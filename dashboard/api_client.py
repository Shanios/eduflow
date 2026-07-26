import requests


class ApiError(Exception):
    pass


class ApiClient:
    def __init__(self, base_url, token=None):
        self.base_url = base_url.rstrip("/")
        self.token = token

    def _headers(self):
        h = {}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    def _request(self, method, path, **kwargs):
        url = f"{self.base_url}{path}"
        try:
            resp = requests.request(method, url, headers=self._headers(), timeout=10, **kwargs)
        except requests.exceptions.ConnectionError:
            raise ApiError(f"Could not connect to API at {self.base_url}. Is the Django server running?")
        if resp.status_code >= 400:
            try:
                detail = resp.json()
            except ValueError:
                detail = resp.text
            raise ApiError(f"{resp.status_code}: {detail}")
        if resp.status_code == 204 or not resp.content:
            return None
        return resp.json()

    # --- auth ---
    def login(self, username, password):
        return self._request("POST", "/api/auth/login/", json={"username": username, "password": password})

    def register(self, username, email, password, role):
        return self._request("POST", "/api/auth/register/", json={
            "username": username, "email": email, "password": password, "role": role,
        })

    def me(self):
        return self._request("GET", "/api/auth/me/")

    # --- categories ---
    def list_categories(self):
        return self._request("GET", "/api/categories/")

    # --- courses ---
    def list_courses(self, mine=False, search=None, category=None, difficulty=None):
        params = {}
        if mine:
            params["mine"] = "true"
        if search:
            params["search"] = search
        if category:
            params["category"] = category
        if difficulty:
            params["difficulty"] = difficulty
        return self._request("GET", "/api/courses/", params=params)

    def get_course(self, course_id):
        return self._request("GET", f"/api/courses/{course_id}/")

    def create_course(self, **fields):
        return self._request("POST", "/api/courses/", json=fields)

    def update_course(self, course_id, **fields):
        return self._request("PATCH", f"/api/courses/{course_id}/", json=fields)

    def get_roster(self, course_id):
        return self._request("GET", f"/api/courses/{course_id}/roster/")

    # --- sections & lessons ---
    def create_section(self, course_id, title, order=1):
        return self._request("POST", "/api/sections/", json={"course": course_id, "title": title, "order": order})

    def create_lesson(self, section_id, title, **fields):
        payload = {"section": section_id, "title": title, **fields}
        return self._request("POST", "/api/lessons/", json=payload)

    def update_lesson(self, lesson_id, **fields):
        return self._request("PATCH", f"/api/lessons/{lesson_id}/", json=fields)

    # --- enrollments ---
    def my_enrollments(self):
        return self._request("GET", "/api/enrollments/")

    def enroll(self, course_id):
        return self._request("POST", "/api/enrollments/", json={"course": course_id})
