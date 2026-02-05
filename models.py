"""
Core data models for the invoice processing pipeline.

These models define the "result contract" for data passing between stages.
Enhanced to support price validation, vendor checks, and financial calculations.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class ParseMetadata:
    """
    Metadata about the parsing process for observability.

    Fields:
    - parse_warnings: List of warnings encountered during parsing
    - field_provenance: Where each field came from (e.g., "json.vendor.name")
    - confidence_scores: Confidence level per field (LOW/MED/HIGH)
    """

    parse_warnings: List[str] = field(default_factory=list)
    field_provenance: Dict[str, str] = field(default_factory=dict)
    confidence_scores: Dict[str, str] = field(default_factory=dict)


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

    Fields:
    - code: Stable identifier (UNKNOWN_ITEM, NEGATIVE_QTY, EXCEEDS_STOCK, OUT_OF_STOCK)
    - severity: INFO | WARN | ERROR
    - message: Human-readable description
    - item_name: Item identifier (if applicable)
    - requested_qty: Quantity requested (if applicable)
    - available_qty: Stock available (if applicable)

    Examples:
    - code: "UNKNOWN_ITEM", severity: "ERROR", message: "Item 'SuperGizmo' not found"
    - code: "EXCEEDS_STOCK", severity: "ERROR", message: "Requested 20, only 5 available"
    """

    code: str
    severity: str
    message: str
    item_name: Optional[str] = None
    requested_qty: Optional[int] = None
    available_qty: Optional[int] = None


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
    parse_metadata: Optional[ParseMetadata] = None
    validation_findings: List[ValidationFinding] = field(default_factory=list)
    approval_decision: Optional[ApprovalDecision] = None
    payment_result: Optional[dict] = None
    errors: List[str] = field(default_factory=list)
