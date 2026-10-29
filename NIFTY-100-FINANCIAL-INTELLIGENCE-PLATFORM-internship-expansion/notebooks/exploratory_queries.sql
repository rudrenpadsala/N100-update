-- ===========================================================
-- N100 Financial Intelligence Platform
-- Exploratory SQL Queries
-- Sprint 1 - Day 7
-- ===========================================================

-- -----------------------------------------------------------
-- Query 1: Total Companies
-- -----------------------------------------------------------
SELECT COUNT(*) AS total_companies
FROM companies;


-- -----------------------------------------------------------
-- Query 2: Total Profit & Loss Records
-- -----------------------------------------------------------
SELECT COUNT(*) AS total_profit_records
FROM profitandloss;


-- -----------------------------------------------------------
-- Query 3: Total Balance Sheet Records
-- -----------------------------------------------------------
SELECT COUNT(*) AS total_balance_records
FROM balancesheet;


-- -----------------------------------------------------------
-- Query 4: Total Cash Flow Records
-- -----------------------------------------------------------
SELECT COUNT(*) AS total_cashflow_records
FROM cashflow;


-- -----------------------------------------------------------
-- Query 5: Top 10 Companies by ROE
-- -----------------------------------------------------------
SELECT
    company_name,
    roe_percentage
FROM companies
ORDER BY roe_percentage DESC
LIMIT 10;


-- -----------------------------------------------------------
-- Query 6: Top 10 Companies by ROCE
-- -----------------------------------------------------------
SELECT
    company_name,
    roce_percentage
FROM companies
ORDER BY roce_percentage DESC
LIMIT 10;


-- -----------------------------------------------------------
-- Query 7: Company Count by Sector
-- -----------------------------------------------------------
SELECT
    broad_sector,
    COUNT(*) AS total_companies
FROM sectors
GROUP BY broad_sector
ORDER BY total_companies DESC;


-- -----------------------------------------------------------
-- Query 8: Highest Sales by Company
-- -----------------------------------------------------------
SELECT
    company_id,
    MAX(sales) AS highest_sales
FROM profitandloss
GROUP BY company_id
ORDER BY highest_sales DESC
LIMIT 10;


-- -----------------------------------------------------------
-- Query 9: Average Market Capitalisation
-- -----------------------------------------------------------
SELECT
    ROUND(AVG(market_cap_crore),2) AS average_market_cap
FROM market_cap;


-- -----------------------------------------------------------
-- Query 10: Stock Price Records per Company
-- -----------------------------------------------------------
SELECT
    company_id,
    COUNT(*) AS total_price_records
FROM stock_prices
GROUP BY company_id
ORDER BY total_price_records DESC;