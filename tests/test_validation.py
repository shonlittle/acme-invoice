#!/usr/bin/env python3
"""
Unit tests for validation stage.

Tests all 6 validation rules:
- UNKNOWN_VENDOR (vendor-level)
- SUSPICIOUS_VENDOR (vendor-level)
- UNKNOWN_ITEM (line-item-level)
- NEGATIVE_QTY (line-item-level)
- EXCEEDS_STOCK (line-item-level)
- OUT_OF_STOCK (line-item-level)

Uses in-memory SQLite DB with known test data for determinism.
"""

import os
import sys
import tempfile

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest  # noqa: E402

from agents.validate import validate_stage  # noqa: E402
from db.inventory import init_database  # noqa: E402
from models import Invoice, LineItem, PipelineContext  # noqa: E402

# Known vendor from seed data (trusted)
KNOWN_VENDOR = "Widgets Inc."
# Untrusted vendor from seed data
SUSPICIOUS_VENDOR_NAME = "NoProd Industries"
# Vendor not in DB at all
UNKNOWN_VENDOR_NAME = "Ghost Corp"


def make_test_invoice(
    vendor=KNOWN_VENDOR,
    amount=1000.0,
    line_items=None,
    invoice_number="TEST-001",
):
    """
    Helper to create test Invoice objects without ingestion.

    Args:
        vendor: Vendor name (default: known trusted vendor)
        amount: Total amount
        line_items: List of (item_name, quantity) tuples
        invoice_number: Invoice ID

    Returns:
        Invoice object
    """
    if line_items is None:
        line_items = []

    items = [LineItem(item=name, quantity=qty) for name, qty in line_items]

    return Invoice(
        vendor=vendor,
        amount=amount,
        line_items=items,
        invoice_number=invoice_number,
    )


@pytest.fixture(scope="module")
def test_db():
    """Fixture: Create temporary DB with known inventory for tests."""
    db_file = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    db_path = db_file.name
    db_file.close()

    # Initialize with standard seed data
    # Inventory: WidgetA (15), WidgetB (10), GadgetX (5), FakeItem (0)
    # Vendors: Widgets Inc. (trusted), NoProd Industries (untrusted)
    init_database(db_path)

    yield db_path

    # Cleanup
    os.remove(db_path)


# ------------------------------------------------------------------
# Vendor-level rules
# ------------------------------------------------------------------


def test_unknown_vendor(test_db):
    """UNKNOWN_VENDOR: Vendor not in DB should trigger WARN."""
    invoice = make_test_invoice(
        vendor=UNKNOWN_VENDOR_NAME,
        line_items=[("WidgetA", 1)],
    )

    ctx = PipelineContext(invoice_path="test.txt", invoice=invoice)
    ctx = validate_stage(ctx)

    vendor_findings = [f for f in ctx.validation_findings if f.code == "UNKNOWN_VENDOR"]
    assert len(vendor_findings) == 1

    finding = vendor_findings[0]
    assert finding.severity == "WARN"
    assert finding.item_name == UNKNOWN_VENDOR_NAME
    assert "not found" in finding.message
    assert "vendor database" in finding.message


def test_suspicious_vendor(test_db):
    """SUSPICIOUS_VENDOR: Untrusted vendor should trigger WARN."""
    invoice = make_test_invoice(
        vendor=SUSPICIOUS_VENDOR_NAME,
        line_items=[("WidgetA", 1)],
    )

    ctx = PipelineContext(invoice_path="test.txt", invoice=invoice)
    ctx = validate_stage(ctx)

    vendor_findings = [
        f for f in ctx.validation_findings if f.code == "SUSPICIOUS_VENDOR"
    ]
    assert len(vendor_findings) == 1

    finding = vendor_findings[0]
    assert finding.severity == "WARN"
    assert finding.item_name == SUSPICIOUS_VENDOR_NAME
    assert "untrusted" in finding.message


def test_known_trusted_vendor_no_finding(test_db):
    """Known trusted vendor should produce no vendor findings."""
    invoice = make_test_invoice(
        vendor=KNOWN_VENDOR,
        line_items=[("WidgetA", 1)],
    )

    ctx = PipelineContext(invoice_path="test.txt", invoice=invoice)
    ctx = validate_stage(ctx)

    vendor_findings = [
        f
        for f in ctx.validation_findings
        if f.code in ("UNKNOWN_VENDOR", "SUSPICIOUS_VENDOR")
    ]
    assert len(vendor_findings) == 0


def test_vendor_and_item_findings_combined(test_db):
    """Unknown vendor + unknown item should produce both findings."""
    invoice = make_test_invoice(
        vendor=UNKNOWN_VENDOR_NAME,
        line_items=[("SuperGizmo", 5)],
    )

    ctx = PipelineContext(invoice_path="test.txt", invoice=invoice)
    ctx = validate_stage(ctx)

    codes = [f.code for f in ctx.validation_findings]
    assert "UNKNOWN_VENDOR" in codes
    assert "UNKNOWN_ITEM" in codes
    assert len(ctx.validation_findings) == 2


# ------------------------------------------------------------------
# Line-item-level rules
# ------------------------------------------------------------------


def test_unknown_item(test_db):
    """UNKNOWN_ITEM: Item not in inventory should trigger ERROR."""
    # Not in inventory
    invoice = make_test_invoice(line_items=[("SuperGizmo", 5)])

    ctx = PipelineContext(invoice_path="test.txt", invoice=invoice)
    ctx = validate_stage(ctx)

    item_findings = [f for f in ctx.validation_findings if f.code == "UNKNOWN_ITEM"]
    assert len(item_findings) == 1

    finding = item_findings[0]
    assert finding.severity == "ERROR"
    assert finding.item_name == "SuperGizmo"
    assert finding.requested_qty == 5
    assert finding.available_qty is None
    assert "not found in inventory" in finding.message


def test_negative_quantity(test_db):
    """NEGATIVE_QTY: Quantity < 0 should trigger ERROR."""
    invoice = make_test_invoice(line_items=[("WidgetA", -5)])

    ctx = PipelineContext(invoice_path="test.txt", invoice=invoice)
    ctx = validate_stage(ctx)

    item_findings = [f for f in ctx.validation_findings if f.code == "NEGATIVE_QTY"]
    assert len(item_findings) == 1

    finding = item_findings[0]
    assert finding.severity == "ERROR"
    assert finding.item_name == "WidgetA"
    assert finding.requested_qty == -5
    assert finding.available_qty is None
    assert "Negative quantity" in finding.message


def test_exceeds_stock(test_db):
    """EXCEEDS_STOCK: Requested > available should trigger ERROR."""
    # Only 5 in stock
    invoice = make_test_invoice(line_items=[("GadgetX", 20)])

    ctx = PipelineContext(invoice_path="test.txt", invoice=invoice)
    ctx = validate_stage(ctx)

    item_findings = [f for f in ctx.validation_findings if f.code == "EXCEEDS_STOCK"]
    assert len(item_findings) == 1

    finding = item_findings[0]
    assert finding.severity == "ERROR"
    assert finding.item_name == "GadgetX"
    assert finding.requested_qty == 20
    assert finding.available_qty == 5
    assert "Requested 20, only 5 available" in finding.message


def test_out_of_stock(test_db):
    """OUT_OF_STOCK: Stock == 0 and qty > 0 should trigger ERROR."""
    # Stock is 0
    invoice = make_test_invoice(line_items=[("FakeItem", 3)])

    ctx = PipelineContext(invoice_path="test.txt", invoice=invoice)
    ctx = validate_stage(ctx)

    item_findings = [f for f in ctx.validation_findings if f.code == "OUT_OF_STOCK"]
    assert len(item_findings) == 1

    finding = item_findings[0]
    assert finding.severity == "ERROR"
    assert finding.item_name == "FakeItem"
    assert finding.requested_qty == 3
    assert finding.available_qty == 0
    assert "out of stock" in finding.message


def test_quantity_equals_stock_ok(test_db):
    """Edge case: quantity == stock should pass with no findings."""
    # Exactly 5 in stock, known vendor
    invoice = make_test_invoice(line_items=[("GadgetX", 5)])

    ctx = PipelineContext(invoice_path="test.txt", invoice=invoice)
    ctx = validate_stage(ctx)

    assert len(ctx.validation_findings) == 0


def test_quantity_less_than_stock_ok(test_db):
    """Edge case: quantity < stock should pass with no findings."""
    # 15 available, known vendor
    invoice = make_test_invoice(line_items=[("WidgetA", 10)])

    ctx = PipelineContext(invoice_path="test.txt", invoice=invoice)
    ctx = validate_stage(ctx)

    assert len(ctx.validation_findings) == 0


def test_empty_line_items(test_db):
    """Edge case: No line items with known vendor = no findings."""
    invoice = make_test_invoice(line_items=[])

    ctx = PipelineContext(invoice_path="test.txt", invoice=invoice)
    ctx = validate_stage(ctx)

    assert len(ctx.validation_findings) == 0


def test_multiple_findings(test_db):
    """Multiple violations should generate multiple findings."""
    invoice = make_test_invoice(
        line_items=[
            ("UnknownItem", 5),  # UNKNOWN_ITEM
            ("WidgetA", -2),  # NEGATIVE_QTY
            ("GadgetX", 20),  # EXCEEDS_STOCK (5 available)
            ("FakeItem", 1),  # OUT_OF_STOCK (0 available)
        ]
    )

    ctx = PipelineContext(invoice_path="test.txt", invoice=invoice)
    ctx = validate_stage(ctx)

    # 4 line-item findings (no vendor finding — known vendor)
    assert len(ctx.validation_findings) == 4

    codes = [f.code for f in ctx.validation_findings]
    assert "UNKNOWN_ITEM" in codes
    assert "NEGATIVE_QTY" in codes
    assert "EXCEEDS_STOCK" in codes
    assert "OUT_OF_STOCK" in codes


def test_no_invoice_skips_validation(test_db):
    """Validation should skip gracefully if no invoice parsed."""
    ctx = PipelineContext(invoice_path="test.txt", invoice=None)
    ctx = validate_stage(ctx)

    assert len(ctx.validation_findings) == 0


def test_mixed_valid_invalid_items(test_db):
    """Mix of valid and invalid items should only flag invalid ones."""
    invoice = make_test_invoice(
        line_items=[
            ("WidgetA", 5),  # Valid
            ("UnknownItem", 3),  # UNKNOWN_ITEM
            ("WidgetB", 8),  # Valid
        ]
    )

    ctx = PipelineContext(invoice_path="test.txt", invoice=invoice)
    ctx = validate_stage(ctx)

    # Only 1 finding: UNKNOWN_ITEM (vendor is known)
    assert len(ctx.validation_findings) == 1
    assert ctx.validation_findings[0].code == "UNKNOWN_ITEM"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
