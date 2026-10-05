"""Playwright fallback for the JKT48 bonus endpoint."""

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
def fetch_bonus_json(url, timeout):
    if not shutil.which("chromium") or not shutil.which("xvfb-run"):
        return None
    if not _browser_lock.acquire(timeout=1):
        return None
    failure = "unknown error"
    try:
        print("[browser] trying Playwright bonus fallback", flush=True)
        result = subprocess.run(
            ["xvfb-run", "-a", sys.executable, str(Path(__file__).resolve()), url, str(timeout)],
            capture_output=True, text=True, encoding="utf-8", timeout=timeout + 10,
        )
        if result.returncode:
            lines = [line.strip() for line in result.stderr.splitlines() if line.strip()]
            failure = lines[-1] if lines else f"process exited {result.returncode}"
        payload = json.loads(result.stdout) if result.returncode == 0 else None
        if isinstance(payload, dict) and payload.get("status") is True:
            print("[browser] bonus=OK", flush=True)
            return payload
        failure = "invalid browser response"
    except (OSError, ValueError, subprocess.TimeoutExpired) as error:
        failure = f"{type(error).__name__}: {error}"
    finally:
        _browser_lock.release()
    print(f"[browser] bonus=FAILED reason={failure[:300]}", flush=True)
    return None


if __name__ == "__main__":
    from time import monotonic
    from urllib.parse import urlsplit

    from playwright.sync_api import TimeoutError as PlaywrightTimeout
    from playwright.sync_api import sync_playwright

    url, seconds = sys.argv[1], float(sys.argv[2])
    parsed = urlsplit(url)
    if ((parsed.scheme, parsed.netloc) != ("https", "jkt48.com")
            or not parsed.path.startswith("/api/v1/exclusives/")
            or not parsed.path.endswith("/bonus")):
        raise ValueError("Only the public JKT48 bonus API is supported")
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=shutil.which("chromium"), headless=False, timeout=5000,
            args=["--disable-dev-shm-usage"],
        )
        try:
            page = browser.new_page()
            started = monotonic()
            page.goto(url, wait_until="domcontentloaded", timeout=seconds * 1000)
            try:
                page.wait_for_function(
                    "() => { try { return JSON.parse(document.body.innerText).status === true; } catch { return false; } }",
                    timeout=max(1, (seconds - (monotonic() - started)) * 1000),
                )
            except PlaywrightTimeout:
                pass
            try:
                payload = json.loads(page.locator("body").inner_text(timeout=1000))
            except ValueError as error:
                raise ValueError(f"Non-JSON browser page: {page.title()!r}") from error
            if not isinstance(payload, dict) or payload.get("status") is not True:
                raise ValueError("Invalid bonus API response")
            print(json.dumps(payload))
        finally:
            browser.close()
