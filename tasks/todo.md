# Tasks: Financial Statement Intelligence Platform

## Phase 1: Environment & Project Scaffolding

### Task 1.1: Project Directory Structure and Configuration
**Description:** Initialize monorepo directory layout (`ai-service/`, `backend/`, `frontend/`), basic package configurations, Python virtual environment definitions, and environment variable templates.
**Acceptance criteria:**
- [x] Directory layout matching the planned architecture created.
- [x] Root README and `.env.example` templates defined for all services.
- [x] `ai-service/requirements.txt` created with pinned foundational libraries (FastAPI, LlamaIndex, ChromaDB, PyMuPDF, Pydantic, Groq).
- [x] `backend/package.json` created with Express, TypeScript/Node dependencies.
- [x] `frontend/package.json` initialized with Vite and React.
**Verification:**
- [x] All config files parse cleanly without syntax errors.
**Dependencies:** None
**Estimated scope:** Small (1-3 files per directory)

---

### Task 1.2: Database Schema & Migration Setup
**Description:** Define PostgreSQL relational schemas for users, companies, documents, jobs, financial facts, sources, and chat messages.
**Acceptance criteria:**
- [x] SQL schema / migrations created with tables: `users`, `companies`, `documents`, `document_jobs`, `financial_facts`, `financial_sources`, `chat_sessions`, `chat_messages`.
- [x] `financial_facts` contains columns: `company_id`, `metric`, `value`, `currency`, `fiscal_year`, `period_type`, `unit`, `source_id`, `validation_status`.
- [x] Foreign keys, indexing on `company_id` + `fiscal_year` + `metric`, and unique constraints defined.
**Verification:**
- [x] Schema SQL script runs cleanly against PostgreSQL or SQLite/in-memory test engine.
**Dependencies:** Task 1.1
**Estimated scope:** Small (1-2 files)

---

## Checkpoint: Phase 1 Foundations
- [x] Directory structure, configurations, and database schemas ready.
- [x] Ready to implement ingestion and calculation engines.

---

## Phase 2: Ingestion & Document Processing Engine (`ai-service`)

### Task 2.1: PDF Extraction Engine
**Description:** Implement `pdf_loader.py` using PyMuPDF to extract text, identify page metadata, and detect page layouts (narrative vs. financial statement tables).
**Acceptance criteria:**
- [x] Extracts text page-by-page while tracking 1-based page numbers.
- [x] Identifies headings, table regions, and cleans common header/footer artifacts.
- [x] Returns structured page objects with layout classifications.
**Verification:**
- [x] Unit tests with sample PDF pages verify clean extraction and page tracking.
**Dependencies:** Task 1.1
**Estimated scope:** Medium (2-3 files)

---

### Task 2.2: Financial Table Parsing & Normalization
**Description:** Implement `table_extractor.py` and `financial_normalizer.py` using Pydantic to parse tables and normalize financial numbers (handling currency, scales like 'in thousands', and negative formats).
**Acceptance criteria:**
- [x] Pydantic schema for `NormalizedFinancialFact` with fields: `metric`, `value`, `currency`, `fiscal_year`, `period_type`, `unit`, `source_page`, `validation_status`.
- [x] Normalizer correctly converts scale (e.g. `120,000` with 'in thousands' -> `120,000,000`).
- [x] Flags unresolvable or ambiguous figures as `pending_review`.
**Verification:**
- [x] Unit tests verify currency, scale conversion, and negative parenthesis handling (e.g., `(15,000)` -> `-15000000`).
**Dependencies:** Task 2.1
**Estimated scope:** Medium (3-4 files)

---

### Task 2.3: Section-Aware Narrative Chunker
**Description:** Implement `chunker.py` using LlamaIndex sentence splitters to create semantic chunks partitioned by document sections (MD&A, Risk Factors, Notes).
**Acceptance criteria:**
- [x] Respects section boundaries so notes and MD&A do not bleed together.
- [x] Generates chunks within 400-800 tokens with configurable overlap.
- [x] Attaches rich metadata to each node (`document_id`, `company_id`, `fiscal_year`, `section`, `page_start`, `page_end`, deterministic `chunk_id`).
**Verification:**
- [x] Chunking unit tests confirm metadata retention and section isolation.
**Dependencies:** Task 2.1
**Estimated scope:** Small (2 files)

---

### Task 2.4: ChromaDB Vector Indexing Service
**Description:** Implement `chroma_service.py` and `indexing.py` to embed and index narrative chunks into ChromaDB with metadata filtering support.
**Acceptance criteria:**
- [x] Embeddings generated using configured embedding model.
- [x] Collection initialized with metadata filtering indices (`company_id`, `fiscal_year`, `document_id`).
- [x] Batch upsert supported with idempotent chunk IDs to prevent duplicates on re-ingestion.
**Verification:**
- [x] Integration test inserts mock chunks and executes filtered semantic queries.
**Dependencies:** Task 2.3
**Estimated scope:** Medium (2-3 files)

---

### Task 2.5: Ingestion Pipeline Orchestrator & API
**Description:** Wire together loading, normalization, DB persistence of facts, and ChromaDB vector indexing under a unified ingestion workflow in FastAPI.
**Acceptance criteria:**
- [x] Ingestion endpoint `/internal/documents/process` accepts document ID and file path.
- [x] Stores normalized facts in PostgreSQL and vectors in ChromaDB.
- [x] Emits detailed processing status events (`PARSING`, `EXTRACTING_FACTS`, `INDEXING_VECTORS`, `COMPLETED`, `FAILED`).
**Verification:**
- [x] End-to-end ingestion test processes a sample report and verifies both PostgreSQL and ChromaDB contain expected records.
**Dependencies:** Tasks 1.2, 2.2, 2.4
**Estimated scope:** Medium (3-4 files)

---

## Checkpoint: Phase 2 Ingestion
- [x] Sample financial report can be processed end-to-end.
- [x] Facts are queryable in PostgreSQL and narrative is searchable in ChromaDB.

---

## Phase 3: Deterministic Financial Engine (`ai-service`)

### Task 3.1: Deterministic Ratio & Growth Calculator
**Description:** Implement `ratio_calculator.py` using Python's `decimal.Decimal` for exact mathematical calculations of financial indicators.
**Acceptance criteria:**
- [x] Calculates: YoY Revenue Growth, Gross Margin, Operating Margin, Net Profit Margin, Debt-to-Equity, Current Ratio.
- [x] Distinguishes between percentage change (YoY growth) and percentage-point change (margin difference).
- [x] Robust error handling for division by zero, missing periods, negative revenue/income, and restated periods.
**Verification:**
- [x] Unit tests with known financial edge cases pass with 100% precision.
**Dependencies:** Task 1.1
**Estimated scope:** Small (2 files)

---

### Task 3.2: Financial Data Retrieval Service
**Description:** Implement `financial_retriever.py` to query PostgreSQL for approved facts matching target companies, fiscal years, and required metrics.
**Acceptance criteria:**
- [x] Parameterized SQL query filters by `company_id`, `fiscal_year`, `metric`, and `validation_status == 'verified'`.
- [x] Resolves metric aliases (e.g., 'sales' -> 'revenue', 'net profit' -> 'net_income').
- [x] Returns structured facts with complete provenance (`source_id`, `source_page`).
**Verification:**
- [x] Integration tests verify accurate retrieval and alias resolution.
**Dependencies:** Tasks 1.2, 3.1
**Estimated scope:** Small (2 files)

---

## Phase 4: Hybrid RAG Query Engine & Verification (`ai-service`)

### Task 4.1: Query Understanding & Intent Routing
**Description:** Implement `query_analyzer.py` and `query_router.py` to parse natural language questions into structured query representations and select retrieval strategy.
**Acceptance criteria:**
- [x] Extracts target companies, fiscal years, metrics, and intent (`FACTUAL`, `CALCULATION`, `NARRATIVE_REASON`, `HYBRID_COMPARISON`).
- [x] Routes query to SQL-only, Semantic-only, or Hybrid execution path.
- [x] Validates extracted company and year parameters against known system entities.
**Verification:**
- [x] Unit tests test various natural language queries against expected routing outputs.
**Dependencies:** Task 3.2
**Estimated scope:** Medium (3 files)

---

### Task 4.2: Semantic Retriever & Reranker
**Description:** Implement `vector_retriever.py` and `reranker.py` to retrieve narrative chunks from ChromaDB with metadata filters and score relevance.
**Acceptance criteria:**
- [x] Queries ChromaDB with target metadata filters (`company_id`, `fiscal_year`).
- [x] Cross-encoder reranker re-orders top-K candidate chunks against the specific question.
- [x] Deduplicates overlapping chunks and limits context window budget.
**Verification:**
- [x] Unit test verifies candidates are filtered correctly by company/year and ranked by relevance.
**Dependencies:** Tasks 2.4, 4.1
**Estimated scope:** Medium (2-3 files)

---

### Task 4.3: Context Builder & Groq LLM Answer Generator
**Description:** Implement `context_builder.py` and `answer_generator.py` to construct structured prompt contexts and query the Groq LLM API.
**Acceptance criteria:**
- [x] Assembles prompt containing: verified facts, Python-calculated ratios, and retrieved narrative passages with source IDs.
- [x] System prompt enforces strict evidence rules: no inventing numbers, cite source page numbers, acknowledge missing data.
- [x] Communicates with Groq API (e.g. `llama-3.3-70b-versatile` or `mixtral-8x7b`).
**Verification:**
- [x] Generation test confirms answer references provided facts and adheres to grounded constraints.
**Dependencies:** Tasks 3.1, 4.2
**Estimated scope:** Medium (3 files)

---

### Task 4.4: Answer Verification & Citation Validation Layer
**Description:** Implement `citation_validator.py` and `answer_validator.py` to inspect the generated answer before delivering it to callers.
**Acceptance criteria:**
- [x] Reconciles numbers in the generated response against approved PostgreSQL facts and calculation outputs.
- [x] Verifies all cited `source_id` references exist in the retrieved context.
- [x] Appends validation flags and warnings if an ungrounded claim or mismatch is detected.
**Verification:**
- [x] Tests verify deliberate injection of false numbers triggers verification failure warnings.
**Dependencies:** Task 4.3
**Estimated scope:** Medium (2-3 files)

---

## Checkpoint: Phase 4 AI Service Complete
- [x] FastAPI `/internal/rag/query` returns grounded, verified answers with metrics, calculated ratios, and citation provenance.

---

## Phase 5: Application Gateway & Job Management (`backend`)

### Task 5.1: Express Authentication & Company Management API
**Description:** Setup Express API with JWT authentication, user accounts, and company management endpoints.
**Acceptance criteria:**
- [x] Auth endpoints: `POST /api/auth/register`, `POST /api/auth/login`, `GET /api/auth/me`.
- [x] Company endpoints: `GET /api/companies`, `POST /api/companies`.
- [x] Middleware for JWT verification and tenant scoping.
**Verification:**
- [x] Integration tests verify user registration, login, and protected route access.
**Dependencies:** Task 1.2
**Estimated scope:** Medium (4-5 files)

---

### Task 5.2: Document Upload & Async Processing Jobs
**Description:** Implement file upload endpoint with Multer, local storage handling, and job status tracking.
**Acceptance criteria:**
- [x] Endpoint `POST /api/documents/upload` accepts PDF, validates file type/size, creates document record in PostgreSQL.
- [x] Creates a job record in `document_jobs` and dispatches processing request to FastAPI AI service.
- [x] Endpoint `GET /api/documents/:id/status` returns current ingestion stage and progress.
**Verification:**
- [x] Integration test simulates document upload and monitors job progression.
**Dependencies:** Tasks 2.5, 5.1
**Estimated scope:** Medium (3-4 files)

---

### Task 5.3: Chat Session & Query Proxy
**Description:** Implement endpoints to manage chat sessions and proxy financial questions to `ai-service`.
**Acceptance criteria:**
- [x] Endpoints: `POST /api/chat/query`, `GET /api/chat/sessions`, `GET /api/chat/sessions/:id/messages`.
- [x] Express validates permissions, logs user message, queries FastAPI `/internal/rag/query`, and persists the validated response with citations.
**Verification:**
- [x] Test verifies user submits question, receives structured answer, and session history is preserved.
**Dependencies:** Tasks 4.4, 5.1
**Estimated scope:** Medium (3-4 files)

---

## Phase 6: Frontend Interface & Visualization (`frontend`)

### Task 6.1: Application Shell & Document Ingestion Dashboard
**Description:** Build the core React application layout, navigation, company selector, and document upload UI with live progress indicators.
**Acceptance criteria:**
- [x] Modern UI layout with sidebar, header, and active company context.
- [x] Drag-and-drop PDF upload component with company/fiscal year selection.
- [x] Real-time ingestion progress display polling `/api/documents/:id/status`.
**Verification:**
- [x] Manual check: user can upload document and view real-time stage updates.
**Dependencies:** Task 5.2
**Estimated scope:** Medium (4-5 files)

---

### Task 6.2: Financial Analysis Chat Interface
**Description:** Build interactive chat component for submitting questions, rendering streaming/structured responses, and displaying citation pills.
**Acceptance criteria:**
- [x] Chat conversation feed with user and assistant messages.
- [x] Renders formatted markdown, highlight cards for verified metrics, and calculated ratios.
- [x] Interactive citation badges that open a preview modal displaying source page and cited excerpt.
**Verification:**
- [x] User can ask financial comparison questions and view cited passages.
**Dependencies:** Task 5.3
**Estimated scope:** Medium (4-5 files)

---

### Task 6.3: Financial Visualization & Multi-Year Comparison
**Description:** Build company comparison view using Recharts to plot revenue, profits, and financial ratios across fiscal years.
**Acceptance criteria:**
- [x] Multi-year bar and line charts for revenue, net income, and operating margins.
- [x] Comparison table rendering normalized financial figures side-by-side with YoY variance.
- [x] Ability to compare 2+ companies or multiple fiscal periods.
**Verification:**
- [x] Verified financial metrics render accurately on charts and match table data.
**Dependencies:** Tasks 5.3, 6.1
**Estimated scope:** Medium (3-4 files)

---

## Phase 7: Evaluation, Observability & Hardening

### Task 7.1: Automated Financial Evaluation Benchmark
**Description:** Build automated test harness with 50+ financial evaluation questions covering exact retrieval, ratio calculations, multi-year comparisons, and ungrounded refusal cases.
**Acceptance criteria:**
- [ ] Benchmark runner tests retrieval recall, mathematical exactness, and refusal behavior when data is missing.
- [ ] Reports accuracy metrics across question categories.
**Verification:**
- [ ] Benchmark runs via CLI command and outputs structured accuracy summary report.
**Dependencies:** Tasks 4.4, 3.1
**Estimated scope:** Medium (3-4 files)

---

### Task 7.2: End-to-End Smoke Tests & Docker Compose Setup
**Description:** Provide `docker-compose.yml` orchestrating PostgreSQL, ChromaDB, `ai-service`, `backend`, and `frontend`, plus end-to-end smoke verification script.
**Acceptance criteria:**
- [ ] `docker-compose.yml` boots all services with health checks.
- [ ] Smoke test script runs: register user -> upload test report -> poll completion -> ask comparison question -> verify response and citations.
**Verification:**
- [ ] `docker-compose up` launches clean and smoke test script exits with code 0.
**Dependencies:** All previous tasks
**Estimated scope:** Medium (3 files)
