"""New integrated release checks: public evidence, private route, safe event targets."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def code(name):
    return (ROOT / name).read_text(encoding="utf-8")


def test_model_exhibit_is_public_while_provider_news_is_not():
    html = code("public/index.html")
    assert 'id="qf-v181-evidence"' in html
    assert "Generated prices only" in html
    assert "not evidence of stock-market accuracy" in html
    assert "TF-IDF weighting" not in html
    assert "Headline tone</h3>" not in html
    assert "QFPublicModelEvidenceV181" in html
    assert "private/news-research" not in code("web/site/private.js")
    assert "tf" in code("cloud/news_intelligence_v180.py").lower()


def test_legacy_private_sections_relocated_without_deleting_controls():
    html = code("public/index.html")
    # One each; same ID contract for existing handlers and post-MFA auth checks.
    for control in (
        "private-v90-run", "private-v90-candidate", "qf-v140-next", "qf-v150-mfa",
        "qf-v160-method-trace", "private-guide-run-v79", "private-note-submit",
    ):
        assert len(re.findall(r'id="' + re.escape(control) + r'"', html)) == 1
    research = html.split('data-private-view="decision"', 1)[1].split('data-private-view="candidate"', 1)[0]
    assert 'id="private-v90-run"' in research
    assert 'id="qf-v180-news"' not in research
    assert 'id="qf-v180-predictions"' in research
    assert 'qf-v140-launch' not in research
    assert 'id="private-guide-card-v79"' not in research


def test_details_are_keyboard_visible_in_advanced_research():
    html = code("public/index.html")
    assert "#private-signed details>summary{display:none!important}" not in html
    assert "#private-signed details>summary{display:list-item!important" in html
    assert "flattenPrivateDetailsV180" not in code("web/site/private.js")
    assert "#private-signed #qf-v93-research-ribbon{display:none!important}" in html
    advanced = html.split('data-private-view="lab"', 1)[1]
    assert 'id="qf-v150-mfa"' in advanced
    assert 'id="private-guide-card-v79"' in advanced
    assert 'id="qf-v160-setup"' in advanced


def test_sec_snapshot_and_research_endpoint_are_not_modified():
    # Source integrity checked independently with the release manifest/installer.
    assert 'owner(request, response)' in code("cloud/api.py")
    assert 'owner(request, response)  # MFA required' in code("cloud/api.py")
    assert 'original' not in code("web/site/public_model_evidence_v181.js").lower()
