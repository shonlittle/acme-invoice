"""
Pipeline orchestrator for the invoice processing system.

Executes the 4-stage pipeline:
1. Ingest: Extract structured data from invoice file
2. Validate: Check against inventory/vendor database
3. Approve: Simulate VP review with reflection loop
4. Pay: Execute payment or log rejection

Each stage receives and returns a PipelineContext object.
"""

from agents.approve import approve_stage
from agents.ingest import ingest_stage
from agents.pay import pay_stage
from agents.validate import validate_stage
from db.inventory import init_database
from models import PipelineContext, PipelineResult
from utils.logging import log_error, log_stage_end, log_stage_start


def run_pipeline(invoice_path: str) -> PipelineResult:
    """
    Execute the full invoice processing pipeline.

    Args:
        invoice_path: Path to invoice file to process

    Returns:
        PipelineResult with data from all stages + any errors
    """
    # Auto-initialize database on first run (idempotent)
    init_database()

    # Initialize pipeline context
    ctx = PipelineContext(invoice_path=invoice_path)

    try:
        # Stage 1: Ingest
        log_stage_start("INGEST")
        ctx = ingest_stage(ctx)
        log_stage_end("INGEST")

        # Stage 2: Validate
        log_stage_start("VALIDATE")
        ctx = validate_stage(ctx)
        log_stage_end("VALIDATE")

        # Stage 3: Approve
        log_stage_start("APPROVE")
        ctx = approve_stage(ctx)
        log_stage_end("APPROVE")

        # Stage 4: Pay
        log_stage_start("PAY")
        ctx = pay_stage(ctx)
        log_stage_end("PAY")

    except Exception as e:
        log_error(f"Pipeline failed for {invoice_path}", e)
        ctx.errors.append(f"Pipeline error: {str(e)}")

    # Convert context to final result
    result = PipelineResult(
        invoice_path=ctx.invoice_path,
        invoice=ctx.invoice,
        validation_findings=ctx.validation_findings,
        approval_decision=ctx.approval_decision,
        payment_result=ctx.payment_result,
        errors=ctx.errors,
    )

    return result
