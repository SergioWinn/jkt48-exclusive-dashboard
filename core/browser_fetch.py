"""Isolated Playwright fallback for JKT48 exclusive endpoints."""

import json
import shutil
import subprocess
import sys
from pathlib import Path
from threading import Lock


# Only one Chromium process is needed at a time. The dashboard's five-second
# detail cache prevents this fallback from being launched for every rerun.
_browser_lock = Lock()
_browser_mode_codes = set()


def use_browser_mode(code):
    return code in _browser_mode_codes


def enable_browser_mode(code):
    _browser_mode_codes.add(code)


def clear_browser_modes():
    _browser_mode_codes.clear()


def fetch_event_json(code, timeout):
    """Fetch detail and bonus in a separate process to protect Streamlit's loop."""
    if not shutil.which("chromium") or not _browser_lock.acquire(timeout=1):
        return {}
    failure = "unknown error"
    try:
        print(f"[browser] event={code} trying isolated Playwright fallback", flush=True)
        result = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), code, str(timeout)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=(timeout * 2) + 10,
        )
        if result.returncode:
            lines = [line.strip() for line in result.stderr.splitlines() if line.strip()]
            failure = lines[-1] if lines else f"process exited {result.returncode}"
            return {}
        payloads = json.loads(result.stdout)
        if isinstance(payloads, dict) and any(payloads.values()):
            outcomes = " ".join(
                f"{name}={'OK' if payload else 'FAILED'}" for name, payload in payloads.items()
            )
            print(f"[browser] event={code} {outcomes}", flush=True)
            return payloads
        failure = "invalid browser response"
    except (OSError, ValueError, subprocess.TimeoutExpired, json.JSONDecodeError) as error:
        failure = f"{type(error).__name__}: {error}"
    finally:
        _browser_lock.release()
    print(f"[browser] event={code} FAILED reason={failure[:300]}", flush=True)
    return {}


def _validate_code(code):
    if not code.isascii() or not code.isalnum() or not 3 <= len(code) <= 32:
        raise ValueError("Invalid event code")


def _collect_event_json(code, seconds):
    from playwright.sync_api import TimeoutError as PlaywrightTimeout
    from playwright.sync_api import sync_playwright

    _validate_code(code)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=shutil.which("chromium"), headless=True, timeout=5000,
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
                    payloads[resource] = (
                        payload if isinstance(payload, dict) and payload.get("status") is True else None
                    )
                except (PlaywrightTimeout, ValueError):
                    payloads[resource] = None
            return payloads
        finally:
            browser.close()


if __name__ == "__main__":
    event_code, event_timeout = sys.argv[1], float(sys.argv[2])
    print(json.dumps(_collect_event_json(event_code, event_timeout)))
