"""Bounded Playwright fallback for Community Cloud's Linux runtime."""

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
def fetch_response(url, timeout):
    failed = {"status_code": 503, "headers": {"content-type": "text/plain"}, "text": "Browser fetch unavailable"}
    if not _browser_lock.acquire(timeout=1):
        return failed
    try:
        print("[browser] trying Playwright", flush=True)
        result = subprocess.run(
            ["xvfb-run", "-a", sys.executable, str(Path(__file__).resolve()), url, str(timeout)],
            capture_output=True, text=True, encoding="utf-8", timeout=timeout + 10,
        )
        if result.returncode:
            print("[browser] FAILED: browser process", flush=True)
            return failed
        response = json.loads(result.stdout)
        print(f"[browser] status={response['status_code']} type={response['headers'].get('content-type')}", flush=True)
        return response
    except (OSError, ValueError, subprocess.TimeoutExpired):
        print("[browser] FAILED: startup or timeout", flush=True)
        return failed
    finally:
        _browser_lock.release()


if __name__ == "__main__":
    from time import monotonic
    from urllib.parse import urlsplit
    from playwright.sync_api import sync_playwright, TimeoutError

    url, seconds = sys.argv[1], float(sys.argv[2])
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.netloc != "jkt48.com" or not parsed.path.startswith("/api/v1/"):
        raise ValueError("Only the public JKT48 API is supported")
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path=shutil.which("chromium"), headless=False, timeout=5000)
        try:
            page = browser.new_page()
            started = monotonic()
            page.goto(url, wait_until="domcontentloaded", timeout=seconds * 1000)
            try:
                page.wait_for_function(
                    "() => { try { return JSON.parse(document.body.innerText).status === true; } catch { return false; } }",
                    timeout=max(1, (seconds - (monotonic() - started)) * 1000),
                )
            except TimeoutError:
                pass
            body = page.locator("body").inner_text(timeout=1000)
            try:
                payload = json.loads(body)
                success = isinstance(payload, dict) and payload.get("status") is True
            except ValueError:
                success = False
            print(json.dumps({"status_code": 200 if success else 403,
                              "headers": {"content-type": "application/json" if success else "text/html",
                                          **({} if success else {"cf-mitigated": "challenge"})}, "text": body}))
        finally:
            browser.close()
