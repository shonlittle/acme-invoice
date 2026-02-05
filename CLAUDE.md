# CLAUDE.md — Invoice Processing Prototype (Cline + Claude Sonnet 4.5)

This file defines guardrails and working conventions for AI-assisted development in this repository using **Cline** with **claude-sonnet-4-5-20250929**.

## Project Goal

Build a **local, runnable invoice-processing prototype** with a 4-stage pipeline:

1. **Ingestion**: Extract structured fields from invoice inputs (PDF/TXT/CSV/JSON):
   - vendor
   - amount/total
   - due date (if present)
   - line items (name + quantity)
2. **Validation**: Check items/quantities against a local **SQLite** `inventory.db` and produce structured findings:
   - unknown item
   - negative quantity
   - quantity exceeds stock
   - out of stock (stock == 0)
3. **Approval**: Simulate VP review with **rule-based** logic PLUS a **reflection/critique loop** that can revise the initial decision.
4. **Payment**: If approved, call a local `mock_payment(vendor, amount)`; if rejected, log rejection + reasoning.

## Non-Negotiables

- **Runs fully locally** (no external API calls).
- **Must run end-to-end** even if no keys are present:
  - If an LLM interface is requested, implement a **deterministic mock backend** so reviewers can run everything.
- **Keep dependencies minimal**:
  - Prefer Python stdlib (`sqlite3`, `argparse`, `json`, `csv`, `logging`, `re`, `datetime`).
  - Ask before adding any new dependency (especially PDF libs).
- **Primary interface** is CLI:
  - `python main.py --invoice_path <path>`
- **Outputs**:
  - structured logs per stage
  - final `PipelineResult` printed as JSON
  - (optional but recommended) write result JSON to `out/`

## Repo Reality Check (First Step)

Before implementing anything:

- list repo files/folders
- read `README.md` end-to-end
- identify data inputs under `data/`
- identify any existing `.env` behavior (do not require it to run)

## Development Workflow (Slices)

Do NOT attempt a one-shot implementation. Work in **small, reviewable slices**.

**Stop after each slice** and summarize:

- files changed/added
- how to run
- expected output

## Architecture Guidance

Prefer a simple, explicit module structure, e.g.:

- `main.py` (CLI entrypoint)
- `models.py` (dataclasses or Pydantic models)
- `utils/logging.py` (structured logging helpers)

## Logging & Observability

Each stage should emit a structured event, e.g.:

- `STAGE_START` / `STAGE_END`
- `INGEST_PARSED`
- `VALIDATION_FINDINGS`
- `APPROVAL_INITIAL_DECISION`
- `APPROVAL_REFLECTION`
- `PAYMENT_ATTEMPT` / `PAYMENT_RESULT`

Logs should be understandable by a reviewer reading console output.

## Deterministic “AI” Behavior

If implementing any “LLM-like” calls:

- provide an interface (e.g., `LLMClient`)
- default implementation is **deterministic mock** (rule-based, seeded, or pure function)
- never block the pipeline on an unavailable model

## Guardrails for Cline

Cline must:

- show a short plan before writing new files
- keep diffs minimal and localized
- ask before:
  - adding dependencies
  - changing module layout after slice 1
  - running commands that modify environment
- avoid refactoring unrelated code
- prioritize a runnable prototype over sophistication

## Testing

Minimum:

- DB init smoke test (table exists; seed rows present)
- validation rule tests (one test per rule)
- approval reflection test (covers revised decision case)
- payment gating test (reject => no payment)

Prefer `pytest` only if already allowed/expected; otherwise minimal stdlib tests are fine.

## Reviewer Ergonomics

Make it easy to evaluate:

- one command to run a single invoice
- one command/script to run all sample invoices and summarize results
- README documents:
  - setup
  - commands
  - assumptions/limitations (especially PDF parsing)
  - architecture overview
