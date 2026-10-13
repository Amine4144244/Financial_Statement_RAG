# Implementation Plan: Financial Statement Intelligence Platform

## Overview
A production-grade Financial Analysis platform powered by a Hybrid Retrieval-Augmented Generation (RAG) architecture. The platform combines semantic document understanding (LlamaIndex + ChromaDB) with deterministic financial calculations and structured data storage (PostgreSQL). The system is partitioned into three decoupled tiers: a React frontend, an Express application gateway, and a Python/FastAPI intelligence engine.

---

## Architecture Decisions

1. **Decoupled 3-Tier Services Architecture**:
   - `frontend/`: React + Vite + Tailwind CSS + Recharts (User dashboard, chat UI, reports, financial visualization).
   - `backend/`: Node.js + Express (Authentication, tenant/document access control, job queue coordination, chat session state).
   - `ai-service/`: Python + FastAPI (Document parsing, normalization, LlamaIndex vector indexing, ChromaDB, deterministic Python ratio calculator, Groq LLM inference, verification layer).
2. **Deterministic Financial Math over LLM Arithmetic**:
   - Ratios, YoY variations, and margins are calculated using Python's `decimal` module, not by prompts to an LLM.
   - The LLM is strictly used for synthesis, explanation, and narrative extraction based on pre-calculated facts and retrieved passages.
3. **Dual Knowledge Store**:
   - **PostgreSQL**: Source of truth for structured financial facts (`financial_facts`, `financial_sources`, metadata, periods, scales, verification status).
   - **ChromaDB**: Semantic vector store for narrative sections (MD&A, Risk Factors, Notes to Financial Statements).
4. **Strict Grounding and Verification**:
   - Every answer contains citations traceable to document ID and page number.
   - Numerical reconciliation verifies generated numbers against approved PostgreSQL records before client delivery.

---

## Dependency Graph

```
Monorepo Skeleton & Environment Setup
        │
        ├── PostgreSQL Schema & DB Services (Facts & Provenance)
        │       │
        │       ├── Ingestion Engine (PyMuPDF + Pydantic Normalizer)
        │       │       │
        │       │       └── Vector Indexing Pipeline (LlamaIndex + ChromaDB)
        │       │
        │       └── Financial Calculator Engine (Python decimal math)
        │               │
        │               └── Hybrid Query Engine & LLM Orchestrator (FastAPI + Groq)
        │                       │
        │                       └── Verification & Citation Layer
        │                               │
        ├── Express Gateway (Auth, Document Jobs, Session API)
        │       │
        └── React Frontend (Dashboard, Chat, Visualization & Report Exporter)
                │
        End-to-End Evaluation & Observability (Ragas + Benchmark Test Suite)
```

---

## Phase Breakdown & Milestones

### Phase 1: Environment & Project Scaffolding
- Establish directory structure (`ai-service/`, `backend/`, `frontend/`).
- Configure Docker / environment configs and dependency manifests.
- Setup PostgreSQL relational schema (tables: `users`, `companies`, `documents`, `financial_facts`, `financial_sources`, `document_jobs`, `chat_sessions`, `chat_messages`).

### Phase 2: Ingestion & Document Processing Engine (`ai-service`)
- Build PDF text and layout extractor with PyMuPDF.
- Implement financial table extractor and Pydantic normalizer (currency, units/scale conversion, period validation).
- Implement section-aware narrative chunker using LlamaIndex.
- Setup ChromaDB vector storage and embedding pipeline.
- Implement ingestion orchestrator and async job worker.

### Phase 3: Deterministic Financial Engine (`ai-service`)
- Build standalone financial ratio calculator (`revenue_growth`, `net_profit_margin`, `operating_margin`, `debt_to_equity`, handling edge cases like 0 division and restatements).
- Build PostgreSQL query service for parameterized metric retrieval.
- Implement comprehensive unit test suite for mathematical correctness.

### Phase 4: Hybrid RAG Query Engine & Verification (`ai-service`)
- Build query analyzer & router (detecting company, year, metrics, intent, SQL vs. Semantic vs. Hybrid).
- Build semantic retriever with metadata filtering and cross-encoder reranking.
- Implement context assembly pipeline.
- Implement prompt templates and Groq LLM inference service.
- Implement verification layer (numerical reconciliation + citation validation).

### Phase 5: Application Gateway & Coordination (`backend`)
- Implement Express REST API structure with JWT authentication and RBAC.
- Implement document upload handler (Multer) with storage management.
- Implement asynchronous job queue coordination between Express and `ai-service`.
- Implement chat session management and streaming/polling query proxy.

### Phase 6: Frontend Dashboard & Financial UI (`frontend`)
- Setup modern React + Vite application with Tailwind CSS design tokens.
- Build document upload & processing status manager.
- Build interactive Financial Analysis Chat Interface with source citation popovers.
- Build comparative financial dashboard with Recharts (ratios, multi-year comparisons).
- Build analysis report export view.

### Phase 7: Evaluation, Observability & Hardening
- Build 50-100 question automated financial evaluation benchmark.
- Integrate Ragas for faithfulness, context recall, and precision.
- Implement security validation, rate limiting, and observability tracing.

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| PDF table parsing inaccuracies (merged cells, scale notation) | High | Implement strict Pydantic scale normalization, fallback to XBRL/SEC EDGAR data when available, and label unverified figures as `pending_review`. |
| LLM hallucination of financial figures | Critical | Isolate LLM from arithmetic; pre-calculate metrics deterministically in Python; verify generated output against approved DB values. |
| Mixed reporting periods or currency mismatches in comparisons | Medium | Enforce schema validation ensuring metrics compared share matching period types and normalized currency before ratio calculations. |
| Ingestion latency blocking HTTP calls | Medium | Decouple upload from processing via asynchronous background job queues with status polling. |

---

## Definition of Done for Each Phase
- Code is modular, type-safe, and documented.
- All unit and integration tests pass without error.
- Verified end-to-end integration across active boundaries before advancing to subsequent phases.
