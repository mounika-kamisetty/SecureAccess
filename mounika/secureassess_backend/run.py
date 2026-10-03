"""
SecureAssess — Application Entry Point.

Usage:
    Development:  flask run
    Production:   gunicorn "run:create_app()"
"""

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
