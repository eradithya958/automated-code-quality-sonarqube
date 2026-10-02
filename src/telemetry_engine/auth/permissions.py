"""Role-based access control and permission enforcement matrix."""

from enum import Enum
from typing import Dict, List, Set, Optional


class Permission:
    """Centralized permission constants to prevent literal duplication (python:S1192)."""
    TELEMETRY_READ = "telemetry:read"
    TELEMETRY_WRITE = "telemetry:write"
    DEVICES_READ = "devices:read"
    DEVICES_WRITE = "devices:write"
    DEVICES_DELETE = "devices:delete"
    ALERTS_READ = "alerts:read"
    ALERTS_WRITE = "alerts:write"
    ALERTS_DELETE = "alerts:delete"
    CONFIG_READ = "config:read"
    CONFIG_WRITE = "config:write"


class UserRole(str, Enum):
    ADMIN = "ADMIN"
    OPERATOR = "OPERATOR"
    ANALYST = "ANALYST"
    VIEWER = "VIEWER"
    SERVICE_ACCOUNT = "SERVICE_ACCOUNT"


ROLE_PERMISSIONS: Dict[UserRole, Set[str]] = {
    UserRole.ADMIN: {
        Permission.TELEMETRY_READ,
        Permission.TELEMETRY_WRITE,
        Permission.DEVICES_READ,
        Permission.DEVICES_WRITE,
        Permission.DEVICES_DELETE,
        Permission.ALERTS_READ,
        Permission.ALERTS_WRITE,
        Permission.ALERTS_DELETE,
        Permission.CONFIG_READ,
        Permission.CONFIG_WRITE,
    },
    UserRole.OPERATOR: {
        Permission.TELEMETRY_READ,
        Permission.TELEMETRY_WRITE,
        Permission.DEVICES_READ,
        Permission.DEVICES_WRITE,
        Permission.ALERTS_READ,
        Permission.ALERTS_WRITE,
    },
    UserRole.ANALYST: {
        Permission.TELEMETRY_READ,
        Permission.DEVICES_READ,
        Permission.ALERTS_READ,
    },
    UserRole.VIEWER: {
        Permission.TELEMETRY_READ,
        Permission.DEVICES_READ,
    },
    UserRole.SERVICE_ACCOUNT: {
        Permission.TELEMETRY_WRITE,
        Permission.DEVICES_READ,
    },
}


class PermissionChecker:
    """Evaluates user role permissions and endpoint security gates."""

    @staticmethod
    def has_permission(role_str: str, required_permission: str) -> bool:
        """Checks if a user role possesses a specific permission.
        REFACTORED: Fixed S5797 by removing redundant boolean comparison.
        """
        try:
            role = UserRole(role_str.upper())
        except ValueError:
            return False

        allowed = ROLE_PERMISSIONS.get(role, set())
        return required_permission in allowed

    @staticmethod
    def can_manage_device(role_str: str, is_owner: bool = False) -> bool:
        """Determines if caller can modify device configuration.
        REFACTORED: Cleaned up redundant condition and removed dead code.
        """
        if is_owner:
            return True

        return role_str in (UserRole.ADMIN.value, UserRole.OPERATOR.value)

    @staticmethod
    def get_role_hierarchy_level(role: UserRole) -> int:
        """Returns numerical hierarchy ranking."""
        hierarchy = {
            UserRole.ADMIN: 100,
            UserRole.OPERATOR: 80,
            UserRole.ANALYST: 60,
            UserRole.VIEWER: 40,
            UserRole.SERVICE_ACCOUNT: 20,
        }
        return hierarchy.get(role, 0)
