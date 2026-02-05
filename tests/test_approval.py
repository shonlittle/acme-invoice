#!/usr/bin/env python3
"""
Unit tests for approval stage.

Tests policy rules, reflection logic, and LLM backend integration.
"""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from agents.approve import approve_stage, check_contradictions, make_initial_decision
from models import (
    InitialDecision,
    Invoice,
    LineItem,
    PipelineContext,
    ValidationFinding,
)


def make_test_invoice(vendor="Test Vendor", amount=1000.0, line_items=None):
    """Helper to create test Invoice objects."""
    if line_items is None:
        line_items = []

    items = [LineItem(item=name, quantity=qty) for name, qty in line_items]

    return Invoice(
        vendor=vendor,
        amount=amount,
        line_items=items,
        invoice_number="TEST-001",
    )


def test_error_finding_rejects():
    """ERROR findings should trigger rejection."""
    invoice = make_test_invoice(line_items=[("WidgetA", 5)])
    findings = [
        ValidationFinding(
            code="UNKNOWN_ITEM",
            severity="ERROR",
            message="Item not found",
            item_name="UnknownItem",
        )
    ]

    decision = make_initial_decision(invoice, findings)

    assert decision.approved is False
    assert any("ERROR-level" in r for r in decision.reasons)
    assert any("1 ERROR" in r for r in decision.reasons)


def test_high_value_scrutiny():
    """Amount > $10K should add scrutiny reason."""
    invoice = make_test_invoice(amount=15000.0, line_items=[("WidgetA", 5)])
    findings = []

    decision = make_initial_decision(invoice, findings)

    assert decision.approved is True  # Doesn't auto-reject
    assert any("scrutiny" in r.lower() for r in decision.reasons)
    assert any("15,000" in r for r in decision.reasons)


def test_missing_vendor_rejects():
    """Missing vendor should reject."""
    invoice = make_test_invoice(vendor="Unknown", line_items=[("WidgetA", 5)])
    findings = []

    decision = make_initial_decision(invoice, findings)

    assert decision.approved is False
    assert any("vendor" in r.lower() for r in decision.reasons)


def test_missing_amount_rejects():
    """Missing or zero amount should reject."""
    invoice = make_test_invoice(amount=0.0, line_items=[("WidgetA", 5)])
    findings = []

    decision = make_initial_decision(invoice, findings)

    assert decision.approved is False
    assert any("amount" in r.lower() for r in decision.reasons)


def test_clean_invoice_approves():
    """Clean invoice with no errors should approve."""
    invoice = make_test_invoice(
        vendor="Valid Vendor", amount=5000.0, line_items=[("WidgetA", 5)]
    )
    findings = []

    decision = make_initial_decision(invoice, findings)

    assert decision.approved is True
    assert any("passed" in r.lower() for r in decision.reasons)


def test_contradiction_approved_despite_errors():
    """Reflection should detect approval despite ERROR findings."""
    invoice = make_test_invoice(line_items=[("WidgetA", 5)])
    findings = [
        ValidationFinding(
            code="UNKNOWN_ITEM", severity="ERROR", message="Item not found"
        )
    ]

    # Manually create contradictory initial decision
    initial_decision = InitialDecision(
        approved=True,  # Contradicts ERROR finding
        reasons=["Approved by mistake"],
        timestamp="2026-01-01T00:00:00",
    )

    has_contradiction, critique = check_contradictions(
        initial_decision, findings, invoice
    )

    assert has_contradiction is True
    assert "approved despite" in critique.lower()
    assert "error" in critique.lower()


def test_contradiction_missing_scrutiny():
    """Reflection should detect missing high-value scrutiny flag."""
    invoice = make_test_invoice(amount=15000.0, line_items=[("WidgetA", 5)])
    findings = []

    initial_decision = InitialDecision(
        approved=True,
        reasons=["Approved"],  # Missing scrutiny flag
        timestamp="2026-01-01T00:00:00",
    )

    has_contradiction, critique = check_contradictions(
        initial_decision, findings, invoice
    )

    assert has_contradiction is True
    assert "scrutiny" in critique.lower()


def test_no_contradiction_clean_approval():
    """Clean approval should have no contradictions."""
    invoice = make_test_invoice(amount=5000.0, line_items=[("WidgetA", 5)])
    findings = []

    initial_decision = InitialDecision(
        approved=True,
        reasons=["Approved: All validation checks passed"],
        timestamp="2026-01-01T00:00:00",
    )

    has_contradiction, critique = check_contradictions(
        initial_decision, findings, invoice
    )

    assert has_contradiction is False
    assert critique == ""


def test_approval_stage_integration():
    """Full approval stage integration test."""
    invoice = make_test_invoice(
        vendor="Test Vendor", amount=5000.0, line_items=[("WidgetA", 5)]
    )

    ctx = PipelineContext(invoice_path="test.json", invoice=invoice)
    ctx = approve_stage(ctx)

    assert ctx.approval_decision is not None
    assert ctx.approval_decision.approved is True
    assert ctx.approval_decision.decision_policy == "v1_rule_based"
    assert len(ctx.approval_decision.reasons) > 0
    assert ctx.approval_decision.initial_decision is not None
    assert ctx.approval_decision.final_decision_timestamp is not None


def test_mock_backend_deterministic():
    """Mock backend should be deterministic."""
    # Create a client without API key by directly instantiating
    # (bypass .env loading for this test)
    from llm.client import LLMClient

    # Save and clear env var
    original_key = os.environ.get("XAI_API_KEY")
    if "XAI_API_KEY" in os.environ:
        del os.environ["XAI_API_KEY"]

    try:
        # Create client - should use mock backend
        client = LLMClient()

        # If .env was already loaded, manually override
        if client.backend == "grok":
            client.backend = "mock"
            client.api_key = None

        messages = [{"role": "user", "content": "Test message"}]
        response1 = client.chat_completion(messages)
        response2 = client.chat_completion(messages)

        assert response1 == response2  # Deterministic
        assert "Approved" in response1  # Expected mock response
    finally:
        # Restore original key
        if original_key:
            os.environ["XAI_API_KEY"] = original_key


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
