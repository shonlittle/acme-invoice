"""
Ingestion stage: Extract structured data from invoice files.

Supports multiple formats:
- JSON (.json)
- CSV (.csv)
- TXT (.txt)
- PDF (.pdf)

TODO: [Slice 4] Implement JSON/CSV/TXT parsing logic
TODO: [Slice 7] Implement PDF text extraction
"""

from models import Invoice, PipelineContext
from utils.logging import log_error, log_event


def ingest_stage(ctx: PipelineContext) -> PipelineContext:
    """
    Extract structured invoice data from the input file.

    Currently a stub - returns context unchanged.

    TODO: [Slice 4] Implement actual parsing:
    - Detect file format from extension
    - Parse JSON/CSV/TXT with format-specific logic
    - Handle missing/malformed data gracefully
    - Populate ctx.invoice with extracted Invoice object
    - Add errors to ctx.errors on failure
    """
    log_event("INGEST_STARTED", {"path": ctx.invoice_path})

    # Stub: No parsing yet
    log_event("INGEST_STUB", {"message": "Parsing not implemented yet"})

    return ctx
