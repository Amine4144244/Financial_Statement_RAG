-- ==============================================================================
-- Financial Statement Intelligence Platform - Seed Data
-- ==============================================================================

-- 1. Insert Sample Companies
INSERT INTO companies (id, name, ticker, country, reporting_currency, sector, industry)
VALUES
    ('company_a', 'Example Corp A', 'EXA', 'US', 'USD', 'Technology', 'Enterprise Software'),
    ('msft', 'Microsoft Corporation', 'MSFT', 'US', 'USD', 'Technology', 'Software Infrastructure'),
    ('aapl', 'Apple Inc.', 'AAPL', 'US', 'USD', 'Technology', 'Consumer Electronics')
ON CONFLICT (id) DO NOTHING;

-- 2. Insert Sample Financial Facts for Company A (Matching Illustrative Scenario in Specs)
-- FY2024: Revenue = $100M, Net Income = $15M, Operating Expenses = $60M
-- FY2025: Revenue = $120M, Net Income = $18M, Operating Expenses = $72M
INSERT INTO financial_facts (company_id, metric, value, currency, unit, scale, fiscal_year, period_type, source_page, statement_type, validation_status)
VALUES
    ('company_a', 'revenue', 100000000.0000, 'USD', 'USD', 'exact', 2024, 'FY', 42, 'income_statement', 'verified'),
    ('company_a', 'net_income', 15000000.0000, 'USD', 'USD', 'exact', 2024, 'FY', 42, 'income_statement', 'verified'),
    ('company_a', 'operating_expenses', 60000000.0000, 'USD', 'USD', 'exact', 2024, 'FY', 42, 'income_statement', 'verified'),
    ('company_a', 'revenue', 120000000.0000, 'USD', 'USD', 'exact', 2025, 'FY', 42, 'income_statement', 'verified'),
    ('company_a', 'net_income', 18000000.0000, 'USD', 'USD', 'exact', 2025, 'FY', 42, 'income_statement', 'verified'),
    ('company_a', 'operating_expenses', 72000000.0000, 'USD', 'USD', 'exact', 2025, 'FY', 42, 'income_statement', 'verified')
ON CONFLICT (company_id, fiscal_year, period_type, metric, is_restated) DO UPDATE 
SET value = EXCLUDED.value, validation_status = EXCLUDED.validation_status;
