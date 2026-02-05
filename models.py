"""
Core data models for the invoice processing pipeline.

These models define the "result contract" for data passing between stages.
Enhanced to support price validation, vendor checks, and financial calculations.
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class LineItem:
    """Represents a single line item on an invoice."""

    item: str
    quantity: int
    unit_price: Optional[float] = None
    amount: Optional[float] = None  # For validation: qty × unit_price should match this


@dataclass
class Invoice:
    """
    Structured invoice data extracted from various formats.

    Core fields (always required):
    - vendor: Vendor name
    - amount: Total invoice amount
    - line_items: List of items ordered

    Optional fields (enable richer validation):
    - due_date, invoice_number, vendor_address
    - subtotal, tax_rate, tax_amount (for financial validation)
    - payment_terms, currency
    """

    vendor: str
    amount: float
    line_items: List[LineItem]
    due_date: Optional[str] = None
    invoice_number: Optional[str] = None
    vendor_address: Optional[str] = None
    subtotal: Optional[float] = None
    tax_rate: Optional[float] = None
    tax_amount: Optional[float] = None
    currency: str = "USD"
    payment_terms: Optional[str] = None


@dataclass
class ValidationFinding:
    """
    Represents a single validation issue found during the validation stage.

    Examples:
    - rule: "unknown_item", item: "SuperGizmo", message: "Item not found in inventory"
    - rule: "quantity_exceeds_stock", item: "GadgetX", message: "Requested 20, only 5 in stock"
    - rule: "price_mismatch", item: "WidgetA", message: "Invoice price $300, expected $250"
    """

    rule: str
    item: str
    message: str


@dataclass
class ApprovalDecision:
    """
    Represents the approval decision from the approval stage.

    Supports reflection/critique loop:
    - approved: Final decision (True/False)
    - reasoning: Initial decision reasoning
    - reflection: Optional critique/revision notes from reflection loop
    """

    approved: bool
    reasoning: str
    reflection: Optional[str] = None  # Result of critique/revision loop


@dataclass
class PipelineResult:
    """
    Final result of the entire pipeline execution.

    This is the "result contract" that gets printed as JSON at the end.
    Includes data from all stages + any errors encountered.
    """

    invoice_path: str
    invoice: Optional[Invoice]
    validation_findings: List[ValidationFinding]
    approval_decision: Optional[ApprovalDecision]
    payment_result: Optional[dict]
    errors: List[str]


@dataclass
class PipelineContext:
    """
    Context object passed between pipeline stages.

    Accumulates state as the invoice moves through:
    Ingest → Validate → Approve → Pay

    Each stage reads from and writes to this context.
    """

    invoice_path: str
    invoice: Optional[Invoice] = None
    validation_findings: List[ValidationFinding] = field(default_factory=list)
    approval_decision: Optional[ApprovalDecision] = None
    payment_result: Optional[dict] = None
    errors: List[str] = field(default_factory=list)
