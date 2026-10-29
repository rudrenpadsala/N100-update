# ==========================================
# N100 Financial Intelligence Platform
# Makefile
# ==========================================

load:
	python src/etl/load_database.py

validate:
	python src/etl/validator.py

test:
	python -m pytest -v

report:
	python src/etl/review_summary.py

dashboard:
	cd src/dashboard && streamlit run app.py

api:
	@echo API module will be implemented in a later sprint.

ratios:
	python src/analytics/kpi_engine.py

clean:
	@echo Cleaning output folder...

# ---- Internship expansion ----
update-data:
	python src/etl/fetch_market_data.py

quality:
	python -m src.quality.data_quality

research-report:
	python -m src.reports.research_report $(TICKER)

research-reports-all:
	python -m src.reports.research_report --all
