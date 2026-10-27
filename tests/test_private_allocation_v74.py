"""V7.4 acceptance checks for owner-only, read-only allocation simulations."""
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_v74_private_calculator_is_bundled_once():
    script = (ROOT / 'tools/build_unified_site.py').read_text(encoding='utf-8')
    ast.parse(script)
    assert script.count('private_allocation_v74.js') == 1
    assert script.count('id="private-allocation-card-v74"') == 1


def test_v74_has_no_trade_or_portfolio_write_calls():
    calc = (ROOT / 'web/site/private_allocation_v74.js').read_text(encoding='utf-8')
    assert 'function scenario(' in calc
    assert 'function matchedRisk(' in calc
    assert 'function exportResearch(' in calc
    assert 'fetch(' not in calc
    assert 'localStorage' not in calc
    assert 'api(' not in calc
    assert 'private/trade' not in calc
    assert 'private/state' not in calc


def test_v74_bridge_only_uses_owner_read_only_quote_endpoint():
    script = (ROOT / 'web/site/private.js').read_text(encoding='utf-8')
    marker = '/* V7.4 owner-only virtual allocation what-if: read-only; no write API calls. */'
    start = script.find(marker)
    end = script.find("$('private-valuation-run').addEventListener('click',privateValuation);", start)
    assert start >= 0 and end > start
    bridge = script[start:end]
    assert "api('private/quotes?symbols='" in bridge
    assert "api('private/trade'" not in bridge
    assert "api('private/capital'" not in bridge
    assert 'clearAllocationV74' in bridge
    import re
    assert not re.search(r'\bprivateState\s*=(?!=)', bridge)


def test_v74_invalidates_stale_portfolio_scenarios():
    script = (ROOT / 'web/site/private.js').read_text(encoding='utf-8')
    assert 'async function loadState(){\n  clearAllocationV74();' in script
    assert "if(step!=='ready')clearAllocationV74();else allocationChoicesV74();" in script
    assert 'token!==allocationTokenV74||privateState!==state' in script


def test_v74_no_private_data_or_provider_script_in_public_demo():
    js = (ROOT / 'web/site/private_allocation_v74.js').read_text(encoding='utf-8')
    assert 'The export omits portfolio balances' in js
    assert 'cashBefore:' in js  # internal private what-if state; not in the export object
    export = js.split('function exportResearch(', 1)[1].split('root.QFPrivateAllocationV74', 1)[0]
    assert 'holdings:' not in export
    assert 'proposedBudget:' not in export
    assert 'cashBefore:' not in export
    assert 'positions:' not in export
