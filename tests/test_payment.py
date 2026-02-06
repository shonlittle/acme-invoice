#!/usr/bin/env python3
"""
Unit tests for payment stage.

Tests payment gating, mock payment, and audit trail.
"""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest  # noqa: E402

from agents.pay import mock_payment, pay_stage  # noqa: E402
from models import (  # noqa: E402
    ApprovalDecision,
    InitialDecision,
    Invoice,
    LineItem,
    PipelineContext,
)


def make_test_invoice(
    vendor="Test Vendor",
    amount=1000.0,
    invoice_number="INV-TEST",
):
    """Helper to create test Invoice objects."""
    return Invoice(
        vendor=vendor,
        amount=amount,
        line_items=[LineItem(item="WidgetA", quantity=5)],
        invoice_number=invoice_number,
    )


def make_approval(approved=True, reasons=None):
    """Helper to create test ApprovalDecision objects."""
    if reasons is None:
        reasons = ["Approved: All checks passed"] if approved else ["Rejected: ERROR"]

    return ApprovalDecision(
        approved=approved,
        decision_policy="v1_rule_based",
        reasons=reasons,
        severity_summary={},
        initial_decision=InitialDecision(
            approved=approved,
            reasons=reasons,
            timestamp="2026-01-01T00:00:00",
        ),
        reflection=None,
        final_decision_timestamp=("2026-01-01T00:00:00"),
    )


def test_approved_invoice_pays():
    """Approved invoice should execute payment."""
    invoice = make_test_invoice()
    approval = make_approval(approved=True)

    ctx = PipelineContext(
        invoice_path="test.json",
        invoice=invoice,
        approval_decision=approval,
    )
    ctx = pay_stage(ctx)

    assert ctx.payment_result is not None
    assert ctx.payment_result.status == "PAID"
    assert ctx.payment_result.vendor == "Test Vendor"
    assert ctx.payment_result.amount == 1000.0
    assert ctx.payment_result.payment_reference_id.startswith("TXN-INV-TEST-")
    assert ctx.payment_result.reason is None


def test_rejected_invoice_skips():
    """Rejected invoice should skip payment."""
    invoice = make_test_invoice()
    approval = make_approval(
        approved=False, reasons=["Rejected: 1 ERROR-level validation findings"]
    )

    ctx = PipelineContext(
        invoice_path="test.json",
        invoice=invoice,
        approval_decision=approval,
    )
    ctx = pay_stage(ctx)

    assert ctx.payment_result is not None
    assert ctx.payment_result.status == "SKIPPED"
    assert "rejected" in ctx.payment_result.reason.lower()
    assert ctx.payment_result.payment_reference_id == "N/A"


def test_no_approval_decision_skips():
    """Missing approval decision should skip payment."""
    invoice = make_test_invoice()

    ctx = PipelineContext(
        invoice_path="test.json",
        invoice=invoice,
        approval_decision=None,
    )
    ctx = pay_stage(ctx)

    assert ctx.payment_result is not None
    assert ctx.payment_result.status == "SKIPPED"
    assert "no approval" in ctx.payment_result.reason.lower()


def test_payment_reference_id_format():
    """Payment reference ID should follow stable format."""
    invoice = make_test_invoice(invoice_number="INV-1004")
    approval = make_approval(approved=True)

    ctx = PipelineContext(
        invoice_path="test.json",
        invoice=invoice,
        approval_decision=approval,
    )
    ctx = pay_stage(ctx)

    assert ctx.payment_result.payment_reference_id.startswith("TXN-INV-1004-")
    # Should be TXN-{invoice_id}-{timestamp}
    parts = ctx.payment_result.payment_reference_id.split("-")
    assert len(parts) >= 3


def test_payment_logs_rejection_reason():
    """Skipped payment should include rejection reasons."""
    invoice = make_test_invoice()
    approval = make_approval(
        approved=False,
        reasons=["Rejected: Missing vendor", "Rejected: Zero amount"],
    )

    ctx = PipelineContext(
        invoice_path="test.json",
        invoice=invoice,
        approval_decision=approval,
    )
    ctx = pay_stage(ctx)

    assert ctx.payment_result.status == "SKIPPED"
    assert "Missing vendor" in ctx.payment_result.reason
    assert "Zero amount" in ctx.payment_result.reason


def test_mock_payment_returns_success():
    """Mock payment should return success with transaction ID."""
    result = mock_payment("Test Vendor", 1000.0, "INV-TEST")

    assert result["success"] is True
    assert result["transaction_id"].startswith("TXN-INV-TEST-")
    assert "1000.00" in result["message"]
    assert "Test Vendor" in result["message"]


def test_payment_result_has_timestamp():
    """Payment result should include ISO timestamp."""
    invoice = make_test_invoice()
    approval = make_approval(approved=True)

    ctx = PipelineContext(
        invoice_path="test.json",
        invoice=invoice,
        approval_decision=approval,
    )
    ctx = pay_stage(ctx)

    assert ctx.payment_result.timestamp is not None
    # Should be ISO format
    assert "T" in ctx.payment_result.timestamp


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
