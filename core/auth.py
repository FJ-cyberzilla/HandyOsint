"""
Minimal JWT-based authentication helpers for HandyOsint.
"""

from dataclasses import dataclass
from typing import Any, Dict

from jose import jwt

JWT_ALGORITHM = "HS256"
JWT_SECRET = "CHANGE_ME_HANDYOSINT_SECRET"
JWT_AUDIENCE = "handyosint-api"
JWT_ISSUER = "handyosint"


@dataclass
class UserPayload:
    """Minimal user info extracted from the access token."""

    sub: str
    username: str
    scopes: str


def verify_access_token(token: str) -> UserPayload:
    """
    Decode and validate an access token.
    """
    decoded: Dict[str, Any] = jwt.decode(
        token,
        JWT_SECRET,
        algorithms=[JWT_ALGORITHM],
        audience=JWT_AUDIENCE,
        issuer=JWT_ISSUER,
    )

    return UserPayload(
        sub=str(decoded.get("sub", "")),
        username=str(decoded.get("preferred_username", decoded.get("sub", ""))),
        scopes=" ".join(str(decoded.get("scope", "")).split()),
    )
