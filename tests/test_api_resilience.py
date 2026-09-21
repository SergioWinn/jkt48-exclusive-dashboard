import tempfile
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from threading import Thread
from unittest.mock import Mock, patch

from core import api


class ApiResilienceTest(unittest.TestCase):
    @patch("core.api.USING_BROWSER_CLIENT", True)
    @patch("core.api.browser_requests.Session.get")
    def test_chrome_challenge_falls_back_to_safari(self, get):
        challenge = Mock(status_code=403, headers={"content-type": "text/html"})
        live = Mock(status_code=200, headers={"content-type": "application/json"})
        get.side_effect = [challenge, live]
        self.assertIs(api._send_http_get("https://jkt48.com/api/v1/members", 12, api.FALLBACK_HEADERS), live)
        self.assertEqual([c.kwargs["impersonate"] for c in get.call_args_list], ["chrome136", "safari184"])
        for call in get.call_args_list:
            self.assertEqual(call.kwargs["headers"], api.BASE_HEADERS)

    def test_session_reuses_cookies_without_mixing_browsers_or_users(self):
        received = []

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                received.append(self.headers.get("Cookie"))
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Set-Cookie", "visit=retained; Path=/")
                self.end_headers()
                self.wfile.write(b'{}')

            def log_message(self, *args):
                pass

        with HTTPServer(("127.0.0.1", 0), Handler) as server:
            thread = Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                with patch("core.api.st.session_state", {}):
                    url = f"http://127.0.0.1:{server.server_port}/"
                    api._send_http_get(url, 5, api.FALLBACK_HEADERS)
                    api._send_http_get(url, 5, api.FALLBACK_HEADERS)
                    chrome = api._get_http_session("chrome136")
                    safari = api._get_http_session("safari184")
                    self.assertIsNot(chrome, safari)
                    self.assertNotIn("visit", safari.cookies)
                    for session in api.st.session_state["_http_sessions"].values():
                        session.close()
                with patch("core.api.st.session_state", {}):
                    fresh = api._get_http_session("chrome136")
                    self.assertIsNot(fresh, chrome)
                    self.assertNotIn("visit", fresh.cookies)
                    fresh.close()
            finally:
                server.shutdown()
                thread.join()
        self.assertEqual(received, [None, "visit=retained"])

    @patch("core.api._set_wr_status")
    @patch("core.api._write_cache")
    @patch("core.api._read_latest_cache")
    @patch("core.api._get_json")
    def test_live_main_data_survives_bonus_failure(self, get_json, cache, write, status):
        api.clear_exclusive_detail_cache()
        live = {"code": "EXPARTIAL", "title": "New title", "session": []}
        cache.return_value = {"data": {**live, "title": "Old title"}, "last_updated": "old"}
        get_json.side_effect = [{"data": live}, api.LiveApiUnavailable("Cloudflare challenge")]
        self.assertEqual(api.fetch_exclusive_detail("EXPARTIAL"), live)
        self.assertTrue(status.call_args.args[1])
        self.assertIn("Bonus:", status.call_args.args[3])
        write.assert_not_called()

    def tearDown(self):
        api.get_active_exclusive_events.clear()
        api.clear_exclusive_detail_cache()

    def test_failed_atomic_write_preserves_previous_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory) / "event.json")
            api._write_cache(path, {"data": "old"})
            with patch("core.api.os.replace", side_effect=PermissionError):
                api._write_cache(path, {"data": "new"})
            self.assertEqual(api._read_cache(path), {"data": "old"})
            self.assertEqual(len(list(Path(directory).iterdir())), 1)

    @patch("core.api._read_latest_cache", return_value={"data": [{"code": "EXSAFE"}]})
    @patch("core.api._get_json")
    def test_bad_catalogue_uses_fallback(self, get_json, _cache):
        for data in (None, "bad", [None], {"data": None}):
            api.get_active_exclusive_events.clear()
            get_json.return_value = {"status": True, "data": data}
            self.assertEqual(api.get_active_exclusive_events(), [{"code": "EXSAFE"}])

    @patch("core.api._set_wr_status")
    @patch("core.api._write_cache")
    @patch("core.api._read_latest_cache")
    @patch("core.api._get_json")
    def test_failed_or_malformed_refresh_preserves_stock_and_recovers(self, get_json, cache, write, status):
        saved = {"code": "EXSAFE", "session": [{
            "date": "2099-09-13", "start_time": "11:00", "session_detail": [{
                "label": "1", "jkt48_member_name": "Member", "available_quota": 7,
            }],
        }]}
        cache.return_value = {"last_updated": "last good", "data": saved}
        for detail in (api.LiveApiUnavailable("timeout"), {"session": None},
                       {"session": [None]}, {"session": [{"session_detail": [None]}]}):
            api.clear_exclusive_detail_cache()
            response = detail if isinstance(detail, Exception) else {"status": True, "data": {"code": "EXSAFE", **detail}}
            get_json.side_effect = [response, api.LiveApiUnavailable("Cloudflare challenge")]
            self.assertEqual(api.fetch_exclusive_detail("EXSAFE"), saved)
            self.assertEqual(status.call_args.args[1:3], (False, "last good"))
            write.assert_not_called()
        api.clear_exclusive_detail_cache()
        get_json.side_effect = [{"status": True, "data": saved}, {"status": True, "data": [{
            "date": "2099-09-13", "start_time": "11:00", "session_members": [{
                "label": "1", "member_name": "Member", "available_quota": 2,
            }],
        }]}]
        result = api.fetch_exclusive_detail("EXSAFE")
        self.assertEqual(result["session"][0]["session_detail"][0]["available_quota"], 2)
        self.assertTrue(status.call_args.args[1])
        write.assert_called_once()

    @patch("core.api.USING_BROWSER_CLIENT", True)
    @patch("core.api.browser_requests.Session.get")
    def test_timeout_is_limited_to_two_browser_attempts(self, get):
        get.side_effect = TimeoutError
        with self.assertRaises(api.LiveApiUnavailable):
            api._get_json("https://jkt48.com/api/v1/members", 20)
        self.assertEqual(get.call_count, 2)
        self.assertEqual(get.call_args.kwargs["timeout"], 20)

    @patch("core.api.USING_BROWSER_CLIENT", True)
    @patch("core.api.browser_requests.Session.get")
    def test_successful_chrome_keeps_cookie_and_timeout_with_profile_headers(self, get):
        get.return_value = Mock(status_code=200, headers={"content-type": "application/json"})
        url = "https://jkt48.com/api/v1/members"
        headers = {**api.FALLBACK_HEADERS, "Cookie": "manual=value"}
        api._send_http_get(url, 12, headers)
        get.assert_called_once_with(url, impersonate="chrome136", timeout=12,
                                   headers={**api.BASE_HEADERS, "Cookie": "manual=value"})
        self.assertEqual(headers["User-Agent"], api.FALLBACK_HEADERS["User-Agent"])

    @patch("core.api._http_get", return_value=Mock(status_code=403, headers={"content-type": "text/html"}, text="Forbidden"))
    def test_plain_403_is_not_a_cloudflare_challenge(self, _get):
        with self.assertRaisesRegex(api.LiveApiUnavailable, "HTTP 403"):
            api._get_json("https://jkt48.com/api/v1/members", 5)
