"""
test_api.py

Sprint 6
Day 42

Integration tests for every /api/v1 endpoint using
FastAPI's TestClient against the real project database.
"""

from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


# -------------------------------------------------
# Health
# -------------------------------------------------


def test_health_returns_ok_status():
    response = client.get("/api/v1/health")
    assert response.status_code == 200

    body = response.json()
    assert body["status"] == "ok"
    assert "version" in body
    assert "uptime_seconds" in body
    assert "database_row_counts" in body
    assert body["database_row_counts"]["companies"] > 0


# -------------------------------------------------
# Companies
# -------------------------------------------------


def test_list_companies_returns_results():
    response = client.get("/api/v1/companies")
    assert response.status_code == 200

    body = response.json()
    assert body["total"] > 0
    assert len(body["results"]) > 0


def test_list_companies_respects_limit():
    response = client.get("/api/v1/companies?limit=5")
    assert response.status_code == 200
    assert len(response.json()["results"]) <= 5


def test_list_companies_filters_by_sector():
    response = client.get("/api/v1/companies?sector=Financials")
    assert response.status_code == 200

    for company in response.json()["results"]:
        assert company["broad_sector"] == "Financials"


def test_get_company_returns_profile_for_known_ticker():
    response = client.get("/api/v1/companies/ABB")
    assert response.status_code == 200
    assert response.json()["company"]["id"] == "ABB"


def test_get_company_returns_404_for_unknown_ticker():
    response = client.get("/api/v1/companies/NOTAREALTICKER")
    assert response.status_code == 404


def test_get_profit_and_loss_returns_history():
    response = client.get("/api/v1/companies/ABB/pl")
    assert response.status_code == 200
    assert len(response.json()["results"]) > 0


def test_get_balance_sheet_returns_history():
    response = client.get("/api/v1/companies/ABB/bs")
    assert response.status_code == 200
    assert len(response.json()["results"]) > 0


def test_get_cashflow_returns_history():
    response = client.get("/api/v1/companies/ABB/cashflow")
    assert response.status_code == 200
    assert len(response.json()["results"]) > 0


def test_get_ratios_returns_history():
    response = client.get("/api/v1/companies/ABB/ratios")
    assert response.status_code == 200
    assert len(response.json()["results"]) > 0


def test_get_tearsheet_returns_pdf_when_present():
    response = client.get("/api/v1/companies/ABB/tearsheet")
    assert response.status_code in (200, 404)
    if response.status_code == 200:
        assert response.headers["content-type"] == "application/pdf"


# -------------------------------------------------
# Screener
# -------------------------------------------------


def test_list_strategies_returns_named_presets():
    response = client.get("/api/v1/screener/strategies")
    assert response.status_code == 200
    assert "quality_compounder" in response.json()["strategies"]


def test_screener_applies_named_strategy():
    response = client.get("/api/v1/screener?strategy=quality_compounder")
    assert response.status_code == 200

    body = response.json()
    for company in body["results"]:
        if company["return_on_equity_pct"] is not None:
            assert company["return_on_equity_pct"] >= 15


def test_screener_applies_ad_hoc_filter():
    response = client.get("/api/v1/screener?roe_min=20")
    assert response.status_code == 200

    for company in response.json()["results"]:
        if company["return_on_equity_pct"] is not None:
            assert company["return_on_equity_pct"] >= 20


def test_screener_rejects_unknown_strategy():
    response = client.get("/api/v1/screener?strategy=not_a_real_strategy")
    assert response.status_code == 400


# -------------------------------------------------
# Sectors
# -------------------------------------------------


def test_list_sectors_returns_results():
    response = client.get("/api/v1/sectors")
    assert response.status_code == 200
    assert len(response.json()["results"]) > 0


def test_get_sector_companies_returns_results_for_known_sector():
    sectors_response = client.get("/api/v1/sectors")
    first_sector = sectors_response.json()["results"][0]["broad_sector"]

    response = client.get(f"/api/v1/sectors/{first_sector}/companies")
    assert response.status_code == 200
    assert len(response.json()["results"]) > 0


def test_get_sector_companies_returns_404_for_unknown_sector():
    response = client.get("/api/v1/sectors/NotARealSector/companies")
    assert response.status_code == 404


# -------------------------------------------------
# Peers
# -------------------------------------------------


def test_list_peer_groups_returns_results():
    response = client.get("/api/v1/peers/groups")
    assert response.status_code == 200
    assert len(response.json()["results"]) > 0


def test_get_peer_group_members_returns_404_for_unknown_group():
    response = client.get("/api/v1/peers/groups/not_a_real_group")
    assert response.status_code == 404


# -------------------------------------------------
# Valuation
# -------------------------------------------------


def test_get_valuation_history_returns_404_for_unknown_ticker():
    response = client.get("/api/v1/valuation/NOTAREALTICKER")
    assert response.status_code == 404


def test_get_valuation_rankings_top():
    response = client.get("/api/v1/valuation/rankings/top?metric=pe_ratio&limit=5")
    assert response.status_code == 200
    assert len(response.json()["results"]) <= 5


def test_get_valuation_rankings_rejects_unsupported_metric():
    response = client.get("/api/v1/valuation/rankings/top?metric=not_a_metric")
    assert response.status_code == 400


# -------------------------------------------------
# Portfolio
# -------------------------------------------------


def test_get_cluster_composition_returns_results():
    response = client.get("/api/v1/portfolio/clusters")
    assert response.status_code == 200
    assert len(response.json()["results"]) > 0


def test_get_cluster_summary_covers_five_clusters():
    response = client.get("/api/v1/portfolio/clusters/summary")
    assert response.status_code == 200
    assert len(response.json()["results"]) == 5


def test_get_portfolio_stats_returns_results():
    response = client.get("/api/v1/portfolio/stats")
    assert response.status_code == 200
    assert len(response.json()["results"]) > 0


# -------------------------------------------------
# Documents
# -------------------------------------------------


def test_get_company_documents_returns_404_for_unknown_ticker():
    response = client.get("/api/v1/documents/NOTAREALTICKER")
    assert response.status_code == 404


# -------------------------------------------------
# Swagger / OpenAPI
# -------------------------------------------------


def test_swagger_docs_are_served():
    response = client.get("/docs")
    assert response.status_code == 200


def test_openapi_schema_lists_every_router():
    response = client.get("/openapi.json")
    assert response.status_code == 200

    schema = response.json()
    assert len(schema["paths"]) >= 20
