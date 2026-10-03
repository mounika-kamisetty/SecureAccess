"""
SecureAssess — Seed Data Script.

Creates test users:
- Examiner
- Student
- Admin

Creates sample exams and publishes them.

Run with:
    py seed_data.py

Backend must be running on:
    http://localhost:5000
"""

import requests


# ============================================================
# CONFIGURATION
# ============================================================

BASE = "http://localhost:5000/api/v1"

TIMEOUT = 10


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def safe_json(response):
    """
    Safely convert an HTTP response to JSON.

    Prevents JSONDecodeError when the backend returns:
    - HTML
    - empty response
    - plain text
    - server error page
    """

    try:
        return response.json()

    except requests.exceptions.JSONDecodeError:
        print("\nERROR: Backend did not return JSON.")
        print(f"HTTP Status : {response.status_code}")
        print(f"URL         : {response.url}")
        print("Response:")
        print(response.text[:2000])
        print()

        return {}


def print_separator():
    print("=" * 60)


# ============================================================
# REGISTER USER
# ============================================================

def register(name, email, password, role):

    try:
        response = requests.post(
            f"{BASE}/auth/register",
            json={
                "name": name,
                "email": email,
                "password": password,
                "role": role
            },
            timeout=TIMEOUT
        )

    except requests.exceptions.ConnectionError:
        print("\nERROR: Cannot connect to backend.")
        print("Make sure the backend is running:")
        print("    py run.py")
        return None

    except requests.exceptions.Timeout:
        print("\nERROR: Backend request timed out.")
        return None

    except requests.exceptions.RequestException as error:
        print(f"\nERROR while registering {email}:")
        print(error)
        return None

    data = safe_json(response)

    message = data.get(
        "message",
        "No message returned by server."
    )

    print(
        f"Register {role} ({email}): "
        f"{response.status_code} - {message}"
    )

    return response


# ============================================================
# LOGIN USER
# ============================================================

def login(email, password):

    try:
        response = requests.post(
            f"{BASE}/auth/login",
            json={
                "email": email,
                "password": password
            },
            timeout=TIMEOUT
        )

    except requests.exceptions.ConnectionError:
        print("\nERROR: Cannot connect to backend.")
        print("Make sure the backend is running:")
        print("    py run.py")
        return None

    except requests.exceptions.Timeout:
        print("\nERROR: Login request timed out.")
        return None

    except requests.exceptions.RequestException as error:
        print("\nERROR during login:")
        print(error)
        return None

    data = safe_json(response)

    if data.get("success"):

        print(f"Login ({email}): OK")

        try:
            return data["data"]["access_token"]

        except (KeyError, TypeError):

            print(
                "ERROR: Login succeeded but "
                "access_token was not found."
            )

            print("Server response:")
            print(data)

            return None

    print(
        f"Login ({email}): FAILED - "
        f"{data.get('message', 'Unknown error')}"
    )

    return None


# ============================================================
# CREATE EXAM
# ============================================================

def create_exam(
    token,
    title,
    duration,
    description,
    questions
):

    try:

        response = requests.post(
            f"{BASE}/exams",

            json={
                "title": title,
                "duration": duration,
                "description": description,
                "questions": questions
            },

            headers={
                "Authorization": f"Bearer {token}"
            },

            timeout=TIMEOUT
        )

    except requests.exceptions.ConnectionError:
        print("\nERROR: Cannot connect to backend.")
        return None

    except requests.exceptions.Timeout:
        print("\nERROR: Create exam request timed out.")
        return None

    except requests.exceptions.RequestException as error:
        print("\nERROR while creating exam:")
        print(error)
        return None

    data = safe_json(response)

    if data.get("success"):

        try:

            exam_id = data["data"]["exam"]["id"]

            print(
                f"Create Exam '{title}': "
                f"OK (id={exam_id})"
            )

            return exam_id

        except (KeyError, TypeError):

            print(
                f"Create Exam '{title}': "
                "FAILED - exam ID not found."
            )

            print("Server response:")
            print(data)

            return None

    print(
        f"Create Exam '{title}': "
        f"FAILED - "
        f"{data.get('message', 'Unknown error')}"
    )

    return None


# ============================================================
# PUBLISH EXAM
# ============================================================

def publish_exam(token, exam_id):

    try:

        response = requests.patch(
            f"{BASE}/exams/{exam_id}/publish",

            headers={
                "Authorization": f"Bearer {token}"
            },

            timeout=TIMEOUT
        )

    except requests.exceptions.ConnectionError:
        print("\nERROR: Cannot connect to backend.")
        return None

    except requests.exceptions.Timeout:
        print("\nERROR: Publish request timed out.")
        return None

    except requests.exceptions.RequestException as error:
        print("\nERROR while publishing exam:")
        print(error)
        return None

    data = safe_json(response)

    print(
        f"Publish Exam: "
        f"{response.status_code} - "
        f"{data.get('message', 'No message')}"
    )

    return response


# ============================================================
# MAIN SEEDING PROCESS
# ============================================================

def main():

    print_separator()

    print("SecureAssess — Seeding Test Data")

    print_separator()

    # --------------------------------------------------------
    # 1. REGISTER USERS
    # --------------------------------------------------------

    print("\n--- Registering Users ---")

    register(
        "Test Examiner",
        "examiner@test.com",
        "Exam@1234",
        "examiner"
    )

    register(
        "Test Student",
        "student@test.com",
        "Stud@1234",
        "student"
    )

    register(
        "Admin User",
        "admin@test.com",
        "Admin@1234",
        "admin"
    )

    # --------------------------------------------------------
    # 2. LOGIN AS EXAMINER
    # --------------------------------------------------------

    print("\n--- Logging in as Examiner ---")

    examiner_token = login(
        "examiner@test.com",
        "Exam@1234"
    )

    if not examiner_token:

        print("\nCould not login as examiner.")
        print("Stopping exam creation.")

        print_separator()

        return

    # --------------------------------------------------------
    # 3. CREATE SAMPLE EXAMS
    # --------------------------------------------------------

    print("\n--- Creating Sample Exams ---")

    # ========================================================
    # EXAM 1
    # ========================================================

    exam1_id = create_exam(

        examiner_token,

        "Python Fundamentals Quiz",

        30,

        "Test your Python knowledge with this quiz "
        "covering variables, data types, and basic operations.",

        [

            {
                "text": "What is the output of print(2 + 3)?",

                "type": "mcq",

                "marks": 5,

                "options": [
                    "5",
                    "23",
                    "Error",
                    "None"
                ],

                "correct_answer": "5"
            },

            {
                "text": "Which keyword is used to define a function?",

                "type": "mcq",

                "marks": 5,

                "options": [
                    "func",
                    "def",
                    "function",
                    "define"
                ],

                "correct_answer": "def"
            },

            {
                "text": "Python is a compiled language.",

                "type": "true_false",

                "marks": 5,

                "options": [
                    "True",
                    "False"
                ],

                "correct_answer": "False"
            },

            {
                "text": "What data type is the result of: 10 / 3?",

                "type": "mcq",

                "marks": 5,

                "options": [
                    "int",
                    "float",
                    "str",
                    "bool"
                ],

                "correct_answer": "float"
            },

            {
                "text": "Lists in Python are mutable.",

                "type": "true_false",

                "marks": 5,

                "options": [
                    "True",
                    "False"
                ],

                "correct_answer": "True"
            }

        ]
    )

    # ========================================================
    # EXAM 2
    # ========================================================

    exam2_id = create_exam(

        examiner_token,

        "Data Structures & Algorithms",

        45,

        "Assess your understanding of fundamental "
        "data structures and algorithmic concepts.",

        [

            {
                "text": "What is the time complexity of binary search?",

                "type": "mcq",

                "marks": 10,

                "options": [
                    "O(n)",
                    "O(log n)",
                    "O(n²)",
                    "O(1)"
                ],

                "correct_answer": "O(log n)"
            },

            {
                "text": "A stack follows LIFO "
                        "(Last In First Out) principle.",

                "type": "true_false",

                "marks": 5,

                "options": [
                    "True",
                    "False"
                ],

                "correct_answer": "True"
            },

            {
                "text": "Which data structure uses FIFO?",

                "type": "mcq",

                "marks": 10,

                "options": [
                    "Stack",
                    "Queue",
                    "Tree",
                    "Graph"
                ],

                "correct_answer": "Queue"
            },

            {
                "text": "What is the worst-case time "
                        "complexity of quicksort?",

                "type": "mcq",

                "marks": 10,

                "options": [
                    "O(n log n)",
                    "O(n²)",
                    "O(n)",
                    "O(log n)"
                ],

                "correct_answer": "O(n²)"
            }

        ]
    )

    # ========================================================
    # EXAM 3
    # ========================================================

    exam3_id = create_exam(

        examiner_token,

        "Web Development Basics",

        20,

        "A quick quiz on HTML, CSS, "
        "and JavaScript fundamentals.",

        [

            {
                "text": "HTML stands for "
                        "HyperText Markup Language.",

                "type": "true_false",

                "marks": 5,

                "options": [
                    "True",
                    "False"
                ],

                "correct_answer": "True"
            },

            {
                "text": "Which CSS property is used "
                        "to change text color?",

                "type": "mcq",

                "marks": 5,

                "options": [
                    "font-color",
                    "text-color",
                    "color",
                    "foreground"
                ],

                "correct_answer": "color"
            },

            {
                "text": "JavaScript is a statically typed language.",

                "type": "true_false",

                "marks": 5,

                "options": [
                    "True",
                    "False"
                ],

                "correct_answer": "False"
            }

        ]
    )

    # --------------------------------------------------------
    # 4. PUBLISH EXAMS
    # --------------------------------------------------------

    print("\n--- Publishing Exams ---")

    if exam1_id:

        publish_exam(
            examiner_token,
            exam1_id
        )

    if exam2_id:

        publish_exam(
            examiner_token,
            exam2_id
        )

    if exam3_id:

        publish_exam(
            examiner_token,
            exam3_id
        )

    # --------------------------------------------------------
    # COMPLETE
    # --------------------------------------------------------

    print("\n")

    print_separator()

    print("Seeding complete!")

    print_separator()

    print("\nTest Credentials:")

    print(
        "  Examiner: examiner@test.com / Exam@1234"
    )

    print(
        "  Student:  student@test.com  / Stud@1234"
    )

    print(
        "  Admin:    admin@test.com    / Admin@1234"
    )

    print("\nURLs:")

    print(
        "  Frontend: http://localhost:3000"
    )

    print(
        "  Backend:  http://localhost:5000"
    )

    print(
        "  Health:   http://localhost:5000/api/v1/health"
    )

    print()


# ============================================================
# PROGRAM ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()
