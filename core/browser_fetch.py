"""Playwright fallback for JKT48 event detail and bonus endpoints."""

import json
import shutil
from threading import Lock

import streamlit as st


# ponytail: one browser at a time; use a dedicated collector if throughput matters.
_browser_lock = Lock()
_browser_mode_codes = set()


def use_browser_mode(code):
    return code in _browser_mode_codes


def enable_browser_mode(code):
    _browser_mode_codes.add(code)


def clear_browser_modes():
    _browser_mode_codes.clear()


@st.cache_resource(show_spinner=False)
def _get_browser():
    chromium = shutil.which("chromium")
    if not chromium:
        return None
    from playwright.sync_api import sync_playwright

    playwright = sync_playwright().start()
    return playwright, playwright.chromium.launch(executable_path=chromium, headless=True, timeout=5000)


def fetch_event_json(code, timeout):
    if not _browser_lock.acquire(timeout=1):
        return {}
    failure = "unknown error"
    context = None
    try:
        browser_resource = _get_browser()
        if not browser_resource:
            return {}
        _, browser = browser_resource
        print(f"[browser] event={code} using persistent Playwright", flush=True)
        context = browser.new_context()
        page = context.new_page()
        payloads = {}
        for resource, suffix in (("detail", ""), ("bonus", "/bonus")):
            url = f"https://jkt48.com/api/v1/exclusives/{code}{suffix}?lang=id"
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=timeout * 1000)
                page.wait_for_function(
                    "() => { try { return JSON.parse(document.body.innerText).status === true; } catch { return false; } }",
                    timeout=timeout * 1000,
                )
                payload = json.loads(page.locator("body").inner_text(timeout=1000))
                payloads[resource] = payload if isinstance(payload, dict) and payload.get("status") is True else None
            except Exception:
                payloads[resource] = None
        if any(payloads.values()):
            outcomes = " ".join(f"{name}={'OK' if payload else 'FAILED'}" for name, payload in payloads.items())
            print(f"[browser] event={code} {outcomes}", flush=True)
            return payloads
        failure = "invalid browser response"
    except Exception as error:
        failure = f"{type(error).__name__}: {error}"
    finally:
        if context:
            context.close()
        _browser_lock.release()
    print(f"[browser] event={code} FAILED reason={failure[:300]}", flush=True)
    return {}
