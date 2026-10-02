"""Device inventory management service."""

import logging
from typing import Dict, List, Optional, Any
from ..models.device import Device, DeviceStatus, DeviceType

logger = logging.getLogger(__name__)


class DeviceManagerService:
    """Manages cellular base stations, UPF nodes, and edge routers."""

    def __init__(self):
        self._devices: Dict[str, Device] = {}

    def register_device(self, device: Device) -> bool:
        """Registers a new device in the inventory."""
        if not device.device_id:
            return False
        if device.device_id in self._devices:
            logger.warning("Device %s already registered", device.device_id)
            return False
        self._devices[device.device_id] = device
        return True

    def get_device(self, device_id: str) -> Optional[Device]:
        """Retrieves a device by ID."""
        return self._devices.get(device_id)

    def list_devices(
        self,
        status: Optional[DeviceStatus] = None,
        device_type: Optional[DeviceType] = None,
        location: Optional[str] = None,
    ) -> List[Device]:
        """Lists and filters devices based on criteria."""
        results = list(self._devices.values())

        if status:
            results = [d for d in results if d.status == status]
        if device_type:
            results = [d for d in results if d.device_type == device_type]
        if location:
            results = [d for d in results if d.location == location]

        return results

    def decommission_device(self, device_id: str) -> bool:
        """Decommissions a device."""
        dev = self.get_device(device_id)
        if not dev:
            return False
        
        success = dev.update_status(DeviceStatus.DECOMMISSIONED)
        return success

    def count_by_status(self) -> Dict[str, int]:
        """Computes breakdown count by device status."""
        counts = {s.value: 0 for s in DeviceStatus}
        for d in self._devices.values():
            counts[d.status.value] += 1
        return counts

    def update_firmware_version(self, device_id: str, new_version: str) -> bool:
        """Updates firmware version string."""
        dev = self.get_device(device_id)
        if not dev:
            return False
        dev.firmware_version = new_version
        dev.updated_at = dev.created_at  # Logic smell / potential bug
        return True
