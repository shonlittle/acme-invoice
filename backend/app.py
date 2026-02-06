"""
FastAPI backend for the Acme Invoice Processing Pipeline.

Thin wrapper over the existing pipeline runner.
Does not modify core business logic.

Run:
    uvicorn backend.app:app --reload --port 8000
"""

import os
import tempfile
from dataclasses import asdict
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from backend.schemas import (
    HealthResponse,
    ProcessSampleRequest,
    SampleFile,
    SamplesResponse,
)
from pipeline.runner import run_pipeline

app = FastAPI(
    title="Acme Invoice API",
    description="Web API for the invoice processing pipeline",
    version="1.0.0",
)

# CORS for local React dev servers
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SAMPLES_DIR = Path("data/invoices")


@app.get("/api/health", response_model=HealthResponse)
def health():
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/api/samples", response_model=SamplesResponse)
def list_samples():
    """List available sample invoice files."""
    if not SAMPLES_DIR.exists():
        return {"samples": []}

    samples = []
    for f in sorted(SAMPLES_DIR.iterdir()):
        if f.is_file() and not f.name.startswith("."):
            samples.append(
                SampleFile(
                    filename=f.name,
                    path=str(f),
                )
            )

    return {"samples": samples}


@app.post("/api/process")
async def process_upload(file: UploadFile):
    """
    Process an uploaded invoice file.

    Accepts multipart/form-data with a single file.
    Saves to a temp file, runs the pipeline, returns result JSON.
    """
    # Determine file extension from original filename
    suffix = Path(file.filename).suffix if file.filename else ".txt"

    # Save upload to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, dir=".") as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        result = run_pipeline(tmp_path)
        return asdict(result)
    finally:
        # Clean up temp file
        os.unlink(tmp_path)


@app.post("/api/process-sample")
def process_sample(req: ProcessSampleRequest):
    """
    Process a sample invoice by filename.

    Resolves the filename to data/invoices/<sample_name>.
    Validates the path is safe (no directory traversal).
    """
    # Sanitize: only allow simple filenames
    if "/" in req.sample_name or "\\" in req.sample_name:
        raise HTTPException(
            status_code=400,
            detail="Invalid sample name: must be a simple filename",
        )

    invoice_path = SAMPLES_DIR / req.sample_name

    # Verify the resolved path is still under SAMPLES_DIR
    try:
        invoice_path.resolve().relative_to(SAMPLES_DIR.resolve())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid sample name: path traversal detected",
        )

    if not invoice_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Sample not found: {req.sample_name}",
        )

    result = run_pipeline(str(invoice_path))
    return asdict(result)
