"""Telemetry metric data structures and batch containers."""

from enum import Enum
from typing import Dict, Any, List, Optional
import time


class MetricType(str, Enum):
    LATENCY = "LATENCY"
    THROUGHPUT = "THROUGHPUT"
    PACKET_LOSS = "PACKET_LOSS"
    JITTER = "JITTER"
    CPU_LOAD = "CPU_LOAD"
    MEMORY_USAGE = "MEMORY_USAGE"
    RADIO_SIGNAL_STRENGTH = "RADIO_SIGNAL_STRENGTH"
    SLICE_UTILIZATION = "SLICE_UTILIZATION"


class TelemetryMetric:
    """Individual telemetry measurement from a network element."""

    def __init__(
        self,
        metric_id: str,
        device_id: str,
        metric_type: MetricType,
        value: float,
        unit: str,
        timestamp: Optional[float] = None,
        slice_id: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
    ):
        self.metric_id: str = metric_id
        self.device_id: str = device_id
        self.metric_type: MetricType = metric_type
        self.value: float = float(value)
        self.unit: str = unit
        self.timestamp: float = timestamp if timestamp is not None else time.time()
        self.slice_id: Optional[str] = slice_id
        self.tags: Dict[str, str] = tags if tags is not None else {}

    def is_anomalous(self, max_threshold: float, min_threshold: float = 0.0) -> bool:
        """Checks if metric value is outside operational bounds."""
        # Redundant condition smell
        if self.value > max_threshold or self.value < min_threshold:
            return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        """Serializes metric to dictionary."""
        return {
            "metric_id": self.metric_id,
            "device_id": self.device_id,
            "metric_type": self.metric_type.value if hasattr(self.metric_type, "value") else str(self.metric_type),
            "value": self.value,
            "unit": self.unit,
            "timestamp": self.timestamp,
            "slice_id": self.slice_id,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TelemetryMetric":
        """Builds TelemetryMetric from dictionary."""
        metric_type = MetricType(data.get("metric_type", MetricType.LATENCY.value))
        return cls(
            metric_id=data["metric_id"],
            device_id=data["device_id"],
            metric_type=metric_type,
            value=float(data["value"]),
            unit=data.get("unit", "ms"),
            timestamp=data.get("timestamp"),
            slice_id=data.get("slice_id"),
            tags=data.get("tags"),
        )


class TelemetryBatch:
    """Represents a batch payload of telemetry metrics for ingestion."""

    def __init__(self, batch_id: str, source_service: str, metrics: Optional[List[TelemetryMetric]] = None):
        self.batch_id: str = batch_id
        self.source_service: str = source_service
        self.metrics: List[TelemetryMetric] = metrics if metrics is not None else []
        self.received_at: float = time.time()

    def add_metric(self, metric: TelemetryMetric) -> None:
        """Appends metric to batch."""
        self.metrics.append(metric)

    def size(self) -> int:
        """Returns count of metrics."""
        return len(self.metrics)

    def get_metrics_by_device(self, device_id: str) -> List[TelemetryMetric]:
        """Filters metrics by specific device."""
        res = []
        for m in self.metrics:
            if m.device_id == device_id:
                res.append(m)
        return res

    def to_dict(self) -> Dict[str, Any]:
        """Serializes batch."""
        return {
            "batch_id": self.batch_id,
            "source_service": self.source_service,
            "metrics": [m.to_dict() for m in self.metrics],
            "received_at": self.received_at,
            "size": len(self.metrics),
        }
