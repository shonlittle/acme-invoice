# Architecture Decision Records (ADR)

This document tracks key architectural decisions, trade-offs, and rationale for the invoice processing pipeline.
It is intended to help reviewers understand *why* the system is designed the way it is, not just *how* it works.

---

## Decision #1: Auto-Initialize Database in Pipeline

**Date:** 2026-02-05  
**Status:** Accepted  

**Context:**  
The system requires a local SQLite database with inventory and vendor data. We needed to decide whether initialization should be manual or automatic.

### Options Considered

**Option A: Auto-initialize database in the pipeline (Chosen)**  
The pipeline checks for the database on first run and initializes/seeds it automatically if missing.

**Pros:**
- Zero manual setup for reviewers
- Fully runnable out of the box
- Better developer and demo ergonomics
- Aligns with prototype-first delivery

**Cons:**
- Slightly less explicit than a manual init step
- Requires care to avoid accidental re-initialization

---

## Decision #2: Agentic Pipeline Decomposition

**Date:** 2026-02-05  
**Status:** Accepted  

**Decision:**  
Decompose invoice processing into explicit agents:
Ingestion → Validation → Approval → Reflection → Payment.

**Rationale:**
- Mirrors real enterprise workflows
- Enables independent testing and reasoning per stage
- Makes audit, replay, and evaluation straightforward

**Trade-offs:**
- More structure and boilerplate than a monolithic script
- Requires well-defined contracts between agents

---

## Decision #3: Deterministic-First, LLM-Optional Design

**Date:** 2026-02-05  
**Status:** Accepted  

**Decision:**  
Use deterministic logic by default, with optional LLM (Grok via xAI) integration only in the Approval → Reflection step.

**Rationale:**
- Business-critical logic must be predictable and testable
- Enterprises require graceful degradation when LLMs are unavailable
- Keeps CI and tests deterministic

**Trade-offs:**
- Less “flashy” than fully LLM-driven systems
- Some nuanced judgment is deferred until LLM is enabled

---

## Decision #4: Reflection Loop for Approval Decisions

**Date:** 2026-02-05  
**Status:** Accepted  

**Decision:**  
Include a reflection/critique step that can revise the initial approval decision.

**Rationale:**
- Demonstrates agentic self-correction
- Matches real-world review workflows (initial decision → second look)
- Improves reliability without constant human oversight

**Trade-offs:**
- Additional decision-modeling complexity
- Requires careful logging for explainability

---

## Decision #5: Local-First, Fully Runnable Prototype

**Date:** 2026-02-05  
**Status:** Accepted  

**Decision:**  
Ensure the entire system runs locally with no external services required.

**Rationale:**
- Reviewer-friendly
- Predictable execution for demos and tests
- Matches early customer prototype constraints

**Trade-offs:**
- Mocked integrations (payment, LLM) instead of real services
- Auth and secrets management intentionally out of scope

---

## Decision #6: SQLite for Inventory and Vendor Data

**Date:** 2026-02-05  
**Status:** Accepted  

**Decision:**  
Use SQLite as the backing store for inventory and vendor data.

**Rationale:**
- Zero setup
- Clear, inspectable SQL schema
- Sufficient for prototype scale

**Trade-offs:**
- Not horizontally scalable
- Limited concurrency guarantees

---

## Decision #7: Structured Logs and JSON Artifacts

**Date:** 2026-02-05  
**Status:** Accepted  

**Decision:**  
Emit structured logs at each stage and persist PipelineResult JSON artifacts.

**Rationale:**
- Enables debugging and auditability
- Supports future history and metrics features
- Aligns with enterprise observability expectations

**Trade-offs:**
- Slight logging overhead
- Requires discipline to keep schemas stable

---

## Decision #8: CLI as Canonical Interface

**Date:** 2026-02-05  
**Status:** Accepted  

**Decision:**  
Treat the CLI as the primary interface; UI is a thin optional wrapper.

**Rationale:**
- Easiest surface to test and automate
- Prevents UI concerns from leaking into business logic
- Backend and API reuse the same execution path

**Trade-offs:**
- Less immediately friendly without UI
- Requires wrapper for non-technical users

---

## Decision #9: FastAPI + React for Optional Web UI

**Date:** 2026-02-05  
**Status:** Accepted  

**Decision:**  
Use FastAPI (backend) and React + TypeScript (frontend) for the optional web UI.

**Rationale:**
- Production-shaped, widely adopted stack
- Clear separation of concerns
- Familiar to enterprise teams

**Trade-offs:**
- More setup than single-file UI frameworks
- Requires packaging (Docker) for easiest launch

---

## Decision #10: Docker as Optional Packaging Layer

**Date:** 2026-02-05  
**Status:** Accepted  

**Decision:**  
Treat Docker and docker-compose as optional, not required.

**Rationale:**
- Demonstrates deployability without forcing tooling
- Keeps local dev friction low
- Matches forward-deployed realities

**Trade-offs:**
- Additional files to maintain
- Risk of over-engineering if introduced too early

---

## Decision #11: Explicit Scope Control via TODO.md

**Date:** 2026-02-05  
**Status:** Accepted  

**Decision:**  
Explicitly mark “Above & Beyond” features as optional in TODO.md.

**Rationale:**
- Prevents scope creep
- Communicates delivery discipline
- Helps reviewers separate core requirements from extensions

**Trade-offs:**
- Attractive features intentionally deferred
- Requires clear documentation to avoid misinterpretation

---

**Last Updated:** {datetime.now().strftime("%Y-%m-%d %H:%M")}
