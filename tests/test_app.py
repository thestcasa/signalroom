from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_interactive_app_loads_both_cases_without_exceptions():
    app_path = Path(__file__).resolve().parents[1] / "app.py"
    app = AppTest.from_file(app_path, default_timeout=20).run()
    assert len(app.exception) == 0
    assert [tab.label for tab in app.tabs] == [
        "Briefing",
        "Dead-ball Lab",
        "SetPieceLab",
        "Evidence room",
        "Method & limits",
    ]
    selector = app.selectbox[0]
    assert len(selector.options) == 2
    selector.select_index(1).run()
    assert len(app.exception) == 0
