# Sprint 1 Retrospective

## Sprint
Sprint 1 – Data Foundation

Duration:
Day 01 – Day 07

Story Points:
34 SP

---

## Sprint Goal

Build a fully loaded and validated SQLite database (nifty100.db) from 12 Excel source files with ETL, validation, and reporting.

---

## What Was Completed

- Environment setup
- Excel Loader
- Data Normalisation
- SQLite Schema
- Database Loading
- 16 Data Quality Rules
- Validation Reports
- Load Audit
- Manual Data Review
- 35+ Unit Tests
- Exploratory SQL Queries

---

## Deliverables

- ✔ nifty100.db
- ✔ db/schema.sql
- ✔ src/etl/loader.py
- ✔ src/etl/validator.py
- ✔ src/etl/normaliser.py
- ✔ output/load_audit.csv
- ✔ output/validation_failures.csv
- ✔ output/validation_summary.csv
- ✔ notebooks/exploratory_queries.sql

---

## Challenges

- Company ID mismatches
- Foreign key validation
- Excel header inconsistencies
- Data normalization issues

---

## Solutions

- Implemented normalize_ticker()
- Implemented normalize_year()
- Added DQ-01 to DQ-16
- Corrected loader logic
- Revalidated all datasets

---

## Lessons Learned

- Importance of data validation
- Proper ETL pipeline design
- SQLite schema design
- Writing reusable validation functions
- Unit testing ETL modules

---

## Sprint Outcome

Sprint 1 completed successfully.

Ready for Sprint 2.