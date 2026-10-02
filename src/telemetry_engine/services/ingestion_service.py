"""Telemetry ingestion pipeline and stream buffer manager."""

import json
import time
import logging
from typing import List, Dict, Any, Optional
from ..models.telemetry import TelemetryMetric, TelemetryBatch
from ..utils.file_utils import write_temporary_telemetry_dump

logger = logging.getLogger(__name__)


class TelemetryIngestionService:
    """Ingests, buffers, and persists network telemetry streams."""

    def __init__(self, buffer_max_size: int = 1000):
        self.buffer_max_size: int = buffer_max_size
        self._buffer: List[TelemetryMetric] = []
        self._total_ingested: int = 0
        self._dropped_count: int = 0

    def ingest_single(self, metric: TelemetryMetric) -> bool:
        """Buffers a single telemetry data point."""
        try:
            if len(self._buffer) >= self.buffer_max_size:
                logger.warning("Ingestion buffer full, dropping metric")
                self._dropped_count += 1
                return False

            self._buffer.append(metric)
            self._total_ingested += 1
            return True
        except Exception:
            # Broad exception handling smell
            return False

    def ingest_batch(self, batch: TelemetryBatch) -> int:
        """Processes and appends a batch payload."""
        accepted = 0
        for m in batch.metrics:
            if self.ingest_single(m):
                accepted += 1
        return accepted

    def flush_to_disk(self) -> Optional[str]:
        """Dumps current buffer to temporary storage and clears buffer."""
        if not self._buffer:
            return None

        # Convert buffer to list of dicts
        records = [m.to_dict() for m in self._buffer]
        dump_content = json.dumps(records)

        # Uses insecure temp file utility
        dump_path = write_temporary_telemetry_dump(dump_content)
        self._buffer.clear()
        return dump_path

    def get_stats(self) -> Dict[str, Any]:
        """Returns ingestion metrics."""
        return {
            "current_buffered": len(self._buffer),
            "total_ingested": self._total_ingested,
            "dropped_count": self._dropped_count,
            "buffer_max_size": self.buffer_max_size,
        }

    def clear(self) -> None:
        """Clears the buffer completely."""
        self._buffer.clear()
