"""
Ingestion stage: Extract structured data from invoice files.

Supports multiple formats:
- JSON (.json) - Direct mapping with HIGH confidence
- CSV (.csv) - Key-value format with MEDIUM confidence
- TXT (.txt) - Regex-based extraction with LOW-MEDIUM confidence
- PDF (.pdf) - Not implemented yet (Slice 7)

Implements best-effort parsing with structured warnings and provenance tracking.
"""

import csv
import json
import re
from pathlib import Path
from typing import Tuple

from models import Invoice, LineItem, ParseMetadata, PipelineContext
from utils.logging import log_error, log_event


def parse_json(file_path: str) -> Tuple[Invoice, ParseMetadata]:
    """
    Parse JSON invoice with direct mapping.

    Handles nested vendor structure and provides HIGH confidence scores.
    """
    metadata = ParseMetadata()

    with open(file_path, "r") as f:
        data = json.load(f)

    # Extract vendor (handle nested structure)
    vendor = data.get("vendor")
    if isinstance(vendor, dict):
        vendor_name = vendor.get("name", "Unknown")
        vendor_address = vendor.get("address")
        metadata.field_provenance["vendor"] = "json.vendor.name"
        metadata.confidence_scores["vendor"] = "HIGH"
    else:
        vendor_name = vendor or "Unknown"
        vendor_address = None
        metadata.field_provenance["vendor"] = "json.vendor"
        metadata.confidence_scores["vendor"] = "HIGH" if vendor else "LOW"
        if not vendor:
            metadata.parse_warnings.append("Vendor field missing or empty")

    # Extract line items
    line_items = []
    for item_data in data.get("line_items", []):
        line_items.append(
            LineItem(
                item=item_data.get("item", "Unknown"),
                quantity=item_data.get("quantity", 0),
                unit_price=item_data.get("unit_price"),
                amount=item_data.get("amount"),
            )
        )

    metadata.field_provenance["line_items"] = "json.line_items"
    metadata.confidence_scores["line_items"] = "HIGH"

    # Extract total amount
    total = data.get("total", 0.0)
    if total == 0.0 and "total" not in data:
        metadata.parse_warnings.append("Total amount missing, using 0.0")
        metadata.confidence_scores["amount"] = "LOW"
    else:
        metadata.confidence_scores["amount"] = "HIGH"

    metadata.field_provenance["amount"] = "json.total"

    invoice = Invoice(
        vendor=vendor_name,
        amount=total,
        line_items=line_items,
        invoice_number=data.get("invoice_number"),
        due_date=data.get("due_date"),
        vendor_address=vendor_address,
        subtotal=data.get("subtotal"),
        tax_rate=data.get("tax_rate"),
        tax_amount=data.get("tax_amount"),
        currency=data.get("currency", "USD"),
        payment_terms=data.get("payment_terms"),
        revision=data.get("revision"),
    )

    return invoice, metadata


def parse_csv(file_path: str) -> Tuple[Invoice, ParseMetadata]:
    """
    Parse CSV invoice (key-value format with repeated item rows).

    Uses state machine to accumulate fields and line items.
    Provides MEDIUM confidence scores.
    """
    metadata = ParseMetadata()

    # State machine: accumulate fields and line items
    fields = {}
    line_items = []
    current_item = {}

    with open(file_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            field = row.get("field", "")
            value = row.get("value", "")

            if field == "item":
                # Start new line item
                if current_item and "item" in current_item:
                    line_items.append(LineItem(**current_item))
                current_item = {"item": value}
            elif field == "quantity":
                current_item["quantity"] = int(value) if value else 0
            elif field == "unit_price":
                current_item["unit_price"] = float(value) if value else None
            else:
                fields[field] = value

        # Add last item
        if current_item and "item" in current_item:
            line_items.append(LineItem(**current_item))

    # Extract vendor
    vendor = fields.get("vendor", "Unknown")
    if vendor == "Unknown":
        metadata.parse_warnings.append("Vendor not found in CSV")
        metadata.confidence_scores["vendor"] = "LOW"
    else:
        metadata.confidence_scores["vendor"] = "MEDIUM"

    metadata.field_provenance["vendor"] = "csv.field:vendor"

    # Extract total
    total_str = fields.get("total", "0.0")
    try:
        total = float(total_str)
        metadata.confidence_scores["amount"] = "MEDIUM"
    except ValueError:
        total = 0.0
        metadata.parse_warnings.append(f"Invalid total value: {total_str}")
        metadata.confidence_scores["amount"] = "LOW"

    metadata.field_provenance["amount"] = "csv.field:total"
    metadata.field_provenance["line_items"] = "csv.field:item"
    metadata.confidence_scores["line_items"] = "MEDIUM"

    invoice = Invoice(
        vendor=vendor,
        amount=total,
        line_items=line_items,
        invoice_number=fields.get("invoice_number"),
        due_date=fields.get("due_date"),
        payment_terms=fields.get("payment_terms"),
        revision=fields.get("revision"),
    )

    return invoice, metadata


def parse_txt_from_string(content: str) -> Tuple[Invoice, ParseMetadata]:
    """
    Parse invoice text using regex heuristics.

    Extracted from parse_txt() to enable reuse for PDF parsing.
    Uses pattern matching for vendor, amount, due date, and line items.
    Provides LOW-MEDIUM confidence scores based on match success.
    """
    metadata = ParseMetadata()

    # Regex patterns
    vendor_match = re.search(r"Vendor:\s*(.+)", content, re.IGNORECASE)
    invoice_num_match = re.search(r"Invoice Number:\s*(.+)", content, re.IGNORECASE)
    total_match = re.search(
        r"Total Amount:\s*\$?([\d,]+\.?\d*)", content, re.IGNORECASE
    )
    due_date_match = re.search(r"Due Date:\s*(\d{4}-\d{2}-\d{2})", content)
    payment_terms_match = re.search(r"Payment Terms:\s*(.+)", content, re.IGNORECASE)
    revision_match = re.search(r"Revision:\s*(.+)", content, re.IGNORECASE)

    # Extract vendor
    if vendor_match:
        vendor = vendor_match.group(1).strip()
        metadata.confidence_scores["vendor"] = "MEDIUM"
        metadata.field_provenance["vendor"] = "txt.regex.vendor"
    else:
        vendor = "Unknown"
        metadata.parse_warnings.append("Vendor not found in text")
        metadata.confidence_scores["vendor"] = "LOW"
        metadata.field_provenance["vendor"] = "txt.default"

    # Extract total amount
    if total_match:
        total = float(total_match.group(1).replace(",", ""))
        metadata.confidence_scores["amount"] = "MEDIUM"
        metadata.field_provenance["amount"] = "txt.regex.total"
    else:
        total = 0.0
        metadata.parse_warnings.append("Total amount not found in text")
        metadata.confidence_scores["amount"] = "LOW"
        metadata.field_provenance["amount"] = "txt.default"

    # Extract line items
    line_items = []
    # Pattern: "WidgetA    qty: 10    unit price: $250.00"
    item_pattern = r"(\w+)\s+qty:\s*(\d+)\s+unit price:\s*\$?([\d.]+)"
    for match in re.finditer(item_pattern, content, re.IGNORECASE):
        line_items.append(
            LineItem(
                item=match.group(1),
                quantity=int(match.group(2)),
                unit_price=float(match.group(3)),
            )
        )

    if line_items:
        metadata.confidence_scores["line_items"] = "MEDIUM"
    else:
        metadata.parse_warnings.append("No line items found in text")
        metadata.confidence_scores["line_items"] = "LOW"

    metadata.field_provenance["line_items"] = "txt.regex.line_items"

    invoice = Invoice(
        vendor=vendor,
        amount=total,
        line_items=line_items,
        invoice_number=(
            invoice_num_match.group(1).strip() if invoice_num_match else None
        ),
        due_date=due_date_match.group(1) if due_date_match else None,
        payment_terms=(
            payment_terms_match.group(1).strip() if payment_terms_match else None
        ),
        revision=revision_match.group(1).strip() if revision_match else None,
    )

    return invoice, metadata


def parse_txt(file_path: str) -> Tuple[Invoice, ParseMetadata]:
    """
    Parse TXT invoice file.

    Reads file content and delegates to parse_txt_from_string().
    """
    with open(file_path, "r") as f:
        content = f.read()
    return parse_txt_from_string(content)


def parse_pdf(file_path: str) -> Tuple[Invoice, ParseMetadata]:
    """
    Extract text from PDF and parse using TXT heuristics.

    Best-effort extraction with clear warnings about limitations.
    """
    metadata = ParseMetadata()

    try:
        import PyPDF2

        log_event("INGEST_PDF_START", {"path": file_path})

        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)

            # Extract text from all pages
            text_parts = []
            for page in reader.pages:
                text_parts.append(page.extract_text())

            extracted_text = "\n".join(text_parts)

        # Log extraction metadata
        metadata.field_provenance["extraction_method"] = "pdf_text_extract"
        metadata.field_provenance["extracted_text_length"] = str(len(extracted_text))

        # Warn about PDF limitations
        metadata.parse_warnings.append(
            "PDF text extraction is best-effort - layout/formatting may be lost"
        )

        log_event(
            "INGEST_PDF_EXTRACTED",
            {
                "text_length": len(extracted_text),
                "warnings_count": len(metadata.parse_warnings),
            },
        )

        if not extracted_text.strip():
            metadata.parse_warnings.append("PDF text extraction yielded empty text")
            log_event("INGEST_PDF_END", {"status": "empty_text"})
            return Invoice(vendor="Unknown", amount=0.0, line_items=[]), metadata

        # Reuse TXT parsing logic on extracted text
        invoice, txt_metadata = parse_txt_from_string(extracted_text)

        # Merge metadata (PDF warnings + TXT extraction results)
        metadata.parse_warnings.extend(txt_metadata.parse_warnings)
        metadata.field_provenance.update(txt_metadata.field_provenance)

        # Downgrade confidence scores for PDF (less reliable than direct TXT)
        for field, confidence in txt_metadata.confidence_scores.items():
            if confidence == "HIGH":
                metadata.confidence_scores[field] = "MEDIUM"
            elif confidence == "MEDIUM":
                metadata.confidence_scores[field] = "LOW"
            else:
                metadata.confidence_scores[field] = confidence

        log_event("INGEST_PDF_END", {"status": "complete"})

        return invoice, metadata

    except ImportError:
        metadata.parse_warnings.append("PyPDF2 not installed - cannot extract PDF text")
        log_event("INGEST_PDF_END", {"status": "missing_library"})
        return Invoice(vendor="PARSE_ERROR", amount=0.0, line_items=[]), metadata

    except Exception as e:
        metadata.parse_warnings.append(f"PDF extraction failed: {str(e)}")
        log_event("INGEST_PDF_END", {"status": "error", "error": str(e)})
        return Invoice(vendor="PARSE_ERROR", amount=0.0, line_items=[]), metadata


def ingest_stage(ctx: PipelineContext) -> PipelineContext:
    """
    Extract structured invoice data from the input file.

    Supports JSON, CSV, and TXT formats. Never crashes - returns minimal
    invoice with errors on failure to allow pipeline to continue.
    """
    log_event(
        "INGEST_START",
        {"path": ctx.invoice_path, "type": Path(ctx.invoice_path).suffix},
    )

    try:
        ext = Path(ctx.invoice_path).suffix.lower()

        if ext == ".json":
            invoice, metadata = parse_json(ctx.invoice_path)
        elif ext == ".csv":
            invoice, metadata = parse_csv(ctx.invoice_path)
        elif ext == ".txt":
            invoice, metadata = parse_txt(ctx.invoice_path)
        elif ext == ".pdf":
            invoice, metadata = parse_pdf(ctx.invoice_path)
        else:
            raise ValueError(f"Unsupported file type: {ext}")

        ctx.invoice = invoice
        ctx.parse_metadata = metadata

        # Log extraction results
        log_event(
            "INGEST_EXTRACTED",
            {
                "vendor": invoice.vendor,
                "amount": invoice.amount,
                "due_date": invoice.due_date,
                "item_count": len(invoice.line_items),
                "warnings_count": len(metadata.parse_warnings),
                "confidence_summary": metadata.confidence_scores,
            },
        )

    except Exception as e:
        log_error(f"Ingestion failed for {ctx.invoice_path}", e)
        ctx.errors.append(f"Ingestion error: {str(e)}")

        # Return minimal invoice to allow pipeline to continue
        ctx.invoice = Invoice(vendor="PARSE_ERROR", amount=0.0, line_items=[])
        ctx.parse_metadata = ParseMetadata(
            parse_warnings=[f"Fatal parse error: {str(e)}"],
            confidence_scores={"vendor": "LOW", "amount": "LOW", "line_items": "LOW"},
        )

    log_event("INGEST_END", {"status": "complete"})

    return ctx
