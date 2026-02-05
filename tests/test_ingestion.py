#!/usr/bin/env python3
"""
Unit tests for ingestion stage.

Tests JSON, CSV, and TXT parsers with happy paths and edge cases.
"""

import os
import sys
import tempfile

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from agents.ingest import ingest_stage, parse_csv, parse_json, parse_txt
from models import PipelineContext


def test_json_happy_path():
    """JSON parser: Full invoice with all fields."""
    json_content = """{
  "invoice_number": "INV-TEST",
  "vendor": {
    "name": "Test Vendor",
    "address": "123 Test St"
  },
  "due_date": "2026-03-01",
  "line_items": [
    {"item": "WidgetA", "quantity": 5, "unit_price": 100.00},
    {"item": "WidgetB", "quantity": 3, "unit_price": 200.00}
  ],
  "total": 1100.00
}"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write(json_content)
        temp_path = f.name

    try:
        invoice, metadata = parse_json(temp_path)

        assert invoice.vendor == "Test Vendor"
        assert invoice.amount == 1100.00
        assert invoice.invoice_number == "INV-TEST"
        assert invoice.due_date == "2026-03-01"
        assert len(invoice.line_items) == 2
        assert invoice.line_items[0].item == "WidgetA"
        assert invoice.line_items[0].quantity == 5

        assert metadata.confidence_scores["vendor"] == "HIGH"
        assert metadata.confidence_scores["amount"] == "HIGH"
        assert len(metadata.parse_warnings) == 0
    finally:
        os.remove(temp_path)


def test_json_missing_fields():
    """JSON parser: Missing vendor and total should use defaults with warnings."""
    json_content = """{
  "line_items": [
    {"item": "WidgetA", "quantity": 5}
  ]
}"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write(json_content)
        temp_path = f.name

    try:
        invoice, metadata = parse_json(temp_path)

        assert invoice.vendor == "Unknown"
        assert invoice.amount == 0.0
        assert len(invoice.line_items) == 1

        assert metadata.confidence_scores["vendor"] == "LOW"
        assert metadata.confidence_scores["amount"] == "LOW"
        assert len(metadata.parse_warnings) >= 1
        assert any("missing" in w.lower() for w in metadata.parse_warnings)
    finally:
        os.remove(temp_path)


def test_csv_line_items():
    """CSV parser: Multiple line items with key-value format."""
    csv_content = """field,value
invoice_number,INV-CSV-001
vendor,CSV Vendor Inc
date,2026-01-15
due_date,2026-02-15
item,WidgetA
quantity,10
unit_price,250.00
item,WidgetB
quantity,5
unit_price,500.00
total,5000.00
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write(csv_content)
        temp_path = f.name

    try:
        invoice, metadata = parse_csv(temp_path)

        assert invoice.vendor == "CSV Vendor Inc"
        assert invoice.amount == 5000.00
        assert invoice.invoice_number == "INV-CSV-001"
        assert len(invoice.line_items) == 2
        assert invoice.line_items[0].item == "WidgetA"
        assert invoice.line_items[0].quantity == 10
        assert invoice.line_items[1].item == "WidgetB"

        assert metadata.confidence_scores["vendor"] == "MEDIUM"
        assert metadata.confidence_scores["amount"] == "MEDIUM"
    finally:
        os.remove(temp_path)


def test_csv_missing_total():
    """CSV parser: Missing total field should use 0.0 with warning."""
    csv_content = """field,value
vendor,Test Vendor
item,WidgetA
quantity,5
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write(csv_content)
        temp_path = f.name

    try:
        invoice, metadata = parse_csv(temp_path)

        assert invoice.vendor == "Test Vendor"
        assert invoice.amount == 0.0
        assert len(invoice.line_items) == 1

        assert (
            metadata.confidence_scores["amount"] == "MEDIUM"
        )  # No error, just default
    finally:
        os.remove(temp_path)


def test_txt_regex_extraction():
    """TXT parser: Standard format with all fields."""
    txt_content = """INVOICE

Vendor: TXT Vendor Corp
Invoice Number: INV-TXT-001
Date: 2026-01-20
Due Date: 2026-02-20

Items:
  WidgetA    qty: 8    unit price: $300.00
  WidgetB    qty: 4    unit price: $600.00

Total Amount: $4,800.00
Payment Terms: Net 30
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write(txt_content)
        temp_path = f.name

    try:
        invoice, metadata = parse_txt(temp_path)

        assert invoice.vendor == "TXT Vendor Corp"
        assert invoice.amount == 4800.00
        assert invoice.invoice_number == "INV-TXT-001"
        assert invoice.due_date == "2026-02-20"
        assert len(invoice.line_items) == 2
        assert invoice.line_items[0].item == "WidgetA"
        assert invoice.line_items[0].quantity == 8

        assert metadata.confidence_scores["vendor"] == "MEDIUM"
        assert metadata.confidence_scores["amount"] == "MEDIUM"
        assert len(metadata.parse_warnings) == 0
    finally:
        os.remove(temp_path)


def test_txt_malformed():
    """TXT parser: Missing patterns should use defaults with warnings."""
    txt_content = """Some random text
No structured data here
Just plain text
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write(txt_content)
        temp_path = f.name

    try:
        invoice, metadata = parse_txt(temp_path)

        assert invoice.vendor == "Unknown"
        assert invoice.amount == 0.0
        assert len(invoice.line_items) == 0

        assert metadata.confidence_scores["vendor"] == "LOW"
        assert metadata.confidence_scores["amount"] == "LOW"
        assert len(metadata.parse_warnings) >= 2
    finally:
        os.remove(temp_path)


def test_unsupported_format():
    """Ingest stage: Unsupported file type should error gracefully."""
    xml_content = """<?xml version="1.0"?>
<invoice>
  <vendor>XML Vendor</vendor>
</invoice>
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
        f.write(xml_content)
        temp_path = f.name

    try:
        ctx = PipelineContext(invoice_path=temp_path)
        ctx = ingest_stage(ctx)

        # Should not crash, but return PARSE_ERROR invoice
        assert ctx.invoice is not None
        assert ctx.invoice.vendor == "PARSE_ERROR"
        assert len(ctx.errors) > 0
        assert "Unsupported file type" in ctx.errors[0]
    finally:
        os.remove(temp_path)


def test_ingest_stage_integration():
    """Ingest stage: Full integration test with context."""
    json_content = """{
  "vendor": "Integration Test Vendor",
  "total": 999.99,
  "line_items": [{"item": "TestItem", "quantity": 1}]
}"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write(json_content)
        temp_path = f.name

    try:
        ctx = PipelineContext(invoice_path=temp_path)
        ctx = ingest_stage(ctx)

        assert ctx.invoice is not None
        assert ctx.invoice.vendor == "Integration Test Vendor"
        assert ctx.invoice.amount == 999.99
        assert ctx.parse_metadata is not None
        assert len(ctx.errors) == 0
    finally:
        os.remove(temp_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
