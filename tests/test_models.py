"""Unit tests for domain models."""

import pytest
from src.telemetry_engine.models.device import Device, DeviceStatus, DeviceType
from src.telemetry_engine.models.telemetry import TelemetryMetric, TelemetryBatch, MetricType
from src.telemetry_engine.models.alert import AlertRule, AlertEvent, AlertSeverity


def test_device_lifecycle(sample_device):
    assert sample_device.status == DeviceStatus.ACTIVE
    assert sample_device.is_operational() is True

    # Transition to DEGRADED (still operational)
    assert sample_device.update_status(DeviceStatus.DEGRADED) is True
    assert sample_device.status == DeviceStatus.DEGRADED
    assert sample_device.is_operational() is True

    # Transition to MAINTENANCE (non-operational, tests S3516 fix)
    assert sample_device.update_status(DeviceStatus.MAINTENANCE) is True
    assert sample_device.is_operational() is False

    # Add and remove tag
    sample_device.add_tag("env", "production")
    assert sample_device.tags.get("env") == "production"
    assert sample_device.remove_tag("env") is True
    assert "env" not in sample_device.tags


def test_device_serialization(sample_device):
    data = sample_device.to_dict()
    assert data["device_id"] == "gNB-001"
    assert data["status"] == "ACTIVE"

    restored = Device.from_dict(data)
    assert restored.device_id == sample_device.device_id
    assert restored.name == sample_device.name


def test_telemetry_batch():
    m1 = TelemetryMetric("m-1", "dev-1", MetricType.LATENCY, 10.0, "ms")
    m2 = TelemetryMetric("m-2", "dev-2", MetricType.LATENCY, 20.0, "ms")
    batch = TelemetryBatch("batch-1", "service-a", [m1, m2])

    assert batch.size() == 2
    dev1_metrics = batch.get_metrics_by_device("dev-1")
    assert len(dev1_metrics) == 1
    assert dev1_metrics[0].value == 10.0


def test_alert_rule_evaluation():
    rule = AlertRule("r-1", "CPU Alert", "CPU_LOAD", 80.0, operator=">", severity=AlertSeverity.CRITICAL)
    assert rule.evaluate(85.0) is True
    assert rule.evaluate(75.0) is False
