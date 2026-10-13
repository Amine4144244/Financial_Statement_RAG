# Graph Report - Financial Statement RAG  (2026-10-10)

## Corpus Check
- Corpus is ~28,229 words - fits in a single context window. You may not need a graph.

## Summary
- 434 nodes · 808 edges · 34 communities (22 shown, 12 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 54 edges (avg confidence: 0.53)
- Token cost: 1,200 input · 800 output

## Community Hubs (Navigation)
- RAG Query & Orchestration API
- Financial Fact Normalization
- Multi-Period Financial Comparison
- Section-Aware Document Chunking
- Backend Gateway Dependencies
- Express Application Server
- Document Chunk Data Model
- CSS Build & PostCSS Configuration
- Backend TypeScript Tooling
- Frontend UI Dependencies
- Relational Database & Fact Storage
- TypeScript Compiler Options
- React Client & Application Root
- AI Service Health & Ingestion API
- Core Financial RAG Architecture & Verification
- Financial Metric Definitions & Models
- Canonical Financial Retrieval
- Backend Gateway Testing Script
- AI Service API Modules
- Evaluation Benchmark Module
- Deterministic Finance Package
- Answer Generation Package
- Document Ingestion Package
- AI Service Application Package
- Pydantic Schemas Package
- External Services Package
- Test Suite Package
- Table Extraction & Statements
- Example Annual Report Filing

## God Nodes (most connected - your core abstractions)
1. `FinancialNormalizer` - 20 edges
2. `DatabaseService` - 19 edges
3. `ChromaService` - 18 edges
4. `RatioCalculator` - 17 edges
5. `FinancialRAGOrchestrator` - 16 edges
6. `PDFLoader` - 16 edges
7. `TableExtractor` - 16 edges
8. `NormalizedFinancialFact` - 16 edges
9. `FinancialRetriever` - 15 edges
10. `DocumentPage` - 15 edges

## Surprising Connections (you probably didn't know these)
- `Query Router & Semantic Subquery Generator` --calls--> `Deterministic Financial Engine`  [INFERRED]
  RAG_pipeline.md → project_description.md
- `Consolidated Financial Statements` --conceptually_related_to--> `Table Extractor & Normalizer`  [INFERRED]
  sample_annual_report_2025.md → RAG_pipeline.md
- `Item 1A Risk Factors` --conceptually_related_to--> `ChromaDB Vector Retriever`  [INFERRED]
  sample_annual_report_2025.md → RAG_pipeline.md
- `FinancialRetriever` --uses--> `RatioCalculator`  [INFERRED]
  ai-service/app/retrieval/financial_retriever.py → ai-service/app/finance/ratio_calculator.py
- `FinancialRAGOrchestrator` --uses--> `VectorRetriever`  [INFERRED]
  ai-service/app/generation/answer_generator.py → ai-service/app/retrieval/vector_retriever.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Financial RAG Core Architecture Pillars** — project_description_deterministic_financial_engine, project_description_hybrid_rag_architecture, project_description_audit_provenance_verification [EXTRACTED 1.00]

## Communities (34 total, 12 thin omitted)

### Community 0 - "RAG Query & Orchestration API"
Cohesion: 0.07
Nodes (40): execute_rag_query(), BaseModel, post, RAGQueryRequest, FinancialRAGOrchestrator, Full hybrid RAG pipeline coordinating query analysis, dual retrieval,…, AnswerValidator, Any (+32 more)

### Community 1 - "Financial Fact Normalization"
Cohesion: 0.10
Nodes (27): FinancialNormalizer, Maps a raw line-item label to a canonical metric key., Normalizes raw financial metrics, scales, and figures into standardized facts., Inspects table headers, titles, or page snippets to detect currency scale., IngestionPipeline, Any, End-to-end ingestion pipeline coordinating PDF parsing, fact extraction, and…, Runs full ingestion on a financial document PDF. (+19 more)

### Community 2 - "Multi-Period Financial Comparison"
Cohesion: 0.14
Nodes (22): FinancialComparison, Any, Decimal, Compares financial metrics between two fiscal years for the same company., Prepares annual data points formatted for Recharts or dashboard graphs., Provides comparative financial analysis across fiscal years and companies., CalculationError, Any (+14 more)

### Community 3 - "Section-Aware Document Chunking"
Cohesion: 0.12
Nodes (16): Returns a chunk splitting function, using LlamaIndex if available, or regex…, Partitions financial documents into semantic narrative chunks respecting…, SectionAwareChunker, PDFLoader, Extracts text, metadata, and structural layout from financial PDFs., Detects whether a line is likely a major financial section header., Cleans and normalizes extracted narrative text from financial PDF reports., TextCleaner (+8 more)

### Community 4 - "Backend Gateway Dependencies"
Cohesion: 0.06
Nodes (30): dependencies, axios, bcrypt, cors, dotenv, express, jsonwebtoken, multer (+22 more)

### Community 5 - "Express Application Server"
Cohesion: 0.14
Nodes (21): createApp(), config, authController, chatController, companyController, documentController, storage, uploadMiddleware (+13 more)

### Community 6 - "Document Chunk Data Model"
Cohesion: 0.12
Nodes (11): DocumentChunk, Any, Any, Reranks candidate retrieved passages based on relevance to query keywords and…, SimpleReranker, Any, Retrieves narrative passages from ChromaDB with metadata filtering and…, VectorRetriever (+3 more)

### Community 7 - "CSS Build & PostCSS Configuration"
Cohesion: 0.08
Nodes (23): autoprefixer, devDependencies, autoprefixer, postcss, tailwindcss, @types/react, @types/react-dom, vite (+15 more)

### Community 8 - "Backend TypeScript Tooling"
Cohesion: 0.09
Nodes (23): devDependencies, nodemon, ts-node, @types/bcrypt, @types/cors, @types/express, @types/jsonwebtoken, @types/multer (+15 more)

### Community 9 - "Frontend UI Dependencies"
Cohesion: 0.11
Nodes (19): clsx, dependencies, axios, clsx, lucide-react, react, react-dom, react-markdown (+11 more)

### Community 10 - "Relational Database & Fact Storage"
Cohesion: 0.21
Nodes (9): CompanyModel, DatabaseService, DocumentModel, FinancialFactModel, FinancialSourceModel, Any, Manages relational database sessions and operations., Base (+1 more)

### Community 11 - "TypeScript Compiler Options"
Cohesion: 0.15
Nodes (12): compilerOptions, esModuleInterop, forceConsistentCasingInFileNames, module, moduleResolution, outDir, rootDir, skipLibCheck (+4 more)

### Community 12 - "React Client & Application Root"
Cohesion: 0.31
Nodes (6): apiClient, App(), ChatView(), CitationModal(), DashboardView(), UploadView()

### Community 13 - "AI Service Health & Ingestion API"
Cohesion: 0.22
Nodes (7): health_check(), process_document(), ProcessDocumentRequest, Any, BaseModel, post, get

### Community 14 - "Core Financial RAG Architecture & Verification"
Cohesion: 0.20
Nodes (10): Audit Provenance and Verification Layer, Deterministic Financial Engine, Hybrid RAG Architecture, Context Builder & Answer Generator, Query Router & Semantic Subquery Generator, ChromaDB Vector Retriever, Platform Overview & Quickstart, Item 1A Risk Factors (+2 more)

### Community 15 - "Financial Metric Definitions & Models"
Cohesion: 0.40
Nodes (5): FinancialRatioDefinition, MetricType, BaseModel, Enum, str

### Community 16 - "Canonical Financial Retrieval"
Cohesion: 0.40
Nodes (3): Any, Resolves colloquial or alias metric names into canonical keys., Fetches structured facts and computes deterministic ratios for requested…

## Knowledge Gaps
- **79 isolated node(s):** `name`, `version`, `description`, `main`, `build` (+74 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **12 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `uuid` connect `Backend Gateway Dependencies` to `Financial Fact Normalization`, `Relational Database & Fact Storage`, `Section-Aware Document Chunking`?**
  _High betweenness centrality (0.137) - this node is a cross-community bridge._
- **Are the 7 inferred relationships involving `FinancialNormalizer` (e.g. with `NormalizedFinancialFact` and `ScaleType`) actually correct?**
  _`FinancialNormalizer` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `DatabaseService` (e.g. with `IngestionPipeline` and `FinancialRetriever`) actually correct?**
  _`DatabaseService` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `ChromaService` (e.g. with `IngestionPipeline` and `VectorRetriever`) actually correct?**
  _`ChromaService` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `RatioCalculator` (e.g. with `FinancialComparison` and `FinancialRetriever`) actually correct?**
  _`RatioCalculator` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Are the 9 inferred relationships involving `FinancialRAGOrchestrator` (e.g. with `AnswerValidator` and `CitationValidator`) actually correct?**
  _`FinancialRAGOrchestrator` has 9 INFERRED edges - model-reasoned connections that need verification._
- **What connects `name`, `version`, `description` to the rest of the system?**
  _79 weakly-connected nodes found - possible documentation gaps or missing edges._