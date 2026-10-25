# Source rights, retention and publication policy

> **V5 current scope:** QuantForge is a private local desk. Publish source, tests and fictional screenshots only; do not deploy its personalized UI or real Alpaca data. See [V5 publication checklist](RELEASE_CHECKLIST.md).

## Critical October 2026 change

Tiingo's Terms of Use updated October 6, 2026 say that a **Starter or Trial user cannot retain Tiingo Data or Derived Products in persistent storage**, even for private internal research. The same terms restrict redistribution for individual-tier users. See [official Terms section 1.6](https://app.tiingo.com/tos/) and [Tiingo API documentation](https://www.tiingo.com/documentation/). This overrides the earlier V0–V3 project documentation that assumed keeping cached Starter snapshots and results was permitted.

If using Tiingo Starter, do not continue storing, archiving, or publishing `data/private/tiingo`, `outputs/real_etfs`, `outputs/v1_real_risk`, `outputs/v2_real_research`, their backups or derived charts generated from Tiingo. Review terms and delete retained copies as required. Do not assume changing a filename, replotting a curve or upgrading to Power resolves rights issues. For any unusual reuse/distribution proposal, seek written permission or appropriate data-provider licensing.

V4 does **not** include any Tiingo downloaded data or derived empirical market outputs. The `tiingo` and `v1-risk` CLI commands from older versions are disabled; V4 integrated reports require synthetic V1/V2 evidence. This is a deliberately conservative boundary, not a claim that all other market-data sources permit redistribution.

## Permitted by design within this sample

- Deterministic synthetically generated market series created inside QuantForge and clearly labelled as such.
- Fictional SEC-shaped accounting fixtures for pipeline verification (never represented as real financial statements).
- Public SEC Company Facts analysis with accurate as-of dates, independent disclosure audit, and appropriate attribution; share only after reviewing applicable requirements and quality.
- Original source code, tests, architecture, methodology and source-agnostic validation logic.

## Privacy and provenance

- No API keys, SEC contact email, `.env` files or provider snapshots should be committed.
- Evidence-manifest SHA-256 digests identify source versions but do not confer redistribution rights.
- Any public figure must disclose whether its underlying data are fictional, public SEC disclosures, or data used with express publication rights.
- Never describe a non-peer-reviewed research draft as a refereed paper.

Review the active provider agreement yourself before relying on these notes as a definitive licensing determination.

## Public replacement source: ECB daily reference exchange rates

ECB/ESCB policy permits reuse of published ESCB statistics (including commercial reuse) with source attribution, original statistics/metadata unchanged, and third-party exceptions. Source: https://www.ecb.europa.eu/stats/ecb_statistics/governance_and_quality_framework/html/usage_policy.en.html . Daily euro reference rates are fetched using https://data-api.ecb.europa.eu/service/data/EXR . The `public-ecb` command stores original CSV unchanged and generates derived FX analytics separately. These quote changes are not an investable total-return index and are not executable bid/ask prices.
