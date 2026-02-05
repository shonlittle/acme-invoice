"""
Approval stage: Simulate VP-level review with reflection/critique loop.

Rule-based logic:
- Invoices over $10K require additional scrutiny
- Validation findings trigger rejection/review
- Reflection loop allows decision revision

TODO: [Slice 5] Implement rule-based approval logic
TODO: [Slice 5] Integrate Grok for decision reasoning
TODO: [Slice 5] Implement reflection/critique loop with revision
"""

from models import ApprovalDecision, PipelineContext
from utils.logging import log_event


def approve_stage(ctx: PipelineContext) -> PipelineContext:
    """
    Simulate VP approval decision with reflection loop.

    Currently a stub - returns context unchanged.

    TODO: [Slice 5] Implement approval logic:
    - Apply rule-based thresholds ($10K, validation findings)
    - Use Grok for decision reasoning (with mock fallback)
    - Implement initial decision
    - Implement reflection/critique loop
    - Allow decision revision based on critique
    - Populate ctx.approval_decision
    """
    log_event("APPROVAL_STARTED", {"invoice": ctx.invoice_path})

    # Stub: No approval logic yet
    log_event("APPROVAL_STUB", {"message": "Approval not implemented yet"})

    return ctx
