"""Unit tests for Settings configuration manager."""

import os
import json
import pytest
from src.telemetry_engine.config import Settings


def test_settings_default_initialization():
    cfg = Settings()
    assert cfg.app_name == "NetworkTelemetryEngine"
    assert cfg.port == 8080
    assert cfg.jwt_algorithm == "HS256"
    assert cfg.batch_size == 500

    cfg_dict = cfg.to_dict()
    assert cfg_dict["app_name"] == "NetworkTelemetryEngine"
    assert cfg.get_setting("port") == 8080
    assert cfg.get_setting("non_existent_key", "default") == "default"


def test_settings_load_from_file(tmp_path):
    config_file = tmp_path / "test_config.json"
    data = {
        "app_name": "CustomTelemetryEngine",
        "port": 9090,
        "batch_size": 1000,
    }
    config_file.write_text(json.dumps(data))

    cfg = Settings(config_file=str(config_file))
    assert cfg.app_name == "CustomTelemetryEngine"
    assert cfg.port == 9090
    assert cfg.batch_size == 1000
