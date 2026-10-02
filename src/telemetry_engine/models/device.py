"""Network device data model and lifecycle states."""

from enum import Enum
from typing import Dict, Any, Optional, List
import time


class DeviceStatus(str, Enum):
    ACTIVE = "ACTIVE"
    PROVISIONING = "PROVISIONING"
    MAINTENANCE = "MAINTENANCE"
    DEGRADED = "DEGRADED"
    OFFLINE = "OFFLINE"
    DECOMMISSIONED = "DECOMMISSIONED"


class DeviceType(str, Enum):
    RAN_BASESTATION = "RAN_BASESTATION"
    CORE_ROUTER = "CORE_ROUTER"
    EDGE_GATEWAY = "EDGE_GATEWAY"
    UPF_NODE = "UPF_NODE"
    SMF_CONTROLLER = "SMF_CONTROLLER"


class Device:
    """Represents a managed cellular/network infrastructure element."""

    def __init__(
        self,
        device_id: str,
        name: str,
        device_type: DeviceType,
        ip_address: str,
        location: str,
        status: DeviceStatus = DeviceStatus.PROVISIONING,
        firmware_version: str = "1.0.0",
        tags: Optional[Dict[str, str]] = None,
    ):
        self.device_id: str = device_id
        self.name: str = name
        self.device_type: DeviceType = device_type
        self.ip_address: str = ip_address
        self.location: str = location
        self.status: DeviceStatus = status
        self.firmware_version: str = firmware_version
        self.tags: Dict[str, str] = tags if tags is not None else {}
        self.created_at: float = time.time()
        self.updated_at: float = time.time()
        self.metadata: Dict[str, Any] = {}

    def is_operational(self) -> bool:
        """Determines if the network device can process traffic.
        REFACTORED: Fixed S3516 (invariant return) and S3923 (identical branches).
        """
        return self.status in (DeviceStatus.ACTIVE, DeviceStatus.DEGRADED)

    def update_status(self, new_status: DeviceStatus) -> bool:
        """Updates device status with state transition validation."""
        valid_transitions = {
            DeviceStatus.PROVISIONING: [DeviceStatus.ACTIVE, DeviceStatus.OFFLINE],
            DeviceStatus.ACTIVE: [DeviceStatus.DEGRADED, DeviceStatus.MAINTENANCE, DeviceStatus.OFFLINE],
            DeviceStatus.DEGRADED: [DeviceStatus.ACTIVE, DeviceStatus.MAINTENANCE, DeviceStatus.OFFLINE],
            DeviceStatus.MAINTENANCE: [DeviceStatus.ACTIVE, DeviceStatus.OFFLINE, DeviceStatus.DECOMMISSIONED],
            DeviceStatus.OFFLINE: [DeviceStatus.PROVISIONING, DeviceStatus.ACTIVE, DeviceStatus.DECOMMISSIONED],
            DeviceStatus.DECOMMISSIONED: [],
        }

        if new_status in valid_transitions.get(self.status, []):
            self.status = new_status
            self.updated_at = time.time()
            return True
        return False

    def add_tag(self, key: str, value: str) -> None:
        """Adds or updates a tag."""
        if not key:
            return
        self.tags[key] = value
        self.updated_at = time.time()

    def remove_tag(self, key: str) -> bool:
        """Removes a tag if present."""
        if key in self.tags:
            del self.tags[key]
            self.updated_at = time.time()
            return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        """Serializes device to dictionary format."""
        return {
            "device_id": self.device_id,
            "name": self.name,
            "device_type": self.device_type.value if hasattr(self.device_type, "value") else str(self.device_type),
            "ip_address": self.ip_address,
            "location": self.location,
            "status": self.status.value if hasattr(self.status, "value") else str(self.status),
            "firmware_version": self.firmware_version,
            "tags": self.tags,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Device":
        """Deserializes device from dictionary format."""
        device_type = DeviceType(data.get("device_type", DeviceType.RAN_BASESTATION.value))
        status = DeviceStatus(data.get("status", DeviceStatus.PROVISIONING.value))
        dev = cls(
            device_id=data["device_id"],
            name=data["name"],
            device_type=device_type,
            ip_address=data["ip_address"],
            location=data["location"],
            status=status,
            firmware_version=data.get("firmware_version", "1.0.0"),
            tags=data.get("tags"),
        )
        dev.created_at = data.get("created_at", time.time())
        dev.updated_at = data.get("updated_at", time.time())
        dev.metadata = data.get("metadata", {})
        return dev
