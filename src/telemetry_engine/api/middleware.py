"""API request processing middleware, timing, and security logging."""

import time
import logging
from typing import Dict, Any, Callable

logger = logging.getLogger(__name__)


class RequestMiddleware:
    """Interceptors for incoming HTTP calls."""

    @staticmethod
    def log_request_timing(path: str, method: str, handler: Callable[[], Any]) -> Any:
        """Measures request duration and logs slow endpoints."""
        start_time = time.time()
        try:
            result = handler()
            duration_ms = (time.time() - start_time) * 1000.0
            logger.info("Executed %s %s in %.2fms", method, path, duration_ms)
            return result
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000.0
            logger.error("Failed %s %s in %.2fms: %s", method, path, duration_ms, str(e))
            raise e
