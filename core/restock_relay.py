import hmac
import json
import logging
import os
import re
import time
from datetime import datetime, timedelta, timezone
from threading import Lock

import streamlit as st
from starlette.concurrency import run_in_threadpool
from starlette.responses import JSONResponse

from core.api import LiveApiUnavailable, _get_json, get_active_exclusive_events
from core.browser_fetch import fetch_event_json

_poll_lock = Lock()
_categories = {"PHOTOCARD", "TWO_SHOT", "DIGITAL_PHOTOBOOK", "VIDEO_CALL"}


def collect_stock(tracked_codes, categories):
    deadline = time.monotonic() + 100

    def get_json(url):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise LiveApiUnavailable("Stock collection timed out")
        return _get_json(url, min(20, remaining))

    events = get_active_exclusive_events()
    if not isinstance(events, list):
        raise LiveApiUnavailable("Invalid event list")
    cutoff = datetime.now(timezone.utc) - timedelta(days=45)
    results = []
    seen = set()
    for event in events:
        if not isinstance(event, dict):
            continue
        code = str(event.get("code", "")).strip()
        category = str(event.get("category", "")).strip().upper()
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,48}", code) or code in seen or category not in categories:
            continue
        try:
            starts = datetime.fromisoformat(str(event.get("valid_date_from", "")).replace("Z", "+00:00"))
            recent = starts.replace(tzinfo=starts.tzinfo or timezone.utc) >= cutoff
        except ValueError:
            recent = False
        if code not in tracked_codes and not recent:
            continue
        seen.add(code)
        try:
            bonus = get_json(f"https://jkt48.com/api/v1/exclusives/{code}/bonus?lang=id")
        except LiveApiUnavailable as error:
            if str(error) == "HTTP 404":
                continue
            if deadline - time.monotonic() < 35:
                raise
            bonus = fetch_event_json(code, 12).get("bonus")
            if not isinstance(bonus, dict) or bonus.get("status") is not True:
                raise error
        results.append({"event": {"code": code, "category": category, "title": event.get("title") or code}, "bonus": bonus})
        if len(results) == 30:
            break
    return {"results": results}


async def restock(request):
    try:
        token = os.getenv("RESTOCK_RELAY_TOKEN") or st.secrets.get("RESTOCK_RELAY_TOKEN", "")
    except Exception:
        logging.exception("Restock relay secret could not be loaded")
        return JSONResponse({"error": "Relay secret could not be loaded"}, status_code=503)
    if not token:
        return JSONResponse({"error": "Relay secret is not configured"}, status_code=503)
    body = bytearray()
    async for chunk in request.stream():
        body.extend(chunk)
        if len(body) > 4096:
            return JSONResponse({"error": "Payload too large"}, status_code=413)
    try:
        params = json.loads(body)
        received = params.get("relayToken", "")
        if not isinstance(received, str) or not hmac.compare_digest(received.encode(), token.encode()):
            print(f"[restock-relay] auth={'token_mismatch' if received else 'missing_token'}", flush=True)
            return JSONResponse({"error": "Unauthorized"}, status_code=401)
        tracked = params.get("trackedEventCodes", [])
        categories = params.get("categories", [])
        if not isinstance(tracked, list) or len(tracked) > 30 or any(not isinstance(code, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,48}", code) for code in tracked):
            raise ValueError("Invalid tracked events")
        if not isinstance(categories, list) or not categories or len(categories) > 4 or any(not isinstance(category, str) or category not in _categories for category in categories):
            raise ValueError("Invalid categories")
    except (ValueError, AttributeError, TypeError):
        return JSONResponse({"error": "Invalid payload"}, status_code=400)
    if not _poll_lock.acquire(blocking=False):
        return JSONResponse({"error": "Stock collection is already running"}, status_code=503)
    try:
        payload = await run_in_threadpool(collect_stock, set(tracked), set(categories))
        return JSONResponse(payload, headers={"Cache-Control": "no-store"})
    except Exception:
        logging.exception("Restock relay could not collect live stock")
        return JSONResponse({"error": "Live stock is unavailable"}, status_code=502)
    finally:
        _poll_lock.release()
