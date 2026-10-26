# QuantForge V5.6.1 — Hosted Authenticator MFA

This is a **source-code security upgrade** for the existing V5.6 hosted project: Cloudflare Pages → Render → Supabase Auth/DB. It is **not deployed by the ZIP**. The existing private PostgreSQL portfolio row is retained. A private owner's password by itself is no longer enough to use the private API or database.

## New flow

1. Enter the owner email and password on My workspace.
2. On the first login, select **Start authenticator setup**, scan the displayed QR with an authenticator app, and enter the six-digit code before leaving the page.
3. On subsequent logins, enter the current six-digit code from that app. A successful verification upgrades the Supabase session to `aal2` and unlocks the workspace.
4. The private portfolio, quote, paper trade, and research-note APIs reject `aal1` tokens. Supabase RLS independently requires the user's UUID and JWT `aal2`. A validated Supabase Auth user identity, matching JWT `sub`, and a verified TOTP factor are checked on the backend.

**Never share the QR, TOTP secret, access cookies, private keys, or codes.** Keep an authenticator recovery plan. Losing the second factor can lock the account; recovery must be performed through the owner's authenticated Supabase administrative controls, not by temporarily disabling MFA for the public site.

## Change inventory (existing GitHub repository)

Copy the following files from this release into the existing `RishiRatnakarData/quantforge-hosted` working tree, keeping paths intact:

```text
cloud/api.py
cloud/supabase.sql
tools/build_unified_site.py
web/site/private.js
tests/test_hosted_web.py
pyproject.toml
public/index.html
public/_headers
RELEASE_NOTES_V5_6_1.md
docs/MFA_UPGRADE_V5_6_1.md
docs/STATUS.md
README.md
```

Do not copy over `.git`, `.venv`, `.env`, `.private` or user data. A file-by-file copy is safer than merging old and new repository directories. Inspect `git diff` before committing.

## Windows verification (PowerShell, from repository root)

First check you are in the correct Git repository and that you have no unrelated edits to lose:

```powershell
Test-Path .\pyproject.toml
Test-Path .\.git
git status --short
```

Then run (if your current Python virtual environment still works):

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe tools/build_unified_site.py
node --check web/site/private.js
node --test web/tests/demo.test.cjs
.\.venv\Scripts\python.exe tools/prepublish_check.py
```

If the virtual environment is absent, first run `py -3.12 -m venv .venv`, then use its `python.exe` commands above. A full install needs internet access. Optional integrations may report skips on systems without their packages; no failed tests are acceptable.

## Deployment order (minimize disruption)

1. **Review** code and existing Render/Pages environment configuration; do not change or post secrets. Keep backups of Supabase data and repository history. No new environment variable is required.
2. From your existing Git clone, build, test, and push the changed code to `main`:

```powershell
git add cloud/api.py cloud/supabase.sql tools/build_unified_site.py web/site/private.js tests/test_hosted_web.py pyproject.toml public/index.html public/_headers RELEASE_NOTES_V5_6_1.md docs/MFA_UPGRADE_V5_6_1.md docs/STATUS.md README.md
git commit -m "security: require Supabase authenticator MFA for private workspace"
git push origin main
```

3. Confirm **Render** has deployed that commit, then confirm **Cloudflare Pages** deployed the same commit (Cloudflare build command remains `python tools/build_unified_site.py`, output `public`). Deployments can finish in either order; the workspace may temporarily report an MFA requirement until both are updated. The public fictional demo should continue to load.
4. In **Supabase → SQL Editor**, execute the updated `cloud/supabase.sql`. It uses `create table if not exists` and replaces the three existing row-level policies with UID **and** JWT AAL2 checks; it does not delete existing portfolio rows. Verify RLS is enabled and that only authenticated users can access the table under the new policies.
5. On the live site, open My workspace, sign out first if already signed in, and run the first-time setup with your authenticator. Keep the enrollment QR private and verify the six-digit code. Then sign out and back in to validate the subsequent-login flow.

**Fail-closed behavior:** from the moment the new Render backend is deployed, password-only sessions lose access to `/api/private/*`. The SQL policy update must also be completed; otherwise a password-only JWT could still independently access the database's Supabase REST API if someone has the user's credentials. Do not consider deployment finished until both layers enforce MFA.

## Security acceptance checklist

- [ ] Public Explore Demo works logged out with PC shut down.
- [ ] Direct Render `/api/private/state` without proxy secret returns 403.
- [ ] Password accepted but My workspace remains locked until authenticator verification.
- [ ] A wrong or expired authenticator code is rejected; no tokens appear in browser responses or JavaScript.
- [ ] Correct authenticator code unlocks portfolio and saved research notes.
- [ ] After signing out, private positions and notes are inaccessible.
- [ ] Logging back in requires a fresh authenticator code.
- [ ] RLS `owner_select`, `owner_insert`, `owner_update` require `auth.jwt()->>'aal' = 'aal2'`.
- [ ] No TOTP QR, access token, Alpaca secret, or private data is committed.
- [ ] Render and Cloudflare deployments reflect the same tested commit; GitHub Actions CI is green.

## Testing scope and limitations

In this environment the complete Python test suite was run in four batches: **221 passed and 1 optional skipped** (DuckDB unavailable). Additional checks: **8 Node.js demonstration tests passed**; JavaScript syntax and the publication/privacy preflight passed. Ruff was unavailable in this environment and was **not** verified; run Ruff on Windows or in CI. The HTTP integration tests use mocked Supabase responses. **Live authenticator enrollment, actual Supabase database policies, Render deployment, Cloudflare proxy cookies, and complete browser flow remain unverified.** An independent security review is advisable before storing material financial credentials.

If setup was interrupted before verifying the factor, start enrollment again. Supabase may retain an unverified factor; if further enrollment is refused, inspect the owner's unverified factors in Supabase Auth instead of disabling MFA or putting secrets into the repository. Make sure the phone's clock is accurate if TOTP codes are rejected.

Reference: [Supabase authenticator MFA](https://supabase.com/docs/guides/auth/auth-mfa/totp); [Supabase MFA AAL and RLS](https://supabase.com/docs/guides/auth/auth-mfa).
