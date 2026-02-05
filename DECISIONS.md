# Architecture Decision Records (ADR)

This document tracks key architectural decisions, trade-offs, and rationale for the invoice processing pipeline.

---

## Decision #1: Auto-Initialize Database in Pipeline (Option A)

**Date:** 2026-02-05  
**Status:** Accepted  
**Context:** Need to decide how to trigger database initialization

### Options Considered

**Option A: Auto-init in pipeline**

- Call `init_database()` at the start of `pipeline/runner.py`
- DB initializes automatically on first pipeline run
- Idempotent design (safe to call multiple times)

**Option B: Standalone initialization script**

- Create `scripts/init_db.py`
- Requires manual setup step: `python -m scripts.init_db`
- Clearer separation of concerns

### Decision

**Chosen: Option A (Auto-init in pipeline)**

### Rationale

- **Developer ergonomics:** Zero-setup experience — just run the pipeline
- **Reduces friction:** No manual initialization step for reviewers/users
- **Idempotent design:** Minimal performance overhead (~1-2ms check per run)
- **Local development friendly:** Works immediately after `git clone`

### Trade-offs

**Pros:**

- Immediate usability
- No forgotten setup steps
- Aligns with "runs fully locally" requirement

**Cons:**

- Slight performance overhead on every pipeline run (mitigated by idempotent check)
- Mixes initialization with runtime logic (less clean separation)

### Implementation Notes

- `init_database()` checks if tables exist before creating
- Seed data only inserted if tables are empty
- Safe to call on every pipeline run

---

## Decision #2: Enhanced Database Schema (Slice 1)

**Date:** 2026-02-05  
**Status:** Accepted  
**Context:** Choose between minimal schema (item + stock) vs enhanced schema (pricing, vendor trust, etc.)

### Options Considered

**Option A: Minimal schema**

- Tables: `inventory(item, stock)`
- Supports 4 validation rules

**Option B: Enhanced schema**

- Tables: `inventory(item, stock, unit_price, category, min/max_order_qty, active)`
- Tables: `vendors(vendor_name, address, payment_terms, trusted)`
- Supports 8 validation rules

### Decision

**Chosen: Option B (Enhanced schema)**

### Rationale

- Enables richer validation (price mismatch, vendor trust, line item amount validation)
- Closer to production-like system
- Sample invoices include price/vendor data — schema should reflect that
- Demonstrates "above & beyond" sophistication

### Trade-offs

**Pros:**

- 8 validation rules vs 4
- Financial validation (price, tax, subtotal)
- Vendor whitelist/blacklist functionality
- More realistic business logic

**Cons:**

- More complex schema to implement
- Slightly more seed data to manage
- Larger surface area for bugs

### Implementation Notes

See `db/schema.py` for full schema definitions and seed data.

---

## Decision #3: Grok + Deterministic Mock Fallback (Slice 1)

**Date:** 2026-02-05  
**Status:** Accepted  
**Context:** Ensure pipeline runs locally without external API dependencies

### Decision

**LLM Client Architecture:**

- Primary: xAI Grok (via `XAI_API_KEY` env var)
- Fallback: Deterministic mock LLM (rule-based responses)

### Rationale

- **Local reproducibility:** System runs end-to-end even without API key
- **Reviewer friendly:** No external dependencies to test the prototype
- **xAI ecosystem alignment:** Supports Grok-first environments when key is available
- **Interface-based design:** LLM backend is transparent to calling code

### Implementation Notes

See `llm/client.py` for interface design.

---

## Decision #4: Database File Location (db/ vs Root)

**Date:** 2026-02-05  
**Status:** Accepted  
**Context:** Initial implementation placed `inventory.db` in project root, violating best practices

### Problem

Original implementation created database file at project root:

```
/
├── inventory.db  ❌ (pollutes project root)
├── db/
│   ├── schema.py
│   └── inventory.py
```

**Issues:**

- Clutters project root directory
- Risk of accidental git commits
- Poor separation of concerns (data mixed with code)
- Not production-ready structure

### Decision

**Move database to `db/inventory.db`**

### Rationale

- **Co-location:** Database file lives with database code (`db/schema.py`, `db/inventory.py`)
- **Clean root:** Project root stays focused on configuration and entry points
- **Git safety:** Clear `.gitignore` pattern (`db/*.db`)
- **Industry standard:** Common Python project convention
- **Semantic clarity:** `db/` directory signals "this is database storage"

### Implementation

1. Changed default path in all `db/inventory.py` functions:

   ```python
   def init_database(db_path: str = "db/inventory.db") -> None:
   ```

2. Updated `.gitignore`:

   ```
   # Database files
   db/*.db
   inventory.db  # Also exclude legacy root location
   ```

3. Updated smoke test to use `db/test_inventory.db`

### Trade-offs

**Pros:**

- Cleaner project structure
- Better separation of concerns
- Follows Python best practices
- Easier to manage in production

**Cons:**

- Breaking change (old `inventory.db` at root won't be found)
- Requires path update in any existing tooling

---

**Last Updated:** 2026-02-05 10:40
