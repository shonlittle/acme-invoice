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
- [ ] Write query helper functions for validation stage (deferred to Slice 3)

## Slice 3: Validation Stage + Unit Tests

- [ ] Implement validation rule: unknown_item
- [ ] Implement validation rule: negative_quantity
- [ ] Implement validation rule: quantity_exceeds_stock
- [ ] Implement validation rule: out_of_stock
- [ ] Implement validation rule: price_mismatch
- [ ] Implement validation rule: unknown_vendor
- [ ] Implement validation rule: suspicious_vendor
- [ ] Implement validation rule: line_item_amount_mismatch
- [ ] Write unit tests for each validation rule
- [ ] Integration test with sample invoices

## Slice 4: Ingestion for JSON/CSV/TXT

- [ ] Implement JSON parser (invoice_1004.json, etc.)
- [ ] Implement CSV parser (invoice_1006.csv, etc.)
- [ ] Implement TXT parser with heuristics (invoice_1001.txt, etc.)
- [ ] Handle missing/malformed data gracefully
- [ ] Write smoke script to test all sample inputs
- [ ] Handle edge cases (empty vendor, null due_date, etc.)

## Slice 5: Approval Stage with Reflection/Critique Loop

- [ ] Implement rule-based approval logic (threshold: $10K)
- [ ] Integrate Grok for decision reasoning
- [ ] Implement initial approval decision
- [ ] Implement reflection/critique loop
- [ ] Implement decision revision mechanism
- [ ] Write tests for revision behavior
- [ ] Add fallback to deterministic mock if Grok unavailable

## Slice 6: Payment Stage

- [ ] Implement mock_payment function
- [ ] Gate payment on approval status
- [ ] Log payment attempts
- [ ] Log rejections with reasoning
- [ ] Write tests for payment gating
- [ ] Ensure no payment on rejected invoices

## Slice 7: PDF Ingestion (Last)

- [ ] Research minimal PDF text extraction library
- [ ] Implement basic PDF text extraction
- [ ] Reuse TXT parsing heuristics on extracted text
- [ ] Test with sample PDFs (invoice_1011.pdf, etc.)
- [ ] Document limitations in README

## Slice 8: Polish + Documentation

- [ ] Create "run all samples" helper script
- [ ] Update README with setup instructions
- [ ] Update README with command examples
- [ ] Document assumptions and limitations
- [ ] Add architecture overview to README
- [ ] Tighten logs for readability
- [ ] Review and clean up TODO comments
- [ ] Final end-to-end test with all samples

## Optional Enhancements (Above & Beyond)

- [ ] Web UI for invoice submission
- [ ] Batch processing mode
- [ ] Export results to CSV/JSON
- [ ] Historical audit log
- [ ] Performance metrics dashboard
- [ ] Additional validation rules (duplicate invoices, etc.)
- [ ] Email notification on approval/rejection
- [ ] Integration with real payment APIs

---

**Current Status:** Slice 2 complete ✓ | Ready for Slice 3 (Validation Rules)
**Last Updated:** 2026-02-05 09:56
