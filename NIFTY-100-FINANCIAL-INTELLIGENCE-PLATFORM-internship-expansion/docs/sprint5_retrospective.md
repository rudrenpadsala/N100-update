# Sprint 5 Retrospective

**Project:** N100 Financial Platform  
**Sprint:** Sprint 5  
**Duration:** Day 29 – Day 35  
**Story Points:** 70 SP  
**Completed By:** Rudren Padsala

---

# Sprint Goal

The objective of Sprint 5 was to build advanced financial intelligence features by implementing:

- NLP-based analysis parser
- Automated Pros & Cons Generator
- Cash Flow Intelligence Engine
- Capital Allocation Analytics
- Company Tearsheet PDF Generator
- Sector Report Generator
- Portfolio Summary Report

All major deliverables were completed successfully.

---

# Work Completed

## Day 29 – NLP Analysis Parser

### Features Implemented

- Parsed analysis.xlsx using Regular Expressions
- Extracted:
  - Compounded Sales Growth
  - Compounded Profit Growth
  - Stock Price CAGR
  - ROE
- Logged parsing failures
- Cross-validated parsed values against calculated CAGR
- Generated:
  - output/analysis_parsed.csv
  - output/parse_failures.csv

---

## Day 30 – Pros & Cons Generator

### Features Implemented

- Implemented rule-based NLP engine
- Generated investment Pros & Cons automatically
- Added confidence scoring
- Ensured every company has:
  - At least one Pro
  - At least one Con

Generated:

- output/pros_cons_generated.csv

---

## Day 31 – Cash Flow Intelligence

### Features Implemented

Calculated:

- Free Cash Flow
- CFO Quality Score
- CapEx Intensity
- FCF Conversion
- Distress Detection
- Deleveraging Detection
- Capital Allocation Pattern

Generated:

- output/cashflow_intelligence.xlsx
- output/distress_alerts.csv

---

## Day 32 – Capital Allocation Report

### Features Implemented

- Verified historical capital allocation data
- Generated pattern distribution
- Generated yearly pattern changes
- Updated Cash Flow Intelligence workbook

Generated:

- output/capital_allocation.csv
- output/pattern_distribution.csv
- output/pattern_changes.csv

---

## Day 33 – Company Tearsheet

Generated professional two-page PDF reports containing:

- Company KPIs
- Revenue Trend
- Profit Trend
- Balance Sheet
- Cash Flow Summary
- Pros & Cons
- Capital Allocation Pattern

Generated sample reports for multiple companies.

---

## Day 34 – Batch Report Generation

Generated:

- Company Tearsheet PDFs
- Sector Reports
- Skipped Company Log

Reports saved under:

reports/tearsheets/

reports/sector/

---

## Day 35 – Portfolio Summary

Generated complete Portfolio Summary PDF.

Features included:

- Company Overview
- Financial KPIs
- Trend Indicators
- Portfolio Summary

Saved:

reports/portfolio/portfolio_summary.pdf

---

# Challenges Faced

During Sprint 5 several technical challenges were encountered.

## 1. Excel Header Issues

The source Excel files contained title rows before actual headers.

Solution:

Used custom header positions while loading Excel files.

---

## 2. Regex Parsing Errors

Several text values contained inconsistent formatting.

Solution:

Improved regex pattern and logged unmatched records for manual review.

---

## 3. Duplicate Financial Records

Some financial tables contained duplicate year entries.

Solution:

Removed duplicate company-year combinations before analysis.

---

## 4. Missing Cash Flow Records

Certain companies were missing cash flow data.

Solution:

Added placeholder records where appropriate and verified coverage.

---

## 5. PDF Layout Issues

Initial ReportLab templates experienced text overflow.

Solution:

Adjusted spacing, margins, font sizes and enabled word wrapping.

---

# Achievements

Successfully completed:

- NLP Analysis Parser
- Automatic Pros & Cons Generation
- Cash Flow Intelligence Engine
- Capital Allocation Analytics
- Company Tearsheet Generator
- Sector Report Generator
- Portfolio Summary Report

Generated over 100 project output files including CSV, Excel and PDF reports.

---

# Key Learnings

During Sprint 5 the following concepts were learned:

- Advanced Regular Expressions
- Financial Ratio Interpretation
- Cash Flow Analysis
- Capital Allocation Patterns
- Automated Report Generation
- PDF Generation using ReportLab
- Data Validation Techniques
- Financial Data Cleaning
- NLP Rule-Based Systems
- End-to-End Analytics Pipeline Development

---

# Deliverables

Completed Deliverables:

- analysis_parsed.csv
- parse_failures.csv
- pros_cons_generated.csv
- cashflow_intelligence.xlsx
- distress_alerts.csv
- capital_allocation.csv
- pattern_distribution.csv
- pattern_changes.csv
- Company Tearsheet PDFs
- Sector Reports
- Portfolio Summary PDF

---

# Sprint Outcome

Sprint 5 objectives were successfully achieved.

The project now includes:

- Automated NLP analysis
- Financial Intelligence
- Cash Flow Analytics
- Capital Allocation Analysis
- Professional Company Reports
- Sector Reports
- Portfolio Summary Reports

This sprint significantly enhanced the analytical capabilities of the N100 Financial Platform and prepared the system for the next development phase.

---

# Sprint Status

**Sprint:** Sprint 5

**Status:** ✅ Completed

**Overall Progress:** 100%
