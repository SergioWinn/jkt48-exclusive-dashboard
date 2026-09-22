"""Open Chrome for manual verification, then save public event API responses."""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def parse_response(raw, code, bonus=False):
    payload = json.loads(raw)
    if not isinstance(payload, dict) or payload.get("status") is not True:
        raise ValueError("Respons API belum berhasil.")
    data = payload.get("data")
    if bonus:
        valid = isinstance(data, list) and all(isinstance(item, dict) for item in data)
    else:
        valid = isinstance(data, dict) and data.get("code") == code and isinstance(data.get("session"), list)
    if not valid:
        raise ValueError("Data API tidak sesuai event atau format yang diminta.")
    return payload


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("code", nargs="?", default="EXA6F1")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        detail = {"status": True, "data": {"code": "EXA6F1", "session": []}}
        assert parse_response(json.dumps(detail), "EXA6F1") == detail
        assert parse_response('{"status":true,"data":[]}', "EXA6F1", True)["data"] == []
        for raw in ('<html>Verify you are human</html>', '{"status":false}', '[]', json.dumps(detail)):
            try:
                parse_response(raw, "WRONG")
            except ValueError:
                continue
            raise AssertionError("Invalid response was accepted")
        print("Response validation: OK")
        return
    code = args.code.upper()
    if not code.isascii() or not code.isalnum() or not code.startswith("EX"):
        parser.error("Gunakan kode event, misalnya EXA6F1.")

    # Reuse the isolated Playwright installation from the local trial, when available.
    packages = ROOT / ".runtime_cache" / "playwright-probe" / "packages"
    if packages.is_dir():
        sys.path.insert(0, str(packages))
    from playwright.sync_api import sync_playwright, TimeoutError

    output = ROOT / ".runtime_cache" / "manual-json" / code / datetime.now().strftime("%Y%m%d-%H%M%S")
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="chrome", headless=False)
        try:
            page = browser.new_page()
            for name, suffix in (("detail", ""), ("bonus", "/bonus")):
                print(f"Membuka {name}. Selesaikan verifikasi di jendela Chrome jika diminta (maksimal 5 menit).", flush=True)
                try:
                    page.goto(f"https://jkt48.com/api/v1/exclusives/{code}{suffix}?lang=id",
                              wait_until="domcontentloaded", timeout=30000)
                    page.wait_for_function(
                        "() => { try { const p = JSON.parse(document.body.innerText); return p.status === true && 'data' in p; } catch { return false; } }",
                        timeout=300000,
                    )
                    payload = parse_response(page.locator("body").inner_text(), code, name == "bonus")
                    output.mkdir(parents=True, exist_ok=True)
                    path = output / f"{name}.json"
                    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
                    print(f"Tersimpan: {path}", flush=True)
                except (TimeoutError, ValueError) as error:
                    print(f"{name} gagal: {error}", flush=True)
        finally:
            browser.close()


if __name__ == "__main__":
    main()
