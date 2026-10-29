---

# Sprint 4 Retrospective

## Sprint Goal

The objective of Sprint 4 was to develop a complete Streamlit-based Financial Analytics Dashboard for Nifty 100 companies. The dashboard provides financial analysis, screening, sector comparison, valuation insights, and annual report access through eight interactive pages.

---

## Work Completed

### Dashboard Development

- Built a Streamlit multi-page application.
- Implemented all 8 dashboard screens.
- Added sidebar navigation.
- Improved responsive UI.

### Financial Analytics

- Company Profile
- Stock Screener
- Peer Comparison
- Trend Analysis
- Sector Analysis
- Capital Allocation
- Annual Reports
- Dashboard Overview

### Data Integration

Integrated data from:

- Companies
- Financial Ratios
- Profit & Loss
- Balance Sheet
- Cash Flow
- Sector Information
- Market Capitalization

### Visualization

Implemented interactive Plotly charts including:

- KPI Cards
- Line Charts
- Bar Charts
- Bubble Charts
- Radar Charts
- Treemap
- Donut Charts

### Valuation Module

Developed valuation calculations using:

- FCF Yield
- Sector Median P/E
- Discount Flag
- Fair Value Flag
- Caution Flag

Generated:

- valuation_summary.xlsx
- valuation_flags.csv

---

# Challenges Faced

During development several issues were identified.

### 1. Missing Financial Data

Some companies did not contain complete financial records.

**Solution**

Implemented safe helper functions and displayed N/A instead of crashing.

---

### 2. Screener Filters

Some filters returned incorrect results because filtering order was incorrect.

**Solution**

Reordered filtering logic and validated each financial filter independently.

---

### 3. Missing Revenue and Market Cap

Revenue and Market Capitalization fields were unavailable for some datasets.

**Solution**

Added fallback logic and warning messages.

---

### 4. Chart Responsiveness

Several Plotly charts overflowed the page.

**Solution**

Applied

- use_container_width=True
- responsive layouts
- automatic resizing

---

### 5. Company Profile Stability

Some companies had incomplete historical data causing page errors.

**Solution**

Added validation checks before displaying charts and metrics.

---

# Performance Results

| Test | Result |
|------|--------|
| Dashboard Startup | Passed |
| Company Profile Load Time | Under 3 Seconds |
| Screener Performance | Passed |
| Trend Charts | Passed |
| Sector Analysis | Passed |
| Capital Allocation | Passed |
| Annual Reports | Passed |

---

# QA Summary

Completed testing on:

- 8 Dashboard Screens
- 10 Companies
- Multiple Financial Years
- Missing Data Cases
- Extreme Screener Filters
- CSV Export
- Excel Export

No critical issues remained after QA.

---

# Lessons Learned

- Always validate financial datasets before visualization.
- Cache database queries for faster performance.
- Handle missing values safely.
- Build reusable helper functions.
- Test every screen using multiple companies before deployment.

---

# Sprint Outcome

Sprint 4 was successfully completed.

Deliverables achieved:

- Streamlit Dashboard
- Financial Analytics
- Stock Screener
- Valuation Module
- Export Functionality
- Interactive Visualizations
- Project Documentation
- Quality Assurance

Sprint Status:

**Completed Successfully**

---

# Sprint 4 Task Board

| Day | Task | Status |
|------|------|--------|
| Day 22 | Streamlit Dashboard Scaffold | ✅ Completed |
| Day 23 | Dashboard & Company Profile | ✅ Completed |
| Day 24 | Stock Screener & Peer Comparison | ✅ Completed |
| Day 25 | Trend, Sector, Capital Allocation & Reports | ✅ Completed |
| Day 26 | Valuation Module | ✅ Completed |
| Day 27 | Integration QA & Bug Fixes | ✅ Completed |
| Day 28 | Documentation & Sprint Review | ✅ Completed |

---

# Sprint 4 Deliverables

The following deliverables were successfully completed during Sprint 4.

| Deliverable | Status |
|-------------|--------|
| Streamlit Dashboard | ✅ |
| Dashboard Navigation | ✅ |
| Dashboard Home Screen | ✅ |
| Company Profile Screen | ✅ |
| Stock Screener | ✅ |
| Peer Comparison | ✅ |
| Trend Analysis | ✅ |
| Sector Analysis | ✅ |
| Capital Allocation Map | ✅ |
| Annual Reports | ✅ |
| Cached Database Loader | ✅ |
| Valuation Module | ✅ |
| valuation_summary.xlsx | ✅ |
| valuation_flags.csv | ✅ |
| CSV Export | ✅ |
| Excel Export | ✅ |
| README Documentation | ✅ |
| QA Testing | ✅ |

---

# Definition of Done (Exit Criteria)

The Sprint is considered complete when all of the following conditions are satisfied.

| Requirement | Status |
|-------------|--------|
| All 8 Streamlit screens load successfully | ✅ |
| Dashboard runs without errors | ✅ |
| Company Profile loads in under 3 seconds | ✅ |
| Stock Screener filters work correctly | ✅ |
| CSV Export works | ✅ |
| Excel Export works | ✅ |
| Valuation Summary generated | ✅ |
| Valuation Flags generated | ✅ |
| Responsive charts | ✅ |
| Missing data handled safely | ✅ |
| QA testing completed | ✅ |
| Documentation completed | ✅ |

---

# Sprint 4 Summary

## Dashboard Statistics

- Total Dashboard Screens: **8**
- Companies Covered: **92**
- Financial Years: **Multiple**
- Database: **SQLite**
- Charts: **Plotly**
- Framework: **Streamlit**

---

## Overall Sprint Status

🟢 **Sprint 4 Successfully Completed**

All planned dashboard features, valuation analytics, QA testing, documentation, and deliverables have been completed successfully.