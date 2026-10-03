# SecureAssess — Backend

A secure online examination platform designed to reduce malpractice and provide reliable student evaluation.

## Features
- **Role-Based Access Control (RBAC):** Students, Examiners, Admins.
- **JWT Authentication:** Powered by Flask-JWT-Extended with a MongoDB blocklist for instant revocation.
- **Exam Management:** Create, draft, and publish exams with various question types.
- **Attempt Tracking:** Server-side scoring and time validation to prevent cheating.
- **Anti-Malpractice Logging:** Logs suspicious events (tab switches, full-screen exits) and generates a risk score.
- **Audit Trails:** Comprehensive logging of all system actions (logins, registrations, password changes).

## Prerequisites
- Python 3.12+
- MongoDB 6.0+
- `uv` (recommended) or `pip`

## Installation

1. **Clone and setup virtual environment**
   ```bash
   uv venv
   .\.venv\Scripts\activate
   uv pip install -r requirements.txt
   ```

2. **Configure Environment Variables**
   Create a `.env` file in the root directory:
   ```env
   MONGO_URI=mongodb://localhost:27017/secureassess
   JWT_SECRET_KEY=your-super-secret-key
   CORS_ORIGINS=http://localhost:3000
   ```

3. **Run the Application**
   ```bash
   python run.py
   ```

## Docker Deployment
To run the backend with MongoDB easily using Docker Compose:
```bash
docker-compose up --build -d
```
The API will be available at `http://localhost:5000`.

## Testing
Run the test suite using pytest:
```bash
pytest tests/
```
