# Invoice Processing Prototype

## Overview

Acme Corp loses **$2M/year** on manual invoice processing due to:

- 30% error rate from manual data entry
- 5-day processing delays
- Frustrated stakeholders across finance and operations

This system automates the end-to-end invoice workflow with a **4-stage agentic pipeline**:

1. **Ingest** — Extract structured data from invoices (PDF/JSON/CSV/TXT)
2. **Validate** — Check against inventory database for errors
3. **Approve** — Simulate VP review with reflection/critique loop
4. **Pay** — Execute mock payment if approved

**Impact:** Reduce errors, accelerate processing, provide audit trail.

---

## Quick Start

### 1. Setup Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate  # On macOS/Linux
# OR
.venv\Scripts\activate  # On Windows
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Database Setup

The database auto-initializes with seed data on first pipeline run.

**Optional manual initialization:**

```bash
python db/inventory.py
```

**First run behavior:**

- Creates `db/inventory.db` with seed data
- Adds 4 inventory items (WidgetA, WidgetB, GadgetX, FakeItem)
- Adds 4 trusted vendors
- Idempotent (safe to run multiple times)

### 4. Run Pipeline

```bash
# Single invoice
python main.py --invoice_path=data/invoices/invoice_1004.json

# All samples (batch mode)
python main.py --run_all

# Tests
pytest tests/ -v
```

**Note:** Results are automatically saved to `out/<invoice_id>.json`

---

## Implemented Features

### 4-Stage Pipeline

- ✅ **Ingestion** - JSON, CSV, TXT, PDF support
- ✅ **Validation** - SQLite inventory checking (4 rules)
- ✅ **Approval** - Rule-based policy + reflection/critique loop
- ✅ **Payment** - Mock payment with strict gating

### Key Capabilities

- **Structured Logging** - Observable at every stage
- **Deterministic Testing** - 36 unit tests (all passing)
- **Graceful Degradation** - Never crashes, returns minimal data on error
- **Optional LLM Integration** - Grok via xAI API (falls back to mock)
- **Audit Trail** - Full provenance tracking and confidence scores

---

## PDF Ingestion Limitations

PDF invoice processing uses best-effort text extraction:

- **Layout/Formatting Loss:** PDF text extraction does not preserve visual layout, tables, or complex formatting
- **Digital Text Only:** OCR (image-to-text) is out of scope - PDFs must contain extractable text
- **Lower Confidence:** All PDF-extracted fields are marked with reduced confidence scores
- **Library Required:** Requires `PyPDF2` (installed via `requirements.txt`)

If PDF extraction fails or yields empty text, the pipeline continues with a minimal invoice and clear warnings.

---

## How to Run

### Single Invoice

```bash
python main.py --invoice_path=data/invoices/invoice_1004.json
```

**Output:**

- Structured logs to console
- Final JSON result
- Result saved to `out/<invoice_id>.json`

### All Sample Invoices (Batch Mode)

```bash
python main.py --run_all
# Processes 19 invoices, saves JSON to out/
```

**Alternative (equivalent result):**

```bash
python scripts/run_samples.py
```

**When to use which:**

- `python main.py --run_all` — Built-in batch mode, part of main CLI
- `python scripts/run_samples.py` — Standalone script, includes additional metrics table
- Both process all invoices and save results to `out/`

### Run Tests

```bash
pytest tests/ -v
# 36 unit tests covering validation, approval, payment gating
```

---

## Architecture

**Pipeline Flow:**

```
main.py → run_pipeline()
├── INGEST   (PDF/JSON/CSV/TXT → Invoice with metadata)
├── VALIDATE (Check inventory.db for stock/errors)
├── APPROVE  (Rule-based + reflection/critique loop)
└── PAY      (Execute mock payment if approved)
```

**Stage Responsibilities:**

- **Ingest:** Extract vendor, amount, line items, due date. Handles missing/malformed data gracefully.
- **Validate:** 4 rules — unknown_item, negative_qty, exceeds_stock, out_of_stock
- **Approve:** $10K threshold + ERROR-level findings trigger rejection. Optional LLM reflection loop.
- **Pay:** Gated on approval. Mock payment always succeeds. Full audit trail.

**Observable:** Structured logs at every stage (STAGE_START, STAGE_END, decision points).

---

## Optional xAI/Grok Integration

The approval stage supports **optional Grok integration** for LLM-powered decision reasoning:

**With Grok (optional):**

```bash
# Create .env file
echo "XAI_API_KEY=your_key_here" > .env

# Run pipeline (uses Grok for approval reasoning)
python main.py --invoice_path=data/invoices/invoice_1004.json
```

**Without Grok (default):**

```bash
# No .env or XAI_API_KEY → uses deterministic mock
python main.py --invoice_path=data/invoices/invoice_1004.json
```

**Fallback Behavior:**

- If `XAI_API_KEY` not set → deterministic mock (always works)
- If Grok API fails → falls back to mock (graceful degradation)
- Uses stdlib `urllib` for HTTP (no external SDK required)

**Why This Matters:**

- Reviewers can run the system with **zero setup** (no API key needed)
- Production can enable Grok for richer reasoning
- System never crashes due to missing/failed LLM calls

---

## Assumptions & Tradeoffs

**Ingestion:**

- PDF extraction: best-effort, digital text only (no OCR)
- Layout/formatting loss expected for PDFs
- CSV/JSON parsing is HIGH confidence; TXT/PDF is LOW-MEDIUM

**Validation:**

- 4 rules implemented (stock checks, negative qty)
- No duplicate invoice detection
- No price mismatch validation (line item amounts)
- Vendor trust flag exists in DB but not used in approval logic yet

**Approval:**

- Rule-based policy: $10K threshold + ERROR-level findings → reject
- Reflection loop can revise initial decision
- Deterministic mock provides consistent test behavior

**Payment:**

- Mock payment always succeeds (no real banking integration)
- Strict gating: payment only if approved
- Full audit trail with reference IDs

**Design Philosophy:**

- Prefer stdlib over external dependencies (urllib vs requests, manual .env parsing)
- Graceful degradation everywhere (never crash, return minimal data on error)
- Observable by default (structured logs, confidence scores, provenance tracking)

---

## Limitations

**Current Scope:**

- PDF parsing: layout/formatting loss expected (uses PyPDF2 text extraction)
- No OCR support for scanned invoices
- No duplicate invoice detection
- No vendor fraud scoring (trust flag not used in approval logic)
- No email notifications
- No batch retry/recovery mechanisms
- Mock payment only (no real banking API)

**Test Coverage:**

- 36 unit tests covering core business logic
- End-to-end integration tests via `python main.py --run_all`
- No formal load/performance testing

---

## Run with Docker (Optional)

Start the backend API with Docker Compose (no local Python setup needed):

```bash
# Build and start
docker compose up --build

# Backend available at http://localhost:8080
```

**Test it:**

```bash
# Health check
curl http://localhost:8080/api/health

# List sample invoices
curl http://localhost:8080/api/samples

# Process a sample invoice
curl -X POST http://localhost:8080/api/process-sample \
  -H "Content-Type: application/json" \
  -d '{"sample_name": "invoice_1001.txt"}'

# Upload a file
curl -X POST http://localhost:8080/api/process \
  -F "file=@data/invoices/invoice_1004.json"
```

**Volumes:**

- `./data` is mounted read-only (sample invoices)
- `./out` is mounted read-write (results persist on host)

**Stop:**

```bash
docker compose down
```

> **Note:** Docker is optional. Local dev instructions above still work without Docker.

---

## Next Steps (Production-Oriented)

**Near-term (1-2 sprints):**

- Add vendor fraud scoring to approval logic (use trust flag)
- Implement duplicate invoice detection (check invoice_number history)
- Add price mismatch validation rule (verify line item amounts)
- Integrate with real banking API for payments (replace mock_payment)

**Medium-term (3-6 months):**

- Web UI for invoice submission and approval workflow
- Historical audit log with queryable interface (SQLite → PostgreSQL)
- Email/Slack notifications for approval requests
- Batch processing with retry logic and dead-letter queue

**Long-term (6-12 months):**

- OCR support for scanned invoices (Tesseract or cloud OCR service)
- ML-based anomaly detection (flag suspicious patterns)
- Multi-currency support (FX rate lookups)
- Integration with ERP systems (SAP, Oracle, NetSuite)

---

## Test Coverage

The system includes **36 unit tests** covering:

- Database initialization and seeding (idempotency, seed data)
- Validation rules (unknown_item, negative_qty, exceeds_stock, out_of_stock)
- Approval logic (rule-based decisions, reflection/revision scenarios)
- Payment gating (approved → paid, rejected → skipped)
- PDF ingestion (text extraction, confidence downgrade)

**Run tests:**

```bash
pytest tests/ -v
```

**Scope Note:** Tests focus on core business logic. End-to-end integration across all file formats is demonstrated via `python main.py --run_all`.

---

## Architecture (Detailed)

```
main.py (CLI)
└── pipeline/runner.py (orchestrator)
    ├── agents/ingest.py    (JSON/CSV/TXT/PDF → Invoice)
    ├── agents/validate.py  (Invoice → ValidationFindings)
    ├── agents/approve.py   (Findings → ApprovalDecision)
    └── agents/pay.py       (Decision → PaymentResult)
```

---

## Testing

```bash
# All tests
pytest tests/ -v

# Specific test files
pytest tests/test_ingestion.py -v
pytest tests/test_validation.py -v
pytest tests/test_approval.py -v
pytest tests/test_payment.py -v
```

---

<!-- DO NOT CHANGE: Original README content below this line -->
<!-- This section is the original project specification and should be preserved as-is -->

# Galatiq Case: Invoice Processing Automation

## Background

Acme Corp is a PE-backed manufacturing firm losing **$2M/year** on manual invoice processing. Invoices arrive via email as PDFs in messy formats with frequent errors. Staff manually extract data, validate against a legacy inventory database (inconsistent), obtain VP approval (via email chains), and process payment (via a banking API).

**Current pain points:**

- 30% error rate
- 5-day processing delays
- Frustrated stakeholders

## Objective

Build a **multi-agent system** that automates the end-to-end invoice processing workflow. The system must run as a working prototype — not just designs or slides.

## Workflow

The system should handle four stages:

1. **Ingestion** — Extract structured data from invoice documents (PDFs, text files). Fields include: Vendor, Amount, Items (with quantities), and Due Date. Expect unstructured text, typos, missing data, and potentially fraudulent entries.

2. **Validation** — Verify extracted data against a mock inventory database (SQLite). Flag mismatches such as quantity exceeding available stock or items not found in inventory.

3. **Approval** — Simulate VP-level review with rule-based decision-making (e.g., invoices over $10K require additional scrutiny). The agent should reason through approval/rejection with a reflection or critique loop.

4. **Payment** — If approved, call a mock payment function. If rejected, log the rejection with reasoning.

## Technical Requirements

- **LLM Integration**: Use xAI's Grok as the core reasoning engine (via the xAI API at https://grok.x.ai). Other models are acceptable if you don't have an API key.
- **Multi-Agent Orchestration**: Use a framework such as LangGraph, CrewAI, AutoGen, or a custom solution.
- **Agent Capabilities**: Function calling / tool use, structured outputs, and self-correction loops.
- **Runtime**: Assume no internet for external APIs — simulate everything locally.
- **Tech Stack**: Python (preferred), with libraries like `langchain`, `crewai`, `autogen`, `pdfplumber`, `PyMuPDF`, etc. Run locally — no cloud deployment.

## Provided Resources

### Mock Invoice Data

Sample invoices are provided in the `data/invoices/` directory in various formats (PDF, CSV, JSON, TXT). Use these as inputs for testing. The data intentionally includes a mix of clean entries and problematic ones — identifying and handling issues is part of the challenge.

### Mock Inventory Database (Required Setup)

Before running the system, you **must** create a local SQLite database that the validation agent will check invoices against. The sample invoices in `data/invoices/` reference specific items and quantities — your database needs to contain matching inventory records so the validation stage can flag mismatches, out-of-stock items, and unknown products.

Below is a starter schema and seed data that covers the core items referenced across the provided invoices:

```python
import sqlite3

conn = sqlite3.connect('inventory.db')  # Persist to file so all agents can access it
cursor = conn.cursor()

cursor.execute('CREATE TABLE IF NOT EXISTS inventory (item TEXT PRIMARY KEY, stock INTEGER)')
cursor.execute("""
    INSERT INTO inventory VALUES
    ('WidgetA', 15),
    ('WidgetB', 10),
    ('GadgetX', 5),
    ('FakeItem', 0)
""")
conn.commit()
```

**Why this matters:** The sample invoices are designed to test your validation logic against this database. For example:

| Scenario                     | Invoice                                                 | What should happen                                |
| ---------------------------- | ------------------------------------------------------- | ------------------------------------------------- |
| Normal order within stock    | INV-1001, INV-1004, INV-1006                            | Items found, quantities valid — passes validation |
| Quantity exceeds stock       | INV-1002 (requests 20× GadgetX, only 5 in stock)        | Flagged as stock mismatch                         |
| Fraudulent / zero-stock item | INV-1003 (references FakeItem, 0 stock)                 | Flagged as out of stock or suspicious             |
| Item not in database at all  | INV-1008 (SuperGizmo, MegaSprocket), INV-1016 (WidgetC) | Flagged as unknown item                           |
| Invalid data                 | INV-1009 (negative quantity)                            | Flagged as data integrity issue                   |

You may extend the seed data with additional items or columns (e.g., unit price, category) to support richer validation — the above is the minimum needed to exercise the provided test invoices. If you want your system to also validate pricing or vendor information, consider adding tables for those as well.

### Mock Payment API

```python
def mock_payment(vendor, amount):
    print(f"Paid {amount} to {vendor}")
    return {"status": "success"}
```

### Grok API Setup

```python
from xai import Grok

client = Grok(api_key="your_key")
response = client.chat.completions.create(
    model="grok-3",
    messages=[{"role": "user", "content": "Reason about this..."}]
)
```

## Running the System

The system should be executable from the command line:

```bash
python main.py --invoice_path=data/invoices/invoice1.txt
```

Output should include structured logs and results.

## Evaluation Criteria

- **Functionality** — Does the system work end-to-end?
- **Code Quality** — Clean, testable, well-structured code with error handling and observability
- **Agentic Sophistication** — LLM integration, multi-agent flow, tool use, self-correction loops
- **Shipping Mindset** — Valuable MVP delivered under ambiguity; scope ruthlessly cut where needed
- **Presentation** — Clear translation of technical decisions to business impact
- **Above/Beyond** - Have you made it your own? Implemented additional features that make the solution feel great? Expanded assumptions? Added to test cases?
- **UI/UX** - Users will understand and enjoy using this system.
