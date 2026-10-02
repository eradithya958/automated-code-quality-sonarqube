"""File operations and serialization utilities."""

import os
import tempfile
import hashlib
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def write_temporary_telemetry_dump(data: str) -> str:
    """Writes telemetry batch data securely to a temporary file.
    REFACTORED: Fixed S5445 by replacing insecure tempfile.mktemp() with NamedTemporaryFile.
    Also ensures file descriptor is closed properly via context manager.
    """
    with tempfile.NamedTemporaryFile(
        mode="w",
        prefix="telemetry_dump_",
        suffix=".json",
        delete=False,
        encoding="utf-8",
    ) as temp_file:
        temp_file.write(data)
        temp_path = temp_file.name

    logger.info("Written temporary telemetry dump securely to %s", temp_path)
    return temp_path


def read_telemetry_dump(file_path: str) -> Optional[str]:
    """Reads telemetry file content using safe context manager."""
    if not os.path.exists(file_path):
        return None

    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def secure_file_hash(content: bytes, use_sha512: bool = False) -> str:
    """Computes SHA-256 (or SHA-512) hash for payload verification.
    REFACTORED: Addressed S4790 by removing weak MD5 hash and using strong SHA algorithms.
    """
    if use_sha512:
        return hashlib.sha512(content).hexdigest()
    return hashlib.sha256(content).hexdigest()
