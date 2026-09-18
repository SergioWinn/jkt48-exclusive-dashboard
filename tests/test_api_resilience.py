import tempfile
import unittest
from pathlib import Path
from threading import local
from unittest.mock import Mock, patch

from core import api


class ApiResilienceTest(unittest.TestCase):
    @patch("core.api.USING_BROWSER_CLIENT", True)
    @patch("core.api._get_http_session")
    def test_chrome_challenge_falls_back_to_safari(self, get_session):
        challenge = Mock(status_code=403, headers={"content-type": "text/html"})
        live = Mock(status_code=200, headers={"content-type": "application/json"})
        get_session.return_value.get.side_effect = [challenge, live]
        self.assertIs(api._send_http_get("https://jkt48.com/api/v1/members", 12, api.FALLBACK_HEADERS), live)
        self.assertEqual([c.args[0] for c in get_session.call_args_list], ["chrome136", "safari184"])

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
    @patch("core.api._get_http_session")
    def test_timeout_is_limited_to_two_browser_attempts(self, get_session):
        get = get_session.return_value.get
        get.side_effect = TimeoutError
        with self.assertRaises(api.LiveApiUnavailable):
            api._get_json("https://jkt48.com/api/v1/members", 20)
        self.assertEqual(get.call_count, 2)
        self.assertEqual(get.call_args.kwargs["timeout"], 5)
        self.assertEqual(get_session.return_value.cookies.clear.call_count, 4)

    @patch("core.api.USING_BROWSER_CLIENT", True)
    @patch("core.api._http_clients", new_callable=local)
    @patch("core.api.browser_requests.Session")
    def test_session_reuses_connections_without_retaining_cookies(self, factory, _clients):
        factory.return_value.get.return_value = Mock(status_code=200, headers={"content-type": "application/json"})
        for _ in range(2):
            api._send_http_get("https://jkt48.com/api/v1/members", 12, api.FALLBACK_HEADERS)
        factory.assert_called_once_with()
        self.assertEqual(factory.return_value.get.call_count, 2)
        self.assertEqual(factory.return_value.cookies.clear.call_count, 4)
        options = factory.return_value.get.call_args.kwargs
        self.assertEqual(options["impersonate"], "chrome136")
        self.assertTrue(options["discard_cookies"])
        self.assertNotIn("User-Agent", options["headers"])
        self.assertIn("User-Agent", api.FALLBACK_HEADERS)

    @patch("core.api._http_get", return_value=Mock(status_code=403, headers={"content-type": "text/html"}, text="Forbidden"))
    def test_plain_403_is_not_a_cloudflare_challenge(self, _get):
        with self.assertRaisesRegex(api.LiveApiUnavailable, "HTTP 403"):
            api._get_json("https://jkt48.com/api/v1/members", 5)
