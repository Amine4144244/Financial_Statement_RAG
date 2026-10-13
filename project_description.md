# Financial Statement Intelligence Platform

Complete project workflow, system architecture, technology responsibilities, and implementation strategy

We're going to design this as a financial analysis platform powered by Retrieval-Augmented Generation (RAG), rather than a conventional chatbot that answers questions about uploaded PDFs.

The platform will allow users to upload financial reports, automatically extract and organize financial information, ask complex questions, compare companies across different years, and generate analyses supported by verifiable sources.

An important design decision: we will combine semantic RAG for understanding documents with structured financial data processing for accurate calculations.

## 1. Understanding the project

Imagine you're a financial analyst working with the annual reports of three companies.

Traditionally, you would read their financial statements, extract the important figures into Excel, calculate ratios, compare performance, study management explanations, and write a report.

Our application will help automate much of this workflow.

### Main functionalities

Financial document management

Upload annual reports, balance sheets, income statements, and cash flow statements in PDF format. Organize documents by company and fiscal year.

Automatic extraction and indexing

Extract narrative text, financial tables, accounting figures, reporting periods, and document metadata. Make them searchable.

Financial RAG assistant

Ask questions such as "What were the main factors behind the company's declining profitability?" and receive grounded answers with document citations.

Financial ratios and company comparisons

Calculate revenue growth, operating margins, net profit margins, debt ratios, and other indicators. Compare companies and reporting periods.

Analytical reports and evidence

Create summaries, comparison tables, and downloadable reports that reference the underlying financial data and original documents.

## 2. Complete system architecture

I recommend a three-service application, with React for the interface, Express for the application backend, and FastAPI for document intelligence and financial analysis.

Frontend — React + Tailwind CSS

Dashboard · Upload · Chat · Comparisons · Charts

HTTPS / REST API

Backend — Node.js + Express

Authentication · Document ownership · API · Job coordination

PostgreSQL

Users, companies, document metadata, financial facts, chat history

File Storage

Original PDF reports and extracted artifacts

Private authenticated API calls

AI Service — Python + FastAPI

Document processing · Retrieval · Analysis · Calculations

LlamaIndex

RAG orchestration

PyMuPDF

PDF extraction

ChromaDB

Vector retrieval

Groq API

LLM inference

Evaluation & Observability

Ragas · Retrieval metrics · Numerical tests · Logs and traces

This architecture has two major workflows:

1. Ingestion workflow: Transform raw financial documents into usable knowledge and verified financial facts.
2. Query workflow: Understand the user's question, retrieve the appropriate information, calculate necessary figures, and generate an evidence-backed answer.

## 3. Workflow A — Financial document ingestion

This workflow happens when a user uploads a financial report.

1

Upload PDF

React → Express

2

Store file and create job

Express → Storage + PostgreSQL

3

Process document

Worker → Python/FastAPI logic

4

Extract text and tables

PyMuPDF + table extraction

5

Normalize financial facts

Python validation → PostgreSQL

6

Chunk narrative content

LlamaIndex

7

Generate embeddings

Embedding model

8

Index chunks and metadata

ChromaDB

9

Publish processing result

Worker → Express → React

### Step 1 — User uploads a financial document

Technology: React, Express, Multer

The user selects a company and year, uploads the financial report, and starts ingestion.

Example:

| Field       | Example       |
| ----------- | ------------- |
| Company     | Microsoft     |
| Document    | Annual Report |
| Fiscal year | 2025          |
| Format      | PDF           |
| Status      | Uploaded      |

React sends the file to the Express backend using `multipart/form-data`.

```
POST /api/documents/upload
Content-Type: multipart/form-data
```

Express is responsible for authenticating the user, checking permissions, validating file type and size, and creating a document record.

The original PDF is stored in local file storage for the MVP, or object storage such as S3 in a deployed version. PostgreSQL stores its identifier and storage location, not the entire PDF.

The ingestion task receives a unique job ID and moves to the processing queue.

Why not process the document immediately inside Express? PDF extraction, embeddings, and indexing can take much longer than an ordinary HTTP request. A background worker processes the queued task while the interface displays its progress.

### Step 2 — Extract financial document content

Technology: Python, PyMuPDF, table extraction tools

The AI processing worker reads the document and extracts two different types of information.

Narrative information

Management discussions, risk factors, business strategy, operational performance, and explanations for financial changes.

Structured information

Income statements, balance sheets, cash flow statements, accounting figures, units, and reporting periods.

Example of extracted text:

> "Operating expenses increased due to investments in research and development."

Example of an extracted table:

| Financial metric   | FY2024 | FY2025 |
| ------------------ | ------ | ------ |
| Revenue            | $100M  | $120M  |
| Net income         | $15M   | $18M   |
| Operating expenses | $60M   | $72M   |

Illustrative financial figures, not actual Microsoft results.

Financial tables require special attention. A standard text extractor can lose row-column relationships, units, or negative-value notation. You should validate extracted tables against the original document before treating the figures as trustworthy.

For publicly listed US companies, structured XBRL filings can also provide a more reliable source for many financial figures than PDF table extraction alone.

### Step 3 — Normalize and validate financial figures

Technology: Python, Pydantic, PostgreSQL

This stage is essential because financial values have contextual meaning.

For example, `120` could mean $120, $120 million, a quarterly figure, or an annual figure.

We transform extracted figures into consistent, structured records.

```
{
  "company": "Example Corp",
  "metric": "revenue",
  "value": 120000000,
  "currency": "USD",
  "fiscal_year": 2025,
  "period_type": "FY",
  "unit": "USD",
  "source_page": 42,
  "validation_status": "verified"
}
```

Pydantic validates the expected structure and types. Python performs unit conversion and consistency checks.

The application must distinguish between extracted facts and verified facts. A successfully parsed value is not automatically correct.

The records should preserve their sources, reporting period, currency, units, accounting basis, and whether they represent consolidated or segment-level results.

### Step 4 — Chunk narrative documents

Technology: LlamaIndex

We cannot simply embed an entire 150-page annual report as one searchable unit.

LlamaIndex divides text into smaller chunks while retaining useful metadata.

For example, a report might produce:

SAMPLE DOCUMENT CHUNKS

Chunk 001 — Business Overview

Company operations, products, strategic positioning...

Chunk 002 — Risk Factors

Market competition, regulatory and financial risks...

Chunk 003 — Management Discussion

Factors influencing revenue growth, expenses, and margins...

For each chunk, preserve:

- Document ID, company ID, and fiscal year.
- Page number and section name.
- Chunk ID and content.
- Source document version.
- User or organization ownership information.

Start with section-aware chunking using around 400–800 tokens and test different sizes. Don't split financial tables arbitrarily. Keep related headings and explanations together.

### Step 5 — Generate embeddings and index chunks

Technology: Embedding model, ChromaDB

An embedding model converts each chunk into a numerical vector representing semantic information.

ORIGINAL CHUNK

"Operating profit increased due to stronger cloud service demand."

Embedding model

Text → numerical vector

VECTOR (ILLUSTRATIVE)

[0.124, -0.382, 0.762, 0.091, ...]

ChromaDB Collection

Vector + chunk text + metadata + chunk ID

ChromaDB stores and indexes these embeddings so that, when the user asks a question, the system can find related passages even without exact keyword matches.

For example, a question about profitability improvement may retrieve text discussing higher margins or lower operating costs.

ChromaDB also supports metadata filters, so a search can be restricted to a specific company, report, or fiscal year.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://github.com\&sz=32)

GitHub



One distinction is important: ChromaDB does not necessarily generate embeddings itself. You configure an embedding function or generate vectors with a separate model. Use the same compatible embedding model for indexing and queries.

For your first version, use ChromaDB's persistent local mode. Later, if you need independent processes connecting to a shared vector database, move to its client-server mode.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://github.com\&sz=32)

GitHub



## 4. Workflow B — How the financial RAG assistant answers questions

This is what happens after documents have been processed and indexed.

Let's use a practical example.

User question:

> "How did Company A's revenue and net profit margin change from 2024 to 2025, and what explains the changes?"

The system needs financial figures, calculations, and written explanations. A single vector search is insufficient.

### Complete query workflow

User Question

React chat interface

Express API

Authentication, authorization, request validation

Python Query Planner

Identify company, periods, metrics, and question type

Select the necessary retrieval paths

Structured Retrieval

PostgreSQL

Fetch revenue, net income, reporting periods

Semantic Retrieval

ChromaDB

Find explanations, management commentary, and source passages

Python Calculator

Compute and validate financial ratios

Reranker

Select the most relevant evidence

LLM — Answer Generation

Combine verified figures, calculations, and retrieved passages

Validation & Citation Layer

Verify numbers, source references, and unsupported claims

Final Response

Financial explanation · Tables · Charts · Citations

### Step 1 — Understand the user's question

Technology: Python, Pydantic, optionally LLM structured output

The query planner transforms the natural-language question into a structured request.

```
{
  "intent": "financial_comparison",
  "companies": ["Company A"],
  "years": [2024, 2025],
  "metrics": [
    "revenue",
    "net_income",
    "net_profit_margin"
  ],
  "requires_calculation": true,
  "requires_narrative_retrieval": true
}
```

The planner decides whether it needs the SQL database, ChromaDB, or both.

| Question                              | Retrieval strategy       |
| ------------------------------------- | ------------------------ |
| What was revenue in 2025?             | Structured SQL           |
| What risks did management identify?   | Semantic RAG             |
| Calculate profit margin in 2025.      | SQL + Python calculator  |
| Why did profitability decline?        | SQL + RAG                |
| Compare three companies' performance. | SQL + calculations + RAG |

For basic questions, you do not need an LLM to do complex planning. Explicit rules and typed parameters are often faster and more reliable.

### Step 2 — Retrieve relevant information

Technologies: PostgreSQL, ChromaDB, LlamaIndex

The AI service executes two retrieval paths.

Path A: Structured financial retrieval

The Python service obtains numerical values from PostgreSQL.

Example:

| Metric     | FY2024 | FY2025 |
| ---------- | ------ | ------ |
| Revenue    | $100M  | $120M  |
| Net income | $15M   | $18M   |

Path B: Semantic document retrieval

LlamaIndex prepares the semantic search, including metadata filters for Company A and the relevant reporting years.

ChromaDB retrieves passages mentioning revenue drivers, changes in expenses, company strategy, and management explanations.

A reranker can then reorder the retrieved passages based on their relevance to the exact question.

This avoids relying solely on embedding similarity, which may not rank every relevant financial passage correctly.

### Step 3 — Perform financial calculations

Technology: Python

This is where the financial intelligence comes from.

The calculations should be deterministic and independently testable.

Example calculation — Illustrative data

Revenue growth

\\[ \frac{Revenue\_{2025}-Revenue\_{2024}}{Revenue\_{2024}}\times100 \\]

\\[ \frac{120-100}{100}\times100=20\\% \\]

Net profit margin

\\[ \frac{Net\ Income}{Revenue}\times100 \\]

2024 margin

# 15%

2025 margin

# 15%

Interpretation: Revenue grew by 20%, but the net profit margin stayed constant. Net income increased proportionally with revenue.

The LLM should explain these results, not invent or independently recalculate them.

Your calculator also needs to handle division by zero, missing values, negative income, currency differences, changes in fiscal periods, and reporting restatements.

### Step 4 — Generate the financial answer

Technology: Groq API + LLM, orchestrated through Python

The AI service builds a prompt containing:

- The original user question.
- Verified financial metrics and calculated ratios.
- Retrieved narrative excerpts.
- Source identifiers, years, and page references.
- Explicit instructions to separate facts from interpretation and acknowledge missing evidence.

Example of a generated response:

Financial Analysis — Company A

Example

Revenue increased from $100M in FY2024 to $120M in FY2025, representing 20% growth. Net income also rose by 20%, from $15M to $18M.

Revenue

Net income

$0$35$70$105$14020242025

Illustrative financial data, USD millions.

Despite higher revenue, the company's net profit margin remained at 15%.

A supporting management commentary passage in the fictional source report attributes revenue growth to stronger product demand.

Source: Example Annual Report, Page 42

Illustrative citation only. In the real application this links to the exact uploaded document and source passage.

### Step 5 — Validate the response

Technology: Python validators, Pydantic, source verification

Before displaying the answer, the AI service should check that:

1. Every displayed financial metric matches a retrieved, approved database record.
2. Calculated values match the deterministic calculation results.
3. Every cited passage exists and belongs to the correct document.
4. Statements about causes, risks, or management explanations are actually supported by retrieved passages.
5. Missing evidence is disclosed rather than replaced with speculation.

Automatic LLM-based verification can help, but it cannot guarantee factual correctness. Numerical reconciliation and source-ID checks are therefore separate responsibilities.

The final structured response is returned to Express and then React.

## 5. Role of each technology

Here is how I would organize the technology choices for this project.

| Technology         | Main responsibility            | Why we need it                                                       |
| ------------------ | ------------------------------ | -------------------------------------------------------------------- |
| React + Vite       | Frontend pages and components  | Responsive interactive application                                   |
| Tailwind CSS       | UI styling                     | Dashboard design and reusable styling                                |
| Recharts           | Financial visualizations       | Graphs for revenue, profit, and ratios                               |
| Node.js + Express  | Main application API           | Authentication, users, document management, chat history             |
| PostgreSQL         | Relational database            | Financial figures, companies, reports, sources, and application data |
| File storage       | Store original reports         | Preserve PDFs independently of vector indexes                        |
| Python + FastAPI   | AI processing service          | RAG workflows, extraction, numerical analysis                        |
| PyMuPDF            | PDF text and layout extraction | Read annual reports                                                  |
| Pydantic           | Data validation                | Enforce structured extraction and query schemas                      |
| LlamaIndex         | RAG framework                  | Chunking, retrieval, indexing, and query orchestration               |
| ChromaDB           | Vector database                | Store embeddings and retrieve semantically relevant passages         |
| Embedding model    | Text vectorization             | Represent document passages and queries numerically                  |
| Groq API           | Hosted LLM inference           | Query understanding, financial explanations, summaries               |
| Ragas              | RAG evaluation                 | Measure retrieval relevance and answer faithfulness                  |
| Job queue + worker | Asynchronous processing        | Process PDF ingestion outside user-facing HTTP requests              |

### Why have Express and FastAPI?

They solve different problems.

Express = Application backend

Handles accounts, permissions, file uploads, chat sessions, company records, API routing, and coordination with the AI service.

FastAPI = Intelligence backend

Processes financial documents, orchestrates retrieval, calls AI models, performs financial calculations, and produces structured analyses.

The React application communicates only with Express, not directly with the AI service or the vector database.

Express calls private FastAPI endpoints with service authentication. FastAPI accesses financial data using appropriately limited database credentials.

You could technically implement everything in Python. The two-backend architecture is an intentional choice for separating product functionality from AI processing, but it adds deployment and integration complexity.

### Why PostgreSQL and ChromaDB together?

Because they represent two fundamentally different ways of finding information.

PostgreSQL:

> "Return Company A's net income for fiscal year 2025."

It performs exact filtering, aggregation, and numerical operations.

ChromaDB:

> "Find passages that explain why Company A's profitability declined."

It finds text using semantic similarity.

ChromaDB should not be treated as the source of truth for financial metrics. PostgreSQL should not be expected to replace semantic document understanding without additional search capabilities.

### Why LlamaIndex rather than LangChain?

Both can support this project. I would start with LlamaIndex because the initial challenge is document ingestion, metadata-aware retrieval, and connecting retrieval to structured analysis.

You do not need LangChain, LlamaIndex, and LangGraph simultaneously.

You can implement the initial pipeline with LlamaIndex and ordinary Python functions. Add a workflow engine only when conditional routing, retries, or more advanced processing genuinely justify it.

## 6. Database design

I recommend PostgreSQL because we need structured relationships between users, companies, financial reports, and individual financial figures.

For the MVP, these are the core tables:

| Table               | Purpose                     | Important fields                                 |
| ------------------- | --------------------------- | ------------------------------------------------ |
| `users`             | Account management          | id, email, password_hash                         |
| `companies`         | Company information         | id, name, ticker, country, currency              |
| `documents`         | Uploaded financial reports  | id, company_id, year, storage_key, status        |
| `document_jobs`     | Processing status           | id, document_id, stage, error                    |
| `financial_facts`   | Extracted financial figures | id, company_id, metric, value, period, source_id |
| `financial_sources` | Provenance records          | id, document_id, page, table, source_reference   |
| `chat_sessions`     | User conversations          | id, user_id, company_id                          |
| `chat_messages`     | Questions and answers       | id, session_id, role, content                    |

The key table is `financial_facts`. It should also record currency, unit, period start/end, source filing, accounting taxonomy, and verification status.

For multiple users, add ownership and organization relationships to company documents and chat sessions. A user's access to a company must not automatically provide access to every private document about that company.

ChromaDB stores chunks separately, but they reference the same `document_id` and source identifiers. This is how a retrieved passage can be traced back to its original PDF.

## 7. API design and service communication

The frontend should have a single public API boundary: Express.

### Express endpoints

| Endpoint                        | Method   | Function                   |
| ------------------------------- | -------- | -------------------------- |
| `/api/auth/register`            | POST     | Create account             |
| `/api/auth/login`               | POST     | Authenticate               |
| `/api/auth/me`                  | GET      | Current user               |
| `/api/companies`                | GET/POST | List or add companies      |
| `/api/documents/upload`         | POST     | Upload financial report    |
| `/api/documents/:id/status`     | GET      | Check ingestion progress   |
| `/api/companies/:id/financials` | GET      | Retrieve financial figures |
| `/api/companies/compare`        | POST     | Compare selected companies |
| `/api/chat/query`               | POST     | Submit financial question  |
| `/api/chat/sessions`            | GET      | Chat history               |
| `/api/reports/generate`         | POST     | Generate analysis report   |

### Internal FastAPI endpoints

| Endpoint                         | Function                           |
| -------------------------------- | ---------------------------------- |
| `/internal/documents/process`    | Run document ingestion             |
| `/internal/rag/query`            | Execute financial RAG queries      |
| `/internal/financials/extract`   | Extract structured financial facts |
| `/internal/financials/calculate` | Calculate financial indicators     |
| `/internal/retrieval/search`     | Retrieve document evidence         |
| `/health`                        | Service health                     |

For long-running ingestion, prefer a job queue rather than calling an HTTP processing endpoint and keeping the request open. A worker can reuse the same Python processing functions that FastAPI exposes.

### Example: asking a financial question

POST /api/chat/query

```
{
  "company_ids": ["company_123"],
  "years": [2024, 2025],
  "question": "Why did profitability decline?"
}
```

RESPONSE

```
{
  "answer": "The available reports indicate...",
  "metrics": [],
  "citations": [
    {
      "document_id": "doc_456",
      "page": 42,
      "chunk_id": "chunk_789"
    }
  ],
  "status": "completed"
}
```

These are proposed endpoints and response formats, not existing APIs.

## 8. Where will the financial data come from?

For your initial version, I'd use US public company reports because of the availability of standardized regulatory data.

The [SEC EDGAR APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces) provide publicly accessible submissions and XBRL financial data. In particular, `companyfacts` exposes structured financial concepts, including units and reporting contexts.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://www.sec.gov\&sz=32)

EDGAR Application Programming Interfaces (APIs)



This gives us two complementary ingestion routes:

PDF / annual report pipeline

Extract narrative sections, management commentary, risks, and the original page references. Store embeddings in ChromaDB.

XBRL financial data pipeline

Retrieve standardized accounting facts, map the financial metrics, verify their units and fiscal periods, and store the selected figures in PostgreSQL.

This dual ingestion approach is preferable to relying entirely on PDF text extraction.

A potential limitation: not every company reports the same metrics in directly comparable ways. The system must consider differences in accounting policies, fiscal years, company-specific taxonomy tags, and restated financial statements.

## 9. Evaluation: how will you prove the system works?

For this project, I would evaluate three things independently.

| Component          | Evaluation                                                                 |
| ------------------ | -------------------------------------------------------------------------- |
| Retrieval          | Recall\@K, Precision\@K, MRR, source-page relevance                        |
| Generation         | Faithfulness, answer relevance, citation support                           |
| Financial accuracy | Exact-value accuracy, calculation correctness, unit and period consistency |

Ragas provides retrieval and generation metrics such as context precision, recall, and faithfulness.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://docs.ragas.io\&sz=32)

Ragas



However, a high faithfulness score is not sufficient to prove that a financial calculation is accurate. The system could faithfully repeat an incorrectly extracted figure.

I would build a dedicated benchmark with approximately 50–100 questions covering direct fact retrieval, ratios, multi-year comparisons, narrative explanations, and missing-data cases.

Use tests where the expected numerical answer is known, and ensure the system refuses to calculate when required information is unavailable or incomparable.