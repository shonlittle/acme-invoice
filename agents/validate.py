"""
Validation stage: Check invoice data against inventory/vendor database.

Validation rules implemented:
- UNKNOWN_ITEM: Item not in inventory database
- NEGATIVE_QTY: Quantity < 0
- EXCEEDS_STOCK: Requested quantity > available stock
- OUT_OF_STOCK: Item has 0 stock (and qty > 0)

Future rules (not in this slice):
- price_mismatch: Invoice unit_price != database unit_price
- unknown_vendor: Vendor not in whitelist
- suspicious_vendor: Vendor flagged as untrusted
- line_item_amount_mismatch: quantity × unit_price != stated amount
"""

from db.inventory import get_item_info
from models import PipelineContext, ValidationFinding
from utils.logging import log_event


def validate_stage(ctx: PipelineContext) -> PipelineContext:
    """
    Validate invoice data against inventory database.

    Implements 4 core validation rules:
    - UNKNOWN_ITEM
    - NEGATIVE_QTY
    - EXCEEDS_STOCK
    - OUT_OF_STOCK

    Populates ctx.validation_findings with structured findings.
    """
    # Skip if no invoice parsed yet
    if ctx.invoice is None:
        log_event("VALIDATION_SKIPPED", {"reason": "No invoice data"})
        return ctx

    log_event(
        "VALIDATION_START",
        {
            "invoice_id": ctx.invoice.invoice_number,
            "vendor": ctx.invoice.vendor,
            "line_items_count": len(ctx.invoice.line_items),
        },
    )

    findings = []

    for line_item in ctx.invoice.line_items:
        # Rule: NEGATIVE_QTY
        if line_item.quantity < 0:
            findings.append(
                ValidationFinding(
                    code="NEGATIVE_QTY",
                    severity="ERROR",
                    message=f"Negative quantity: {line_item.quantity}",
                    item_name=line_item.item,
                    requested_qty=line_item.quantity,
                    available_qty=None,
                )
            )
            continue  # Skip further checks for this item

        # Query inventory
        item_info = get_item_info(line_item.item)

        # Rule: UNKNOWN_ITEM
        if item_info is None:
            findings.append(
                ValidationFinding(
                    code="UNKNOWN_ITEM",
                    severity="ERROR",
                    message=f"Item '{line_item.item}' not found in inventory",
                    item_name=line_item.item,
                    requested_qty=line_item.quantity,
                    available_qty=None,
                )
            )
            continue

        stock = item_info["stock"]

        # Rule: OUT_OF_STOCK
        if stock == 0 and line_item.quantity > 0:
            findings.append(
                ValidationFinding(
                    code="OUT_OF_STOCK",
                    severity="ERROR",
                    message=f"Item '{line_item.item}' is out of stock",
                    item_name=line_item.item,
                    requested_qty=line_item.quantity,
                    available_qty=0,
                )
            )
            continue

        # Rule: EXCEEDS_STOCK
        if line_item.quantity > stock:
            findings.append(
                ValidationFinding(
                    code="EXCEEDS_STOCK",
                    severity="ERROR",
                    message=f"Requested {line_item.quantity}, only {stock} available",
                    item_name=line_item.item,
                    requested_qty=line_item.quantity,
                    available_qty=stock,
                )
            )

    ctx.validation_findings = findings

    # Structured summary logging
    counts_by_code = {}
    counts_by_severity = {}
    for f in findings:
        counts_by_code[f.code] = counts_by_code.get(f.code, 0) + 1
        counts_by_severity[f.severity] = counts_by_severity.get(f.severity, 0) + 1

    log_event(
        "VALIDATION_FINDINGS",
        {
            "total_findings": len(findings),
            "by_code": counts_by_code,
            "by_severity": counts_by_severity,
            "top_messages": [f.message for f in findings[:3]],
        },
    )

    log_event("VALIDATION_END", {"status": "complete"})

    return ctx
