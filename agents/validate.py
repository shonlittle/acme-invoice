"""
Validation stage: Check invoice data against inventory/vendor database.

Validation rules implemented:
- UNKNOWN_VENDOR: Vendor not in vendors table
- SUSPICIOUS_VENDOR: Vendor flagged as untrusted
- UNKNOWN_ITEM: Item not in inventory database
- NEGATIVE_QTY: Quantity < 0
- EXCEEDS_STOCK: Requested quantity > available stock
- OUT_OF_STOCK: Item has 0 stock (and qty > 0)
- PRICE_MISMATCH: Invoice unit_price != database unit_price
- LINE_ITEM_AMOUNT_MISMATCH: qty × unit_price != stated line amount
"""

from db.inventory import get_item_info, get_vendor_info
from models import PipelineContext, ValidationFinding
from utils.logging import log_event


def validate_stage(ctx: PipelineContext) -> PipelineContext:
    """
    Validate invoice data against inventory database.

    Implements 8 validation rules:
    - UNKNOWN_VENDOR (vendor-level)
    - SUSPICIOUS_VENDOR (vendor-level)
    - UNKNOWN_ITEM (line-item-level)
    - NEGATIVE_QTY (line-item-level)
    - EXCEEDS_STOCK (line-item-level)
    - OUT_OF_STOCK (line-item-level)
    - PRICE_MISMATCH (line-item-level)
    - LINE_ITEM_AMOUNT_MISMATCH (line-item-level)

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

    # --- Vendor-level rules ---
    vendor_name = ctx.invoice.vendor
    vendor_info = get_vendor_info(vendor_name)

    if vendor_info is None:
        findings.append(
            ValidationFinding(
                code="UNKNOWN_VENDOR",
                severity="WARN",
                message=(f"Vendor '{vendor_name}' not found " f"in vendor database"),
                item_name=vendor_name,
            )
        )
    elif vendor_info["trusted"] == 0:
        findings.append(
            ValidationFinding(
                code="SUSPICIOUS_VENDOR",
                severity="WARN",
                message=(f"Vendor '{vendor_name}' is flagged " f"as untrusted"),
                item_name=vendor_name,
            )
        )

    # --- Line-item-level rules ---
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

        # Rule: PRICE_MISMATCH
        db_price = item_info["unit_price"]
        if (
            line_item.unit_price is not None
            and db_price is not None
            and abs(line_item.unit_price - db_price) > 0.01
        ):
            findings.append(
                ValidationFinding(
                    code="PRICE_MISMATCH",
                    severity="WARN",
                    message=(
                        f"Invoice price ${line_item.unit_price:.2f} "
                        f"!= inventory price ${db_price:.2f} "
                        f"for '{line_item.item}'"
                    ),
                    item_name=line_item.item,
                    requested_qty=line_item.quantity,
                )
            )

        # Rule: LINE_ITEM_AMOUNT_MISMATCH
        if line_item.unit_price is not None and line_item.amount is not None:
            expected = line_item.unit_price * line_item.quantity
            if abs(line_item.amount - expected) > 0.01:
                findings.append(
                    ValidationFinding(
                        code="LINE_ITEM_AMOUNT_MISMATCH",
                        severity="WARN",
                        message=(
                            f"Line amount ${line_item.amount:.2f} "
                            f"!= qty({line_item.quantity}) × "
                            f"price(${line_item.unit_price:.2f}) "
                            f"= ${expected:.2f} "
                            f"for '{line_item.item}'"
                        ),
                        item_name=line_item.item,
                        requested_qty=line_item.quantity,
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
