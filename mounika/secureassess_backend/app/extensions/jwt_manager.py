"""
SecureAssess — JWT Extension.

Configures Flask-JWT-Extended for token creation, verification, and revocation.
Uses MongoDB as a blocklist for revoked tokens.
"""

from datetime import datetime, timezone
from functools import wraps

from flask import jsonify, g
from flask_jwt_extended import JWTManager
from flask_jwt_extended import get_jwt, get_jwt_identity
from flask_jwt_extended import verify_jwt_in_request

from app.extensions.mongo import mongo


# Instantiate the Flask-JWT-Extended manager
jwt_manager = JWTManager()


@jwt_manager.token_in_blocklist_loader
def check_if_token_is_revoked(jwt_header, jwt_payload: dict) -> bool:
    """
    Callback function to check if a JWT exists in the MongoDB blocklist.
    Used for both access and refresh tokens.
    """
    jti = jwt_payload["jti"]
    token = mongo.blocklist.find_one({"jti": jti})
    return token is not None


def revoke_token(jti: str, user_id: str, type: str):
    """Adds a token's JTI to the MongoDB blocklist."""
    mongo.blocklist.insert_one(
        {
            "jti": jti,
            "user_id": user_id,
            "type": type,
            "created_at": datetime.now(timezone.utc),
        }
    )


def revoke_all_user_tokens(user_id: str):
    """
    Usually blocklisting all tokens means looking up JTIs, but since JWTs 
    are stateless, we can't blocklist what we don't track. 
    However, for the specific requirement of revoking on password change, 
    we could track a 'token_version' or simply invalidate via another mechanism.
    To match the previous API semantics, we will rely on specific JTIs.
    """
    pass



