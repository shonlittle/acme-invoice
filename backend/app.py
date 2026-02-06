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


@app.post("/api/run-all")
def run_all_samples():
    """
    Process all sample invoices in data/invoices/.

    Returns a batch result with individual PipelineResults and aggregate summary.
    No persistence — lightweight, in-memory summary.

    Deduplicates invoices by invoice_number, preferring higher-quality formats
    (JSON > CSV > TXT > PDF > XML).
    """
    if not SAMPLES_DIR.exists():
        raise HTTPException(status_code=404, detail="Samples directory not found")

    # Process all files
    all_results = []
    for invoice_file in sorted(SAMPLES_DIR.iterdir()):
        if invoice_file.is_file() and not invoice_file.name.startswith("."):
            result = run_pipeline(str(invoice_file))
            result_dict = asdict(result)
            result_dict["_filename"] = (
                invoice_file.name
            )  # Track filename for deduplication
            all_results.append(result_dict)

    files_processed = len(all_results)

    # Format quality scoring (higher is better)
    def get_format_score(filename: str) -> int:
        ext = Path(filename).suffix.lower()
        scores = {".json": 5, ".csv": 4, ".txt": 3, ".pdf": 2, ".xml": 1}
        return scores.get(ext, 0)

    # Group by invoice_number (with filename fallback for failed parsing)
    # Revisions are treated as separate invoices, not duplicates
    invoice_groups = {}
    for result in all_results:
        invoice = result.get("invoice")
        if invoice and invoice.get("invoice_number"):
            # Primary: group by invoice_number
            inv_num = invoice["invoice_number"]

            # If invoice has a revision, treat it as a separate invoice
            if invoice.get("revision"):
                group_key = f"{inv_num}_rev_{invoice['revision']}"
            else:
                group_key = inv_num

            if group_key not in invoice_groups:
                invoice_groups[group_key] = []
            invoice_groups[group_key].append(result)
        else:
            # Fallback: group by filename pattern
            filename = result["_filename"]
            # Extract base name without extension
            base_name = Path(filename).stem
            group_key = f"_nonum_{base_name}"
            if group_key not in invoice_groups:
                invoice_groups[group_key] = []
            invoice_groups[group_key].append(result)

    # Post-processing: merge filename-based groups with invoice_number groups
    # (e.g., merge "_nonum_invoice_1013" with "INV-1013" if both exist)
    merged_groups = {}
    for group_key, group in invoice_groups.items():
        # Check if this is a filename-based group
        if group_key.startswith("_nonum_"):
            # Extract the base filename (e.g., "invoice_1013" from "_nonum_invoice_1013")
            base_name = group_key.replace("_nonum_", "")

            # Try to find a matching invoice_number group
            # Look for groups that might contain the same invoice number
            merged = False
            for existing_key in list(merged_groups.keys()):
                # Check if the filename contains digits that match the invoice number
                # e.g., "invoice_1013" contains "1013" which matches "INV-1013"
                if not existing_key.startswith("_nonum_"):
                    # Extract digits from both
                    filename_digits = "".join(filter(str.isdigit, base_name))
                    existing_digits = "".join(filter(str.isdigit, existing_key))

                    if filename_digits and filename_digits == existing_digits:
                        # Merge this group into the existing one
                        merged_groups[existing_key].extend(group)
                        merged = True
                        break

            if not merged:
                merged_groups[group_key] = group
        else:
            merged_groups[group_key] = group

    # Deduplicate: keep best format for each invoice
    results = []
    duplicate_groups = []

    for inv_num, group in merged_groups.items():
        if len(group) > 1:
            # Found duplicates — keep best format
            group_sorted = sorted(
                group, key=lambda r: get_format_score(r["_filename"]), reverse=True
            )
            best = group_sorted[0]
            results.append(best)

            # Track duplicate info
            duplicate_groups.append(
                {
                    "invoice_number": inv_num,
                    "files": [r["_filename"] for r in group],
                    "kept": best["_filename"],
                    "reason": (
                        f"Preferred format: "
                        f"{Path(best['_filename']).suffix.upper()}"
                    ),
                }
            )
        else:
            # No duplicates
            results.append(group[0])

    # Remove _filename from results (internal tracking only)
    for r in results:
        r.pop("_filename", None)

    # Compute aggregate summary on deduplicated results
    total = len(results)
    approved = sum(1 for r in results if r.get("approval_decision", {}).get("approved"))
    rejected = total - approved
    revised = sum(
        1 for r in results if r.get("invoice", {}) and r["invoice"].get("revision")
    )

    findings_by_severity = {"ERROR": 0, "WARN": 0, "INFO": 0}
    findings_by_code = {}

    for r in results:
        for finding in r.get("validation_findings", []):
            severity = finding.get("severity", "INFO")
            code = finding.get("code", "unknown")
            findings_by_severity[severity] = findings_by_severity.get(severity, 0) + 1
            findings_by_code[code] = findings_by_code.get(code, 0) + 1

    summary = {
        "total": total,
        "files_processed": files_processed,
        "duplicates_found": len(duplicate_groups),
        "approved": approved,
        "rejected": rejected,
        "revised": revised,
        "approval_rate": round(approved / total * 100, 1) if total > 0 else 0,
        "revision_rate": round(revised / total * 100, 1) if total > 0 else 0,
        "findings_by_severity": findings_by_severity,
        "findings_by_code": findings_by_code,
    }

    return {
        "results": results,
        "summary": summary,
        "duplicate_groups": duplicate_groups,
    }
