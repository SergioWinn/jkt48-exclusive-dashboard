"""Playwright fallback for JKT48 event detail and bonus endpoints."""

import json
import shutil
import subprocess
import sys
from pathlib import Path
from threading import Lock

import streamlit as st


# ponytail: one browser at a time; use a dedicated collector if throughput matters.
_browser_lock = Lock()


@st.cache_data(ttl=30, show_spinner=False)
def fetch_event_json(code, timeout):
    if not shutil.which("chromium") or not shutil.which("xvfb-run"):
        return {}
    if not _browser_lock.acquire(timeout=1):
        return {}
    failure = "unknown error"
    try:
        print(f"[browser] event={code} trying Playwright fallback", flush=True)
        result = subprocess.run(
            ["xvfb-run", "-a", sys.executable, str(Path(__file__).resolve()), code, str(timeout)],
            capture_output=True, text=True, encoding="utf-8", timeout=(timeout * 2) + 10,
        )
        if result.returncode:
            lines = [line.strip() for line in result.stderr.splitlines() if line.strip()]
            failure = lines[-1] if lines else f"process exited {result.returncode}"
        payloads = json.loads(result.stdout) if result.returncode == 0 else None
        if isinstance(payloads, dict) and any(payloads.values()):
            outcomes = " ".join(f"{name}={'OK' if payload else 'FAILED'}" for name, payload in payloads.items())
            print(f"[browser] event={code} {outcomes}", flush=True)
            return payloads
        failure = "invalid browser response"
    except (OSError, ValueError, subprocess.TimeoutExpired) as error:
        failure = f"{type(error).__name__}: {error}"
    finally:
        _browser_lock.release()
    print(f"[browser] event={code} FAILED reason={failure[:300]}", flush=True)
    return {}


if __name__ == "__main__":
    from playwright.sync_api import TimeoutError as PlaywrightTimeout
    from playwright.sync_api import sync_playwright

    code, seconds = sys.argv[1], float(sys.argv[2])
    if not code.isascii() or not code.isalnum() or not 3 <= len(code) <= 32:
        raise ValueError("Invalid event code")
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=shutil.which("chromium"), headless=False, timeout=5000,
        )
        try:
            context = browser.new_context()
            page = context.new_page()
            payloads = {}
            for resource, suffix in (("detail", ""), ("bonus", "/bonus")):
                url = f"https://jkt48.com/api/v1/exclusives/{code}{suffix}?lang=id"
                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=seconds * 1000)
                    page.wait_for_function(
                        "() => { try { return JSON.parse(document.body.innerText).status === true; } catch { return false; } }",
                        timeout=seconds * 1000,
                    )
                    payload = json.loads(page.locator("body").inner_text(timeout=1000))
                    payloads[resource] = payload if isinstance(payload, dict) and payload.get("status") is True else None
                except (PlaywrightTimeout, ValueError):
                    payloads[resource] = None
            print(json.dumps(payloads))
        finally:
            browser.close()
