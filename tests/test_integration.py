#!/usr/bin/env python3
"""
End-to-end integration tests using real sample invoices.

Runs the full pipeline (Ingest → Validate → Approve → Pay) on actual
invoice files and asserts stable structural properties.

Uses mock LLM backend (no XAI_API_KEY required).
"""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest  # noqa: E402

from pipeline.runner import run_pipeline  # noqa: E402

# ------------------------------------------------------------------
# Happy path: invoice_1001.txt
# Clean invoice with known items, expected to approve and pay.
# ------------------------------------------------------------------


@pytest.fixture(scope="module")
def happy_result():
    """Run pipeline on a clean invoice (once for all happy-path tests)."""
    return run_pipeline("data/invoices/invoice_1001.txt")


class TestHappyPath:
    """invoice_1001.txt — clean invoice, approved and paid."""

    def test_pipeline_completes_without_errors(self, happy_result):
        """Pipeline should complete with no errors."""
        assert happy_result.errors == []

    def test_invoice_parsed(self, happy_result):
        """Invoice should be fully parsed."""
        inv = happy_result.invoice
        assert inv is not None
        assert inv.vendor == "Widgets Inc."
        assert inv.amount == 5000.0
        assert len(inv.line_items) == 2

    def test_no_validation_findings(self, happy_result):
        """All items are valid — no findings expected."""
        assert happy_result.validation_findings == []

    def test_approved(self, happy_result):
        """Invoice should be approved."""
        ad = happy_result.approval_decision
        assert ad is not None
        assert ad.approved is True
        assert ad.decision_policy == "v1_rule_based"
        assert len(ad.reasons) >= 1

    def test_initial_decision_present(self, happy_result):
        """Initial decision should be captured."""
        ad = happy_result.approval_decision
        assert ad.initial_decision is not None
        assert ad.initial_decision.approved is True
        assert ad.initial_decision.timestamp is not None

    def test_reflection_not_triggered(self, happy_result):
        """No contradictions — reflection should be None."""
        ad = happy_result.approval_decision
        assert ad.reflection is None

    def test_paid(self, happy_result):
        """Approved invoice should be paid."""
        pr = happy_result.payment_result
        assert pr is not None
        assert pr.status == "PAID"
        assert pr.vendor == "Widgets Inc."
        assert pr.amount == 5000.0
        assert pr.payment_reference_id.startswith("TXN-")
        assert pr.timestamp is not None
        assert pr.reason is None


# ------------------------------------------------------------------
# Unhappy path: invoice_1016.json
# Contains WidgetC (unknown item) — expected to reject and skip.
# ------------------------------------------------------------------


@pytest.fixture(scope="module")
def unhappy_result():
    """Run pipeline on an invoice with an unknown item."""
    return run_pipeline("data/invoices/invoice_1016.json")


class TestUnhappyPath:
    """invoice_1016.json — unknown item, rejected and skipped."""

    def test_pipeline_completes_without_errors(self, unhappy_result):
        """Pipeline should complete (rejection is not an error)."""
        assert unhappy_result.errors == []

    def test_invoice_parsed(self, unhappy_result):
        """Invoice should be fully parsed."""
        inv = unhappy_result.invoice
        assert inv is not None
        assert inv.vendor == "Widgets Inc."
        assert inv.amount == 3233.0
        assert len(inv.line_items) == 3

    def test_validation_findings_exist(self, unhappy_result):
        """Should have at least one UNKNOWN_ITEM finding."""
        findings = unhappy_result.validation_findings
        assert len(findings) >= 1

        codes = [f.code for f in findings]
        assert "UNKNOWN_ITEM" in codes

    def test_finding_details(self, unhappy_result):
        """UNKNOWN_ITEM finding should have correct details."""
        finding = next(
            f for f in unhappy_result.validation_findings if f.code == "UNKNOWN_ITEM"
        )
        assert finding.severity == "ERROR"
        assert finding.item_name == "WidgetC"
        assert finding.requested_qty == 3
        assert finding.available_qty is None

    def test_rejected(self, unhappy_result):
        """Invoice should be rejected due to ERROR findings."""
        ad = unhappy_result.approval_decision
        assert ad is not None
        assert ad.approved is False
        assert ad.decision_policy == "v1_rule_based"
        assert any("ERROR" in r for r in ad.reasons)

    def test_initial_decision_present(self, unhappy_result):
        """Initial decision should be captured."""
        ad = unhappy_result.approval_decision
        assert ad.initial_decision is not None
        assert ad.initial_decision.approved is False
        assert ad.initial_decision.timestamp is not None

    def test_reflection_not_triggered(self, unhappy_result):
        """Rejection is correct — no contradiction, no reflection."""
        ad = unhappy_result.approval_decision
        assert ad.reflection is None

    def test_payment_skipped(self, unhappy_result):
        """Rejected invoice should skip payment."""
        pr = unhappy_result.payment_result
        assert pr is not None
        assert pr.status == "SKIPPED"
        assert pr.reason is not None
        assert "rejected" in pr.reason.lower()
        assert pr.payment_reference_id == "N/A"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
