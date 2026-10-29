-- ============================================
-- TABLE 1 : COMPANIES
-- ============================================

CREATE TABLE companies (

    id TEXT PRIMARY KEY,

    company_logo TEXT,
    company_name TEXT,
    chart_link TEXT,
    about_company TEXT,
    website TEXT,
    nse_profile TEXT,
    bse_profile TEXT,

    face_value REAL,
    book_value REAL,
    roce_percentage REAL,
    roe_percentage REAL

);

-- ============================================
-- TABLE 2 : ANALYSIS
-- ============================================

CREATE TABLE analysis (

    id INTEGER PRIMARY KEY,

    company_id TEXT,

    compounded_sales_growth REAL,
    compounded_profit_growth REAL,
    stock_price_cagr REAL,
    roe REAL,

    FOREIGN KEY(company_id)
        REFERENCES companies(id)

);

-- ============================================
-- TABLE 3 : BALANCE SHEET
-- ============================================

CREATE TABLE balancesheet (

    id INTEGER PRIMARY KEY,

    company_id TEXT,
    year INTEGER,

    equity_capital REAL,
    reserves REAL,
    borrowings REAL,
    other_liabilities REAL,
    total_liabilities REAL,

    fixed_assets REAL,
    cwip REAL,
    investments REAL,
    other_asset REAL,
    total_assets REAL,

    FOREIGN KEY(company_id)
        REFERENCES companies(id)

);

-- ============================================
-- TABLE 4 : CASHFLOW
-- ============================================

CREATE TABLE cashflow (

    id INTEGER PRIMARY KEY,

    company_id TEXT,
    year INTEGER,

    operating_activity REAL,
    investing_activity REAL,
    financing_activity REAL,
    net_cash_flow REAL,

    FOREIGN KEY(company_id)
        REFERENCES companies(id)

);

-- ============================================
-- TABLE 5 : DOCUMENTS
-- ============================================

CREATE TABLE documents (

    id INTEGER PRIMARY KEY,

    company_id TEXT,
    year INTEGER,

    annual_report TEXT,

    FOREIGN KEY(company_id)
        REFERENCES companies(id)

);

-- ============================================
-- TABLE 6 : FINANCIAL RATIOS
-- ============================================

CREATE TABLE financial_ratios (

    id INTEGER PRIMARY KEY,

    company_id TEXT,
    year INTEGER,

    net_profit_margin_pct REAL,
    operating_profit_margin_pct REAL,
    return_on_equity_pct REAL,

    debt_to_equity REAL,
    interest_coverage REAL,
    asset_turnover REAL,

    free_cash_flow_cr REAL,
    capex_cr REAL,

    earnings_per_share REAL,
    book_value_per_share REAL,

    dividend_payout_ratio_pct REAL,

    total_debt_cr REAL,
    cash_from_operations_cr REAL,

    FOREIGN KEY(company_id)
        REFERENCES companies(id)

);

-- ============================================
-- TABLE 7 : MARKET CAP
-- ============================================

CREATE TABLE market_cap (

    id INTEGER PRIMARY KEY,

    company_id TEXT,
    year INTEGER,

    market_cap_crore REAL,
    enterprise_value_crore REAL,

    pe_ratio REAL,
    pb_ratio REAL,
    ev_ebitda REAL,

    dividend_yield_pct REAL,

    FOREIGN KEY(company_id)
        REFERENCES companies(id)

);

-- ============================================
-- TABLE 8 : PEER GROUPS
-- ============================================

CREATE TABLE peer_groups (

    id INTEGER PRIMARY KEY,

    peer_group_name TEXT,
    company_id TEXT,
    is_benchmark INTEGER,

    FOREIGN KEY(company_id)
        REFERENCES companies(id)

);

-- ============================================
-- TABLE 9 : PROFIT & LOSS
-- ============================================

CREATE TABLE profitandloss (

    id INTEGER PRIMARY KEY,

    company_id TEXT,
    year INTEGER,

    sales REAL,
    expenses REAL,

    operating_profit REAL,
    opm_percentage REAL,

    other_income REAL,
    interest REAL,
    depreciation REAL,

    profit_before_tax REAL,
    tax_percentage REAL,

    net_profit REAL,

    eps REAL,
    dividend_payout REAL,

    FOREIGN KEY(company_id)
        REFERENCES companies(id)

);

-- ============================================
-- TABLE 10 : PROS & CONS
-- ============================================

CREATE TABLE prosandcons (

    id INTEGER PRIMARY KEY,

    company_id TEXT,

    pros TEXT,
    cons TEXT,

    FOREIGN KEY(company_id)
        REFERENCES companies(id)

);

-- ============================================
-- TABLE 11 : SECTORS
-- ============================================

CREATE TABLE sectors (

    id INTEGER PRIMARY KEY,

    company_id TEXT,

    broad_sector TEXT,
    sub_sector TEXT,

    index_weight_pct REAL,
    market_cap_category TEXT,

    FOREIGN KEY(company_id)
        REFERENCES companies(id)

);

-- ============================================
-- TABLE 12 : STOCK PRICES
-- ============================================

CREATE TABLE stock_prices (

    id INTEGER PRIMARY KEY,

    company_id TEXT,
    date TEXT,

    open_price REAL,
    high_price REAL,
    low_price REAL,
    close_price REAL,

    volume INTEGER,

    adjusted_close REAL,

    FOREIGN KEY(company_id)
        REFERENCES companies(id)

);

-- =====================================================
-- PEER PERCENTILES
-- =====================================================

CREATE TABLE IF NOT EXISTS peer_percentiles (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    company_id TEXT NOT NULL,

    peer_group_name TEXT NOT NULL,

    metric TEXT NOT NULL,

    value REAL,

    percentile_rank REAL,

    year TEXT

);