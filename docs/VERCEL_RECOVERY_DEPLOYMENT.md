> Historical recovery record. For current operations and verified source identity use [Deployment, security and rollback](current/DEPLOYMENT_SECURITY_ROLLBACK.md) and [Release status](current/RELEASE_STATUS.md).

# Recovered API: source and release boundary

The active API is `https://quantforge-api-recovery.vercel.app`. The Cloudflare proxy accepts exactly this origin and the former named Render origin; arbitrary Vercel/Render tenants, credentials, ports, paths and lookalike hosts are rejected. Changing the configured provider is an explicit deployment operation, not an automatic fallback.

The November 16 recovery directory was compared with this repository: 225 of 226 packaged library files matched after newline normalization. The remaining file was an empty `tools/__init__.py`, now retained here. The recovered application entrypoint and 60-second Vercel function configuration are retained in `deploy/vercel-api/`. The API implementation, MFA, state schema and numerical engines are shared source, not a second maintained backend.

## Reproduce without publishing

From a clean reviewed commit, run `python tools/package_vercel_api.py outputs/vercel-api-COMMIT`. The destination must be empty. The explicit allowlist includes only runtime Python modules, the SEC transformation helper and public SEC snapshot. It excludes local CLI state, provider credentials, account data, tests and generated browser assets. `SOURCE_MANIFEST.json` records the source commit, dirty flag and hashes. `--allow-dirty` is for local inspection only and must not establish a production release claim. The command performs no network or deployment action.

Use the existing authenticated Vercel project only after release approval and free-plan verification. Runtime secrets stay in provider environment settings. Never include `.vercel`, `.wrangler`, `.env` or protection-bypass values in the package or Git. Do not use a bypass token to make ordinary API traffic work. Review project protection/bypass settings separately; authentication/permission changes need explicit authorization.

## Acceptance and rollback

Verify direct health, direct private denial, same-origin proxied health and signed-out session. Then verify owner-controlled MFA and read-only private access separately. Fixtures are not owner acceptance. Health must report the expected contract; the existing recovered deployment reports `revision: not-reported`, so its source identity is established only by the local package comparison and deployment evidence, not an asserted remote commit.

Keep the existing recovered API deployment and Cloudflare deployment ID before publishing. Roll back to those existing deployment artifacts if an acceptance check fails. Do not change the proxy environment back to Render as a default rollback: that path had unresolved upstream 429 behavior. No Supabase migration, record reset or runtime restart is part of rollback. The original Render-only release documents remain historical evidence and are not current deployment instructions.

The reviewed candidate health endpoint accepts validated Render/Vercel Git commit variables, or the clean CLI package source manifest. Dirty local packages report no source revision. This supports future deployment parity checks; it does not retrospectively identify the currently deployed recovery package.
