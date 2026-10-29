# 📈 N100 Financial Platform

A comprehensive financial analytics platform for the Nifty 100 companies that performs automated ETL, financial ratio analysis, NLP-based insights, cash flow intelligence, and professional PDF report generation.

---

# 🚀 Project Overview

The N100 Financial Platform processes financial statements of Nifty 100 companies and automatically generates:

- Financial KPI calculations
- Ratio analysis
- Cash Flow Intelligence
- NLP-generated Pros & Cons
- Company Tearsheet PDFs
- Sector Reports
- Portfolio Summary Report

The project is built using Python with SQLite as the database and ReportLab for professional PDF generation.

---

# 🏗️ Technology Stack

- Python 3.12
- SQLite
- Pandas
- NumPy
- OpenPyXL
- ReportLab
- Matplotlib
- Regex (NLP Parsing)
- Scikit-learn (Clustering)
- FastAPI + Uvicorn (REST API)
- Streamlit + Plotly (Dashboard)
- Pytest (Testing)

---

# 📂 Project Structure

```
N100-Financial-Platform
│
├── data/
│   ├── raw/
│   └── processed/
│
├── db/
│   ├── nifty100.db
│   └── schema.sql
│
├── src/
│   ├── analytics/
│   ├── api/
│   │   └── routers/
│   ├── dashboard/
│   ├── etl/
│   ├── nlp/
│   ├── reports/
│   ├── screener/
│   └── utils/
│
├── output/
│   └── final_deliverables/
│
├── reports/
│   ├── tearsheets/
│   ├── sector/
│   └── portfolio/
│
├── docs/
│
├── tests/
│   ├── analytics/
│   ├── api/
│   ├── etl/
│   └── kpi/
│
├── requirements.txt
└── README.md
```

---

# 📅 Sprint Progress

---

# ✅ Sprint 1 — Data Foundation

Completed

### Features

- Environment Setup
- SQLite Database Design
- ETL Pipeline
- Data Validation
- Data Quality Rules
- Loader Engine
- Validation Reports

### Deliverables

- SQLite Database
- Validation Reports
- ETL Scripts

---

# ✅ Sprint 2 — Financial KPI Engine

Completed

### Features

Implemented financial KPI calculations

- ROE
- ROCE
- Debt to Equity
- Current Ratio
- Interest Coverage
- Operating Margin
- Net Margin
- Dividend Yield
- EPS CAGR
- Revenue CAGR
- PAT CAGR
- Cash Flow KPIs

---

# ✅ Sprint 3 — Analytics Engine

Completed

### Features

- Peer Comparison
- Percentile Rankings
- CAGR Engine
- Growth Analysis
- Sector Analytics
- Trend Detection

---

# ✅ Sprint 4 — Dashboard & Intelligence

Completed

### Features

- Dashboard Dataset
- Financial Scoring
- Company Rankings
- Sector Rankings
- KPI Aggregation
- Reporting Pipeline

---

# ✅ Sprint 5 — NLP + Reports + Cash Flow Intelligence

Completed

---

## 📖 Day 29

### NLP Analysis Parser

Automatically parses textual financial analysis fields.

Parses

- Revenue CAGR
- Profit CAGR
- Stock CAGR
- ROE

Outputs

```
output/analysis_parsed.csv
```

```
output/parse_failures.csv
```

---

## 📖 Day 30

### Auto Pros & Cons Generator

Generates AI-style investment insights using financial rules.

Features

- 12 Pro Rules
- 12 Con Rules
- Confidence Score
- Automatic Rule Engine

Output

```
output/pros_cons_generated.csv
```

---

## 📖 Day 31

### Cash Flow Intelligence

Automatically computes

- Free Cash Flow
- CFO Quality Score
- CapEx Intensity
- FCF Conversion
- Distress Detection
- Deleveraging Detection
- Capital Allocation Pattern

Outputs

```
output/cashflow_intelligence.xlsx
```

```
output/distress_alerts.csv
```

---

## 📖 Day 32

### Capital Allocation Report

Generates

- Capital Allocation Summary
- Pattern Distribution
- Pattern Changes
- Latest Pattern Classification

Outputs

```
output/capital_allocation.csv
```

```
output/pattern_distribution.csv
```

```
output/pattern_changes.csv
```

---

## 📖 Day 33

### Company Tearsheet Generator

Automatically creates professional 2-page PDF reports.

Each report contains

- Company Overview
- KPI Dashboard
- Revenue Trend
- Net Profit Trend
- Balance Sheet Analysis
- Cash Flow Analysis
- Pros
- Cons
- Capital Allocation Badge

Output

```
reports/tearsheets/
```

---

## 📖 Day 34

### Batch Report Generation

Automatically generates

- 92 Company Tearsheets
- Sector Reports

Outputs

```
reports/tearsheets/
```

```
reports/sector/
```

---

## 📖 Day 35

### Portfolio Summary Report

Creates a complete portfolio report.

Includes

- One page per company
- Top KPIs
- Trend Indicators
- Company Summary

Output

```
reports/portfolio/
```

---

# ✅ Sprint 6 — Clustering, REST API & Production Hardening

Completed

---

## 📖 Day 36

### KMeans Clustering

Groups every company into 5 quantitative clusters using ROE, debt-to-equity,
revenue CAGR, FCF CAGR and operating profit margin (sector-median imputation,
StandardScaler, KMeans(n_clusters=5, random_state=42)).

Outputs

```
reports/elbow_plot.png
output/cluster_labels.csv
```

---

## 📖 Day 37

### Cluster Profiling

Profiles every cluster's mean/median feature values and assigns readable
names (High-Quality Compounders, Defensive Dividend Payers, Value Cyclicals,
Distressed or Turnaround, Emerging Growth) based on composite quality and
growth scores.

Outputs

```
reports/correlation_heatmap.png
output/outlier_report.csv
output/portfolio_stats.csv
```

---

## 📖 Day 38-40

### FastAPI REST Layer

23 endpoints across 8 routers under `/api/v1`, with CORS and request-logging
middleware.

| Router | Base Path |
|---|---|
| health | `/api/v1/health` |
| companies | `/api/v1/companies` |
| screener | `/api/v1/screener` |
| sectors | `/api/v1/sectors` |
| peers | `/api/v1/peers` |
| valuation | `/api/v1/valuation` |
| portfolio | `/api/v1/portfolio` |
| documents | `/api/v1/documents` |

Outputs

```
docs/openapi.json
docs/postman_collection.json
```

---

## 📖 Day 41-42

### Testing

144 tests (ETL / DQ / KPI / analytics / clustering / API), 0 failures.

Outputs

```
reports/pytest_report.html
```

---

## 📖 Day 43

### Performance

Added SQLite indexes on `financial_ratios`, `sectors`, `peer_groups`,
`peer_percentiles`, `documents` and `prosandcons`; load-tested every API
endpoint.

Outputs

```
output/perf_notes.md
```

---

## 📖 Day 44-45

### Documentation & Acceptance

Outputs

```
docs/analyst_guide.pdf
acceptance_checklist.pdf
output/final_deliverables/
```

---

# 📊 Generated Reports

### CSV

- analysis_parsed.csv
- parse_failures.csv
- pros_cons_generated.csv
- distress_alerts.csv
- capital_allocation.csv
- pattern_distribution.csv
- pattern_changes.csv
- cluster_labels.csv
- outlier_report.csv
- portfolio_stats.csv

### Excel

- cashflow_intelligence.xlsx

### PDFs

- 92 Company Tearsheets
- Sector Reports
- Portfolio Summary
- Analyst Guide
- Acceptance Checklist

### API

- docs/openapi.json
- docs/postman_collection.json

---

# ⚙️ Installation

Clone repository

```bash
git clone https://github.com/your-username/N100-Financial-Platform.git
```

Install dependencies

```bash
pip install -r requirements.txt
```

---

# ▶️ Run Modules

### NLP Parser

```bash
python -m src.nlp.parser
```

---

### Pros & Cons Generator

```bash
python -m src.nlp.pros_cons_generator
```

---

### Cash Flow Intelligence

```bash
python -m src.analytics.cashflow_kpis
```

---

### Capital Allocation Report

```bash
python -m src.analytics.capital_allocation
```

---

### Company Tearsheet

```bash
python -m src.reports.tearsheet TCS
```

---

### Sector Report

```bash
python -m src.reports.sector_report
```

---

### Batch Generation

```bash
python -m src.reports.batch_generate
```

---

### Portfolio Report

```bash
python -m src.reports.portfolio_report
```

---

### KMeans Clustering

```bash
python -m src.analytics.clustering
```

---

### Cluster Profiling

```bash
python -m src.analytics.cluster_profiling
```

---

### Run the REST API

```bash
uvicorn src.api.main:app --reload
```

Interactive docs: http://localhost:8000/docs

---

### Export OpenAPI Schema + Postman Collection

```bash
python -m src.api.export_api_docs
```

---

### Create Performance Indexes

```bash
python -m src.etl.create_indexes
```

---

### Run Tests

```bash
pytest
```

---

### Generate Analyst Guide

```bash
python -m docs.generate_analyst_guide
```

---

# 📈 Project Statistics

| Metric | Value |
|---------|------:|
| Companies | 92 |
| Financial Ratio Records | 1065 |
| Profit & Loss Records | 1276 |
| Balance Sheet Records | 1312 |
| Cash Flow Records | 1187 |
| NLP Parsed Records | 79 |
| Pros & Cons Generated | 806 |
| Company Tearsheets | 92 |
| Sector Reports | 10 |
| Portfolio Reports | 1 |
| Clusters | 5 |
| API Endpoints | 23 |
| Automated Tests | 144 (0 failures) |

---

# 🎯 Key Features

- Automated ETL Pipeline
- Financial Ratio Engine
- CAGR Analysis
- Peer Comparison
- NLP-Based Insights
- Cash Flow Intelligence
- Capital Allocation Analysis
- Professional PDF Reports
- Portfolio Analytics
- KMeans Company Clustering
- REST API (FastAPI, 23 endpoints)
- Interactive Streamlit Dashboard
- SQLite Database
- Modular Python Architecture
- 144 Automated Tests

---

# 📌 Future Scope

- AI Stock Recommendation Engine
- Forecasting Models
- Real-Time Market Data Integration
- Portfolio Optimization
- Cloud Deployment
- User Authentication

---

# 👨‍💻 Author

**Parth Bhutaiya**

B.Tech Computer Science Engineering (AI & ML)

Adani University

---

# 📄 License

This project is developed for educational and internship purposes.

---

# 🎓 Internship Expansion — Explainable Analytics, Peer Benchmarking & Automated Reporting

Adds five modules on top of the existing platform. All calculations are deterministic
(no paid AI services, no price prediction). See `UPDATES_CHANGELOG.txt` for the exact list of
files added and changed.

| Module | Code | What it does |
|---|---|---|
| 1. Data quality monitoring | `src/quality/` | Finds missing values, duplicate records, inconsistent periods and invalid metrics, each with a severity |
| 2. Explainable analytics | `src/analytics/financial_metrics.py`, `health_score.py` | Transparent indicators and a documented 0-100 health score with a per-metric breakdown |
| 3. Peer benchmarking | `src/analytics/benchmarking.py` | Company vs peer median, percentile and rank (curated peer group, else broad sector) |
| 4. Automated PDF reports | `src/reports/research_report.py` | KPIs, charts, peer comparison, methodology and data-quality warnings |
| 5. Automated testing | `tests/quality`, `tests/analytics`, `tests/reports`, `tests/dashboard` | 150+ new tests including dashboard smoke tests |

### Health score in one paragraph
Eight metrics in four pillars (Profitability 30, Leverage 25, Growth 25, Cash quality 20).
Each metric earns 0-100 points by straight-line interpolation between two documented thresholds;
points are weighted and added. Missing or implausible metrics are dropped and the remaining
weights re-scaled (coverage is reported; below 50% the score is withheld). Banks, NBFCs and
insurers are not scored on leverage, interest coverage, operating margin or cash conversion.
Grades: A 75+, B 60+, C 45+, D 30+, E below 30. Thresholds are in
`src/analytics/health_score.py` and on the methodology page of every PDF.

### Run it
```
pip install -r requirements.txt
make dashboard                       # new pages: "Health & Peer Benchmark", "Data Quality"
make quality                         # writes output/data_quality_report.csv
make research-report TICKER=TCS      # one PDF -> reports/research/
make research-reports-all            # all 92 PDFs
python -m pytest                     # full test suite
```

### Screenshots
`docs/screenshots/` — score breakdown, peer benchmark, sector league, data-quality monitor.

### Data findings (from the data-quality monitor on the shipped database)
* Statement tables contain company ids that are not in the 92-company master list
  (e.g. WIPRO, VEDL, ZOMATO) - reported as `orphan_company_id` errors.
* Period labels are mixed (`Mar 2024`, `Mar-24`, `2024`, `TTM`, `2024.5`); a shared parser normalises them.
* `Sep 2024` half-year balance-sheet rows sit beside `Mar` annual rows; they are detected as
  off-cycle and excluded from annual analytics.
* Some stored ROE values are impossible (e.g. BEL above 4,000%); they are excluded from scoring
  and shown as a caveat instead of being silently used.
* Some `expenses` / `operating_profit` values break the accounting identity; flagged as warnings.

### Known limitation
3 older tests in `tests/api` fail on a fresh clone because `output/cluster_labels.csv` is
git-ignored (`output/*.csv`). Run the Sprint 6 clustering step first to generate it.
