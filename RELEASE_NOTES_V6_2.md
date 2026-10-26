# QuantForge V6.2 — private company valuation browser and note deletion

## Private valuation improvements
- Open **My workspace → Valuation & peers → Browse companies**. Select a name from the existing authenticated Alpaca asset picker (popular, all companies A–Z, optional search). Symbol entry is not required.
- **Run scenario** loads available **SEC EDGAR Company Facts** annual US-GAAP figures for that issuer through the MFA-protected Render backend. This is independent of Alpaca market quotes.
- The archived SEC public snapshot remains an offline fallback for companies already in that dataset. Broader issuers are matched from the SEC's issuer ticker-to-CIK index, then fetched only when selected. SEC issuer responses are cached (6 hours) and the issuer index cached (24 hours); the backend requests are spaced to respect fair access.
- On-demand SEC requests **require** a Render environment variable `SEC_USER_AGENT` containing the project name and a real contact email. This is not an API key and does not incur a subscription. Without it, the archived snapshot still works, but unbundled issuers cannot load.
- SEC figures are sourced and labeled; missing US-GAAP, ETFs, funds, foreign issuers, or unavailable positive cash-flow figures produce an honest unavailable result. No synthetic company valuation is substituted. Present-value sensitivity is not per-share intrinsic value, an equity target price, or investment advice.
- The private comparison table contains companies you have inspected during the current signed-in session, rather than the fixed public-company list. Differences in fiscal year ends and accounting remain explicit.

## Private note deletion
- Every saved note has an individual **Delete** button with a confirmation prompt.
- A deletion updates the existing version-controlled, MFA-protected Supabase private state using `/api/private/notes`; it removes exactly the selected note and leaves all other notes, holdings, transactions, cash, and settings intact.
- Concurrent edits are protected by the state version. Deleted notes are not recoverable from this interface.

## Privacy and deployment
- Existing Alpaca secrets, MFA, virtual trades, portfolios, notes, public SEC historical snapshot and public simulator models are unchanged by the patch.
- Both Render and Cloudflare must deploy the new commit, and the new SEC environment variable needs to be set in the Render service for any new issuer.
- Financial data licensing: no Alpaca quotes, trades, or private data are incorporated into the public frontend dataset.
- Tests include authenticated endpoint checks, issuer provenance, no fictitious values for unavailable firms, protected note deletion, and source/UI contracts.
