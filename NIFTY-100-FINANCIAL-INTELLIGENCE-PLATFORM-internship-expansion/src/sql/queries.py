"""
queries.py

All SQL Queries used in the project.
"""

# ==========================================
# 1. Total Companies
# ==========================================

TOTAL_COMPANIES = """
SELECT COUNT(*) AS total_companies
FROM companies;
"""


# ==========================================
# 2. Top 10 Companies by ROE
# ==========================================

TOP_ROE = """
SELECT
    company_name,
    roe_percentage
FROM companies
ORDER BY roe_percentage DESC
LIMIT 10;
"""


# ==========================================
# 3. Top 10 Companies by ROCE
# ==========================================

TOP_ROCE = """
SELECT
    company_name,
    roce_percentage
FROM companies
ORDER BY roce_percentage DESC
LIMIT 10;
"""


# ==========================================
# 4. Top Market Cap Companies
# ==========================================

TOP_MARKET_CAP = """
SELECT
    c.company_name,
    m.market_cap_crore

FROM market_cap m

JOIN companies c

ON c.id = m.company_id

ORDER BY m.market_cap_crore DESC

LIMIT 10;
"""


# ==========================================
# 5. Sector-wise Company Count
# ==========================================

SECTOR_COUNT = """
SELECT

    broad_sector,

    COUNT(*) AS companies

FROM sectors

GROUP BY broad_sector

ORDER BY companies DESC;
"""


# ==========================================
# 6. Average PE Ratio
# ==========================================

AVERAGE_PE = """
SELECT

ROUND(AVG(pe_ratio),2) AS average_pe

FROM market_cap;
"""


# ==========================================
# 7. Highest Dividend Yield
# ==========================================

TOP_DIVIDEND = """
SELECT

c.company_name,

m.dividend_yield_pct

FROM market_cap m

JOIN companies c

ON c.id = m.company_id

ORDER BY dividend_yield_pct DESC

LIMIT 10;
"""


# ==========================================
# 8. Latest Stock Prices
# ==========================================

LATEST_PRICE = """
SELECT

company_id,

MAX(date) AS latest_date,

MAX(close_price) AS latest_close

FROM stock_prices

GROUP BY company_id;
"""

TOP_SALES = """
SELECT

    c.company_name,

    MAX(p.sales) AS sales

FROM profitandloss p

JOIN companies c

ON p.company_id = c.id

GROUP BY c.company_name

ORDER BY sales DESC

LIMIT 10;
"""

TOP_PROFIT = """
SELECT

    c.company_name,

    MAX(p.net_profit) AS net_profit

FROM profitandloss p

JOIN companies c

ON p.company_id = c.id

GROUP BY c.company_name

ORDER BY net_profit DESC

LIMIT 10;
"""

HIGHEST_EPS = """
SELECT

    c.company_name,

    MAX(p.eps) AS eps

FROM profitandloss p

JOIN companies c

ON p.company_id = c.id

GROUP BY c.company_name

ORDER BY eps DESC

LIMIT 10;
"""

TOP_BOOK_VALUE = """
SELECT

    company_name,

    book_value

FROM companies

ORDER BY book_value DESC

LIMIT 10;
"""

TOP_FACE_VALUE = """
SELECT

    company_name,

    face_value

FROM companies

ORDER BY face_value DESC

LIMIT 10;
"""

MARKET_CAP_CATEGORY = """
SELECT

    market_cap_category,

    COUNT(*) AS companies

FROM sectors

GROUP BY market_cap_category

ORDER BY companies DESC;
"""

AVERAGE_ROE_SECTOR = """
SELECT

    s.broad_sector,

    ROUND(AVG(c.roe_percentage),2) AS avg_roe

FROM companies c

JOIN sectors s

ON c.id = s.company_id

GROUP BY s.broad_sector

ORDER BY avg_roe DESC;
"""

TOTAL_SECTORS = """
SELECT

COUNT(DISTINCT broad_sector) AS total_sectors

FROM sectors;
"""

