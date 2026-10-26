# QuantForge V5.6.1 — Hosted MFA security upgrade

- Enforced authenticator (TOTP) verification after owner password login.
- Supabase-authenticated access JWT must have `aal=aal2`, with a verified TOTP factor, to access any `/api/private/*` resource.
- Existing private PostgreSQL rows remain intact; row-level policies additionally require an AAL2 JWT.
- Authenticator setup / QR and challenge / verification run through the backend proxy and never persist secrets in the static repository.
- AAL1 sessions can access only MFA enrollment, factor lookup, verification, session introspection and logout.
- **Unverified deployment:** authenticated Supabase/Cloudflare/Render integration requires live manual validation before storing sensitive data.

- See [`docs/MFA_UPGRADE_V5_6_1.md`](docs/MFA_UPGRADE_V5_6_1.md) for deployment and acceptance testing.
