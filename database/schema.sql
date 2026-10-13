-- ==============================================================================
-- Financial Statement Intelligence Platform - PostgreSQL Schema
-- ==============================================================================

-- Enable UUID extension if available
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ------------------------------------------------------------------------------
-- 1. Users Table
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(32) DEFAULT 'analyst',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------------------------
-- 2. Companies Table
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS companies (
    id VARCHAR(64) PRIMARY KEY, -- Standardized ticker/slug e.g. 'company_a', 'msft', 'aapl'
    name VARCHAR(255) NOT NULL,
    ticker VARCHAR(16) UNIQUE,
    country VARCHAR(64) DEFAULT 'US',
    reporting_currency VARCHAR(10) DEFAULT 'USD',
    sector VARCHAR(128),
    industry VARCHAR(128),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------------------------
-- 3. Documents Table (Uploaded Filings / Annual Reports)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id VARCHAR(64) NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    fiscal_year INTEGER NOT NULL,
    period_type VARCHAR(16) NOT NULL DEFAULT 'FY', -- 'FY', 'Q1', 'Q2', 'Q3', 'Q4'
    document_type VARCHAR(64) NOT NULL DEFAULT 'annual_report', -- '10-K', 'annual_report', '10-Q'
    original_filename VARCHAR(255) NOT NULL,
    storage_path TEXT NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'uploaded', -- 'uploaded', 'processing', 'completed', 'failed'
    total_pages INTEGER,
    file_size_bytes BIGINT,
    uploaded_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_documents_company_year ON documents(company_id, fiscal_year);

-- ------------------------------------------------------------------------------
-- 4. Document Processing Jobs Table
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS document_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    stage VARCHAR(64) NOT NULL DEFAULT 'QUEUED', 
    -- 'QUEUED', 'PARSING', 'EXTRACTING_FACTS', 'CHUNKING', 'INDEXING_VECTORS', 'COMPLETED', 'FAILED'
    progress_percent INTEGER DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_document_jobs_document_id ON document_jobs(document_id);

-- ------------------------------------------------------------------------------
-- 5. Financial Sources Table (Audit Provenance & Citation Anchors)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS financial_sources (
    id VARCHAR(128) PRIMARY KEY, -- e.g. 'doc123_page42_tab1'
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    page_number INTEGER NOT NULL,
    section_name VARCHAR(128), -- e.g. 'Consolidated Statements of Income', 'MD&A'
    table_identifier VARCHAR(128),
    raw_snippet TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_financial_sources_doc_page ON financial_sources(document_id, page_number);

-- ------------------------------------------------------------------------------
-- 6. Financial Facts Table (Deterministic Ground-Truth Relational Data)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS financial_facts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id VARCHAR(64) NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    document_id UUID REFERENCES documents(id) ON DELETE SET NULL,
    metric VARCHAR(64) NOT NULL, 
    -- e.g. 'revenue', 'net_income', 'operating_income', 'operating_expenses', 
    --      'total_assets', 'total_liabilities', 'operating_cash_flow'
    value NUMERIC(24, 4) NOT NULL, -- Exact decimal value, e.g. 120000000.0000
    currency VARCHAR(10) NOT NULL DEFAULT 'USD',
    unit VARCHAR(32) NOT NULL DEFAULT 'USD',
    scale VARCHAR(32) NOT NULL DEFAULT 'exact', -- 'exact', 'thousands', 'millions', 'billions'
    fiscal_year INTEGER NOT NULL,
    period_type VARCHAR(16) NOT NULL DEFAULT 'FY',
    source_id VARCHAR(128) REFERENCES financial_sources(id) ON DELETE SET NULL,
    source_page INTEGER,
    statement_type VARCHAR(64), -- 'income_statement', 'balance_sheet', 'cash_flow', 'notes'
    validation_status VARCHAR(32) NOT NULL DEFAULT 'pending', -- 'pending', 'verified', 'pending_review', 'rejected'
    is_restated BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_company_metric_period UNIQUE (company_id, fiscal_year, period_type, metric, is_restated)
);

CREATE INDEX IF NOT EXISTS idx_financial_facts_lookup ON financial_facts(company_id, fiscal_year, metric);
CREATE INDEX IF NOT EXISTS idx_financial_facts_status ON financial_facts(validation_status);

-- ------------------------------------------------------------------------------
-- 7. Chat Sessions Table
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) DEFAULT 'New Financial Analysis',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------------------------
-- 8. Chat Messages Table
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role VARCHAR(32) NOT NULL, -- 'user', 'assistant', 'system'
    content TEXT NOT NULL,
    structured_payload JSONB, -- Stores metrics, calculations, citations, validation status
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_chat_messages_session ON chat_messages(session_id, created_at);
