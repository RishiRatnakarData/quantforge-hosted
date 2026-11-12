# PR #1 session and Home acceptance — 2026-11-12

This continues `chatgpt/home-evidence-polish-20261112` from `c4dbd33`.
Production main was `b0691ef4cea30dcaa0f78e01f94c7201819060fd` at review.
This document records candidate validation, not production release approval.

## Findings and changes

- The existing CI browser job failed in `beginner_walkthrough`: the test tried
  to fill the Explore search while the new first-visit Home hid Explore.
  The journey now opens Home, searches there, and verifies the handoff to Explore.
  Research-specific quality cases explicitly visit `#explore`.
- The cold-start fixture omitted the initial anonymous session response. Its
  unhandled mocked route looked like a second outage. That response is now
  modeled explicitly; the invalid-credentials case still asserts one login
  request and zero health retries.
- Supabase HTTP outages and rate limits were incorrectly collapsed into invalid
  credentials or expired sessions. They now remain service errors (503/429),
  without clearing a still-valid remembered session on a transient failure.
- Auth requests and health polls have time limits; health readiness requires
  JSON `status: ok`. Only transient password/session failures use bounded
  recovery. MFA verification and account mutations are never blindly replayed.
- Sign-out clears visible private content and the restoration preference before
  waiting for the network. It waits for outstanding auth responses before
  revocation, and ignores late MFA/enrollment/session results. An expired access
  cookie is refreshed when necessary to revoke the current device's refresh
  session. An unavailable revocation leaves a visible warning on the public shell.
- The Pages proxy normalizes upstream HTML/interstitial responses to a no-store
  JSON 503 and withholds their markup/cookies. Real JSON 401/403/429 responses
  retain their status and do not trigger credential retries.

## Security semantics

The browser stores only the opt-in preference. Credentials, MFA codes, tokens,
and account records are not written to browser storage. Secure, HttpOnly,
SameSite=Strict cookies remain on `/api`; the existing cookie lifetimes are
unchanged. Every restored session still requires the verified owner, confirmed
email, enrolled authenticator, and validated AAL2 token before private access.
Refreshing an AAL1 session does not make it AAL2. Revocation targets this device
(`scope=local`). Supabase access JWTs retain their normal expiry semantics;
refresh-token revocation is not a claim of instantaneous JWT invalidation.

Sources: [Supabase sign-out](https://supabase.com/docs/reference/javascript/auth-signout),
[Supabase sessions](https://supabase.com/docs/guides/auth/sessions),
[Render free services](https://render.com/docs/free).

## Local evidence

- Full Python suite: 636 passed.
- Full JavaScript suite: 424 passed.
- Privacy preflight, lint, and compiled CSP/hash audit passed.
- Fresh HTTPS Home: 320, 390, 768, 1024, 1440 CSS-pixel widths; search and
  navigation passed. Mobile and desktop screenshots inspected.
- Guided research: Chromium, Firefox, WebKit at all five widths passed,
  including visible guide sections, expanded thesis prompts, append-only
  revision/reload, full-archive refusal, and private/public isolation.
- Independent quality: all three engines at all five widths passed, including
  the corrected Home search, keyboard controls, direct routes, missing data,
  benchmark isolation, and delayed-response cases.
- Session lifecycle: all three engines passed transient restoration, actual
  expiry, AAL1 MFA gating, opt-in reload, preference clearing, late MFA/sign-out
  ordering, and visible failed-revocation notice. All account data was isolated
  fictional fixture state.

Generated screenshots/logs remain in ignored `outputs/`; no owner account data
or credentials are included in this commit. Remote CI must pass on the final SHA.

## Hosted acceptance remains open

Read-only production browser inspection reproduced the sign-in error. At the
same visit, `/api/health` displayed a hosting security-verification page naming
the Render backend, rather than API JSON. This is evidence of an upstream
interstitial during that inspection, not proof of its cause or permanence.
No challenge was bypassed and no deployment or hosting security setting changed.

Before merge/release, inspect the actual Render service and upstream response,
verify its Auto Deploy branch/configuration and deployed revision, and resolve
the interstitial through supported hosting controls. Then validate the candidate
through an authorized same-origin hosted environment: owner-controlled login/MFA,
opt-in reload, expired access-cookie refresh, post-idle reconnect, sign-out and
reload, with matching frontend/backend revisions. Preview-origin restrictions
must remain intact. Do not request credentials or MFA codes in chat.

No real notes, portfolios, funding, trades, MFA enrollment, or private records
were changed. The PR remains draft and production is unchanged.
