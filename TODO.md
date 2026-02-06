# Invoice Processing Pipeline - Implementation Checklist

## Slice 1: Scaffolding + Models + Pipeline Skeleton ✓

- [x] Create TODO.md master checklist
- [x] Implement enhanced data models (models.py)
- [x] Implement database schema (db/schema.py, db/inventory.py)
- [x] Implement pipeline runner skeleton (pipeline/runner.py)
- [x] Implement stub stage functions (agents/\*.py)
- [x] Implement LLM client interface (llm/client.py)
- [x] Implement structured logging (utils/logging.py)
- [x] Implement CLI entrypoint (main.py)
- [x] Create output directory structure
- [x] Test end-to-end with sample invoice

## Slice 2: SQLite DB Init + Seeding ✓

- [x] Implement database initialization script
- [x] Create enhanced inventory table with pricing
- [x] Create vendors table with trust flags
- [x] Seed inventory with test data (WidgetA, WidgetB, GadgetX, FakeItem)
- [x] Seed vendors with test data (Widgets Inc., Precision Parts, etc.)
- [x] Write smoke test for DB creation
- [x] Write query helper functions for validation stage (deferred to Slice 3)

## Slice 3: Validation Stage + Unit Tests ✓

- [x] Implement validation rule: unknown_item
- [x] Implement validation rule: negative_quantity
- [x] Implement validation rule: quantity_exceeds_stock
- [x] Implement validation rule: out_of_stock
- [x] Implement validation rule: price_mismatch
- [x] Implement validation rule: unknown_vendor
- [x] Implement validation rule: suspicious_vendor
- [x] Implement validation rule: line_item_amount_mismatch
- [x] Write unit tests for each validation rule
- [x] Integration test with sample invoices (requires ingestion - Slice 4)

## Slice 4: Ingestion for JSON/CSV/TXT ✓

- [x] Implement JSON parser (invoice_1004.json, etc.)
- [x] Implement CSV parser (invoice_1006.csv, etc.)
- [x] Implement TXT parser with heuristics (invoice_1001.txt, etc.)
- [x] Handle missing/malformed data gracefully
- [x] Write smoke script to test all sample inputs (scripts/run_samples.py)
- [x] Handle edge cases (empty vendor, null due_date, etc.)

## Slice 5: Approval Stage with Reflection/Critique Loop ✓

- [x] Implement rule-based approval logic (threshold: $10K)
- [x] Integrate Grok for decision reasoning
- [x] Implement initial approval decision
- [x] Implement reflection/critique loop
- [x] Implement decision revision mechanism
- [x] Write tests for revision behavior
- [x] Add fallback to deterministic mock if Grok unavailable
- [x] Implement .env auto-loader (stdlib only)
- [x] Add approval metrics to run_samples.py

## Slice 6: Payment Stage ✓

- [x] Implement mock_payment function
- [x] Gate payment on approval status
- [x] Log payment attempts
- [x] Log rejections with reasoning
- [x] Write tests for payment gating (7 tests, all passing)
- [x] Ensure no payment on rejected invoices
- [x] Add PaymentResult model with audit trail
- [x] Add payment metrics to run_samples.py

## Slice 7: PDF Ingestion (Last) ✓

- [x] Research minimal PDF text extraction library (PyPDF2)
- [x] Implement basic PDF text extraction
- [x] Reuse TXT parsing heuristics on extracted text
- [x] Test with sample PDFs (invoice_1011.pdf, etc.)
- [x] Document limitations in README
- [x] Create requirements.txt with PyPDF2
- [x] Update README with setup instructions
- [x] Add PDF support to run_samples.py

## Slice 8: Polish + Documentation ✓

- [x] Create "run all samples" helper script (python main.py --run_all)
- [x] Update README with setup instructions
- [x] Update README with command examples
- [x] Document assumptions and limitations
- [x] Add architecture overview to README
- [x] Tighten logs for readability (already production-shaped)
- [x] Review and clean up TODO comments (removed from db/inventory.py, llm/client.py)
- [x] Add --run_all flag to main.py for batch processing
- [x] Make result saving default behavior (always saves to out/)
- [x] Add comprehensive sections to README (Overview, How to Run, Architecture, etc.)
- [x] Verify all tests pass (36/36 tests passing)
- [x] Final end-to-end test with all samples

## Above & Beyond: Web UI — FastAPI + React (Optional)

_This section is optional / above-and-beyond. It does not affect CLI functionality._

### Backend (FastAPI) ✓

- [x] Create backend/ directory with FastAPI app scaffold
- [x] Implement POST /api/process endpoint (file upload → run_pipeline)
- [x] Implement GET /api/samples endpoint (list data/invoices/)
- [x] Implement POST /api/process-sample endpoint (sample path → run_pipeline)
- [x] Implement GET /api/health endpoint
- [x] Add Pydantic response schemas matching PipelineResult
- [x] Add CORS middleware for local dev
- [x] Add backend deps to requirements.txt (fastapi, uvicorn, python-multipart, httpx)
- [x] Write backend smoke test (6 tests, all passing)

### Frontend (React + TypeScript) ✓

- [x] Scaffold React app with TypeScript (Vite)
- [x] Create API client module (api.ts)
- [x] Create InvoiceUpload component (file upload + sample selector dropdown)
- [x] Create PipelineResult component (full result display)
- [x] Create ValidationFindings component (findings table with severity badges)
- [x] Create ApprovalDecision component (approved/rejected with reasons)
- [x] Create PaymentResult component (status + reference ID)
- [x] Add basic styling (clean, readable layout)
- [x] Add proxy config for local dev (port 8080)

### Integration ✓

- [x] Verify CLI still works unchanged after adding backend/frontend
- [x] Add run instructions to README
- [x] End-to-end test: upload invoice via UI → see result

## Other Optional Enhancements

- [ ] Batch processing mode
- [ ] Export results to CSV/JSON
- [ ] Historical audit log
- [ ] Performance metrics dashboard
- [ ] Additional validation rules (duplicate invoices, etc.)
- [ ] Email notification on approval/rejection
- [ ] Integration with real payment APIs

---

**Current Status:** All slices complete ✓ | Production-ready prototype delivered
**Last Updated:** 2026-02-05 20:05
