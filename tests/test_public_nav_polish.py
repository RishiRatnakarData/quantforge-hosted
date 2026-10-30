"""Read-only tests for the public Method page's fragment links and README freshness."""
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class AnchorAudit(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.targets = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get("id"):
            if a["id"] in self.ids:
                raise AssertionError(f"Duplicate element id: {a['id']}")
            self.ids.add(a["id"])
        if tag == "a" and a.get("href", "").startswith("#"):
            self.targets.append(a["href"][1:])


def test_public_navigation_targets():
    parser = AnchorAudit()
    parser.feed((ROOT / "web/site/site.template.html").read_text(encoding="utf-8"))
    missing = sorted(set(parser.targets) - parser.ids)
    assert not missing, f"Public fragment targets do not exist: {missing}"


def test_readme_not_stale():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "V7.0 — Current hosted platform" not in readme
    assert "V6.9 release was validated" not in readme


def test_public_overview_is_distinct_from_private_exit():
    """A private return-to-public control is not a duplicate public nav route."""
    import sys

    tools = str(ROOT / "tools")
    if tools not in sys.path:
        sys.path.insert(0, tools)
    from audit_v82_readiness import PUBLIC_ROUTES, Analyzer

    page = (ROOT / "public/index.html").read_text(encoding="utf-8")
    analyzer = Analyzer()
    analyzer.feed(page)
    assert analyzer.private_exits == ["overview"]
    assert all(analyzer.nav.get(route) == 1 for route in PUBLIC_ROUTES)

    # A second real public Overview control must still be rejected.
    extra = '<button data-page="overview">Duplicate overview</button>'
    duplicate = Analyzer()
    duplicate.feed(page + extra)
    assert duplicate.nav.get("overview") == 2
