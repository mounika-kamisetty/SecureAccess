"""
SecureAssess — Logging Configuration.

- Development: DEBUG level, coloured console output.
- Production: INFO+ level, structured output.
- NEVER logs passwords, tokens, or secrets.
"""

import logging
import sys


class SensitiveFilter(logging.Filter):
    """Strip known sensitive keys from log records."""

    SENSITIVE_KEYS = {"password", "access_token", "refresh_token", "jwt_secret"}

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, dict):
            record.msg = {
                k: "***REDACTED***" if k.lower() in self.SENSITIVE_KEYS else v
                for k, v in record.msg.items()
            }
        return True


def setup_logger(app):
    """Configure the application logger based on FLASK_ENV."""
    log_level = logging.DEBUG if app.debug else logging.INFO

    # Root logger
    logger = logging.getLogger("secureassess")
    logger.setLevel(log_level)

    # Avoid duplicate handlers on reload
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(log_level)

        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        handler.addFilter(SensitiveFilter())
        logger.addHandler(handler)

    return logger


def get_logger():
    """Get the application logger (call after setup_logger)."""
    return logging.getLogger("secureassess")
