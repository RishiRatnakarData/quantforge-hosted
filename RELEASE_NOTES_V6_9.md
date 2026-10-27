# QuantForge V6.9 — CI and Security Verification

V6.9 improves deployment assurance without changing private investment logic, data sources, Supabase state, or website UX.

- Runs **every** `web/tests/*.test.cjs` in GitHub CI instead of only the eight original public-demo calculations.
- Adds syntax validation for all frontend JavaScript and the Cloudflare Pages API proxy.
- Independently compares each built HTML inline-script SHA-256 hash against `public/_headers` CSP, fails closed if compiled output was altered, and screens out server-config identifiers.
- Adds offline Cloudflare proxy regression tests for secret configuration, Render destination restrictions, sensitive header handling, cookies, cache prevention, and safe network-failure responses.
- Restricts GitHub workflow token permission to `contents: read`; updates standard GitHub actions to their Node 24-compatible major versions.
- Records an evidence-based review of the V6.8 strategy-robustness export in the private `AUDIT_V6_9.md` included with the installer package; this report is not published to the public GitHub repository.

No real market-data files or private user records are included. Full project tests and GitHub Actions must pass before release. Live Render authorization, Supabase RLS, and deployment configuration must be audited separately using authorized account access.
