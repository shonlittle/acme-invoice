"""
Payment stage: Execute payment or log rejection.

Mock payment function:
- If approved: call mock_payment(vendor, amount)
- If rejected: log rejection with reasoning

Implements payment gating, audit trail, and lightweight idempotency.
"""

from datetime import datetime

from models import PaymentResult, PipelineContext
from utils.logging import log_event


def mock_payment(vendor: str, amount: float, invoice_id: str) -> dict:
    """
    Mock payment function (deterministic for MVP).

    In production, this would call a real banking API.
    For now, always returns success.

    Args:
        vendor: Vendor name
        amount: Payment amount
        invoice_id: Invoice identifier

    Returns:
        dict with success, transaction_id, message
    """
    print(f"💰 MOCK PAYMENT: ${amount:.2f} to {vendor}")

    transaction_id = f"TXN-{invoice_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

    return {
        "success": True,
        "transaction_id": transaction_id,
        "message": f"Payment of ${amount:.2f} to {vendor} processed successfully",
    }


def pay_stage(ctx: PipelineContext) -> PipelineContext:
    """
    Execute payment if approved, otherwise skip with reason.

    Payment gating:
    - Requires approval_decision to exist
    - Requires approval_decision.approved == True
    - Skips payment for rejected invoices with clear audit trail
    """
    log_event(
        "PAYMENT_START",
        {
            "invoice_id": ctx.invoice.invoice_number if ctx.invoice else None,
            "invoice_path": ctx.invoice_path,
        },
    )

    # Check if approval decision exists
    if ctx.approval_decision is None:
        ctx.payment_result = PaymentResult(
            status="SKIPPED",
            vendor="N/A",
            amount=0.0,
            payment_reference_id="N/A",
            timestamp=datetime.utcnow().isoformat(),
            reason="No approval decision available",
        )
        log_event("PAYMENT_SKIPPED", {"reason": "No approval decision"})
        return ctx

    # Check if approved
    if not ctx.approval_decision.approved:
        rejection_reason = "; ".join(ctx.approval_decision.reasons)
        ctx.payment_result = PaymentResult(
            status="SKIPPED",
            vendor=ctx.invoice.vendor if ctx.invoice else "N/A",
            amount=ctx.invoice.amount if ctx.invoice else 0.0,
            payment_reference_id="N/A",
            timestamp=datetime.utcnow().isoformat(),
            reason=f"Invoice rejected: {rejection_reason}",
        )
        log_event(
            "PAYMENT_SKIPPED",
            {
                "reason": "Invoice rejected",
                "rejection_reasons": ctx.approval_decision.reasons,
            },
        )
        return ctx

    # Approved - execute payment
    vendor = ctx.invoice.vendor
    amount = ctx.invoice.amount
    invoice_id = ctx.invoice.invoice_number or "UNKNOWN"

    log_event(
        "PAYMENT_ATTEMPT",
        {"vendor": vendor, "amount": amount, "invoice_id": invoice_id},
    )

    try:
        payment_response = mock_payment(vendor, amount, invoice_id)

        if payment_response.get("success"):
            ctx.payment_result = PaymentResult(
                status="PAID",
                vendor=vendor,
                amount=amount,
                payment_reference_id=payment_response["transaction_id"],
                timestamp=datetime.utcnow().isoformat(),
                reason=None,
            )
            log_event(
                "PAYMENT_RESULT",
                {
                    "status": "PAID",
                    "reference_id": payment_response["transaction_id"],
                    "amount": amount,
                },
            )
        else:
            ctx.payment_result = PaymentResult(
                status="FAILED",
                vendor=vendor,
                amount=amount,
                payment_reference_id="N/A",
                timestamp=datetime.utcnow().isoformat(),
                reason=payment_response.get("message", "Unknown error"),
            )
            log_event("PAYMENT_FAILED", {"reason": payment_response.get("message")})

    except Exception as e:
        ctx.payment_result = PaymentResult(
            status="FAILED",
            vendor=vendor,
            amount=amount,
            payment_reference_id="N/A",
            timestamp=datetime.utcnow().isoformat(),
            reason=f"Payment error: {str(e)}",
        )
        log_event("PAYMENT_FAILED", {"error": str(e)})

    return ctx
