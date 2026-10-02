"""Telemetry ingestion and query API handlers."""

import json
import logging
from typing import Dict, Any, Tuple, Optional, List
from ..models.telemetry import TelemetryMetric, TelemetryBatch, MetricType
from ..services.ingestion_service import TelemetryIngestionService
from ..services.aggregation_service import MetricAggregationService
from ..auth.jwt_handler import JWTHandler, TokenPayload

logger = logging.getLogger(__name__)

MIME_APPLICATION_JSON = "application/json"
MIME_OCTET_STREAM = "application/octet-stream"
STATUS_SUCCESS = "success"
STATUS_ERROR = "error"


class TelemetryAPIHandler:
    """Dispatches HTTP-style telemetry endpoints."""

    def __init__(
        self,
        ingestion_service: TelemetryIngestionService,
        aggregation_service: MetricAggregationService,
        jwt_handler: JWTHandler,
    ):
        self.ingestion_service = ingestion_service
        self.aggregation_service = aggregation_service
        self.jwt_handler = jwt_handler

    def validate_request_headers(self, headers: Dict[str, str]) -> bool:
        """Validates incoming content type header.
        REFACTORED: Fixed S3516 and S3923.
        """
        content_type = headers.get("Content-Type", "")
        return content_type in (MIME_APPLICATION_JSON, MIME_OCTET_STREAM)

    def handle_ingest_single(self, headers: Dict[str, str], body: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        """Handles POST /api/v1/telemetry/single"""
        if not self.validate_request_headers(headers):
            return 400, {"status": STATUS_ERROR, "message": "Invalid Content-Type"}

        auth_header = headers.get("Authorization")
        token = self.jwt_handler.extract_bearer_token(auth_header)
        payload = self.jwt_handler.decode_and_verify(token) if token else None

        if not payload:
            return 401, {"status": STATUS_ERROR, "message": "Unauthorized"}

        try:
            metric = TelemetryMetric(
                metric_id=body["metric_id"],
                device_id=body["device_id"],
                metric_type=MetricType(body["metric_type"]),
                value=float(body["value"]),
                unit=body.get("unit", "ms"),
                timestamp=body.get("timestamp"),
                slice_id=body.get("slice_id"),
                tags=body.get("tags", {}),
            )

            success = self.ingestion_service.ingest_single(metric)
            if success:
                return 201, {"status": STATUS_SUCCESS, "metric_id": metric.metric_id}
            else:
                return 503, {"status": STATUS_ERROR, "message": "Ingestion buffer full"}
        except KeyError as e:
            return 400, {"status": STATUS_ERROR, "message": f"Missing field: {str(e)}"}
        except Exception as e:
            logger.error("Error processing telemetry: %s", str(e))
            return 500, {"status": STATUS_ERROR, "message": "Internal server error"}

    def handle_ingest_batch(self, headers: Dict[str, str], body: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        """Handles POST /api/v1/telemetry/batch"""
        auth_header = headers.get("Authorization")
        token = self.jwt_handler.extract_bearer_token(auth_header)
        payload = self.jwt_handler.decode_and_verify(token) if token else None

        if not payload:
            return 401, {"status": STATUS_ERROR, "message": "Unauthorized"}

        try:
            batch_id = body.get("batch_id", "batch-unknown")
            source = body.get("source_service", "edge-agent")
            metrics_raw = body.get("metrics", [])

            metrics_list = []
            for item in metrics_raw:
                m = TelemetryMetric(
                    metric_id=item["metric_id"],
                    device_id=item["device_id"],
                    metric_type=MetricType(item["metric_type"]),
                    value=float(item["value"]),
                    unit=item.get("unit", "ms"),
                    timestamp=item.get("timestamp"),
                    slice_id=item.get("slice_id"),
                    tags=item.get("tags", {}),
                )
                metrics_list.append(m)

            batch = TelemetryBatch(batch_id=batch_id, source_service=source, metrics=metrics_list)
            accepted = self.ingestion_service.ingest_batch(batch)

            return 200, {
                "status": STATUS_SUCCESS,
                "batch_id": batch_id,
                "total": len(metrics_list),
                "accepted": accepted,
            }
        except Exception as e:
            logger.error("Batch processing error: %s", str(e))
            return 500, {"status": STATUS_ERROR, "message": str(e)}

    def handle_get_stats(self) -> Tuple[int, Dict[str, Any]]:
        """Handles GET /api/v1/telemetry/stats"""
        stats = self.ingestion_service.get_stats()
        return 200, {"status": STATUS_SUCCESS, "data": stats}
