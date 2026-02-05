"""
Structured logging utilities for pipeline observability.

Each stage emits structured log events:
- STAGE_START / STAGE_END
- INGEST_PARSED
- VALIDATION_FINDINGS
- APPROVAL_INITIAL_DECISION
- APPROVAL_REFLECTION
- PAYMENT_ATTEMPT / PAYMENT_RESULT
"""

import json
import logging
from typing import Any, Dict

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger("invoice_pipeline")


def log_stage_start(stage_name: str) -> None:
    """Log the start of a pipeline stage."""
    logger.info(f"{'='*60}")
    logger.info(f"STAGE_START: {stage_name}")
    logger.info(f"{'='*60}")


def log_stage_end(stage_name: str) -> None:
    """Log the end of a pipeline stage."""
    logger.info(f"STAGE_END: {stage_name}")
    logger.info(f"{'='*60}\n")


def log_event(event_type: str, data: Dict[str, Any]) -> None:
    """
    Log a structured event with JSON payload.

    Examples:
    - log_event("INGEST_PARSED", {"vendor": "Widgets Inc.", "amount": 5000.00})
    - log_event("VALIDATION_FINDINGS", {"count": 3, "critical": 1})
    """
    logger.info(f"{event_type}: {json.dumps(data, indent=2)}")


def log_error(message: str, exception: Exception = None) -> None:
    """Log an error with optional exception details."""
    if exception:
        logger.error(f"ERROR: {message} - {str(exception)}")
    else:
        logger.error(f"ERROR: {message}")
