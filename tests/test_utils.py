"""Unit tests for utility modules (file_utils, validators)."""

import os
import pytest
from src.telemetry_engine.utils.file_utils import (
    write_temporary_telemetry_dump,
    read_telemetry_dump,
    secure_file_hash,
)
from src.telemetry_engine.utils.validators import IPValidator, MetricValidator


def test_temporary_telemetry_dump():
    data = '{"test": "payload"}'
    file_path = write_temporary_telemetry_dump(data)
    assert os.path.exists(file_path)

    content = read_telemetry_dump(file_path)
    assert content == data

    # Cleanup
    if os.path.exists(file_path):
        os.remove(file_path)


def test_secure_file_hash():
    payload = b"network-telemetry-data"
    hash_sha256 = secure_file_hash(payload, use_sha512=False)
    assert len(hash_sha256) == 64

    hash_sha512 = secure_file_hash(payload, use_sha512=True)
    assert len(hash_sha512) == 128


def test_ip_validator():
    assert IPValidator.is_valid_ipv4("192.168.1.1") is True
    assert IPValidator.is_valid_ipv4("256.0.0.1") is False
    assert IPValidator.is_valid_ipv4("invalid-ip") is False
    assert IPValidator.is_valid_ipv6("2001:0db8:85a3:0000:0000:8a2e:0370:7334") is True


def test_metric_validator():
    assert MetricValidator.validate_metric_payload("LATENCY", 25.0, "ms") is True
    assert MetricValidator.validate_metric_payload("PACKET_LOSS", 150.0, "%") is False
    assert MetricValidator.validate_metric_payload("CPU_LOAD", 50.0, "invalid_unit") is False
