"""Owner-only Alpaca headline research: dated source, bounded lexical themes, transparent tone.

No forecast, no brokerage orders, no remote model download, and no stored article contents.
"""
from __future__ import annotations

import datetime as dt
import math
import os
import re
from collections import Counter
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlsplit

import requests

SYMBOL = re.compile(r"^[A-Z][A-Z0-9.]{0,9}$")
WORDS = re.compile(r"[a-z][a-z']+")
TOPICS = {
    "Earnings": "revenue profits earnings quarterly results guidance forecasts growth margin sales",
    "Products": "product launch release software cloud chip computing artificial intelligence innovation",
    "Regulation": "lawsuit court investigation regulation antitrust rules government compliance fines",
    "Capital": "dividend buyback acquisition merger debt financing bond share stock offering",
    "Operations": "manufacturing production plant factory workers labor supply costs restructuring",
    "Markets": "analyst trading demand competition market shares prices upgrades downgrades",
}
POS = {"beats", "beat", "outperform", "upgrade", "upgraded", "surge", "surges", "growth", "record", "raises", "raised", "strong", "profit", "profits", "gain", "gains", "expands", "higher", "improved", "improves", "approval", "approves", "successful"}
NEG = {"miss", "misses", "cut", "cuts", "downgrade", "downgraded", "decline", "declines", "lawsuit", "loss", "losses", "lower", "weak", "fall", "falls", "fell", "investigation", "recall", "risk", "risks", "warning", "warns", "debt", "layoffs", "fraud", "fine", "fines"}
NEGATION = {"not", "never", "no", "without"}


def _tokens(text: str) -> list[str]:
    return WORDS.findall(text.lower())[:90]


def _tone(headline: str) -> tuple[str, float]:
    """Transparent dictionary baseline; this is not a trained financial sentiment model."""
    words = _tokens(headline)
    balance = 0
    for i, word in enumerate(words):
        val = int(word in POS) - int(word in NEG)
        if any(prev in NEGATION for prev in words[max(0, i - 2):i]):
            val = -val
        balance += val
    label = "Uncertain" if any(w in {"may", "might", "could", "rumor", "rumour", "reportedly", "uncertain"} for w in words) else "Positive" if balance > 0 else "Negative" if balance < 0 else "Mixed / neutral"
    return label, float(balance)


def _semantic_topics(texts: list[str]) -> list[str]:
    """TF-IDF document/category vectors in one corpus; cosine closest theme.

    A labeled context similarity, not a claim that sparse TF-IDF understands language like a transformer.
    """
    docs = [_tokens(text) for text in texts]
    themes = [_tokens(text) for text in TOPICS.values()]
    sets = [set(doc) for doc in docs + themes]
    count = len(sets)
    df = Counter(word for doc in sets for word in doc)
    def vector(tokens: list[str]) -> dict[str, float]:
        tf = Counter(tokens)
        vect = {word: (1 + math.log(freq)) * (1 + math.log((count + 1) / (1 + df[word])))
                for word, freq in tf.items() if len(word) >= 3}
        norm = math.sqrt(sum(x*x for x in vect.values())) or 1
        return {word: v/norm for word, v in vect.items()}
    embeddings = [vector(doc) for doc in docs + themes]
    labels = list(TOPICS)
    output = []
    for row in embeddings[:len(docs)]:
        similarity = [sum(value * row.get(term, 0) for term, value in theme.items())
                      for theme in embeddings[len(docs):]]
        best = max(range(len(similarity)), key=similarity.__getitem__)
        output.append(labels[best] if similarity[best] >= 0.04 else "Other news")
    return output


@lru_cache(maxsize=1)
def _local_finbert():
    """Optional local inference only. Cannot download or silently enable paid model inference."""
    directory = os.getenv("QF_FINBERT_LOCAL_DIR", "").strip()
    if not directory or not Path(directory).is_dir():
        return None
    # Only import the optional local transformer when its model directory exists.
    from transformers import (  # noqa: PLC0415
        AutoModelForSequenceClassification,
        AutoTokenizer,
        pipeline,
    )
    tokenizer = AutoTokenizer.from_pretrained(directory, local_files_only=True)
    model = AutoModelForSequenceClassification.from_pretrained(directory, local_files_only=True)
    return pipeline("text-classification", model=model, tokenizer=tokenizer, device=-1,
                    truncation=True, max_length=256)


def summarize_tone(counts: Counter) -> dict:
    """Descriptive thresholds, not statistical significance or future-return evidence."""
    total = sum(counts.values())
    shares = {label: counts[label] / total if total else 0.0
              for label in ("Positive", "Negative", "Mixed / neutral", "Uncertain")}
    positive, negative, neutral, uncertain = shares.values()
    if not total:
        label, reason = "No recent news", "No valid dated headlines were returned."
    elif total < 5:
        label, reason = "Limited sample", "Fewer than five valid headlines; an overall directional label is withheld."
    elif neutral + uncertain >= .6:
        label = "Mostly neutral" if neutral >= uncertain else "Ambiguous coverage"
        reason = "At least 60% of returned headlines are neutral or uncertain; directional words do not dominate the sample."
    elif positive >= .25 and negative >= .25:
        label, reason = "Conflicting coverage", "At least 25% of headlines occur on each directional side."
    elif positive >= .6 and negative <= .2 and uncertain <= .2:
        label, reason = "Mostly positive", "At least 60% positive; at most 20% negative and at most 20% uncertain."
    elif negative >= .6 and positive <= .2 and uncertain <= .2:
        label, reason = "Mostly negative", "At least 60% negative; at most 20% positive and at most 20% uncertain."
    else:
        label, reason = "Mixed / neutral", "No overall dominance threshold is satisfied."
    return {"label": label, "reason": reason, "sample_size": total, "shares": shares,
            "policy": "Minimum 5 headlines; neutral/uncertain >=60% dominates; opposing shares >=25% conflict; directional dominance requires >=60% with opposing and uncertain shares <=20%. Descriptive rules, not calibrated probabilities or a significance test."}


def analyze_news(news: list[dict], symbols: list[str], *, as_of: str) -> dict:
    if not 1 <= len(symbols) <= 5 or len(set(symbols)) != len(symbols) or any(
        not SYMBOL.fullmatch(s) for s in symbols
    ):
        raise ValueError("Select one to five valid stock symbols.")
    entries = []
    seen = set()
    cutoff = dt.datetime.fromisoformat(as_of.replace("Z", "+00:00"))
    if cutoff.tzinfo is None:
        raise ValueError("Research timestamp requires timezone.")
    for raw in news[:75]:
        if not isinstance(raw, dict):
            continue
        headline = str(raw.get("headline") or "").strip()[:220]
        stamp = str(raw.get("created_at") or "")
        raw_syms = raw.get("symbols")
        if not 8 <= len(headline) <= 220 or not isinstance(raw_syms, list):
            continue
        try:
            published = dt.datetime.fromisoformat(stamp.replace("Z", "+00:00"))
        except ValueError:
            continue
        if published.tzinfo is None or published > cutoff or published < cutoff - dt.timedelta(days=15):
            continue
        linked = [s for s in symbols if s in raw_syms]
        if not linked:
            continue
        unique = (re.sub(r"\W+", " ", headline.casefold()).strip(), stamp[:10], tuple(sorted(linked)))
        if unique in seen:
            continue
        seen.add(unique)
        url = str(raw.get("url") or "")[:400]
        parsed = urlsplit(url)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            url = ""
        entries.append({"headline": headline, "created_at": stamp, "source": str(raw.get("source") or "Unknown")[:40],
                        "url": url, "symbols": linked})
        if len(entries) >= 50:
            break
    topics = _semantic_topics([e["headline"] for e in entries]) if entries else []
    # An optional *locally provisioned* FinBERT model can override dictionary sentiment.
    model = None
    if entries:
        try:
            model = _local_finbert()
        except (ImportError, OSError, ValueError, RuntimeError):
            model = None
    tones = []
    method = "Financial-word baseline (not trained ML)"
    if model is not None:
        try:
            predictions = model([e["headline"] for e in entries], batch_size=8)
            if len(predictions) == len(entries):
                mapping = {"positive": "Positive", "neutral": "Mixed / neutral", "negative": "Negative"}
                tones = [mapping.get(str(r["label"]).lower(), "Mixed / neutral") for r in predictions]
                method = "FinBERT (local pretrained financial language model)"
        except (RuntimeError, ValueError, KeyError, TypeError):
            tones = []
    if not tones:
        tones = [_tone(e["headline"])[0] for e in entries]
    for e, topic, tone in zip(entries, topics, tones, strict=True):
        e["topic"], e["tone"] = topic, tone
    rows = []
    for sym in symbols:
        matched = [e for e in entries if sym in e["symbols"]]
        counts = Counter(e["tone"] for e in matched)
        themes = Counter(e["topic"] for e in matched)
        summary = summarize_tone(counts)
        rows.append({"symbol": sym, "articles": len(matched),
                     "tone": summary["label"], "tone_summary": summary,
                     "positive": counts["Positive"], "negative": counts["Negative"],
                     "neutral": counts["Mixed / neutral"], "uncertain": counts["Uncertain"],
                     "tone_counts": dict(counts), "topic_counts": dict(themes),
                     "coverage": {"first": min((e["created_at"] for e in matched), default=None),
                                  "last": max((e["created_at"] for e in matched), default=None)},
                     "topics": [k for k, _ in themes.most_common(2)],
                     "headlines": [{k: e[k] for k in ("headline", "created_at", "source", "url", "topic", "tone")}
                                   for e in matched[:50]]})
    return {"as_of": as_of, "method": method,
            "topic_method": "TF-IDF cosine theme similarity (not transformer embeddings)",
            "rows": rows, "articles_analyzed": len(entries),
            "limitations": "Headlines reflect coverage, not all relevant events. Tone is not an earnings or price forecast. Sources may have omissions, delays and publisher bias.",
            "licensed_private": True}


def alpaca_news(session: requests.Session, symbols: list[str], *, now: dt.datetime | None = None) -> dict:
    if not 1 <= len(symbols) <= 5 or any(not SYMBOL.fullmatch(s) for s in symbols):
        raise ValueError("Choose one to five valid equity symbols.")
    now = now or dt.datetime.now(dt.UTC)
    key = os.getenv("ALPACA_API_KEY_ID", "").strip() or os.getenv("APCA_API_KEY_ID", "").strip()
    secret = os.getenv("ALPACA_API_SECRET_KEY", "").strip() or os.getenv("APCA_API_SECRET_KEY", "").strip()
    if not key or not secret:
        raise RuntimeError("Alpaca news credentials are not configured.")
    try:
        response = session.get(
            "https://data.alpaca.markets/v1beta1/news",
            headers={"APCA-API-KEY-ID": key, "APCA-API-SECRET-KEY": secret, "Accept": "application/json"},
            params={"symbols": ",".join(symbols), "start": (now - dt.timedelta(days=14)).date().isoformat(),
                    "end": now.isoformat(), "limit": 50, "sort": "desc", "include_content": "false"},
            timeout=12,
        )
        if response.status_code != 200:
            raise RuntimeError("News provider is unavailable or access is restricted.")
        payload = response.json()
        if not isinstance(payload, dict) or not isinstance(payload.get("news"), list):
            raise RuntimeError("News provider returned an invalid response.")
    except (requests.RequestException, ValueError) as exc:
        raise RuntimeError("News provider did not return usable articles.") from exc
    return analyze_news(payload["news"], symbols, as_of=now.isoformat())
