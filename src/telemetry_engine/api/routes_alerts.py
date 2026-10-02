"""Alert management and evaluation API endpoints."""

import logging
from typing import Dict, Any, Tuple, Optional
from ..models.alert import AlertRule, AlertSeverity
from ..services.alert_evaluator import AlertEvaluationService
from ..auth.jwt_handler import JWTHandler
from ..auth.permissions import PermissionChecker

logger = logging.getLogger(__name__)


class AlertAPIHandler:
    """Dispatches alert configuration and notification status endpoints."""

    def __init__(self, alert_service: AlertEvaluationService, jwt_handler: JWTHandler):
        self.alert_service = alert_service
        self.jwt_handler = jwt_handler

    def handle_create_rule(self, headers: Dict[str, str], body: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        """Handles POST /api/v1/alerts/rules"""
        auth_header = headers.get("Authorization")
        token = self.jwt_handler.extract_bearer_token(auth_header)
        payload = self.jwt_handler.decode_and_verify(token) if token else None

        if not payload:
            return 401, {"status": "error", "message": "Unauthorized"}

        if not PermissionChecker.has_permission(payload.role, "alerts:write"):
            return 403, {"status": "error", "message": "Forbidden"}

        try:
            severity = AlertSeverity(body.get("severity", AlertSeverity.WARNING.value))
            rule = AlertRule(
                rule_id=body["rule_id"],
                name=body["name"],
                metric_type=body["metric_type"],
                threshold_value=float(body["threshold_value"]),
                operator=body.get("operator", ">"),
                severity=severity,
                enabled=body.get("enabled", True),
                duration_seconds=int(body.get("duration_seconds", 60)),
            )

            self.alert_service.add_rule(rule)
            return 201, {"status": "success", "rule": rule.to_dict()}
        except KeyError as e:
            return 400, {"status": "error", "message": f"Missing field: {str(e)}"}
        except Exception as e:
            logger.error("Alert rule creation error: %s", str(e))
            return 500, {"status": "error", "message": str(e)}

    def handle_list_active_alerts(self) -> Tuple[int, Dict[str, Any]]:
        """Handles GET /api/v1/alerts/active"""
        events = self.alert_service.get_active_events()
        return 200, {
            "status": "success",
            "count": len(events),
            "alerts": [e.to_dict() for e in events],
        }

    def handle_acknowledge_alert(self, event_id: str) -> Tuple[int, Dict[str, Any]]:
        """Handles POST /api/v1/alerts/{event_id}/ack"""
        success = self.alert_service.acknowledge_event(event_id)
        if success:
            return 200, {"status": "success", "message": "Alert acknowledged"}
        return 404, {"status": "error", "message": "Alert event not found"}
