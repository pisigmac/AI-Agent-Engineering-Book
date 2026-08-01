import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from portfolio import Project, Portfolio, Contribution, score_project, README_CHECKS


def test_score_strong_project():
    p = Project(
        name="x",
        url="u",
        readme_flags={k: True for k in README_CHECKS},
        has_tests=True,
        has_ci=True,
        has_docker=True,
        stars=50,
        production_used=True,
    )
    s = score_project(p)
    assert s["score"] >= 85
    assert s["grade"] == "A"


def test_portfolio_recs():
    folio = Portfolio()
    folio.add_project(Project(name="weak", url="u"))
    r = folio.report()
    assert r["n_projects"] == 1
    assert r["recommendations"]
