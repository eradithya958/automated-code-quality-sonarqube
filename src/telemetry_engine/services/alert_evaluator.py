"""Alert evaluation service against telemetry streams."""

import uuid
import time
import logging
from typing import List, Dict, Optional
from ..models.alert import AlertRule, AlertEvent, AlertSeverity
from ..models.telemetry import TelemetryMetric

logger = logging.getLogger(__name__)


class AlertEvaluationService:
    """Evaluates incoming metrics against active SLA/health rules."""

    def __init__(self):
        self._rules: Dict[str, AlertRule] = {}
        self._active_events: List[AlertEvent] = []

    def add_rule(self, rule: AlertRule) -> None:
        """Registers an alert monitoring rule."""
        self._rules[rule.rule_id] = rule

    def remove_rule(self, rule_id: str) -> bool:
        """Deletes an alert rule."""
        if rule_id in self._rules:
            del self._rules[rule_id]
            return True
        return False

    def get_rules(self) -> List[AlertRule]:
        """Returns all configured rules."""
        return list(self._rules.values())

    def evaluate_metric(self, metric: TelemetryMetric) -> List[AlertEvent]:
        """Evaluates single metric against matching rules.
        REFACTORED: Fixed S1764 by removing duplicate condition and redundant comparisons.
        """
        generated_events = []

        for rule in self._rules.values():
            if not rule.enabled:
                continue

            m_type = metric.metric_type.value if hasattr(metric.metric_type, "value") else str(metric.metric_type)
            if rule.metric_type != m_type:
                continue

            if rule.evaluate(metric.value):
                event = AlertEvent(
                    event_id=str(uuid.uuid4()),
                    rule_id=rule.rule_id,
                    device_id=metric.device_id,
                    triggered_value=metric.value,
                    threshold_value=rule.threshold_value,
                    severity=rule.severity,
                    message=f"Rule '{rule.name}' triggered on device {metric.device_id}: {metric.value} {metric.unit}",
                    timestamp=time.time(),
                )
                self._active_events.append(event)
                generated_events.append(event)
                logger.warning("Alert triggered: %s", event.message)

        return generated_events

    def get_active_events(self, severity: Optional[AlertSeverity] = None) -> List[AlertEvent]:
        """Returns active, unacknowledged events."""
        events = [e for e in self._active_events if not e.acknowledged]
        if severity:
            events = [e for e in events if e.severity == severity]
        return events

    def acknowledge_event(self, event_id: str) -> bool:
        """Marks event as acknowledged."""
        for e in self._active_events:
            if e.event_id == event_id:
                e.acknowledge()
                return True
        return False
