#!/usr/bin/env python3
"""
Smoke tests for the FastAPI backend.

Tests all 4 API endpoints using FastAPI TestClient.
"""

import io
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from backend.app import app  # noqa: E402

client = TestClient(app)


def test_health():
    """GET /api/health returns status ok."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_list_samples():
    """GET /api/samples returns non-empty list of invoice files."""
    response = client.get("/api/samples")
    assert response.status_code == 200
    data = response.json()
    assert "samples" in data
    assert len(data["samples"]) > 0

    # Each sample should have filename and path
    sample = data["samples"][0]
    assert "filename" in sample
    assert "path" in sample


def test_process_sample_happy_path():
    """POST /api/process-sample with valid invoice returns pipeline result."""
    response = client.post(
        "/api/process-sample",
        json={"sample_name": "invoice_1001.txt"},
    )
    assert response.status_code == 200
    data = response.json()

    # Verify pipeline result structure
    assert "invoice_path" in data
    assert "invoice" in data
    assert "validation_findings" in data
    assert "approval_decision" in data
    assert "payment_result" in data
    assert "errors" in data

    # This invoice should be approved and paid
    assert data["invoice"]["vendor"] == "Widgets Inc."
    assert data["approval_decision"]["approved"] is True
    assert data["payment_result"]["status"] == "PAID"
    assert data["errors"] == []


def test_process_sample_not_found():
    """POST /api/process-sample with nonexistent file returns 404."""
    response = client.post(
        "/api/process-sample",
        json={"sample_name": "nonexistent_invoice.txt"},
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_process_sample_path_traversal():
    """POST /api/process-sample rejects path traversal attempts."""
    response = client.post(
        "/api/process-sample",
        json={"sample_name": "../main.py"},
    )
    assert response.status_code == 400


def test_process_upload():
    """POST /api/process with file upload returns pipeline result."""
    # Create a simple invoice file in memory
    invoice_content = b"""INVOICE

Vendor: Widgets Inc.
Invoice Number: INV-TEST
Date: 2026-01-15
Due Date: 2026-02-01

Items:
  WidgetA    qty: 2    unit price: $250.00

Total Amount: $500.00
"""
    response = client.post(
        "/api/process",
        files={"file": ("test_invoice.txt", io.BytesIO(invoice_content), "text/plain")},
    )
    assert response.status_code == 200
    data = response.json()

    assert "invoice" in data
    assert "errors" in data
    assert data["invoice"] is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
