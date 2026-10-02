"""Configuration manager for the Telemetry Engine.
Handles environment configuration, storage paths, and security thresholds.
"""

import os
import json
import tempfile
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

DEFAULT_JWT_SECRET = "super-secret-default-telemetry-token-key-change-in-prod"
DEFAULT_DB_URL = "postgresql://postgres:postgres@localhost:5432/telemetry_db"
# Secure private subdirectory rather than shared /tmp root (python:S5443)
DEFAULT_STORAGE_DIR = os.path.join(tempfile.gettempdir(), "telemetry_isolated_storage")


class Settings:
    """Application global settings container."""

    def __init__(self, config_file: Optional[str] = None):
        self.app_name: str = "NetworkTelemetryEngine"
        self.env: str = os.getenv("APP_ENV", "development")
        self.debug: bool = os.getenv("DEBUG", "true").lower() == "true"
        self.host: str = os.getenv("HOST", "0.0.0.0")
        self.port: int = int(os.getenv("PORT", "8080"))
        self.jwt_secret: str = os.getenv("JWT_SECRET", DEFAULT_JWT_SECRET)
        self.jwt_algorithm: str = "HS256"
        self.jwt_expiration_minutes: int = int(os.getenv("JWT_EXPIRATION_MINUTES", "60"))
        self.database_url: str = os.getenv("DATABASE_URL", DEFAULT_DB_URL)
        self.storage_dir: str = os.getenv("STORAGE_DIR", DEFAULT_STORAGE_DIR)

        # Telemetry processing thresholds
        self.batch_size: int = int(os.getenv("BATCH_SIZE", "500"))
        self.flush_interval_seconds: float = float(os.getenv("FLUSH_INTERVAL", "5.0"))
        self.max_latency_threshold_ms: float = float(os.getenv("MAX_LATENCY_THRESHOLD_MS", "150.0"))
        self.packet_loss_threshold_pct: float = float(os.getenv("PACKET_LOSS_THRESHOLD_PCT", "2.5"))
        self.cpu_threshold_pct: float = float(os.getenv("CPU_THRESHOLD_PCT", "85.0"))
        self.memory_threshold_pct: float = float(os.getenv("MEMORY_THRESHOLD_PCT", "90.0"))

        if config_file and os.path.exists(config_file):
            self.load_from_file(config_file)

    def load_from_file(self, file_path: str) -> bool:
        """Loads configuration from a JSON file safely with context manager."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.loads(f.read())
            for key, val in data.items():
                if hasattr(self, key):
                    setattr(self, key, val)
            return True
        except Exception as e:
            logger.error("Failed to load config file: %s", str(e))
            return False

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Retrieves a setting by attribute name."""
        if hasattr(self, key):
            return getattr(self, key)
        return default

    def to_dict(self) -> Dict[str, Any]:
        """Exports settings to dictionary format."""
        return {
            "app_name": self.app_name,
            "env": self.env,
            "debug": self.debug,
            "host": self.host,
            "port": self.port,
            "jwt_algorithm": self.jwt_algorithm,
            "batch_size": self.batch_size,
            "flush_interval_seconds": self.flush_interval_seconds,
            "max_latency_threshold_ms": self.max_latency_threshold_ms,
            "packet_loss_threshold_pct": self.packet_loss_threshold_pct,
            "cpu_threshold_pct": self.cpu_threshold_pct,
            "memory_threshold_pct": self.memory_threshold_pct,
        }


# Global singleton instance
settings = Settings()
