"""
Pydantic request/response schemas for the FastAPI backend.
"""

from pydantic import BaseModel


class ProcessSampleRequest(BaseModel):
    """Request body for POST /api/process-sample."""

    sample_name: str  # e.g. "invoice_1001.txt"


class HealthResponse(BaseModel):
    """Response for GET /api/health."""

    status: str


class SampleFile(BaseModel):
    """A single sample invoice file."""

    filename: str
    path: str


class SamplesResponse(BaseModel):
    """Response for GET /api/samples."""

    samples: list[SampleFile]
