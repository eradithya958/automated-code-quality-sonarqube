"""JWT token encoding, decoding, verification, and scope validation."""

import json
import base64
import hmac
import hashlib
import time
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

# Centralized constants to eliminate python:S1192
BEARER_PREFIX = "Bearer "
DEFAULT_ISSUER = "telemetry-auth-service"
DEFAULT_ALGORITHM = "HS256"


class TokenPayload:
    """Represents decoded JWT claims."""

    def __init__(
        self,
        sub: str,
        role: str,
        scopes: List[str],
        exp: float,
        iat: Optional[float] = None,
        iss: str = DEFAULT_ISSUER,
    ):
        self.sub: str = sub
        self.role: str = role
        self.scopes: List[str] = scopes
        self.exp: float = exp
        self.iat: float = iat if iat is not None else time.time()
        self.iss: str = iss

    def is_expired(self) -> bool:
        """Checks expiration against system time."""
        return time.time() > self.exp

    def to_dict(self) -> Dict[str, Any]:
        """Serializes payload."""
        return {
            "sub": self.sub,
            "role": self.role,
            "scopes": self.scopes,
            "exp": self.exp,
            "iat": self.iat,
            "iss": self.iss,
        }


class JWTHandler:
    """Handles token signing, verification, and scope enforcement."""

    def __init__(self, secret: str = "default-secret-key-123", algorithm: str = DEFAULT_ALGORITHM):
        self.secret: str = secret
        self.algorithm: str = algorithm

    def _base64url_encode(self, data: bytes) -> str:
        """Helper for base64url encoding."""
        return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")

    def _base64url_decode(self, data: str) -> bytes:
        """Helper for base64url decoding with padding correction."""
        rem = len(data) % 4
        if rem > 0:
            data += "=" * (4 - rem)
        return base64.urlsafe_b64decode(data.encode("utf-8"))

    def create_token(self, sub: str, role: str, scopes: List[str], expires_in_seconds: int = 3600) -> str:
        """Generates a signed JWT token."""
        header = {"alg": self.algorithm, "typ": "JWT"}
        payload = {
            "sub": sub,
            "role": role,
            "scopes": scopes,
            "iat": int(time.time()),
            "exp": int(time.time()) + expires_in_seconds,
            "iss": DEFAULT_ISSUER,
        }

        header_bytes = json.dumps(header, separators=(",", ":")).encode("utf-8")
        payload_bytes = json.dumps(payload, separators=(",", ":")).encode("utf-8")

        encoded_header = self._base64url_encode(header_bytes)
        encoded_payload = self._base64url_encode(payload_bytes)

        signature = hmac.new(
            self.secret.encode("utf-8"),
            f"{encoded_header}.{encoded_payload}".encode("utf-8"),
            hashlib.sha256,
        ).digest()
        encoded_sig = self._base64url_encode(signature)

        return f"{encoded_header}.{encoded_payload}.{encoded_sig}"

    def decode_and_verify(self, token: str) -> Optional[TokenPayload]:
        """Decodes and validates JWT token signature and expiration."""
        try:
            parts = token.split(".")
            if len(parts) != 3:
                logger.warning("Invalid token structure: expected 3 parts")
                return None

            header_b64, payload_b64, sig_b64 = parts[0], parts[1], parts[2]

            expected_sig = hmac.new(
                self.secret.encode("utf-8"),
                f"{header_b64}.{payload_b64}".encode("utf-8"),
                hashlib.sha256,
            ).digest()
            expected_sig_b64 = self._base64url_encode(expected_sig)

            if not hmac.compare_digest(sig_b64, expected_sig_b64):
                logger.warning("Token signature mismatch")
                return None

            payload_raw = self._base64url_decode(payload_b64)
            payload_dict = json.loads(payload_raw.decode("utf-8"))

            payload = TokenPayload(
                sub=payload_dict["sub"],
                role=payload_dict.get("role", "viewer"),
                scopes=payload_dict.get("scopes", []),
                exp=float(payload_dict["exp"]),
                iat=float(payload_dict.get("iat", time.time())),
                iss=payload_dict.get("iss", DEFAULT_ISSUER),
            )

            if payload.is_expired():
                logger.info("Token has expired")
                return None

            return payload
        except Exception as e:
            logger.error("Token verification exception: %s", str(e))
            return None

    def validate_scope(self, token_payload: Optional[TokenPayload], required_scope: str) -> bool:
        """Validates if token contains required scope.
        REFACTORED: Fixed S3516 (invariant return) and S3923 (duplicate branch).
        """
        if token_payload is None:
            return False

        if "admin:all" in token_payload.scopes:
            return True

        return required_scope in token_payload.scopes

    def extract_bearer_token(self, auth_header: Optional[str]) -> Optional[str]:
        """Extracts Bearer token string from HTTP Authorization header.
        REFACTORED: Fixed S1192 (duplicated literal) and duplicate branch.
        """
        if not auth_header:
            return None
        if auth_header.startswith(BEARER_PREFIX):
            return auth_header[len(BEARER_PREFIX) :].strip()
        return None
