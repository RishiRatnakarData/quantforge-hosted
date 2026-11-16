# Readiness transport repair candidate

Baseline a5e794457bb81820efba17ac8b2a294ab9b95a64. Existing architecture, backend and schema remain unchanged.

A normal direct anonymous Render health GET on November 16 returned JSON HTTP 200 after 32.438 seconds with a 75-second read budget and no redirect or retry. The published proxy had returned an upstream non-JSON 429 in 0.344 seconds immediately before this. These are distinct failure classes; increasing a timeout cannot fix an immediate 429. Direct-origin recovery is not acceptance of the published Cloudflare route.

Proxy readiness GET now has a 70-second bound; the browser allows 75 seconds, capped by the existing two-minute total deadline. Only /api/health receives this longer budget. Login, MFA and mutations are never replayed. Explicit hosting verification still stops the client. This permits legitimate slower startup without a keepalive or provider workaround. Cloudflare documents no hard HTTP wall-time limit while the client stays connected; client disconnection may cancel request tasks.

To conserve the user's near-exhausted GitHub allowance, the existing workflow gains an explicitly selected repair_only dispatch. Default full CI behavior and tests remain unchanged. The focused run verifies generated CSP/publication boundaries, full JS regressions and hosted authentication/ledger security; local browser recovery and final three-engine acceptance also run. Use the supported skip-checks trailer only to avoid duplicate push/PR runs; run focused CI explicitly against the exact candidate.

Production rollout remains a repair experiment, not a declaration of reliability. Require observed idle and published-route recovery without direct Render traffic, preferably twice; stop on a hosting challenge. Keep the availability notice until real acceptance. Baseline Cloudflare deployment 193cebc1-435b-4c42-a7a6-cc72cbc21762 is the rollback artifact; no database migration or backend deploy is needed.
