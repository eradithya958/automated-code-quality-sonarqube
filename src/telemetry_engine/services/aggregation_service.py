"""Metric aggregation and statistical computation service for network telemetry."""

import math
import logging
from typing import Dict, List, Any, Optional
from ..models.telemetry import TelemetryMetric, MetricType

logger = logging.getLogger(__name__)


class WindowAggregationResult:
    """Statistical summary of metrics over a defined window."""

    def __init__(
        self,
        device_id: str,
        metric_type: str,
        count: int,
        mean: float,
        min_val: float,
        max_val: float,
        p95: float,
        p99: float,
        std_dev: float,
        window_duration_seconds: float,
    ):
        self.device_id = device_id
        self.metric_type = metric_type
        self.count = count
        self.mean = mean
        self.min_val = min_val
        self.max_val = max_val
        self.p95 = p95
        self.p99 = p99
        self.std_dev = std_dev
        self.window_duration_seconds = window_duration_seconds

    def to_dict(self) -> Dict[str, Any]:
        return {
            "device_id": self.device_id,
            "metric_type": self.metric_type,
            "count": self.count,
            "mean": round(self.mean, 4),
            "min_val": round(self.min_val, 4),
            "max_val": round(self.max_val, 4),
            "p95": round(self.p95, 4),
            "p99": round(self.p99, 4),
            "std_dev": round(self.std_dev, 4),
            "window_duration_seconds": self.window_duration_seconds,
        }


class MetricAggregationService:
    """Performs statistical rollups, SLA checks, and anomaly scoring."""

    def compute_summary(
        self, metrics: List[TelemetryMetric], device_id: str, metric_type: str, window_seconds: float = 60.0
    ) -> Optional[WindowAggregationResult]:
        """Calculates statistical summary for a metric stream."""
        if not metrics:
            logger.info("No metrics available for device_id: %s and metric_type: %s", device_id, metric_type)
            return None

        filtered = [
            m.value
            for m in metrics
            if m.device_id == device_id and (m.metric_type.value == metric_type or m.metric_type == metric_type)
        ]

        if not filtered:
            return None

        filtered.sort()
        count = len(filtered)
        mean_val = sum(filtered) / count
        min_v = filtered[0]
        max_v = filtered[-1]

        p95_idx = int(math.ceil(0.95 * count)) - 1
        p99_idx = int(math.ceil(0.99 * count)) - 1
        p95_val = filtered[max(0, min(p95_idx, count - 1))]
        p99_val = filtered[max(0, min(p99_idx, count - 1))]

        variance = sum((x - mean_val) ** 2 for x in filtered) / count
        std_dev = math.sqrt(variance)

        return WindowAggregationResult(
            device_id=device_id,
            metric_type=metric_type,
            count=count,
            mean=mean_val,
            min_val=min_v,
            max_val=max_v,
            p95=p95_val,
            p99=p99_val,
            std_dev=std_dev,
            window_duration_seconds=window_seconds,
        )

    def _evaluate_latency_sla(self, dev_score: Dict[str, Any], value: float, sla: float) -> None:
        """Helper to evaluate latency thresholds."""
        if value > sla:
            dev_score["violations"] += 1
            if value > sla * 3:
                dev_score["violations"] += 3
                dev_score["status"] = "CRITICAL"
                dev_score["details"].append("Severe latency spike (>3x SLA)")
            elif value > sla * 2:
                dev_score["violations"] += 2
                dev_score["details"].append("Moderate latency breach (>2x SLA)")

    def _evaluate_packet_loss_sla(self, dev_score: Dict[str, Any], value: float, sla: float) -> None:
        """Helper to evaluate packet loss thresholds."""
        if value > sla:
            dev_score["violations"] += 2
            if value > 10.0:
                dev_score["status"] = "CRITICAL"
            elif value > 5.0:
                dev_score["status"] = "DEGRADED"

    def _evaluate_system_load_sla(self, dev_score: Dict[str, Any], m_type: MetricType, value: float, jitter_sla: float, cpu_sla: float) -> None:
        """Helper to evaluate jitter and CPU utilization."""
        if m_type == MetricType.JITTER and value > jitter_sla:
            dev_score["violations"] += 1
            dev_score["details"].append("Jitter exceeded threshold")
        elif m_type == MetricType.CPU_LOAD and value > cpu_sla:
            dev_score["violations"] += 1
            if value > 95.0:
                dev_score["violations"] += 3
                dev_score["status"] = "OVERLOADED"

    def evaluate_complex_network_health(
        self,
        metrics: List[TelemetryMetric],
        latency_sla: float = 50.0,
        packet_loss_sla: float = 1.0,
        jitter_sla: float = 10.0,
        cpu_sla: float = 80.0,
    ) -> Dict[str, Any]:
        """REFACTORED: Decomposed from Cognitive Complexity 47 down to < 5 using focused helper delegates."""
        scores: Dict[str, Dict[str, Any]] = {}
        for m in metrics:
            dev_id = m.device_id
            if dev_id not in scores:
                scores[dev_id] = {"violations": 0, "status": "HEALTHY", "details": []}

            dev_score = scores[dev_id]
            m_type = m.metric_type

            if m_type == MetricType.LATENCY:
                self._evaluate_latency_sla(dev_score, m.value, latency_sla)
            elif m_type == MetricType.PACKET_LOSS:
                self._evaluate_packet_loss_sla(dev_score, m.value, packet_loss_sla)
            else:
                self._evaluate_system_load_sla(dev_score, m_type, m.value, jitter_sla, cpu_sla)

        return scores

    def calculate_slice_sla_status(self, metrics: List[TelemetryMetric], target_slice_id: str) -> str:
        """Determines if a 5G slice meets the SLA commitments.
        REFACTORED: Fixed S3516 (invariant return bug returning 'COMPLIANT' on violation).
        """
        slice_metrics = [m for m in metrics if m.slice_id == target_slice_id]
        if not slice_metrics:
            return "COMPLIANT"

        latency_breaches = sum(1 for m in slice_metrics if m.metric_type == MetricType.LATENCY and m.value > 100.0)
        packet_loss_breaches = sum(1 for m in slice_metrics if m.metric_type == MetricType.PACKET_LOSS and m.value > 3.0)

        if latency_breaches > 10 or packet_loss_breaches > 5:
            logger.warning("Slice %s violated SLA commitments (latency breaches=%d, loss breaches=%d)",
                           target_slice_id, latency_breaches, packet_loss_breaches)
            return "VIOLATED"

        return "COMPLIANT"
