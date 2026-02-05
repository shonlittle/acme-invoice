"""
Validation stage: Check invoice data against inventory/vendor database.

Validation rules to implement:
- unknown_item: Item not in inventory database
- negative_quantity: Quantity < 0
- quantity_exceeds_stock: Requested quantity > available stock
- out_of_stock: Item has 0 stock
- price_mismatch: Invoice unit_price != database unit_price
- unknown_vendor: Vendor not in whitelist
- suspicious_vendor: Vendor flagged as untrusted
- line_item_amount_mismatch: quantity × unit_price != stated amount

TODO: [Slice 3] Implement all validation rules with unit tests
"""

from models import PipelineContext, ValidationFinding
from utils.logging import log_event


def validate_stage(ctx: PipelineContext) -> PipelineContext:
    """
    Validate invoice data against inventory database.

    Currently a stub - returns context unchanged.

    TODO: [Slice 3] Implement validation rules:
    - Check each line item against inventory
    - Check vendor against whitelist
    - Validate quantities, prices, amounts
    - Populate ctx.validation_findings with findings
    """
    log_event("VALIDATION_STARTED", {"invoice": ctx.invoice_path})

    # Stub: No validation yet
    log_event("VALIDATION_STUB", {"message": "Validation not implemented yet"})

    return ctx
