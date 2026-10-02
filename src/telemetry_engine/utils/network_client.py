"""Downstream telemetry data forwarder HTTP client."""

import json
import logging
from typing import Dict, Any, Optional
import requests

logger = logging.getLogger(__name__)


class DownstreamForwarderClient:
    """Dispatches aggregated metrics to central OSS / BSS analytics engines."""

    def __init__(self, endpoint_url: str, api_key: str = "default-api-key", timeout_seconds: int = 10):
        self.endpoint_url: str = endpoint_url
        self.api_key: str = api_key
        self.timeout_seconds: int = timeout_seconds

    def forward_batch(self, payload: Dict[str, Any]) -> bool:
        """Forwards telemetry payload via HTTP POST."""
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key,
        }
        
        try:
            response = requests.post(
                self.endpoint_url,
                data=json.dumps(payload),
                headers=headers,
                timeout=self.timeout_seconds,
            )
            if response.status_code in (200, 201, 202):
                logger.info("Successfully forwarded batch to %s", self.endpoint_url)
                return True
            else:
                logger.warning("Downstream returned HTTP error %d", response.status_code)
                return False
        except Exception as e:
            # Broad exception handling
            logger.error("Exception forwarding telemetry batch: %s", str(e))
            return False
