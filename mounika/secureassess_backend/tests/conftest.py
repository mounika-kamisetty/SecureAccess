"""
SecureAssess — Pytest Configuration & Fixtures.

Provides a test client backed by a temporary MongoDB database
that is dropped after each test session.
"""

# pyrefly: ignore [missing-import]
import pytest

from app import create_app
from app.config import TestingConfig
from app.extensions.mongo import mongo


@pytest.fixture(scope="session")
def app():
    """Create the Flask app with TestingConfig."""
    application = create_app(config_class=TestingConfig)
    yield application

    # Cleanup: drop the test database
    mongo.client.drop_database(TestingConfig.MONGO_DB_NAME)


@pytest.fixture(scope="function")
def client(app):
    """
    Per-test client with a clean database.

    Every test function starts with empty collections.
    """
    # Clear all collections before each test
    for name in mongo.db.list_collection_names():
        mongo.db[name].delete_many({})

    with app.test_client() as c:
        yield c


# ------------------------------------------------------------------
# Auth helper fixtures
# ------------------------------------------------------------------

def _register(client, name, email, password, role="student"):
    return client.post("/api/v1/auth/register", json={
        "name": name,
        "email": email,
        "password": password,
        "role": role,
    })


def _login(client, email, password):
    return client.post("/api/v1/auth/login", json={
        "email": email,
        "password": password,
    })


def _auth_header(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def student_token(client):
    """Register a student and return their access token."""
    _register(client, "Test Student", "student@test.com", "Pass@1234", "student")
    resp = _login(client, "student@test.com", "Pass@1234")
    return resp.get_json()["data"]["access_token"]


@pytest.fixture
def examiner_token(client):
    """Register an examiner and return their access token."""
    _register(client, "Test Examiner", "examiner@test.com", "Pass@1234", "examiner")
    resp = _login(client, "examiner@test.com", "Pass@1234")
    return resp.get_json()["data"]["access_token"]


@pytest.fixture
def admin_token(client):
    """Register an admin and return their access token."""
    _register(client, "Test Admin", "admin@test.com", "Pass@1234", "admin")
    resp = _login(client, "admin@test.com", "Pass@1234")
    return resp.get_json()["data"]["access_token"]


@pytest.fixture
def sample_exam_data():
    """Return valid exam creation payload."""
    return {
        "title": "Python Fundamentals",
        "description": "Test your Python knowledge",
        "duration": 30,
        "questions": [
            {
                "text": "What is the output of print(2 ** 3)?",
                "type": "mcq",
                "options": ["6", "8", "9", "12"],
                "marks": 5,
                "correct_answer": "8",
            },
            {
                "text": "Python is a compiled language.",
                "type": "true_false",
                "options": ["True", "False"],
                "marks": 5,
                "correct_answer": "False",
            },
            {
                "text": "Which is a mutable type?",
                "type": "mcq",
                "options": ["tuple", "str", "list", "int"],
                "marks": 5,
                "correct_answer": "list",
            },
            {
                "text": "What keyword defines a function?",
                "type": "mcq",
                "options": ["func", "def", "function", "define"],
                "marks": 5,
                "correct_answer": "def",
            },
            {
                "text": "len('hello') returns 5.",
                "type": "true_false",
                "options": ["True", "False"],
                "marks": 5,
                "correct_answer": "True",
            },
        ],
    }
