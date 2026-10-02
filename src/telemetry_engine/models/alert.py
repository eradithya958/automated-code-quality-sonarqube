"""Alert rules and notification event models."""

from enum import Enum
from typing import Dict, Any, Optional
import time


class AlertSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    FATAL = "FATAL"


class AlertRule:
    """Threshold monitoring and alerting rule."""

    def __init__(
        self,
        rule_id: str,
        name: str,
        metric_type: str,
        threshold_value: float,
        operator: str = ">",
        severity: AlertSeverity = AlertSeverity.WARNING,
        enabled: bool = True,
        duration_seconds: int = 60,
    ):
        self.rule_id: str = rule_id
        self.name: str = name
        self.metric_type: str = metric_type
        self.threshold_value: float = threshold_value
        self.operator: str = operator
        self.severity: AlertSeverity = severity
        self.enabled: bool = enabled
        self.duration_seconds: int = duration_seconds

    def evaluate(self, value: float) -> bool:
        """Evaluates whether current metric value breaches rule threshold."""
        if self.operator == ">":
            return value > self.threshold_value
        elif self.operator == ">=":
            return value >= self.threshold_value
        elif self.operator == "<":
            return value < self.threshold_value
        elif self.operator == "<=":
            return value <= self.threshold_value
        elif self.operator == "==":
            return value == self.threshold_value
        return False

    def to_dict(self) -> Dict[str, Any]:
        """Serializes alert rule."""
        return {
            "rule_id": self.rule_id,
            "name": self.name,
            "metric_type": self.metric_type,
            "threshold_value": self.threshold_value,
            "operator": self.operator,
            "severity": self.severity.value if hasattr(self.severity, "value") else str(self.severity),
            "enabled": self.enabled,
            "duration_seconds": self.duration_seconds,
        }


class AlertEvent:
    """Triggered alert event instance."""

    def __init__(
        self,
        event_id: str,
        rule_id: str,
        device_id: str,
        triggered_value: float,
        threshold_value: float,
        severity: AlertSeverity,
        message: str,
        timestamp: Optional[float] = None,
        acknowledged: bool = False,
    ):
        self.event_id: str = event_id
        self.rule_id: str = rule_id
        self.device_id: str = device_id
        self.triggered_value: float = triggered_value
        self.threshold_value: float = threshold_value
        self.severity: AlertSeverity = severity
        self.message: str = message
        self.timestamp: float = timestamp if timestamp is not None else time.time()
        self.acknowledged: bool = acknowledged

    def acknowledge(self) -> None:
        """Acknowledge alert event."""
        self.acknowledged = True

    def to_dict(self) -> Dict[str, Any]:
        """Serializes event."""
        return {
            "event_id": self.event_id,
            "rule_id": self.rule_id,
            "device_id": self.device_id,
            "triggered_value": self.triggered_value,
            "threshold_value": self.threshold_value,
            "severity": self.severity.value if hasattr(self.severity, "value") else str(self.severity),
            "message": self.message,
            "timestamp": self.timestamp,
            "acknowledged": self.acknowledged,
        }
