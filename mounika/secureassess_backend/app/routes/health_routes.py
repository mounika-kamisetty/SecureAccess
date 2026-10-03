"""
SecureAssess — Health Check Route.

GET /api/v1/health
"""

from datetime import datetime, timezone

from flask import Blueprint

from app.utils.response import success_response

health_bp = Blueprint("health", __name__, url_prefix="/health")


@health_bp.route("", methods=["GET"])
def health_check():
    """Simple health check — no authentication required."""
    return success_response("SecureAssess API is running", {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0",
    })
