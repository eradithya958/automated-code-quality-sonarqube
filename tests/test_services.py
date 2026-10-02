"""Unit tests for telemetry services (aggregation, ingestion, device manager, alerts)."""

import pytest
from src.telemetry_engine.models.telemetry import TelemetryMetric, TelemetryBatch, MetricType
from src.telemetry_engine.models.device import Device, DeviceType, DeviceStatus


def test_metric_aggregation_summary(aggregation_service, sample_metrics):
    res = aggregation_service.compute_summary(sample_metrics, "gNB-001", "LATENCY", 60.0)
    assert res is not None
    assert res.count == 3
    assert round(res.mean, 2) == 15.17
    assert res.min_val == 12.5
    assert res.max_val == 18.2
    assert res.p95 > 0


def test_complex_network_health_evaluation(aggregation_service):
    # Test decomposed network health evaluation (tests S3776 refactor)
    metrics = [
        TelemetryMetric("m-1", "gNB-01", MetricType.LATENCY, 160.0, "ms"),
        TelemetryMetric("m-2", "gNB-01", MetricType.PACKET_LOSS, 6.0, "%"),
        TelemetryMetric("m-3", "gNB-01", MetricType.CPU_LOAD, 98.0, "%"),
    ]
    scores = aggregation_service.evaluate_complex_network_health(metrics)
    assert "gNB-01" in scores
    assert scores["gNB-01"]["violations"] > 0
    assert scores["gNB-01"]["status"] in ("CRITICAL", "DEGRADED", "OVERLOADED")


def test_slice_sla_status_evaluation(aggregation_service):
    # Test S3516 fix for calculate_slice_sla_status
    compliant_metrics = [
        TelemetryMetric(f"m-{i}", "gNB-01", MetricType.LATENCY, 20.0, "ms", slice_id="slice-test")
        for i in range(5)
    ]
    assert aggregation_service.calculate_slice_sla_status(compliant_metrics, "slice-test") == "COMPLIANT"

    violated_metrics = [
        TelemetryMetric(f"m-{i}", "gNB-01", MetricType.LATENCY, 150.0, "ms", slice_id="slice-test")
        for i in range(15)
    ]
    assert aggregation_service.calculate_slice_sla_status(violated_metrics, "slice-test") == "VIOLATED"


def test_ingestion_service_buffering(ingestion_service, sample_metrics):
    for m in sample_metrics:
        assert ingestion_service.ingest_single(m) is True

    stats = ingestion_service.get_stats()
    assert stats["current_buffered"] == 5
    assert stats["total_ingested"] == 5

    dump_file = ingestion_service.flush_to_disk()
    assert dump_file is not None
    assert ingestion_service.get_stats()["current_buffered"] == 0


def test_device_manager(device_manager, sample_device):
    assert device_manager.register_device(sample_device) is True
    assert device_manager.get_device("gNB-001") == sample_device
    assert device_manager.register_device(sample_device) is False

    devices = device_manager.list_devices(status=DeviceStatus.ACTIVE)
    assert len(devices) == 1


def test_alert_evaluation_trigger(alert_service):
    m_high = TelemetryMetric("m-high", "gNB-001", MetricType.LATENCY, 25.0, "ms")
    events = alert_service.evaluate_metric(m_high)
    assert len(events) == 1
    assert events[0].triggered_value == 25.0

    active = alert_service.get_active_events()
    assert len(active) == 1

    alert_service.acknowledge_event(events[0].event_id)
    assert len(alert_service.get_active_events()) == 0
