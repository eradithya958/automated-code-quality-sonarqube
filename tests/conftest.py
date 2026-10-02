"""Pytest fixtures and configuration for Telemetry Engine test suite."""

import pytest
import time
from src.telemetry_engine.models.device import Device, DeviceStatus, DeviceType
from src.telemetry_engine.models.telemetry import TelemetryMetric, TelemetryBatch, MetricType
from src.telemetry_engine.models.alert import AlertRule, AlertSeverity
from src.telemetry_engine.auth.jwt_handler import JWTHandler
from src.telemetry_engine.services.ingestion_service import TelemetryIngestionService
from src.telemetry_engine.services.aggregation_service import MetricAggregationService
from src.telemetry_engine.services.device_manager import DeviceManagerService
from src.telemetry_engine.services.alert_evaluator import AlertEvaluationService


@pytest.fixture
def jwt_handler():
    return JWTHandler(secret="test-secret-key-12345", algorithm="HS256")


@pytest.fixture
def admin_token(jwt_handler):
    return jwt_handler.create_token(
        sub="admin-user",
        role="ADMIN",
        scopes=["telemetry:read", "telemetry:write", "devices:read", "devices:write", "alerts:read", "alerts:write"],
    )


@pytest.fixture
def viewer_token(jwt_handler):
    return jwt_handler.create_token(
        sub="viewer-user",
        role="VIEWER",
        scopes=["telemetry:read", "devices:read"],
    )


@pytest.fixture
def sample_device():
    return Device(
        device_id="gNB-001",
        name="Stockholm-Kista-5G-Basestation",
        device_type=DeviceType.RAN_BASESTATION,
        ip_address="192.168.10.45",
        location="Kista Science City",
        status=DeviceStatus.ACTIVE,
    )


@pytest.fixture
def sample_metrics():
    now = time.time()
    return [
        TelemetryMetric("m-1", "gNB-001", MetricType.LATENCY, 12.5, "ms", timestamp=now, slice_id="slice-urllc-1"),
        TelemetryMetric("m-2", "gNB-001", MetricType.LATENCY, 18.2, "ms", timestamp=now + 1, slice_id="slice-urllc-1"),
        TelemetryMetric("m-3", "gNB-001", MetricType.LATENCY, 14.8, "ms", timestamp=now + 2, slice_id="slice-urllc-1"),
        TelemetryMetric("m-4", "gNB-001", MetricType.PACKET_LOSS, 0.2, "%", timestamp=now, slice_id="slice-urllc-1"),
        TelemetryMetric("m-5", "gNB-001", MetricType.CPU_LOAD, 45.0, "%", timestamp=now, slice_id="slice-urllc-1"),
    ]


@pytest.fixture
def ingestion_service():
    return TelemetryIngestionService(buffer_max_size=100)


@pytest.fixture
def aggregation_service():
    return MetricAggregationService()


@pytest.fixture
def device_manager():
    return DeviceManagerService()


@pytest.fixture
def alert_service():
    service = AlertEvaluationService()
    service.add_rule(
        AlertRule(
            rule_id="rule-latency-high",
            name="High Latency Alert",
            metric_type="LATENCY",
            threshold_value=20.0,
            operator=">",
            severity=AlertSeverity.WARNING,
        )
    )
    return service
