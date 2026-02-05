"""
Approval stage: Simulate VP-level review with reflection/critique loop.

Policy rules (v1_rule_based):
- ERROR findings → Reject
- Amount > $10K → Extra scrutiny flag
- Missing vendor/amount → Reject
- Otherwise → Approve

Reflection loop detects contradictions and can revise decisions.
Optional Grok integration for LLM-based reasoning (falls back to mock).
"""

from datetime import datetime
from typing import List, Tuple

from llm.client import LLMClient
from models import (
    ApprovalDecision,
    InitialDecision,
    Invoice,
    PipelineContext,
    ReflectionResult,
    ValidationFinding,
)
from utils.logging import log_event


def make_initial_decision(
    invoice: Invoice, validation_findings: List[ValidationFinding]
) -> InitialDecision:
    """
    Apply policy rules to make initial approval decision.

    Policy v1_rule_based:
    1. ERROR findings → Reject
    2. Missing vendor/amount → Reject
    3. Amount > $10K → Add scrutiny flag (doesn't auto-reject)
    4. Otherwise → Approve
    """
    reasons = []
    approved = True

    # Count validation findings by severity
    error_count = sum(1 for f in validation_findings if f.severity == "ERROR")

    # Rule 1: ERROR findings → Reject
    if error_count > 0:
        approved = False
        reasons.append(f"Rejected: {error_count} ERROR-level validation findings")

    # Rule 2: Missing critical fields → Reject
    if invoice.vendor in ["Unknown", "PARSE_ERROR", ""]:
        approved = False
        reasons.append("Rejected: Missing or invalid vendor information")

    if invoice.amount == 0.0:
        approved = False
        reasons.append("Rejected: Missing or invalid total amount")

    # Rule 3: High value → Extra scrutiny (doesn't reject)
    if invoice.amount > 10000:
        reasons.append(
            f"High-value invoice (${invoice.amount:,.2f}) requires extra scrutiny"
        )

    # Rule 4: Otherwise approve
    if approved and not reasons:
        reasons.append("Approved: All validation checks passed")

    return InitialDecision(
        approved=approved, reasons=reasons, timestamp=datetime.utcnow().isoformat()
    )


def check_contradictions(
    initial_decision: InitialDecision,
    validation_findings: List[ValidationFinding],
    invoice: Invoice,
) -> Tuple[bool, str]:
    """
    Detect logical contradictions in the initial decision.

    Returns: (has_contradiction: bool, critique_notes: str)
    """
    contradictions = []

    # Check 1: Approved despite ERROR findings
    error_count = sum(1 for f in validation_findings if f.severity == "ERROR")
    if initial_decision.approved and error_count > 0:
        contradictions.append(
            f"Approved despite {error_count} ERROR findings - policy violation"
        )

    # Check 2: Rejected without clear reason
    if not initial_decision.approved and not initial_decision.reasons:
        contradictions.append("Rejected without providing reasons")

    # Check 3: Missing high-value flag
    if invoice.amount > 10000:
        has_scrutiny = any("scrutiny" in r.lower() for r in initial_decision.reasons)
        if not has_scrutiny:
            contradictions.append(
                f"High-value invoice (${invoice.amount:,.2f}) missing scrutiny flag"
            )

    return (len(contradictions) > 0, "; ".join(contradictions))


def reflect_and_revise(
    initial_decision: InitialDecision,
    critique_notes: str,
    validation_findings: List[ValidationFinding],
    llm_client: LLMClient,
) -> ReflectionResult:
    """
    Use LLM to reflect on contradictions and potentially revise decision.

    Returns ReflectionResult with revised decision if needed.
    """
    # Build reflection prompt
    error_count = sum(1 for f in validation_findings if f.severity == "ERROR")
    prompt = f"""Review this approval decision for contradictions:

Initial Decision: {"Approved" if initial_decision.approved else "Rejected"}
Reasons: {', '.join(initial_decision.reasons)}
Validation Errors: {error_count}

Contradictions Found: {critique_notes}

Provide revised reasoning if needed."""

    messages = [{"role": "user", "content": prompt}]

    # Get LLM response
    llm_response = llm_client.chat_completion(messages)

    # Determine if revision is needed
    revised = "REVISED:" in llm_response.upper()

    revised_reasons = None
    if revised:
        # Extract revised reasoning from LLM response
        revised_reasons = [llm_response.strip()]

    return ReflectionResult(
        critique_notes=critique_notes,
        revised=revised,
        llm_backend=llm_client.backend,
        revised_reasons=revised_reasons,
    )


def approve_stage(ctx: PipelineContext) -> PipelineContext:
    """
    Simulate VP approval decision with reflection loop.

    Implements policy v1_rule_based with contradiction detection
    and optional LLM-based reflection.
    """
    # Skip if no invoice
    if ctx.invoice is None:
        log_event("APPROVAL_SKIPPED", {"reason": "No invoice data"})
        return ctx

    log_event(
        "APPROVAL_START",
        {
            "invoice_id": ctx.invoice.invoice_number,
            "vendor": ctx.invoice.vendor,
            "amount": ctx.invoice.amount,
            "validation_findings_count": len(ctx.validation_findings),
        },
    )

    # Step 1: Make initial decision based on policy rules
    initial_decision = make_initial_decision(ctx.invoice, ctx.validation_findings)

    # Calculate severity summary
    severity_summary = {}
    for finding in ctx.validation_findings:
        severity_summary[finding.severity] = (
            severity_summary.get(finding.severity, 0) + 1
        )

    log_event(
        "APPROVAL_INITIAL_DECISION",
        {
            "approved": initial_decision.approved,
            "reasons": initial_decision.reasons,
            "policy": "v1_rule_based",
            "thresholds_triggered": (
                ["high_value"] if ctx.invoice.amount > 10000 else []
            ),
        },
    )

    # Step 2: Check for contradictions
    has_contradiction, critique_notes = check_contradictions(
        initial_decision, ctx.validation_findings, ctx.invoice
    )

    reflection = None
    final_approved = initial_decision.approved
    final_reasons = initial_decision.reasons

    # Step 3: Reflect and revise if contradictions found
    if has_contradiction:
        llm_client = LLMClient()
        reflection = reflect_and_revise(
            initial_decision, critique_notes, ctx.validation_findings, llm_client
        )

        log_event(
            "APPROVAL_REFLECTION",
            {
                "backend": reflection.llm_backend,
                "revised": reflection.revised,
                "critique_summary": critique_notes[:100],
            },
        )

        # Apply revisions if any
        if reflection.revised and reflection.revised_reasons:
            # Revise based on LLM feedback
            if "reject" in reflection.revised_reasons[0].lower():
                final_approved = False
            final_reasons = reflection.revised_reasons

    # Step 4: Create final approval decision
    final_timestamp = datetime.utcnow().isoformat()

    ctx.approval_decision = ApprovalDecision(
        approved=final_approved,
        decision_policy="v1_rule_based",
        reasons=final_reasons,
        severity_summary=severity_summary,
        initial_decision=initial_decision,
        reflection=reflection,
        final_decision_timestamp=final_timestamp,
    )

    log_event(
        "APPROVAL_FINAL_DECISION",
        {
            "approved": final_approved,
            "reasons": final_reasons,
            "timestamp": final_timestamp,
        },
    )

    return ctx
