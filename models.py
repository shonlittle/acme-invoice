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
class InitialDecision:
    """Captures the initial approval decision before reflection."""

    approved: bool
    reasons: List[str]
    timestamp: str  # ISO format


@dataclass
class ReflectionResult:
    """Captures the reflection/critique step."""

    critique_notes: str
    revised: bool
    llm_backend: str = "mock"  # "grok" or "mock"
    revised_reasons: Optional[List[str]] = None


@dataclass
class ApprovalDecision:
    """
    Production-shaped approval decision with full audit trail.

    Fields:
    - approved: Final decision (bool)
    - decision_policy: Policy version used (e.g., "v1_rule_based")
    - reasons: Final list of reasons (actionable, short)
    - severity_summary: Counts by severity from validation findings
    - initial_decision: The first decision before reflection
    - reflection: Critique/revision step (optional)
    - final_decision_timestamp: When final decision was made
    """

    approved: bool
    decision_policy: str
    reasons: List[str]
    severity_summary: Dict[str, int]
    initial_decision: InitialDecision
    reflection: Optional[ReflectionResult]
    final_decision_timestamp: str


@dataclass
class PaymentResult:
    """
    Payment execution result with audit trail.

    Fields:
    - status: PAID | SKIPPED | FAILED
    - vendor: Vendor name
    - amount: Payment amount
    - payment_reference_id: Stable reference (e.g., "PAY-INV-1004-20260205T131415")
    - timestamp: When payment was attempted
    - reason: Required for SKIPPED/FAILED (e.g., "Invoice rejected")
    """

    status: str  # PAID | SKIPPED | FAILED
    vendor: str
    amount: float
    payment_reference_id: str
    timestamp: str  # ISO format
    reason: Optional[str] = None


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
    payment_result: Optional[PaymentResult]
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
    payment_result: Optional[PaymentResult] = None
    errors: List[str] = field(default_factory=list)
