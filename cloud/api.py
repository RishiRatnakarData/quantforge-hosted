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

from quantforge.desk.engine import FEE_RATE, QTY, DeskError, cents, money, valid_quote
from quantforge.desk.market import AlpacaDeskMarket

app = FastAPI(title="QuantForge private API", docs_url=None, redoc_url=None, openapi_url=None)
SESSION = requests.Session()
MAX_BYTES = 350_000
SYMBOL_RE = re.compile(r"^(?:[A-Z][A-Z0-9.]{0,9}|(?:BTC|ETH|SOL)/USD)$")
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


@app.exception_handler(DeskError)
async def desk_error_handler(_request: Request, exc: DeskError):
    return JSONResponse({"detail": str(exc)}, status_code=422, headers={"Cache-Control": "no-store"})

@app.get("/api/health")
def health():
    return {"status": "ok", "mode": "single-owner-hosted", "paper_only": True}


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
    amount: str  # USD spending budget to buy; units to sell
    expected_version: int = Field(ge=0)


@app.post("/api/private/trade")
def trade(data: TradeRequest, request: Request, response: Response):
    uid, token = owner(request, response)
    current, version = read_state(uid, token)
    if version != data.expected_version:
        raise HTTPException(409, "Portfolio changed. Reload first.")
    sym = data.symbol.strip().upper()
    if not SYMBOL_RE.fullmatch(sym) or data.side not in ("buy", "sell"):
        raise HTTPException(422, "Invalid trade.")
    q = valid_quote(quote(sym), require_fresh=True)
    if q["symbol"] != sym:
        raise HTTPException(422, "Market observation did not match the chosen investment.")
    amount = money(data.amount, "trade amount")
    if amount <= 0:
        raise HTTPException(422, "Enter a positive amount.")
    price = money(q["price"], "price")
    cash = money(current["cash"], "cash")
    old = money(current["holdings"].get(sym, 0), "owned units")
    if data.side == "buy":
        if amount < 1 or amount > cash:
            raise HTTPException(422, "Buy budget must be at least $1 and within available cash.")
        units = (amount / (price * (1 + FEE_RATE))).quantize(QTY, rounding=ROUND_DOWN)
        gross = cents(units * price)
        fee = cents(gross * FEE_RATE)
        delta = gross + fee
        if units <= 0 or delta > cash or delta > amount:
            raise HTTPException(422, "Buy exceeds virtual funds.")
        current["holdings"][sym] = float(old + units)
        cash = cash - delta
    else:
        units = amount.quantize(QTY, rounding=ROUND_DOWN)
        if not units or units > old:
            raise HTTPException(422, "Cannot sell more units than held.")
        gross = cents(units * price)
        fee = cents(gross * FEE_RATE)
        cash += gross - fee
        if old == units:
            current["holdings"].pop(sym, None)
        else:
            current["holdings"][sym] = float(old - units)
    current["cash"] = float(cents(cash))
    current["trades"] = ([{"at": dt.datetime.now(dt.UTC).isoformat(),
                          "symbol": sym, "side": data.side, "units": float(units),
                          "price": q["price"], "fee": float(fee),
                          "venue": q["venue"], "observed_at": q["timestamp"]}]
                        + current.get("trades", []))[:80]
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
