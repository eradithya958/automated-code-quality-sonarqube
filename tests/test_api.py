"""Integration tests for API handlers and middleware."""

import pytest
from src.telemetry_engine.api.routes_telemetry import TelemetryAPIHandler
from src.telemetry_engine.api.routes_devices import DeviceAPIHandler
from src.telemetry_engine.api.routes_alerts import AlertAPIHandler
from src.telemetry_engine.api.middleware import RequestMiddleware
from src.telemetry_engine.utils.network_client import DownstreamForwarderClient


def test_telemetry_api_ingest_single(ingestion_service, aggregation_service, jwt_handler, admin_token):
    handler = TelemetryAPIHandler(ingestion_service, aggregation_service, jwt_handler)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {admin_token}",
    }
    body = {
        "metric_id": "m-api-1",
        "device_id": "gNB-001",
        "metric_type": "LATENCY",
        "value": 15.5,
        "unit": "ms",
    }

    status_code, resp = handler.handle_ingest_single(headers, body)
    assert status_code == 201
    assert resp["status"] == "success"


def test_telemetry_api_ingest_batch(ingestion_service, aggregation_service, jwt_handler, admin_token):
    handler = TelemetryAPIHandler(ingestion_service, aggregation_service, jwt_handler)
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {admin_token}",
    }
    body = {
        "batch_id": "b-1",
        "source_service": "test",
        "metrics": [
            {"metric_id": "m-1", "device_id": "d-1", "metric_type": "LATENCY", "value": 10.0}
        ]
    }
    code, resp = handler.handle_ingest_batch(headers, body)
    assert code == 200
    assert resp["accepted"] == 1


def test_device_api_register_and_get(device_manager, jwt_handler, admin_token):
    handler = DeviceAPIHandler(device_manager, jwt_handler)
    headers = {"Authorization": f"Bearer {admin_token}"}
    body = {
        "device_id": "UPF-01",
        "name": "Core-UPF-Stockholm",
        "device_type": "UPF_NODE",
        "ip_address": "10.0.0.1",
        "location": "Datacenter-A",
        "status": "ACTIVE",
    }

    status_code, resp = handler.handle_register_device(headers, body)
    assert status_code == 201

    get_code, get_resp = handler.handle_get_device("UPF-01")
    assert get_code == 200
    assert get_resp["device"]["name"] == "Core-UPF-Stockholm"

    list_code, list_resp = handler.handle_list_devices({})
    assert list_code == 200
    assert list_resp["count"] >= 1


def test_alert_api_create_rule(alert_service, jwt_handler, admin_token):
    handler = AlertAPIHandler(alert_service, jwt_handler)
    headers = {"Authorization": f"Bearer {admin_token}"}
    body = {
        "rule_id": "r-packet-loss",
        "name": "High Packet Loss Rule",
        "metric_type": "PACKET_LOSS",
        "threshold_value": 2.0,
        "severity": "CRITICAL",
    }

    status_code, resp = handler.handle_create_rule(headers, body)
    assert status_code == 201
    assert resp["rule"]["rule_id"] == "r-packet-loss"

    code, resp_list = handler.handle_list_active_alerts()
    assert code == 200


def test_request_middleware():
    called = False
    def sample_handler():
        nonlocal called
        called = True
        return "ok"

    res = RequestMiddleware.log_request_timing("/api/test", "GET", sample_handler)
    assert res == "ok"
    assert called is True
