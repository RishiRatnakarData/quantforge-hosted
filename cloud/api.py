"""QuantForge hosted single-owner API.

Public demo remains static. No Alpaca key, private state or licensed prices are
sent to unauthenticated clients. Supabase JWT + RLS, without a service-role key.
Never forward this API directly to the public without the documented proxy.
"""
from __future__ import annotations

import datetime as dt
import hmac
import os
import re
from decimal import ROUND_DOWN
from typing import Any

import requests
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from quantforge.desk.engine import FEE_RATE, QTY, DeskError, cents, money, valid_quote
from quantforge.desk.market import AlpacaDeskMarket

app = FastAPI(title="QuantForge private API", docs_url=None, redoc_url=None, openapi_url=None)
SESSION = requests.Session()
MAX_BYTES = 350_000
SYMBOL_RE = re.compile(r"^(?:[A-Z][A-Z0-9.]{0,9}|(?:BTC|ETH|SOL)/USD)$")


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
    cookie(response, auth["access_token"], auth["refresh_token"])
    return {"signed_in": True, "mode": "private"}


def owner(request: Request, response: Response) -> tuple[str, str]:
    """Validate JWT with Supabase Auth, not client claims or unsigned JWT decoding."""
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
    if r.status_code != 200:
        raise HTTPException(401, "Sign in again.")
    user = r.json()
    uid = str(user.get("id", ""))
    if uid != config("OWNER_USER_ID") or not user.get("email_confirmed_at"):
        raise HTTPException(403, "Not authorized.")
    return uid, token


@app.get("/api/auth/session")
def session(request: Request, response: Response):
    try:
        owner(request, response)
    except HTTPException as e:
        if e.status_code in (401, 403):
            return {"signed_in": False}
        raise
    return {"signed_in": True, "mode": "private"}


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
