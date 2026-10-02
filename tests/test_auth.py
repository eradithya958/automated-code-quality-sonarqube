"""Unit tests for authentication, JWT encoding/decoding, and RBAC permissions."""

import pytest
from src.telemetry_engine.auth.jwt_handler import JWTHandler, TokenPayload
from src.telemetry_engine.auth.permissions import PermissionChecker, Permission, UserRole


def test_jwt_create_and_verify(jwt_handler):
    token = jwt_handler.create_token(
        sub="user-123",
        role="OPERATOR",
        scopes=["telemetry:read", "telemetry:write"],
        expires_in_seconds=300,
    )
    assert token is not None
    assert len(token.split(".")) == 3

    payload = jwt_handler.decode_and_verify(token)
    assert payload is not None
    assert payload.sub == "user-123"
    assert payload.role == "OPERATOR"
    assert "telemetry:read" in payload.scopes
    assert not payload.is_expired()


def test_jwt_validate_scope(jwt_handler):
    payload = TokenPayload(
        sub="user-123",
        role="OPERATOR",
        scopes=["telemetry:read", "telemetry:write"],
        exp=9999999999.0,
    )
    # Valid scope
    assert jwt_handler.validate_scope(payload, "telemetry:read") is True
    # Missing scope (Tests S3516 fix)
    assert jwt_handler.validate_scope(payload, "devices:delete") is False
    # None payload
    assert jwt_handler.validate_scope(None, "telemetry:read") is False

    admin_payload = TokenPayload(
        sub="admin-1",
        role="ADMIN",
        scopes=["admin:all"],
        exp=9999999999.0,
    )
    assert jwt_handler.validate_scope(admin_payload, "anything") is True


def test_jwt_invalid_signature():
    handler1 = JWTHandler(secret="key-1")
    handler2 = JWTHandler(secret="key-2")

    token = handler1.create_token(sub="user-1", role="VIEWER", scopes=["telemetry:read"])
    decoded = handler2.decode_and_verify(token)
    assert decoded is None


def test_jwt_extract_bearer_token(jwt_handler):
    assert jwt_handler.extract_bearer_token("Bearer mytoken123") == "mytoken123"
    assert jwt_handler.extract_bearer_token(None) is None
    assert jwt_handler.extract_bearer_token("Basic 1234") is None


def test_permission_checker():
    assert PermissionChecker.has_permission("ADMIN", Permission.DEVICES_WRITE) is True
    assert PermissionChecker.has_permission("VIEWER", Permission.DEVICES_WRITE) is False
    assert PermissionChecker.has_permission("OPERATOR", Permission.TELEMETRY_WRITE) is True
    assert PermissionChecker.has_permission("INVALID_ROLE", Permission.TELEMETRY_READ) is False


def test_can_manage_device():
    assert PermissionChecker.can_manage_device("ADMIN", False) is True
    assert PermissionChecker.can_manage_device("VIEWER", True) is True
    assert PermissionChecker.can_manage_device("VIEWER", False) is False
