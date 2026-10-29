"""Smoke tests: the new dashboard pages render without raising."""

from pathlib import Path

import pytest

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
APP = REPO_ROOT / "src" / "dashboard" / "app.py"

pytestmark = pytest.mark.skipif(
    not (REPO_ROOT / "db" / "nifty100.db").exists(), reason="database not available"
)


@pytest.fixture
def app(monkeypatch):
    monkeypatch.syspath_prepend(str(REPO_ROOT))
    monkeypatch.syspath_prepend(str(APP.parent))
    at = AppTest.from_file(str(APP), default_timeout=240)
    at.run()
    assert not at.exception, [e.value for e in at.exception]
    return at


def go_to(at, fragment):
    radio = at.radio(key="n100_nav_radio")      # horizontal menu in the page header
    label = next(o for o in radio.options if fragment in o)
    at.radio(key="n100_nav_radio").set_value(label).run()
    return at


def test_navigation_lists_the_new_pages(app):
    options = app.radio(key="n100_nav_radio").options
    assert any("Health & Peer Benchmark" in o for o in options)
    assert any("Data Quality" in o for o in options)


def test_health_page_renders_with_tabs_and_tables(app):
    go_to(app, "Health")
    assert not app.exception, [e.value for e in app.exception]
    assert len(app.tabs) == 4
    assert len(app.dataframe) >= 2


@pytest.mark.parametrize("name", ["Bharat Electronics Ltd (BEL)", "Tata Consultancy Services Ltd (TCS)"])
def test_health_page_for_selected_companies(app, name):
    go_to(app, "Health")
    app.selectbox(key="hb_company").select(name).run()
    assert not app.exception, [e.value for e in app.exception]


def test_data_quality_page_renders(app):
    go_to(app, "Data Quality")
    assert not app.exception, [e.value for e in app.exception]
    assert len(app.dataframe) >= 2


def test_existing_pages_still_render(app):
    for fragment in ("Home", "Peer Comparison", "Annual Reports"):
        go_to(app, fragment)
        assert not app.exception, (fragment, [e.value for e in app.exception])
