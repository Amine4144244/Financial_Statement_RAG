# Financial Statement Intelligence Platform

A production-grade Financial Analysis platform powered by a **Hybrid Retrieval-Augmented Generation (RAG)** architecture combining:
- **Semantic Vector RAG (ChromaDB + LlamaIndex):** Narrative understanding of MD&A, Risk Disclosures, and Footnotes.
- **Structured Relational Storage (PostgreSQL):** Normalized financial facts with strict unit/scale tracking and audit provenance.
- **Deterministic Financial Calculations (Python `decimal`):** Exact mathematical computation of YoY growth and financial ratios (margins, liquidity, leverage).
- **Grounding & Verification Layer:** Reconciles LLM statements against database records and verifies citation validity.

---

## Architecture Overview

```
[ React + Tailwind Frontend ] (Port 5173)
              │
              ▼ HTTPS / REST
[ Node.js + Express Gateway ] (Port 4000)
    │                  │
    ▼                  ▼
[ PostgreSQL ]    [ Python / FastAPI AI Service ] (Port 8000)
                       │         │
                       ▼         ▼
                  [ ChromaDB ] [ Groq LLM API ]
```

---

## Project Structure

```
├── ai-service/              # Python / FastAPI RAG & financial analysis service
│   ├── app/
│   │   ├── api/             # FastAPI route controllers
│   │   ├── ingestion/       # PDF parsing, table extraction, chunking, indexing
│   │   ├── retrieval/       # Query analyzer, router, vector retriever, reranker
│   │   ├── generation/      # Context builder, Groq inference, verification
│   │   ├── finance/         # Deterministic financial math & ratio calculations
│   │   ├── services/        # ChromaDB, PostgreSQL, Groq adapters
│   │   └── schemas/         # Pydantic data transfer models
│   ├── tests/               # Unit and integration test suite
│   ├── requirements.txt     # Python dependencies
│   └── .env.example
├── backend/                 # Node.js + Express application gateway
│   ├── src/                 # Controllers, middleware, routes, services
│   ├── package.json
│   ├── tsconfig.json
│   └── .env.example
├── frontend/                # React + Vite + Tailwind CSS dashboard
│   ├── src/                 # Pages, components, visualization, hooks
│   ├── package.json
│   └── vite.config.js
├── database/                # Relational database schema and migrations
│   └── schema.sql
└── tasks/                   # Project planning and tracking
    ├── plan.md              # System design and phase architecture
    └── todo.md              # Granular task checklist with acceptance criteria
```

---

## Getting Started

Refer to [tasks/todo.md](file:///c:/Project/Financial%20Statement%20RAG/tasks/todo.md) for the active development roadmap and execution status.
