"""
Payment stage: Execute payment or log rejection.

Mock payment function:
- If approved: call mock_payment(vendor, amount)
- If rejected: log rejection with reasoning

TODO: [Slice 6] Implement mock_payment function
TODO: [Slice 6] Implement payment gating logic
TODO: [Slice 6] Add rejection logging
"""

from models import PipelineContext
from utils.logging import log_event


def mock_payment(vendor: str, amount: float) -> dict:
    """
    Mock payment function.

    TODO: [Slice 6] Implement actual mock payment logic
    - Print payment confirmation
    - Return success status dict
    """
    return {"status": "not_implemented"}


def pay_stage(ctx: PipelineContext) -> PipelineContext:
    """
    Execute payment if approved, otherwise log rejection.

    Currently a stub - returns context unchanged.

    TODO: [Slice 6] Implement payment logic:
    - Check ctx.approval_decision.approved
    - If approved: call mock_payment and populate ctx.payment_result
    - If rejected: log rejection with ctx.approval_decision.reasoning
    - Handle missing approval decision gracefully
    """
    log_event("PAYMENT_STARTED", {"invoice": ctx.invoice_path})

    # Stub: No payment logic yet
    log_event("PAYMENT_STUB", {"message": "Payment not implemented yet"})

    return ctx
