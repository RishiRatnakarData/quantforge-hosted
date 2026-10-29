"""Build a reproducible, historical SEC-only QuantForge research case study.

No network calls, third-party libraries, price predictions, trading, or account data.
All results derive from web/site/sec_snapshot.json at the time of build.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import html
import io
import json
import math
import re
from datetime import date
from pathlib import Path

DATASET = "SEC EDGAR Company Facts, annual 10-K US-GAAP"
SYMBOLS = ("MSFT", "AMD", "ADBE", "AMAT")
METRICS = ("revenue_usd", "operating_income_usd", "net_income_usd", "operating_cash_flow_usd", "capex_usd", "free_cash_flow_usd")
CASE_STUDY_TITLE = "Do faster-growing companies also lead in profitability and cash generation?"


def valid_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def percentage(numerator, denominator):
    if not valid_number(numerator) or not valid_number(denominator) or denominator <= 0:
        return None
    return 100.0 * numerator / denominator


def yoy(current, previous):
    if not valid_number(previous) or previous <= 0 or not valid_number(current):
        return None
    return (current / previous - 1.0) * 100.0


def clean_issuer(company):
    symbol = company.get("symbol")
    cik = company.get("cik")
    if not isinstance(symbol, str) or not re.fullmatch(r"[A-Z0-9.-]{1,15}", symbol):
        raise ValueError("Invalid issuer symbol")
    if not isinstance(cik, int) or isinstance(cik, bool) or not 1 <= cik < 10**10:
        raise ValueError(f"Invalid issuer CIK for {symbol}")
    if company.get("source_url") != f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json":
        raise ValueError(f"Invalid SEC source URL for {symbol}")
    name = company.get("name")
    if not isinstance(name, str) or not name.strip() or len(name) > 160:
        raise ValueError(f"Invalid issuer name for {symbol}")
    # Original baseline issuers may lack an issuer-level extraction date.
    # Absence is not a license to invent one or to infer it from fiscal dates.
    cutoff = company.get("as_of")
    if cutoff is None:
        cutoff = ""
    elif isinstance(cutoff, str):
        try:
            date.fromisoformat(cutoff)
        except ValueError as exc:
            raise ValueError(f"Invalid SEC extraction cutoff for {symbol}") from exc
    else:
        raise ValueError(f"Invalid SEC extraction cutoff type for {symbol}: {type(cutoff).__name__}")
    annual = company.get("annual")
    if not isinstance(annual, list) or len(annual) < 2:
        raise ValueError(f"Insufficient annual SEC history for {symbol}")
    found = []
    for observation in annual:
        try:
            end = str(observation["fiscal_end"])
            date.fromisoformat(end)
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"Invalid fiscal period for {symbol}") from exc
        metrics = observation.get("metrics")
        sources = observation.get("sources")
        if not isinstance(metrics, dict) or not isinstance(sources, dict):
            raise ValueError(f"Invalid SEC metrics and lineage for {symbol}")
        for k in METRICS:
            value = metrics.get(k)
            if value is not None and not valid_number(value):
                raise ValueError(f"Non-finite {k} for {symbol} {end}")
        if metrics.get("revenue_usd") is None or metrics["revenue_usd"] <= 0:
            raise ValueError(f"Missing or invalid annual revenue for {symbol} {end}")
        ocf = metrics.get("operating_cash_flow_usd")
        capex = metrics.get("capex_usd")
        fcf = metrics.get("free_cash_flow_usd")
        if (valid_number(ocf) and valid_number(capex) and capex >= 0
                and (not valid_number(fcf) or not math.isclose(fcf, ocf - capex, rel_tol=1e-9, abs_tol=1e-4))):
            raise ValueError(f"FCF proxy does not reconcile for {symbol} {end}")
        if fcf is not None and (not valid_number(ocf) or not valid_number(capex) or capex < 0):
            raise ValueError(f"Unsubstantiated FCF proxy for {symbol} {end}")
        for metric, source in sources.items():
            if metric not in METRICS or not isinstance(source, dict):
                raise ValueError(f"Bad lineage for {symbol} {end}")
            accession = source.get("accession")
            if not isinstance(accession, str) or not re.fullmatch(r"\d{10}-\d{2}-\d{6}", accession):
                raise ValueError(f"Invalid SEC accession for {symbol} {end}")
            # Legacy source records may not carry an independent fact-period end.
            # Do not invent one. When it *is* recorded, require exact alignment.
            source_end = source.get("end")
            if source_end not in (None, ""):
                if not isinstance(source_end, str):
                    raise ValueError(f"Invalid recorded SEC source period for {symbol} {end}")
                try:
                    date.fromisoformat(source_end)
                except ValueError as exc:
                    raise ValueError(f"Invalid recorded SEC source period for {symbol} {end}") from exc
                if source_end != end:
                    raise ValueError(f"Misaligned SEC source period for {symbol} {end}: recorded {source_end}")
        for metric in ("revenue_usd", "operating_income_usd", "net_income_usd", "operating_cash_flow_usd", "capex_usd"):
            if metrics.get(metric) is not None and metric not in sources:
                raise ValueError(f"Unattributed {metric} for {symbol} {end}")
        found.append({"date": end, "metrics": metrics, "sources": sources})
    if len({row["date"] for row in found}) != len(found):
        raise ValueError(f"Duplicate fiscal periods for {symbol}")
    found.sort(key=lambda row: row["date"])
    return {"symbol": symbol, "cik": cik, "name": name, "cutoff": cutoff,
            "url": company["source_url"], "annual": found[-3:]}


def load_companies(snapshot):
    if not isinstance(snapshot, dict) or snapshot.get("dataset") != DATASET:
        raise ValueError("Unexpected source dataset; public report not generated")
    all_companies = snapshot.get("companies", [])
    if not isinstance(all_companies, list) or len(all_companies) < 94:
        raise ValueError("Requires the verified expanded public SEC catalog (at least 94 companies)")
    symbols = [company.get("symbol") for company in all_companies if isinstance(company, dict)]
    if len(symbols) != len(all_companies) or len(symbols) != len(set(symbols)):
        raise ValueError("SEC snapshot has duplicate or invalid issuers")
    by_symbol = {company["symbol"]: company for company in all_companies}
    missing = [symbol for symbol in SYMBOLS if symbol not in by_symbol]
    if missing:
        raise ValueError(f"Missing case-study SEC issuer(s): {', '.join(missing)}")
    return [clean_issuer(by_symbol[symbol]) for symbol in SYMBOLS]


def facts(company):
    latest = company["annual"][-1]
    previous = company["annual"][-2]
    current = latest["metrics"]
    prior = previous["metrics"]
    return {**company, "fiscal_end": latest["date"],
            "revenue": current.get("revenue_usd"),
            "operating_margin": percentage(current.get("operating_income_usd"), current.get("revenue_usd")),
            "fcf_margin": percentage(current.get("free_cash_flow_usd"), current.get("revenue_usd")),
            "net_margin": percentage(current.get("net_income_usd"), current.get("revenue_usd")),
            "growth": yoy(current.get("revenue_usd"), prior.get("revenue_usd")),
            "prior_end": previous["date"]}


def fmt_usd(number):
    if not valid_number(number):
        return "Not reported"
    return f"${number / 1e9:,.2f}B" if number >= 0 else f"−${abs(number) / 1e9:,.2f}B"


def fmt_pct(number):
    return f"{number:+.1f}%" if valid_number(number) else "Not reported"


def safe_csv(value):
    s = "" if value is None else str(value)
    return "'" + s if s.lstrip().startswith(("=", "+", "-", "@", "\t", "\r")) and not isinstance(value, (int, float)) else s


def csv_report(companies):
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(("symbol", "issuer", "cik", "fiscal_end", "issuer_as_of", "metric", "value_usd", "source_tag", "source_filed", "source_accession", "source_period_end", "period_end_verification", "sec_companyfacts_url", "interpretation"))
    for company in companies:
        for row in company["annual"]:
            metrics, sources = row["metrics"], row["sources"]
            for metric in METRICS:
                value = metrics.get(metric)
                source = sources.get(metric, {})
                note = ("Derived proxy: operating_cash_flow_usd - capex_usd; source accession IDs are on its input rows"
                        if metric == "free_cash_flow_usd" else "SEC reported amount; no interpolation")
                # The fiscal_end grouping exists in the original published snapshot.
                # Its older source objects may lack independently recorded end dates.
                # Distinguish missing provenance from verified matching dates.
                if source:
                    recorded_end = source.get("end") or ""
                    verification = ("Recorded source period matches fiscal_end" if recorded_end
                                    else "Metric source period unrecorded in legacy snapshot")
                elif metric == "free_cash_flow_usd" and value is not None:
                    recorded_end = ""
                    verification = "Derived from separately sourced cash-flow and capex figures"
                else:
                    recorded_end = ""
                    verification = "No metric value reported"
                writer.writerow((safe_csv(company["symbol"]), safe_csv(company["name"]), company["cik"], row["date"], company["cutoff"], metric,
                                 value if value is not None else "", safe_csv(source.get("tag", "")),
                                 safe_csv(source.get("filed", "")), safe_csv(source.get("accession", "")),
                                 recorded_end, verification, company["url"],
                                 note if value is not None else "Not reported"))
    return stream.getvalue()


def canonical_snapshot_sha256(source_bytes: bytes) -> str:
    """Digest over UTF-8 SEC JSON with CRLF normalized to LF across Git OSes."""
    return hashlib.sha256(source_bytes.replace(b"\r\n", b"\n")).hexdigest()


def bar_chart(rows, key, title, subtitle):
    """Accessible, zero-centered, positive/negative SVG; no third-party scripts."""
    available = [(r["symbol"], r[key]) for r in rows if valid_number(r.get(key))]
    if not available:
        return f'<p class="missing">{html.escape(title)}: not enough SEC observations.</p>'
    max_abs = max(abs(v) for _, v in available)
    max_abs = max(max_abs, 0.01)
    base_x, span = 430, 254
    svg = [f'<svg role="img" aria-label="{html.escape(title, quote=True)}" viewBox="0 0 760 {len(rows) * 66 + 46}" xmlns="http://www.w3.org/2000/svg">',
           f'<title>{html.escape(title)}</title>', f'<desc>{html.escape(subtitle)}</desc>']
    svg.append(f'<line x1="{base_x}" y1="24" x2="{base_x}" y2="{len(rows)*66+18}" stroke="#92a99f" stroke-width="1.5"/>')
    for index, row in enumerate(rows):
        y = 40 + index * 66
        svg.append(f'<text x="16" y="{y + 7}" fill="#233d39" font-size="17" font-weight="650">{html.escape(row["symbol"])}</text>')
        value = row.get(key)
        if not valid_number(value):
            svg.append(f'<text x="85" y="{y + 7}" fill="#60716d" font-size="14">Not reported</text>')
            continue
        width = abs(value) / max_abs * span
        x = base_x if value >= 0 else base_x - width
        fill = "#137a67" if value >= 0 else "#c27b49"
        svg.append(f'<rect x="{x:.2f}" y="{y-14}" width="{max(width, 1):.2f}" height="30" rx="4" fill="{fill}"/>')
        svg.append(f'<text x="{base_x+span+14}" y="{y+7}" fill="#233d39" font-size="16" font-weight="600">{html.escape(fmt_pct(value))}</text>')
    svg.append('</svg>')
    return f'<div class="chart"><div class="chart-head"><h3>{html.escape(title)}</h3><p>{html.escape(subtitle)}</p></div>' + "".join(svg) + '</div>'


def find_summary(rows):
    growths = [(r["symbol"], r["growth"]) for r in rows if valid_number(r["growth"])]
    best = max(growths, key=lambda r: r[1]) if growths else None
    positive_fcf = sum(1 for row in rows if valid_number(row["fcf_margin"]) and row["fcf_margin"] > 0)
    missing = sum(1 for row in rows for key in ("growth", "operating_margin", "fcf_margin") if row[key] is None)
    summary = []
    if best:
        summary.append(f"<strong>{html.escape(best[0])}</strong> has the highest latest observed year-over-year revenue change within this four-company illustration ({fmt_pct(best[1])}). This is not a stock-return ranking.")
    else:
        summary.append("Comparable year-over-year revenue changes are unavailable for these filing periods.")
    summary.append(f"<strong>{positive_fcf} of {len(rows)}</strong> issuers have a positive free-cash-flow-to-revenue proxy in their latest included annual period. This is not a standardized definition of free cash flow or a valuation.")
    summary.append(f"<strong>{missing}</strong> of {len(rows) * 3} latest-period comparison cells are unavailable. Missing values are withheld rather than filled with zero.")
    return summary




def research_brief(rows):
    """Return only observations calculated from current SEC facts, never a forecast."""
    growth = [row for row in rows if valid_number(row.get("growth"))]
    margins = [row for row in rows if valid_number(row.get("operating_margin"))]
    cash = [row for row in rows if valid_number(row.get("fcf_margin"))]
    growth_leader = max(growth, key=lambda row: row["growth"]) if growth else None
    margin_leader = max(margins, key=lambda row: row["operating_margin"]) if margins else None
    cash_positive = sum(row["fcf_margin"] > 0 for row in cash)
    def label(row):
        return html.escape(row["symbol"]) if row else "Unavailable"
    cards = (
        f'<div class="result-card"><span>Revenue growth leader · sample only</span><strong>{label(growth_leader)}</strong>'
        f'<small>{fmt_pct(growth_leader["growth"]) if growth_leader else "Not reported"}</small></div>'
        f'<div class="result-card"><span>Operating-margin leader · sample only</span><strong>{label(margin_leader)}</strong>'
        f'<small>{fmt_pct(margin_leader["operating_margin"]) if margin_leader else "Not reported"}</small></div>'
        f'<div class="result-card"><span>Positive cash-flow proxy margin</span><strong>{cash_positive} / {len(cash)}</strong>'
        f'<small>Of {len(cash)} companies with available cash-flow ratios</small></div>'
    )
    if growth_leader and margin_leader and growth_leader["symbol"] != margin_leader["symbol"]:
        conclusion = (
            f'In the selected latest annual periods, <strong>{label(growth_leader)}</strong> has the highest observed revenue '
            f'growth ({fmt_pct(growth_leader["growth"])}), while <strong>{label(margin_leader)}</strong> has the highest '
            f'operating margin ({fmt_pct(margin_leader["operating_margin"])}). '
            'These are different financial dimensions: ranking the sample by growth alone does not reproduce the '
            'profitability ranking. This is a descriptive result, not proof that growth reduces profitability.'
        )
    elif growth_leader and margin_leader:
        conclusion = (
            f'<strong>{label(growth_leader)}</strong> leads the selected sample on both latest reported revenue growth '
            f'({fmt_pct(growth_leader["growth"])}) and operating margin '
            f'({fmt_pct(margin_leader["operating_margin"])}). That coincidence among four deliberately selected '
            'companies does not establish a general correlation, causal relation or forecast.'
        )
    else:
        conclusion = 'The available filings do not support a complete growth-versus-margin leader comparison; missing values are not filled.'
    conclusion += (
        f' Positive cash-flow-to-revenue proxies were observed for <strong>{cash_positive} of {len(cash)}</strong> '
        'issuers with available inputs. Cash generation adds a distinct lens, but it is not by itself an equity valuation.'
        ' The issuers differ in industry, fiscal year-end and accounting context. No inferential significance '
        'test, investment return backtest or predictive regression was performed.'
    )
    return cards, conclusion


def render_html(snapshot, companies, sha256):
    rows = [facts(c) for c in companies]
    baseline = "".join(
        f'<tr><th scope="row">{html.escape(r["name"])} <span class="ticker">{html.escape(r["symbol"])}</span></th>'
        f'<td>{r["fiscal_end"]}</td><td>{fmt_usd(r["revenue"])}</td><td>{fmt_pct(r["growth"])}</td>'
        f'<td>{fmt_pct(r["operating_margin"])}</td><td>{fmt_pct(r["fcf_margin"])}</td></tr>' for r in rows
    )
    details = []
    for company in companies:
        trs = []
        for entry in company["annual"]:
            m = entry["metrics"]
            trs.append('<tr><th scope="row">'+entry["date"]+'</th>'+''.join(f'<td>{fmt_usd(m.get(k))}</td>' for k in ("revenue_usd", "operating_income_usd", "net_income_usd", "operating_cash_flow_usd", "capex_usd", "free_cash_flow_usd"))+'</tr>')
        entry_urls = sorted({source["accession"] for rec in company["annual"] for source in rec["sources"].values()})
        accessions = ", ".join(entry_urls)
        undocumented_periods = sum(
            not source.get("end")
            for rec in company["annual"] for source in rec["sources"].values()
        )
        period_note = (f" {undocumented_periods} metric source period(s) are not independently recorded in the legacy snapshot; fiscal-year grouping is retained, but those individual periods cannot be checked from this snapshot alone."
                       if undocumented_periods else " All recorded metric source period ends match their displayed fiscal-year grouping.")
        details.append(f'<details class="issuer-detail"><summary>{html.escape(company["name"])} · {html.escape(company["symbol"])} · fiscal history and lineage</summary>'
                       f'<p class="caption">SEC Company Facts source: <a href="{company["url"]}" rel="noopener noreferrer" target="_blank">CIK {company["cik"]:010d}</a>. Issuer extraction cutoff: {company["cutoff"] or "Not recorded in the source snapshot"}. Filing accession references: {html.escape(accessions)}. Full metric-level tags and accessions are in the downloadable CSV.{html.escape(period_note)}</p>'
                       '<div class="table-scroll"><table><thead><tr><th scope="col">Fiscal end</th><th scope="col">Revenue</th><th scope="col">Operating income</th><th scope="col">Net income</th><th scope="col">Operating cash flow</th><th scope="col">Capital expenditure</th><th scope="col">FCF proxy</th></tr></thead><tbody>'
                       + ''.join(trs) + '</tbody></table></div></details>')
    findings = ''.join(f'<li>{text}</li>' for text in find_summary(rows))
    result_cards, decision_conclusion = research_brief(rows)
    latest_cutoffs = ", ".join(f'{html.escape(c["symbol"])}: {c["cutoff"] or "not recorded"}' for c in companies)
    css = """*{box-sizing:border-box}body{margin:0;background:#f6f8f5;color:#1d3430;font:16px/1.58 system-ui,-apple-system,'Segoe UI',sans-serif}a{color:#136c5b;text-underline-offset:3px}a:hover{color:#0b4d40}a:focus-visible,summary:focus-visible{outline:3px solid #77baa6;outline-offset:3px}.wrap{max-width:1100px;padding:24px;margin:auto}.eyebrow{font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:#43796a;font-weight:800}.hero{background:linear-gradient(135deg,#123c34,#1e6050);color:#fff;padding:50px 0}.hero a{color:#d6f3e7}.hero .wrap{padding-top:0;padding-bottom:0}.hero h1{font-size:clamp(2rem,4vw,3.4rem);line-height:1.13;max-width:850px;margin:12px 0}.hero p{max-width:860px;color:#e0eee8;margin:0}h2{font-size:clamp(1.38rem,2.7vw,2rem);line-height:1.25;margin:0 0 16px}.section{padding:32px 0;border-bottom:1px solid #dfe6e0}.lead{max-width:820px;color:#415e57}.metrics{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;margin-top:22px}.metric,.card,.chart,.issuer-detail{border:1px solid #dce7df;border-radius:14px;background:white;padding:20px}.metric strong{font-size:1.6rem;display:block;color:#175d4e}.metric span,.caption{font-size:.83rem;color:#576e66}.cards{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:15px}.card h3{margin:0 0 9px;font-size:1.05rem}.card p{margin:0;color:#526a60}.chart-grid{display:grid;grid-template-columns:1fr;gap:16px}.chart-head{margin-bottom:6px}.chart-head h3{margin:0}.chart-head p{font-size:.85rem;margin:0;color:#5b726a}.chart{overflow-x:auto}.chart svg{width:100%;max-width:760px;min-width:590px;height:auto;display:block}.table-scroll{overflow-x:auto;max-width:100%}table{width:100%;border-collapse:collapse;font-size:.91rem;min-width:740px}th,td{border-bottom:1px solid #e2eae5;padding:11px 12px;text-align:right;white-space:nowrap}th:first-child,td:first-child{text-align:left}thead{background:#edf4ee}.ticker{font-weight:500;color:#5b796d;display:block;font-size:.82rem}.issuer-detail{margin-bottom:12px}.issuer-detail summary{font-weight:750;cursor:pointer}.issuer-detail .caption{overflow-wrap:anywhere}.notes{padding-left:23px}.notes li{margin:9px 0}.method{display:grid;grid-template-columns:1fr 1fr;gap:20px}.method p{margin:0 0 10px}.small{font-size:.85rem;color:#5a7066}.pill{display:inline-block;background:#def1e8;color:#185545;border-radius:50px;padding:6px 12px;font-size:.8rem;font-weight:700}.footer{padding:28px 0;font-size:.85rem;color:#52665f}.chart rect{vector-effect:non-scaling-stroke}.results-summary{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin:18px 0}
.result-card{background:#fff;border:1px solid #d6e5dd;border-radius:12px;padding:19px;display:flex;flex-direction:column;gap:5px}
.result-card span{font-size:.75rem;color:#587368;font-weight:650}
.result-card strong{font-size:2rem;line-height:1.15;color:#195b48}
.result-card small{font-size:.82rem;color:#4c6b5e}
.research-conclusion{border-left:5px solid #328a6f;background:#edf7f1;padding:21px 24px;border-radius:12px;line-height:1.85}
.research-conclusion p{margin:0}
.research-map{display:flex;gap:9px;flex-wrap:wrap;margin-top:15px}
.research-map a{border:1px solid #bdd7ca;border-radius:8px;background:white;padding:7px 11px;font-size:.82rem;text-decoration:none;font-weight:650}
@media(min-width:1000px){.chart-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.chart-grid .chart:last-child:nth-child(odd){grid-column:1/-1}.chart svg{min-width:0;max-width:none}}
@media(max-width:760px){.results-summary{grid-template-columns:1fr}}@media(max-width:760px){.wrap{padding:18px}.hero{padding:30px 0}.metrics,.cards,.method{grid-template-columns:1fr}.card,.chart,.issuer-detail{padding:15px}}@media print{.hero{background:white;color:#1d3430}.hero p,.hero a{color:#1d3430}.wrap{max-width:100%}.chart,.issuer-detail{break-inside:avoid}}"""
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="Reproducible SEC annual-report research case study, with filing-level provenance, computed profitability metrics, chart and accessible tables."><title>SEC Financial Research Case Study | QuantForge</title><style>{css}</style></head><body>
<header class="hero"><div class="wrap"><a href="./index.html#systems">← QuantForge research methods</a><p class="eyebrow" style="color:#bbddce;margin-top:24px">QuantForge / Reproducible financial research</p><h1>{html.escape(CASE_STUDY_TITLE)}</h1><p>A transparent, cross-company illustration using historical SEC annual 10-K facts. All charts and calculations are generated from the public QuantForge snapshot—without stock-price feeds, analyst forecasts, or personal portfolio data.</p></div></header>
<main class="wrap"><section class="section" aria-labelledby="overview-title"><span class="pill">Historical disclosures only · SEC annual filings</span><h2 id="overview-title" style="margin-top:20px">Research question</h2><p class="lead">Across Microsoft, AMD, Adobe and Applied Materials, does the company with the highest latest annual revenue growth also lead in operating profitability and cash generation? The analysis compares three measurable dimensions using SEC annual filings, then assesses why a growth-only screen may be incomplete.</p><div class="metrics"><div class="metric"><strong>{len(companies)}</strong><span>Illustrative issuers, selected in advance</span></div><div class="metric"><strong>{len(snapshot['companies'])}</strong><span>Public SEC companies in the broader catalog</span></div><div class="metric"><strong>3 or fewer</strong><span>Most recent eligible annual periods shown per company</span></div></div></section>
<section class="section" aria-labelledby="findings-title"><h2 id="findings-title">Key findings</h2><p class="lead">These comparisons are computed from the published four-company SEC sample; they are descriptive, not a predictive ranking.</p><div class="results-summary">{result_cards}</div><ol class="notes">{findings}</ol><p class="small">Descriptive comparisons only. Issuers have different fiscal years and business models, and reported facts may include later restatements. Some original issuer records do not specify an extraction cutoff.</p></section>
<section class="section" aria-labelledby="table-title"><h2 id="table-title">Results · latest reported annual periods</h2><p class="lead">Each issuer uses its latest eligible annual observation in the published snapshot; periods are not necessarily the same dates.</p><div class="table-scroll"><table><thead><tr><th scope="col">Company</th><th scope="col">Fiscal year ended</th><th scope="col">Revenue</th><th scope="col">Revenue YoY</th><th scope="col">Operating margin</th><th scope="col">FCF proxy / revenue</th></tr></thead><tbody>{baseline}</tbody></table></div></section>
<section class="section" aria-labelledby="charts-title"><h2 id="charts-title">Visual results · three financial lenses</h2><div class="chart-grid">{bar_chart(rows,'growth','Revenue growth','Latest reported year versus the preceding eligible annual period (percentage).')}{bar_chart(rows,'operating_margin','Operating margin','Reported operating income divided by reported annual revenue (percentage).')}{bar_chart(rows,'fcf_margin','Cash generation proxy','Operating cash flow minus capital expenditure, divided by revenue (percentage).')}</div><p class="small">Zero-centered bars, including negative observations. Missing metrics are not converted to zero; exact values are in the table above and source CSV below.</p></section>
<section class="section" aria-labelledby="conclusion-title"><h2 id="conclusion-title">Conclusion and interpretation</h2><div class="research-conclusion"><p>{decision_conclusion}</p></div><p class="small">The sample is small and deliberately selected. Different fiscal year-ends, reporting conventions, revisions and sector economics limit generalization. Further research would need industry-matched peers, contemporaneous price observations and a documented hypothesis before attempting a return-prediction study.</p></section>
<section class="section" aria-labelledby="sources-title"><h2 id="sources-title">Audit the actual SEC numbers</h2><p class="lead">Expand an issuer to see the annual figures; download the metric-level source ledger for SEC XBRL tags, 10-K accession references, filing dates, and an issuer extraction cutoff where recorded (blank in the CSV if not recorded), and whether a metric-level source period end was independently recorded (never inferred).</p>{''.join(details)}<p><a href="./research-case-study.csv" download>Download filing-level metric ledger (CSV)</a></p></section>
<section class="section" aria-labelledby="method-title"><h2 id="method-title">Methods, decisions and limitations</h2><div class="method"><div><h3>Computation and reproducibility</h3><p>Revenue growth = (latest revenue / previous eligible annual revenue − 1) × 100. Operating margin = operating income / annual revenue × 100. The cash-flow proxy = operating cash flow − payments to acquire property, plant and equipment; its revenue margin uses the same annual period.</p><p>The sample comprises MSFT, AMD, ADBE, and AMAT selected in advance for illustration. The values come only from the pinned <code>web/site/sec_snapshot.json</code> dataset. No network call is made by the build script.</p></div><div><h3>What this analysis cannot establish</h3><p>SEC annual facts are not adjusted stock-price histories, market capitalizations, point-in-time backtests, enterprise valuations, or predictions. Disclosure timing, restatements, accounting choices, sector economics and different fiscal dates limit cross-company comparability.</p><p>Company Facts may contain facts filed after the financial year they describe. Where present, the issuer extraction cutoff describes the published snapshot, <em>not</em> historical information availability; for some original issuers that cutoff is unrecorded. This analysis is unsuitable as an unbiased historical investment signal.</p></div></div><p class="small">Issuer extraction cutoffs (missing values explicitly disclosed): {latest_cutoffs}. Source snapshot SHA-256: <code>{sha256}</code>. The SHA-256 shown above uses LF-normalized JSON line endings for reproducibility across operating systems; the input file is independently verified unchanged during the build.</p><p class="small">The public project includes separate hypothetical portfolio models; their results are not included in this historical SEC financial comparison.</p></section></main><footer class="footer"><div class="wrap">QuantForge · Rishi Ratnakar · Financial research engineering · <a href="./index.html#sec">Explore {len(snapshot['companies'])}-company SEC catalog</a> · <a href="./index.html#systems">Review methodology</a></div></footer></body></html>'''


def write_outputs(repo: Path, *, check_only: bool = False):
    snapshot_path = repo / "web/site/sec_snapshot.json"
    source_bytes = snapshot_path.read_bytes()
    raw_digest = hashlib.sha256(source_bytes).hexdigest()
    source_digest = canonical_snapshot_sha256(source_bytes)
    snapshot = json.loads(source_bytes.decode("utf-8"))
    companies = load_companies(snapshot)
    report = render_html(snapshot, companies, source_digest)
    ledger = csv_report(companies)
    outputs = {repo / "public/research-case-study.html": report,
               repo / "public/research-case-study.csv": ledger}
    if not check_only:
        for path, content in outputs.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8", newline="\n")
    if hashlib.sha256(snapshot_path.read_bytes()).hexdigest() != raw_digest:
        raise ValueError("SEC snapshot mutated during case-study generation")
    print(f"V8.2 {'preflight' if check_only else 'built'}: {len(companies)} issuers, {len(snapshot['companies'])} catalog companies, {len(ledger.splitlines())-1} ledger rows, snapshot SHA256={source_digest[:16]}…")
    return outputs


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--repo", required=True, type=Path)
    p.add_argument("--check", action="store_true")
    args = p.parse_args()
    write_outputs(args.repo.resolve(), check_only=args.check)


if __name__ == "__main__":
    main()
