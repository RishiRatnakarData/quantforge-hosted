"""QuantForge hosted single-owner API.

Public demo remains static. No Alpaca key, private state or licensed prices are
sent to unauthenticated clients. Supabase JWT + RLS, without a service-role key.
Never forward this API directly to the public without the documented proxy.
"""
from __future__ import annotations

import base64
import binascii
import datetime as dt
import hmac
import io
import json
import os
import re
import secrets
from decimal import ROUND_DOWN
from typing import Any
from urllib.parse import parse_qs, unquote, urlsplit
from xml.etree import ElementTree as ET

import qrcode
import requests
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from qrcode.image.svg import SvgPathImage

from cloud import (
    asset_directory,
    crypto_history,
    news_intelligence_v180,
    sec_fundamentals,
    valuation_market_v73,
)
from quantforge.desk.engine import FEE_RATE, QTY, DeskError, cents, money, valid_quote
from quantforge.desk.market import AlpacaDeskMarket
from quantforge.live.provider import AlpacaClient, MarketDataError

app = FastAPI(title="QuantForge private API", docs_url=None, redoc_url=None, openapi_url=None)
SESSION = requests.Session()
MAX_BYTES = 350_000
SYMBOL_RE = re.compile(r"^(?:[A-Z][A-Z0-9.]{0,9}|(?:BTC|ETH|SOL|LTC|AVAX|DOGE|LINK)/USD)$")
FACTOR_RE = re.compile(r"^[0-9a-fA-F-]{36}$")
TOTP_RE = re.compile(r"^[0-9]{6}$")


def config(name: str) -> str:
    val = os.getenv(name, "").strip()
    if not val:
        raise HTTPException(503, f"Server setting {name} is missing.")
    return val


def sb_request(method: str, path: str, *, token: str = "", payload: Any = None,
               params: dict | None = None, prefer: str | None = None) -> requests.Response:
    root = config("SUPABASE_URL").rstrip("/")
    if not root.startswith("https://") or not root.endswith(".supabase.co"):
        raise HTTPException(503, "Invalid Supabase configuration.")
    key = config("SUPABASE_PUBLISHABLE_KEY")
    headers = {"apikey": key, "Content-Type": "application/json", "Accept": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    if prefer:
        headers["Prefer"] = prefer
    try:
        return SESSION.request(method, root + path, headers=headers, json=payload,
                               params=params, timeout=16)
    except requests.RequestException as exc:
        raise HTTPException(503, "Authentication or database provider unavailable.") from exc


def cookie(response: Response, access: str, refresh: str) -> None:
    response.set_cookie("qf_access", access, max_age=3600, secure=True, httponly=True,
                        samesite="strict", path="/api")
    response.set_cookie("qf_refresh", refresh, max_age=30 * 86400, secure=True,
                        httponly=True, samesite="strict", path="/api")


def expire(response: Response) -> None:
    response.delete_cookie("qf_access", path="/api", secure=True, httponly=True, samesite="strict")
    response.delete_cookie("qf_refresh", path="/api", secure=True, httponly=True, samesite="strict")


@app.middleware("http")
async def protect(request: Request, call_next):
    # The Render origin must only accept requests from the secret-bearing Pages proxy.
    if request.url.path != "/api/health":
        expected = os.getenv("QF_PROXY_SECRET", "")
        supplied = request.headers.get("x-qf-proxy-secret", "")
        if not expected or not hmac.compare_digest(expected, supplied):
            return JSONResponse({"error": "Forbidden"}, status_code=403)
        if request.method not in ("GET", "HEAD", "OPTIONS"):
            origin = request.headers.get("origin", "")
            site = os.getenv("PUBLIC_SITE_ORIGIN", "").rstrip("/")
            if not site or origin != site or request.headers.get("x-qf-action") != "1":
                return JSONResponse({"error": "Origin verification failed"}, status_code=403)
        if request.method in ("POST", "PATCH", "PUT") and int(request.headers.get("content-length", "0")) > MAX_BYTES:
            return JSONResponse({"error": "Request too large"}, status_code=413)
    resp = await call_next(request)
    resp.headers["Cache-Control"] = "no-store"
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["Referrer-Policy"] = "no-referrer"
    resp.headers["X-Frame-Options"] = "DENY"
    return resp


PUBLIC_ERROR_CODES = {'Portfolio changed. Reload first.': 'account_changed', 'Portfolio changed. Reload and try again.': 'account_changed', 'Quote is stale. Review the timestamp and try when fresh data is available.': 'quote_stale', 'Quote has no valid timestamp. Paper trading is blocked.': 'quote_timestamp', 'Quote timestamp is in the future.': 'quote_timestamp', 'Market provider returned a zero quote.': 'quote_missing', 'Market observation did not match the chosen investment.': 'quote_mismatch', 'Price changed by more than 0.5%. Review a fresh preview.': 'quote_moved', 'Buy budget must be at least $1 and within available cash.': 'buy_budget', 'Buy exceeds virtual funds.': 'buy_budget', 'Cannot sell more units than held.': 'sell_units', 'Withdrawal exceeds available virtual cash.': 'withdraw_cash', 'Enter $1 to $1,000,000 in virtual funds.': 'funding_amount', 'Virtual capital would exceed the allowed range.': 'funding_limit', 'Request identifier already belongs to another transaction.': 'request_reused'}


PUBLIC_ERROR_CODES.update({
    "Portfolio changed in another session. Reload and try again.": "account_changed",
    "Private database rejected the write; check RLS.": "write_rejected",
    "No IEX trade is available for this ticker.": "quote_missing",
    "Crypto exchange returned no matching recent trade.": "quote_missing",
    "Alpaca network request failed; check your connection and retry.": "provider_unavailable",
    "Alpaca returned invalid JSON.": "provider_unavailable",
    "Alpaca rejected the request or returned an unexpected result.": "provider_unavailable",
})


@app.exception_handler(HTTPException)
async def public_http_error(_request: Request, exc: HTTPException):
    body = {"detail": exc.detail}
    if isinstance(exc.detail, str) and exc.detail in PUBLIC_ERROR_CODES:
        body["code"] = PUBLIC_ERROR_CODES[exc.detail]
    return JSONResponse(body, status_code=exc.status_code, headers=exc.headers)


@app.exception_handler(DeskError)
async def desk_error_handler(_request: Request, exc: DeskError):
    return JSONResponse({"detail": str(exc), "code": PUBLIC_ERROR_CODES.get(str(exc), "invalid_input")}, status_code=422, headers={"Cache-Control": "no-store"})

@app.get("/api/health")
def health():
    revision = os.getenv("RENDER_GIT_COMMIT", "")
    return {"status": "ok", "mode": "single-owner-hosted", "paper_only": True,
            "api_contract": "shared-research-v25",
            "revision": revision if re.fullmatch(r"[0-9a-f]{40}", revision) else "not-reported"}


class Credentials(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=8, max_length=200)


@app.post("/api/auth/login")
def login(data: Credentials, response: Response):
    r = sb_request("POST", "/auth/v1/token", params={"grant_type": "password"},
                   payload={"email": data.email, "password": data.password})
    if r.status_code != 200:
        raise HTTPException(401, "Invalid login or account not authorized.")
    auth = r.json()
    user = auth.get("user") or {}
    if str(user.get("id", "")) != config("OWNER_USER_ID") or not user.get("email_confirmed_at"):
        raise HTTPException(403, "Account not authorized or email unconfirmed.")
    checked = sb_request("GET", "/auth/v1/user", token=auth["access_token"])
    if checked.status_code != 200 or str(checked.json().get("id", "")) != str(user["id"]):
        raise HTTPException(401, "Sign-in session could not be validated.")
    cookie(response, auth["access_token"], auth["refresh_token"])
    # Password authentication alone never opens the private workspace.
    return auth_state(checked.json(), auth["access_token"])


def verified_totp(user: dict) -> list[str]:
    """Only verified authenticator factors may be used for step-up sign-in."""
    factors = user.get("factors") or []
    return [str(f["id"]) for f in factors
            if f.get("status") == "verified"
            and f.get("factor_type", f.get("type")) == "totp"
            and FACTOR_RE.fullmatch(str(f.get("id", "")))]


def trusted_aal(token: str, uid: str) -> str:
    """Inspect claims ONLY after /auth/v1/user has verified this exact token.

    This is not generic JWT verification. The Supabase Auth server is our
    verifier; unvalidated, browser-provided claims must never call this.
    """
    try:
        payload = token.split(".")[1]
        raw = base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4))
        claims = json.loads(raw)
    except (IndexError, ValueError, TypeError, UnicodeDecodeError, binascii.Error) as exc:
        raise HTTPException(401, "Invalid authenticated session token.") from exc
    if claims.get("sub") != uid or claims.get("role") != "authenticated":
        raise HTTPException(401, "Session identity mismatch.")
    return claims.get("aal", "aal1")


def auth_state(user: dict, token: str) -> dict:
    uid = str(user.get("id", ""))
    aal = trusted_aal(token, uid)
    if aal == "aal2" and verified_totp(user):
        return {"signed_in": True, "mode": "private", "mfa_required": False}
    return {"signed_in": False, "mfa_required": True,
            "mfa_setup": not bool(verified_totp(user))}


def authenticated_owner(request: Request, response: Response) -> tuple[str, str, dict]:
    """Validate the exact access token via Supabase, refreshing only when needed."""
    token = request.cookies.get("qf_access", "")
    if not token and not request.cookies.get("qf_refresh"):
        raise HTTPException(401, "Sign in first.")
    r = sb_request("GET", "/auth/v1/user", token=token) if token else None
    if (r is None or r.status_code == 401) and request.cookies.get("qf_refresh"):
        r2 = sb_request("POST", "/auth/v1/token", params={"grant_type": "refresh_token"},
                        payload={"refresh_token": request.cookies["qf_refresh"]})
        if r2.status_code != 200:
            expire(response)
            raise HTTPException(401, "Session expired. Sign in again.")
        new = r2.json()
        token = new["access_token"]
        r = sb_request("GET", "/auth/v1/user", token=token)
        if r.status_code == 200:
            cookie(response, token, new["refresh_token"])
    if r is None or r.status_code != 200:
        raise HTTPException(401, "Sign in again.")
    user = r.json()
    uid = str(user.get("id", ""))
    if uid != config("OWNER_USER_ID") or not user.get("email_confirmed_at"):
        raise HTTPException(403, "Not authorized.")
    return uid, token, user


def owner(request: Request, response: Response) -> tuple[str, str]:
    uid, token, user = authenticated_owner(request, response)
    if not auth_state(user, token)["signed_in"]:
        raise HTTPException(403, "Authenticator verification required to access private data.")
    return uid, token


@app.get("/api/auth/session")
def session(request: Request, response: Response):
    try:
        _uid, token, user = authenticated_owner(request, response)
    except HTTPException as e:
        if e.status_code in (401, 403):
            return {"signed_in": False, "mfa_required": False}
        raise
    return auth_state(user, token)


@app.get("/api/auth/mfa/factors")
def mfa_factors(request: Request, response: Response):
    _uid, _token, user = authenticated_owner(request, response)
    factors = verified_totp(user)
    if not factors:
        raise HTTPException(409, "Authenticator setup required first.")
    return {"factor_id": factors[0]}


def normalize_totp_qr_svg(raw: Any) -> str:
    """Validate the SVG image returned by Supabase Auth without revealing its secret.

    GoTrue's REST API normally returns raw SVG. The same valid SVG can include
    an XML declaration, or be supplied with the data-URL prefix used by some
    Supabase client SDKs. Never log the QR or TOTP secret.
    """
    if not isinstance(raw, str) or not raw or len(raw) > 100_000:
        raise HTTPException(503, "Authenticator enrollment returned an invalid QR image.")
    candidate = raw.strip()
    if candidate.lower().startswith("data:"):
        prefix, separator, payload = candidate.partition(",")
        if not separator or prefix.lower() not in {
            "data:image/svg+xml;utf-8",
            "data:image/svg+xml;charset=utf-8",
        }:
            raise HTTPException(503, "Authenticator enrollment returned an unsupported QR image.")
        candidate = unquote(payload).strip()
    if len(candidate) > 100_000 or any(
        item in candidate.lower()
        for item in ("<!doctype", "<!entity", "<script", "<foreignobject")
    ):
        raise HTTPException(503, "Authenticator enrollment returned an invalid QR image.")
    try:
        node = ET.fromstring(candidate)
    except ET.ParseError as exc:
        raise HTTPException(503, "Authenticator enrollment returned malformed QR SVG.") from exc
    if node.tag not in ("svg", "{http://www.w3.org/2000/svg}svg"):
        raise HTTPException(503, "Authenticator enrollment returned a non-SVG QR image.")
    return candidate


def generate_totp_qr_svg(totp: Any) -> str:
    """Render our own QR image from the private Supabase TOTP enrollment URI.

    Provider SVG format is not trusted and may vary. The URI/secret is never
    logged, persisted, or returned as plaintext. Only an enrolled owner can
    request this SVG; it is a sensitive one-time enrollment credential.
    """
    if not isinstance(totp, dict):
        raise HTTPException(503, "Authenticator enrollment response was incomplete.")
    uri = totp.get("uri")
    if isinstance(uri, str) and uri:
        if len(uri) > 4096 or any(ord(char) < 32 for char in uri):
            raise HTTPException(503, "Authenticator enrollment URI was invalid.")
        parsed = urlsplit(uri)
        if (parsed.scheme != "otpauth" or parsed.netloc != "totp"
                or not parsed.path.strip("/") or parsed.fragment):
            raise HTTPException(503, "Authenticator enrollment URI was invalid.")
        secrets = parse_qs(parsed.query).get("secret", [])
        if len(secrets) != 1 or not re.fullmatch(r"[A-Za-z2-7]{16,128}={0,6}", secrets[0]):
            raise HTTPException(503, "Authenticator enrollment URI was invalid.")
    else:
        # Some provider releases omit 'uri' but still return the Base32 secret.
        # Never place that secret into an error message or log.
        secret = totp.get("secret", "")
        if isinstance(secret, str) and re.fullmatch(r"[A-Za-z2-7]{16,128}={0,6}", secret):
            uri = "otpauth://totp/QuantForge%3AOwner?secret=" + secret + "&issuer=QuantForge"
        else:
            # Compatibility with minimal mocked providers used in earlier tests.
            # This fails closed on malformed provider-controlled SVG.
            return normalize_totp_qr_svg(totp.get("qr_code", ""))
    qr = qrcode.make(uri, image_factory=SvgPathImage, box_size=6, border=4)
    sink = io.BytesIO()
    qr.save(sink)
    svg = sink.getvalue().decode("utf-8")
    if len(svg) > 200_000:
        raise HTTPException(503, "Authenticator QR image was too large.")
    return svg


@app.post("/api/auth/mfa/enroll")
def mfa_enroll(request: Request, response: Response):
    _uid, token, user = authenticated_owner(request, response)
    if verified_totp(user):
        raise HTTPException(409, "An authenticator is already enrolled. Enter its code.")
    r = sb_request("POST", "/auth/v1/factors", token=token,
                   payload={"factor_type": "totp",
                            "friendly_name": "QuantForge " + secrets.token_hex(4)})
    if r.status_code not in (200, 201):
        raise HTTPException(409, "Unable to start authenticator setup. Try signing in again.")
    factor = r.json()
    totp = factor.get("totp") or {}
    factor_id = str(factor.get("id", ""))
    if not FACTOR_RE.fullmatch(factor_id):
        raise HTTPException(503, "Authenticator enrollment returned an invalid factor ID.")
    qr = generate_totp_qr_svg(totp)
    # This QR is sensitive. Return only to authenticated owner over no-store,
    # never save or log it. Do not send the underlying key to static site code.
    return {"factor_id": factor_id, "qr_svg": qr}


class MFAVerification(BaseModel):
    factor_id: str = Field(min_length=36, max_length=36)
    code: str = Field(min_length=6, max_length=6)


@app.post("/api/auth/mfa/verify")
def mfa_verify(data: MFAVerification, request: Request, response: Response):
    uid, token, user = authenticated_owner(request, response)
    if not FACTOR_RE.fullmatch(data.factor_id) or not TOTP_RE.fullmatch(data.code):
        raise HTTPException(422, "Enter the six-digit authenticator code.")
    factors = verified_totp(user)
    if factors and data.factor_id not in factors:
        raise HTTPException(403, "Unknown authenticator factor.")
    challenge = sb_request("POST", f"/auth/v1/factors/{data.factor_id}/challenge",
                           token=token, payload={})
    if challenge.status_code not in (200, 201) or not challenge.json().get("id"):
        raise HTTPException(401, "Could not begin authenticator verification.")
    result = sb_request("POST", f"/auth/v1/factors/{data.factor_id}/verify", token=token,
                        payload={"challenge_id": challenge.json()["id"], "code": data.code})
    if result.status_code != 200:
        raise HTTPException(401, "Invalid or expired authenticator code.")
    tokens = result.json()
    upgraded = tokens.get("access_token", "")
    refresh = tokens.get("refresh_token", "")
    if not upgraded or not refresh:
        raise HTTPException(503, "Supabase did not return the verified session.")
    checked = sb_request("GET", "/auth/v1/user", token=upgraded)
    if checked.status_code != 200 or str(checked.json().get("id", "")) != uid:
        raise HTTPException(401, "Authenticator session could not be validated.")
    if not auth_state(checked.json(), upgraded)["signed_in"]:
        raise HTTPException(403, "Authenticator verification did not reach MFA assurance level.")
    cookie(response, upgraded, refresh)
    return {"signed_in": True, "mode": "private", "mfa_required": False}


@app.post("/api/auth/logout")
def logout(request: Request, response: Response):
    # Explicitly revoke the current refresh session on the auth server if available.
    token = request.cookies.get("qf_access", "")
    if token:
        try:
            sb_request("POST", "/auth/v1/logout", token=token)
        except HTTPException:
            pass
    expire(response)
    return {"signed_in": False}


def default_state():
    return {"cash": 10000.0, "holdings": {}, "cost_basis": {}, "trades": [],
            "watchlist": [], "notes": [], "initial_cash": 10000.0}


def read_state(uid: str, token: str) -> tuple[dict, int]:
    r = sb_request("GET", "/rest/v1/quantforge_private_state", token=token,
                   params={"select": "version,payload", "user_id": "eq." + uid, "limit": "1"})
    if r.status_code != 200:
        raise HTTPException(503, "Private database not available. Check schema and RLS.")
    rows = r.json()
    if not rows:
        return default_state(), 0
    row = rows[0]
    return row["payload"], int(row["version"])


def save_state(uid: str, token: str, state: dict, version: int):
    if version == 0:
        r = sb_request("POST", "/rest/v1/quantforge_private_state", token=token,
                       payload={"user_id": uid, "version": 1, "payload": state},
                       prefer="return=representation")
    else:
        r = sb_request("PATCH", "/rest/v1/quantforge_private_state", token=token,
                       params={"user_id": "eq." + uid, "version": "eq." + str(version)},
                       payload={"version": version + 1, "payload": state},
                       prefer="return=representation")
    if r.status_code not in (200, 201) or not r.json():
        if r.status_code in (400, 401, 403):
            raise HTTPException(503, "Private database rejected the write; check RLS.")
        raise HTTPException(409, "Portfolio changed in another session. Reload and try again.")


@app.get("/api/private/state")
def state(request: Request, response: Response):
    uid, token = owner(request, response)
    s, v = read_state(uid, token)
    return {"portfolio": s, "version": v, "source": "supabase_private", "paper_only": True}


def quote(symbol: str) -> dict:
    if not SYMBOL_RE.fullmatch(symbol):
        raise HTTPException(422, "Unsupported investment symbol.")
    try:
        return AlpacaDeskMarket().quote(symbol)
    except (DeskError, ValueError) as exc:
        raise HTTPException(422, str(exc)) from exc


@app.get("/api/private/assets")
def private_assets(request: Request, response: Response,
                   category: str = "popular", letter: str = "", query: str = "", page: int = 0):
    """Browse Alpaca names without exposing credentials, quotes or private holdings."""
    owner(request, response)
    try:
        return asset_directory.browse(category=category, letter=letter, query=query, page=page)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@app.get("/api/private/valuation-capital")
def private_valuation_capital(request: Request, response: Response, symbol: str):
    """Owner-verified SEC point-in-time financial structure for price-aware research."""
    owner(request, response)
    try:
        return valuation_market_v73.get_capital(symbol)
    except sec_fundamentals.SECFundamentalsError as exc:
        raise HTTPException(422, str(exc)) from exc


@app.get("/api/private/sec/company")
def private_sec_company(request: Request, response: Response, symbol: str):
    """Private on-demand SEC annual figures, never a brokerage fundamentals proxy."""
    owner(request, response)
    try:
        return sec_fundamentals.get_company(symbol)
    except sec_fundamentals.SECFundamentalsError as exc:
        raise HTTPException(422, str(exc)) from exc


@app.get("/api/private/quotes")
def quotes(request: Request, response: Response, symbols: str):
    owner(request, response)
    syms = list(dict.fromkeys(s.strip().upper() for s in symbols.split(",")))
    if not 1 <= len(syms) <= 8 or any(not SYMBOL_RE.fullmatch(s) for s in syms):
        raise HTTPException(422, "Select between one and eight valid investments.")
    return {"quotes": [quote(s) for s in syms], "licensed_private": True}


class TradeRequest(BaseModel):
    symbol: str
    side: str
    amount: str  # USD budget to buy; units to sell
    expected_version: int = Field(ge=0)
    request_id: str = Field(default="", max_length=64, pattern=r"^[a-zA-Z0-9-]*$")
    reference_price: str = ""


def trade_terms(current: dict, data: TradeRequest, observation: dict) -> dict:
    """One decimal calculation shared by preview and commit; never mutates state."""
    sym = data.symbol.strip().upper()
    if not SYMBOL_RE.fullmatch(sym) or data.side not in ("buy", "sell"):
        raise HTTPException(422, "Invalid trade.")
    q = valid_quote(observation, require_fresh=True)
    if q["symbol"] != sym:
        raise HTTPException(422, "Market observation did not match the chosen investment.")
    amount = money(data.amount, "trade amount")
    if amount <= 0:
        raise HTTPException(422, "Enter a positive amount.")
    price = money(q["price"], "price")
    cash = money(current["cash"], "cash")
    old = money(current["holdings"].get(sym, 0), "owned units")
    if data.reference_price:
        reference = money(data.reference_price, "preview price")
        if reference <= 0 or abs(price-reference)/reference > money("0.005", "price tolerance"):
            raise HTTPException(422, "Price changed by more than 0.5%. Review a fresh preview.")
    if data.side == "buy":
        if amount < 1 or amount > cash:
            raise HTTPException(422, "Buy budget must be at least $1 and within available cash.")
        units = (amount / (price * (1 + FEE_RATE))).quantize(QTY, rounding=ROUND_DOWN)
        gross = cents(units * price)
        fee = cents(gross * FEE_RATE)
        delta = gross + fee
        if units <= 0 or delta > cash or delta > amount:
            raise HTTPException(422, "Buy exceeds virtual funds.")
        cash_after = cash-delta
        held_after = old+units
    else:
        units = amount.quantize(QTY, rounding=ROUND_DOWN)
        if not units or units > old:
            raise HTTPException(422, "Cannot sell more units than held.")
        gross = cents(units * price)
        fee = cents(gross * FEE_RATE)
        cash_after = cash+gross-fee
        held_after = old-units
    return {"symbol": sym, "side": data.side, "units": float(units),
            "gross": float(gross), "fee": float(fee), "price": q["price"],
            "cash_before": float(cash), "cash_after": float(cents(cash_after)),
            "cash_impact": float(cents(cash_after-cash)), "held_after": float(held_after),
            "venue": q["venue"], "observed_at": q["timestamp"], "paper_only": True}


@app.post("/api/private/trade-preview")
def preview_trade(data: TradeRequest, request: Request, response: Response):
    uid, token = owner(request, response)
    current, version = read_state(uid, token)
    if version != data.expected_version:
        raise HTTPException(409, "Portfolio changed. Reload first.")
    sym = data.symbol.strip().upper()
    if not SYMBOL_RE.fullmatch(sym) or data.side not in ("buy", "sell"):
        raise HTTPException(422, "Invalid investment or transaction side.")
    return {"preview": trade_terms(current, data, quote(sym)), "version": version}


@app.post("/api/private/trade")
def trade(data: TradeRequest, request: Request, response: Response):
    uid, token = owner(request, response)
    current, version = read_state(uid, token)
    # A lost response may be reconciled with the SAME request ID; never duplicate a receipt.
    repeated = next((t for t in current.get("trades", []) if data.request_id and t.get("request_id") == data.request_id), None)
    if repeated:
        if (repeated["symbol"] != data.symbol.strip().upper() or repeated["side"] != data.side
                or money(repeated.get("request_amount", "0"), "original amount") != money(data.amount, "trade amount")):
            raise HTTPException(409, "Request identifier already belongs to another transaction.")
        return {"portfolio": current, "version": version, "paper_only": True, "reconciled": True}
    if version != data.expected_version:
        raise HTTPException(409, "Portfolio changed. Reload first.")
    sym = data.symbol.strip().upper()
    if not SYMBOL_RE.fullmatch(sym) or data.side not in ("buy", "sell"):
        raise HTTPException(422, "Invalid investment or transaction side.")
    terms = trade_terms(current, data, quote(sym))
    if terms["held_after"]:
        current["holdings"][sym] = terms["held_after"]
    else:
        current["holdings"].pop(sym, None)
    current["cash"] = terms["cash_after"]
    receipt = {k: terms[k] for k in ("symbol", "side", "units", "price", "fee", "gross", "cash_impact", "venue", "observed_at")}
    receipt.update({"at": dt.datetime.now(dt.UTC).isoformat(), "request_id": data.request_id, "request_amount": data.amount})
    current["trades"] = ([receipt] + current.get("trades", []))[:80]
    save_state(uid, token, current, version)
    return {"portfolio": current, "version": version + 1, "paper_only": True}


class PersonalData(BaseModel):
    expected_version: int = Field(ge=0)
    watchlist: list[str] = Field(max_length=50)
    notes: list[dict] = Field(max_length=100)


@app.post("/api/private/notes")
def notes(data: PersonalData, request: Request, response: Response):
    uid, token = owner(request, response)
    current, version = read_state(uid, token)
    if version != data.expected_version:
        raise HTTPException(409, "State changed. Reload first.")
    if any(not SYMBOL_RE.fullmatch(s) for s in data.watchlist):
        raise HTTPException(422, "Invalid watchlist symbol.")
    cleaned = []
    for item in data.notes:
        if not isinstance(item, dict) or len(str(item.get("text", ""))) > 2000:
            raise HTTPException(422, "Invalid note.")
        cleaned.append({"text": str(item.get("text", "")), "symbol": str(item.get("symbol", ""))[:12],
                        "at": str(item.get("at", ""))[:40]})
    current["watchlist"] = data.watchlist
    current["notes"] = cleaned
    save_state(uid, token, current, version)
    return {"portfolio": current, "version": version + 1}


@app.get("/api/private/news-research")
def private_news_research(request: Request, response: Response, symbols: str):
    """Read-only private research on provider-supplied headlines; no full-text distribution."""
    owner(request, response)  # MFA required *before* contacting an external provider.
    selected = [s.strip().upper() for s in symbols.split(",")]
    if not 1 <= len(selected) <= 5 or len(set(selected)) != len(selected) or any(
        not news_intelligence_v180.SYMBOL.fullmatch(s) for s in selected
    ):
        raise HTTPException(422, "Choose one to five distinct valid equity symbols.")
    try:
        return news_intelligence_v180.alpaca_news(SESSION, selected)
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(503, str(exc)) from exc


# Read-only, single-owner historical market research. Historical stock bars are
# split-adjusted but price-only; dividend return is not included.
@app.get("/api/private/history")
def private_history(request: Request, response: Response, symbols: str, days: int = 365):
    owner(request, response)
    parsed = list(dict.fromkeys(x.strip().upper() for x in symbols.split(",")))
    if not 2 <= len(parsed) <= 5 or len(parsed) != len(symbols.split(",")):
        raise HTTPException(422, "Choose 2-5 distinct investments.")
    if any(not SYMBOL_RE.fullmatch(s) for s in parsed):
        raise HTTPException(422, "Select supported stocks, ETFs or USD crypto pairs.")
    if days not in (90, 180, 365, 730):
        raise HTTPException(422, "Choose a supported historical period.")
    # The prior UTC date is complete for 24/7 crypto; equity bars exclude
    # incomplete exchange sessions. No broker orders or database writes.
    end = dt.datetime.now(dt.UTC).date() - dt.timedelta(days=1)
    start = end - dt.timedelta(days=days)
    crypto = [s for s in parsed if s in crypto_history.SUPPORTED]
    equities = [s for s in parsed if s not in crypto_history.SUPPORTED]
    try:
        client = AlpacaClient.from_environment() if equities else None
        stock_feed = "sip"
        stock_observations = {}
        if equities:
            try:
                # Preserve the original SIP attempt for historical market-wide data.
                stock_observations = {
                    symbol: client.history(symbol, start.isoformat(), end.isoformat())
                    for symbol in equities
                }
            except MarketDataError as exc:
                # One denied SIP request means retry *all* stocks on IEX so an
                # analysis never silently combines different equity data feeds.
                if "HTTP 403" not in str(exc) or "feed or endpoint access denied" not in str(exc):
                    raise
                stock_feed = "iex"
                stock_observations = {
                    symbol: client.history(symbol, start.isoformat(), end.isoformat(), feed="iex")
                    for symbol in equities
                }
        observations = {}
        for symbol in parsed:
            observations[symbol] = (
                crypto_history.history(symbol, start.isoformat(), end.isoformat())
                if symbol in crypto else stock_observations[symbol]
            )
    except (MarketDataError, crypto_history.CryptoHistoryError) as exc:
        raise HTTPException(422, str(exc)) from exc
    # Mix only actually observed shared dates. Crypto trades on weekends but
    # no synthetic equity weekend closes are fabricated to force alignment.
    common = set.intersection(*(set(x["date"] for x in obs) for obs in observations.values()))
    dates = sorted(common)
    if len(dates) < 15:
        raise HTTPException(422, "Not enough overlapping daily observations for these investments.")
    closes = {symbol: {x["date"]: x["close"] for x in obs} for symbol, obs in observations.items()}
    annual = 365 if not equities else 252
    equity_source = (
        "Alpaca stocks IEX-only split-adjusted daily bars" if stock_feed == "iex"
        else "Alpaca stocks SIP split-adjusted daily bars"
    )
    source = (
        "Alpaca US crypto daily bars (UTC calendar days)" if not equities else
        equity_source if not crypto else
        f"{equity_source} and US crypto daily bars (shared equity sessions)"
    )
    coverage = (
        "Crypto venue daily closes; market open 24/7. No fees, spread or funding included." if not equities else
        "Stock prices are split-adjusted and exclude dividends. Crypto uses UTC daily bars; only shared stock sessions are compared. No synthetic weekend stock returns."
        if crypto else "Stock prices are split-adjusted and exclude dividends. Latest incomplete session excluded."
    )
    if equities and stock_feed == "iex":
        coverage += " IEX covers only one US exchange, not consolidated US trading; prices, volume and risk estimates can differ from SIP."
    return {"symbols": parsed, "dates": dates,
            "closes": {symbol: [closes[symbol][d] for d in dates] for symbol in parsed},
            "asset_classes": {symbol: "crypto" if symbol in crypto else "us_equity" for symbol in parsed},
            "sessions_per_year": annual,
            "calendar": "UTC calendar days" if not equities else "shared US stock sessions",
            "source": source, "coverage": coverage,
            "equity_feed": stock_feed if equities else None,
            "as_of": end.isoformat(), "licensed_private": True}


@app.get("/api/private/history-single")
def private_history_single(request: Request, response: Response, symbol: str, days: int = 365):
    """MFA-protected single-symbol observations; does not change the 2-5 asset contract.

    Source values are daily split-adjusted closes, not OHLCV/candlestick data.
    Historical rights remain owner-only; the public site never caches this response.
    """
    owner(request, response)
    selected = symbol.strip().upper()
    if not SYMBOL_RE.fullmatch(selected) or "," in symbol:
        raise HTTPException(422, "Select one supported investment symbol.")
    if days not in (90, 180, 365, 730):
        raise HTTPException(422, "Choose a supported historical period.")
    end = dt.datetime.now(dt.UTC).date() - dt.timedelta(days=1)
    start = end - dt.timedelta(days=days)
    crypto = selected in crypto_history.SUPPORTED
    feed = None
    try:
        if crypto:
            observations = crypto_history.history(selected, start.isoformat(), end.isoformat())
        else:
            client = AlpacaClient.from_environment()
            try:
                observations = client.history(selected, start.isoformat(), end.isoformat())
                feed = "sip"
            except MarketDataError as exc:
                if "HTTP 403" not in str(exc) or "feed or endpoint access denied" not in str(exc):
                    raise
                observations = client.history(selected, start.isoformat(), end.isoformat(), feed="iex")
                feed = "iex"
    except (MarketDataError, crypto_history.CryptoHistoryError) as exc:
        raise HTTPException(422, str(exc)) from exc
    if not isinstance(observations, list) or len(observations) < 15:
        raise HTTPException(422, "At least 15 observed daily closes are required.")
    if any(not isinstance(item, dict) for item in observations):
        raise HTTPException(422, "Provider returned malformed observations.")
    checked = []
    prior = ""
    for item in sorted(observations, key=lambda row: str(row.get("date", ""))):
        date, close = item.get("date"), item.get("close")
        if not isinstance(date, str) or date <= prior:
            raise HTTPException(422, "Provider returned duplicate or unordered dates.")
        try:
            dt.date.fromisoformat(date)
        except ValueError as exc:
            raise HTTPException(422, "Provider returned an invalid date.") from exc
        if not isinstance(close, (int, float)) or isinstance(close, bool) or (
            not 0 < float(close) < float("inf")
        ):
            raise HTTPException(422, "Provider returned a nonpositive or invalid close.")
        checked.append({"date": date, "close": float(close)})
        prior = date
    source = (
        "Alpaca US crypto daily UTC closes" if crypto else
        "Alpaca SIP split-adjusted daily stock closes" if feed == "sip" else
        "Alpaca IEX-only split-adjusted daily stock closes"
    )
    coverage = (
        "Crypto calendar days; prices exclude spread and fees." if crypto else
        "Stock sessions; split-adjusted daily closes exclude dividends and fees."
    )
    if feed == "iex":
        coverage += " IEX is a single venue, not a consolidated US market feed."
    return {
        "schema_version": 1, "symbol": selected, "observations": checked,
        "asset_class": "crypto" if crypto else "us_equity",
        "source": source, "coverage": coverage, "equity_feed": feed,
        "as_of": checked[-1]["date"], "requested_end": end.isoformat(),
        "licensed_private": True, "price_adjustment": "split" if not crypto else "none",
        "ohlcv_available": False,
    }


class CapitalRequest(BaseModel):
    action: str
    amount: str
    expected_version: int = Field(ge=0)
    confirmation: str = ""
    request_id: str = Field(default="", max_length=64, pattern=r"^[a-zA-Z0-9-]*$")


def funding_terms(current: dict, data: CapitalRequest) -> dict:
    """Shared Decimal preview/commit arithmetic; funding is not investment profit."""
    if data.action not in ("deposit", "withdraw"):
        raise HTTPException(422, "Select deposit or withdraw.")
    amount = cents(money(data.amount, "virtual capital"))
    if amount < 1 or amount > 1_000_000:
        raise HTTPException(422, "Enter $1 to $1,000,000 in virtual funds.")
    cash = money(current.get("cash", 0), "cash")
    capital = money(current.get("initial_cash", 10000), "initial cash")
    if data.action == "withdraw" and amount > cash:
        raise HTTPException(422, "Withdrawal exceeds available virtual cash.")
    delta = amount if data.action == "deposit" else -amount
    if capital + delta < 0 or capital + delta > 10_000_000:
        raise HTTPException(422, "Virtual capital would exceed the allowed range.")
    return {"action": data.action, "amount": float(amount), "cash_before": float(cash),
            "cash_after": float(cents(cash + delta)), "cash_impact": float(delta),
            "contributions_before": float(capital), "contributions_after": float(cents(capital + delta))}


@app.post("/api/private/capital-preview")
def preview_capital(data: CapitalRequest, request: Request, response: Response):
    uid, token = owner(request, response)
    current, version = read_state(uid, token)
    if version != data.expected_version:
        raise HTTPException(409, "Portfolio changed. Reload first.")
    return {"preview": funding_terms(current, data), "version": version, "paper_only": True}


@app.post("/api/private/capital")
def private_capital(data: CapitalRequest, request: Request, response: Response):
    uid, token = owner(request, response)
    current, version = read_state(uid, token)
    repeated = next((event for event in current.get("capital_events", [])
                     if data.request_id and event.get("request_id") == data.request_id), None)
    if repeated:
        if repeated.get("action") != data.action or money(repeated.get("amount"), "original amount") != cents(money(data.amount, "virtual capital")):
            raise HTTPException(409, "Request identifier already belongs to another transaction.")
        return {"portfolio": current, "version": version, "paper_only": True, "reconciled": True}
    if version != data.expected_version:
        raise HTTPException(409, "Portfolio changed. Reload and try again.")
    if data.action not in ("deposit", "withdraw", "reset"):
        raise HTTPException(422, "Select deposit, withdraw or reset.")
    amount = cents(money(data.amount, "virtual capital"))
    if amount < 1 or amount > 1_000_000:
        raise HTTPException(422, "Enter $1 to $1,000,000 in virtual funds.")
    if data.action == "reset":
        if data.confirmation != "RESET":
            raise HTTPException(422, "Type RESET to clear the virtual ledger.")
        # Leave independent private research notes and watchlist intact.
        preserved = {k: current.get(k, []) for k in ("watchlist", "notes")}
        current = default_state()
        current.update(preserved)
        current["cash"] = float(amount)
        current["initial_cash"] = float(amount)
        current["capital_events"] = [{"action": "reset", "amount": float(amount),
                                      "at": dt.datetime.now(dt.UTC).isoformat()}]
    else:
        terms = funding_terms(current, data)
        current["cash"] = terms["cash_after"]
        current["initial_cash"] = terms["contributions_after"]
        events = current.get("capital_events", [])
        current["capital_events"] = ([{"action": data.action, "amount": float(amount),
                                      "request_id": data.request_id,
                                      "at": dt.datetime.now(dt.UTC).isoformat()}] + events)[:100]
    save_state(uid, token, current, version)
    return {"portfolio": current, "version": version + 1, "paper_only": True}


class ValuationSnapshotRequest(BaseModel):
    expected_version: int = Field(ge=0)


@app.post("/api/private/valuation-snapshot")
def private_valuation_snapshot(data: ValuationSnapshotRequest, request: Request, response: Response):
    """Record an explicit owner-requested mark, never a reconstructed account history."""
    uid, token = owner(request, response)
    current, version = read_state(uid, token)
    if version != data.expected_version:
        raise HTTPException(409, "Portfolio changed. Reload first.")
    cash = money(current.get("cash"), "virtual cash")
    capital = money(current.get("initial_cash"), "net contributed capital")
    holdings = current.get("holdings")
    if cash < 0 or capital < 0 or not isinstance(holdings, dict):
        raise HTTPException(422, "Virtual account is incomplete; valuation withheld.")
    positions = []
    for symbol, raw_units in holdings.items():
        units = money(raw_units, "held units")
        if units < 0 or not SYMBOL_RE.fullmatch(symbol):
            raise HTTPException(422, "Virtual positions are invalid; valuation withheld.")
        if units > 0:
            positions.append((symbol, units))
    if len(positions) > 8:
        raise HTTPException(422, "Snapshot needs complete quote coverage for at most eight positions.")
    total = cash
    observations = []
    for symbol, units in positions:
        observed = valid_quote(quote(symbol), require_fresh=True)
        if observed["symbol"] != symbol:
            raise HTTPException(422, "Quote identity mismatch; valuation withheld.")
        total += units * money(observed["price"], "observed price")
        observations.append({"symbol": symbol, "observed_at": observed["timestamp"],
                             "source": str(observed.get("venue", "Provider"))[:60]})
    history = current.get("valuations", [])
    if not isinstance(history, list):
        raise HTTPException(422, "Stored valuation history is invalid.")
    record = {"at": dt.datetime.now(dt.UTC).isoformat(), "value": float(cents(total)),
              "cash": float(cents(cash)), "net_contributions": float(cents(capital)),
              "pnl": float(cents(total - capital)), "observations": observations,
              "source": "server-verified virtual account mark", "schema_version": 1}
    current["valuations"] = (history + [record])[-365:]
    save_state(uid, token, current, version)
    return {"portfolio": current, "version": version + 1, "paper_only": True}
