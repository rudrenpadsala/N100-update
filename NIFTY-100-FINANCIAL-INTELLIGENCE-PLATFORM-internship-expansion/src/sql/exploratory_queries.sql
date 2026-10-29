-- Total Companies
SELECT COUNT(*) FROM companies;

-- Total Profit & Loss Records
SELECT COUNT(*) FROM profitandloss;

-- Top 10 Companies by ROE
SELECT company_name, roe_percentage
FROM companies
ORDER BY roe_percentage DESC
LIMIT 10;

-- Top 10 Companies by Market Cap
SELECT c.company_name, MAX(m.market_cap_crore) AS market_cap
FROM market_cap m
JOIN companies c ON c.id = m.company_id
GROUP BY c.company_name
ORDER BY market_cap DESC
LIMIT 10;

-- Company Count by Sector
SELECT broad_sector, COUNT(*)
FROM sectors
GROUP BY broad_sector
ORDER BY COUNT(*) DESC;

-- Average ROCE
SELECT AVG(roce_percentage) FROM companies;

-- Highest Sales
SELECT company_id, MAX(sales)
FROM profitandloss
GROUP BY company_id
ORDER BY MAX(sales) DESC
LIMIT 10;

-- Stock Price Count
SELECT company_id, COUNT(*)
FROM stock_prices
GROUP BY company_id
ORDER BY COUNT(*) DESC;