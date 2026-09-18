import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from core import api


class ApiResilienceTest(unittest.TestCase):
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
                       {"session": [None]}, {"session": [{"session_detail": [None]}]},
                       {"session": []}):
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
    @patch("core.api.browser_requests.get", side_effect=TimeoutError)
    def test_timeout_does_not_multiply_browser_attempts(self, get):
        with self.assertRaises(api.LiveApiUnavailable):
            api._get_json("https://jkt48.com/api/v1/members", 20)
        get.assert_called_once()
        self.assertEqual(get.call_args.kwargs["timeout"], 5)

    @patch("core.api._http_get", return_value=Mock(status_code=403, headers={"content-type": "text/html"}, text="Forbidden"))
    def test_plain_403_is_not_a_cloudflare_challenge(self, _get):
        with self.assertRaisesRegex(api.LiveApiUnavailable, "HTTP 403"):
            api._get_json("https://jkt48.com/api/v1/members", 5)
