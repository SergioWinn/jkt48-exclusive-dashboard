import json
import unittest
from unittest.mock import Mock, patch

from core import api, browser_fetch


class BrowserFallbackTest(unittest.TestCase):
    def tearDown(self):
        browser_fetch.fetch_response.clear()

    @patch("core.api.shutil.which", return_value="installed")
    @patch("core.api.get_jkt48_cookie", return_value="")
    @patch("core.api._send_http_get")
    @patch("core.browser_fetch.fetch_response")
    def test_browser_recovers_challenge_and_preserves_failure(self, browser, http, *_):
        blocked = Mock(status_code=403, headers={"cf-mitigated": "challenge"}, text="Just a moment")
        http.return_value = blocked
        payload = {"status": True, "data": {"code": "EXTEST"}}
        browser.return_value = {"status_code": 200, "headers": {"content-type": "application/json"}, "text": json.dumps(payload)}
        self.assertEqual(api._get_json("https://jkt48.com/api/v1/exclusives/EXTEST", 12), payload)
        browser.return_value = {"status_code": 503}
        with self.assertRaisesRegex(api.LiveApiUnavailable, "Cloudflare challenge"):
            api._get_json("https://jkt48.com/api/v1/exclusives/EXTEST", 12)
        browser.reset_mock()
        http.return_value = Mock(status_code=200, headers={"content-type": "application/json"}, json=lambda: payload)
        self.assertEqual(api._get_json("https://jkt48.com/api/v1/exclusives/EXTEST", 12), payload)
        browser.assert_not_called()

    @patch("core.browser_fetch.subprocess.run", side_effect=OSError)
    def test_failed_browser_attempt_is_cached(self, run):
        url = "https://jkt48.com/api/v1/exclusives/EXTEST"
        self.assertEqual(browser_fetch.fetch_response(url, 12)["status_code"], 503)
        self.assertEqual(browser_fetch.fetch_response(url, 12)["status_code"], 503)
        run.assert_called_once()
