## V5.6 hosted deployment status (October 2026)

Cloudflare Pages + Render + Supabase source prepared; **not deployed or live-integrated**. Public synthetic calculators and hosted single-owner virtual portfolio/notes have automated and mocked browser/API tests. Remote authentication, HTTP-only cookies, RLS and live provider integration require independent verification on deployed accounts. The hosted Quant/DCF/ML tabs still use synthetic JavaScript methods; the full Python algorithms remain in the local app. See [hosting instructions](HOSTED_WEBSITE_V5_6.md).

# QuantForge implementation status — V5.4.1 (release-candidate hardening)

**Private single-user local application; GitHub publishes source, fictional demos and math only.**

| Capability | Verified scope | Not verified / limitations |
| --- | --- | --- |
| Current-day MSFT stock/ETF quotes | Personal Alpaca IEX trade observation displayed on Windows | IEX is not the consolidated quote; no live trading; crypto observation not separately verified |
| Portfolio ledger, notes and paper trades | Windows regression suite; SQLite remains private | No real money or tax reporting |
| Investment directory and comparisons | Curated 259 assets; app/browser and unit tests | Not a comprehensive security master |
| Portfolio look-through and rebalancing | Implemented and unit-tested with synthetic inputs | Real ETF constituent-file coverage not independently verified |
| SEC 10-K annual statements | FY2026 MSFT financials displayed on Windows | Filing mapping/reconciliation requires independent review; issuers differ |
| General FCFF DCF and sensitivities | MSFT illustrative $85.51/share shown on Windows; 10% D&A/sales assumption, 10% WACC, 5% growth | Not a calibrated fair value; 71.3% of EV from terminal value |
| Historical return/covariance/optimization | Live personal IEX MSFT/VOO fetch: 552 closes, 275 matched returns; allocations computed on Windows | Data are venue-limited and privately licensed; 18.8% vs 18.4% volatility is in-sample/model-dependent |
| SEC fundamental peer ML | Windows observed 12-company group, five ratios, nearest peers and relative IsolationForest rank | No return labels; 12-company selection is small, nonrandom, varying fiscal dates |
| GARCH/HMM/Ridge/boosting/factor/options research | Separate offline code and synthetic tests | Not live investment desk price predictions |
| Quality | User Windows: **194 passed**, six non-blocking deprecation warnings on V5.4.0 | One F841 lint issue identified there, fixed in V5.4.1 source; fresh Windows rerun and GitHub Actions still required |
| GitHub publication | Docs, screenshots and prepublication scanner prepared | Not published; user must inspect screenshots, staged files and Git history first |

Full evidence, assumptions and open checks: [VERIFICATION_V5_4.md](evidence/VERIFICATION_V5_4.md).
