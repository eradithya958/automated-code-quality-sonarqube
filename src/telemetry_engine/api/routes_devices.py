"""Device management API endpoints."""

import logging
from typing import Dict, Any, Tuple, Optional
from ..models.device import Device, DeviceStatus, DeviceType
from ..services.device_manager import DeviceManagerService
from ..auth.jwt_handler import JWTHandler
from ..auth.permissions import PermissionChecker

logger = logging.getLogger(__name__)


class DeviceAPIHandler:
    """Handles REST interactions for managed base stations and UPFs."""

    def __init__(self, device_manager: DeviceManagerService, jwt_handler: JWTHandler):
        self.device_manager = device_manager
        self.jwt_handler = jwt_handler

    def handle_register_device(self, headers: Dict[str, str], body: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        """Handles POST /api/v1/devices"""
        auth_header = headers.get("Authorization")
        token = self.jwt_handler.extract_bearer_token(auth_header)
        payload = self.jwt_handler.decode_and_verify(token) if token else None

        if not payload:
            return 401, {"status": "error", "message": "Unauthorized"}

        if not PermissionChecker.has_permission(payload.role, "devices:write"):
            return 403, {"status": "error", "message": "Forbidden"}

        try:
            device = Device.from_dict(body)
            success = self.device_manager.register_device(device)
            if success:
                return 201, {"status": "success", "device": device.to_dict()}
            else:
                return 409, {"status": "error", "message": "Device ID already exists"}
        except KeyError as e:
            return 400, {"status": "error", "message": f"Missing required parameter: {str(e)}"}
        except Exception as e:
            logger.error("Device registration error: %s", str(e))
            return 500, {"status": "error", "message": str(e)}

    def handle_get_device(self, device_id: str) -> Tuple[int, Dict[str, Any]]:
        """Handles GET /api/v1/devices/{device_id}"""
        dev = self.device_manager.get_device(device_id)
        if not dev:
            return 404, {"status": "error", "message": "Device not found"}
        return 200, {"status": "success", "device": dev.to_dict()}

    def handle_list_devices(self, query_params: Dict[str, str]) -> Tuple[int, Dict[str, Any]]:
        """Handles GET /api/v1/devices"""
        status_filter = DeviceStatus(query_params["status"]) if "status" in query_params else None
        type_filter = DeviceType(query_params["device_type"]) if "device_type" in query_params else None
        location_filter = query_params.get("location")

        devices = self.device_manager.list_devices(
            status=status_filter,
            device_type=type_filter,
            location=location_filter,
        )

        return 200, {
            "status": "success",
            "count": len(devices),
            "devices": [d.to_dict() for d in devices],
        }
