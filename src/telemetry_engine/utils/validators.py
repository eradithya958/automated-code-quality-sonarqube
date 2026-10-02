"""Validation utilities for network parameters and metrics."""

import re
from typing import Optional


class IPValidator:
    """Validates IPv4 and IPv6 network addresses."""

    IPV4_REGEX = r"^(\d{1,3}\.){3}\d{1,3}$"
    IPV6_REGEX = r"^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$"

    @classmethod
    def is_valid_ipv4(cls, ip: str) -> bool:
        """Validates IPv4 format and octet ranges."""
        if not ip or not isinstance(ip, str):
            return False

        if not re.match(cls.IPV4_REGEX, ip):
            return False

        parts = ip.split(".")
        for p in parts:
            try:
                num = int(p)
                if num < 0 or num > 255:
                    return False
            except ValueError:
                return False
        return True

    @classmethod
    def is_valid_ipv6(cls, ip: str) -> bool:
        """Validates IPv6 format."""
        if not ip or not isinstance(ip, str):
            return False
        return bool(re.match(cls.IPV6_REGEX, ip))


class MetricValidator:
    """Validates telemetry metric ranges and units."""

    VALID_UNITS = {"ms", "Mbps", "Gbps", "%", "dBm", "packets/s", "ratio"}

    @classmethod
    def validate_metric_payload(cls, metric_type: str, value: float, unit: str) -> bool:
        """Validates sanity of telemetry value and measurement unit."""
        if unit not in cls.VALID_UNITS:
            return False

        if metric_type == "PACKET_LOSS" and (value < 0.0 or value > 100.0):
            return False

        if metric_type in ("CPU_LOAD", "MEMORY_USAGE") and (value < 0.0 or value > 100.0):
            return False

        if metric_type == "LATENCY" and value < 0.0:
            return False

        return True
