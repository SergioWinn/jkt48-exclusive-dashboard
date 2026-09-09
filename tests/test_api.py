import json
import os
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import Mock, patch

from core.api import (
    KNOWN_EXCLUSIVE_EVENTS,
    LiveApiUnavailable,
    WAITING_ROOM_COOKIE_NAME,
    build_jkt48_cookie,
    clear_exclusive_detail_cache,
    fetch_exclusive_detail,
    get_active_exclusive_events,
    get_member_database,
    is_waiting_room_detected,
    set_jkt48_cookie,
    validate_jkt48_cookie,
    _http_get,
)


class GetActiveExclusiveEventsTest(unittest.TestCase):
    def tearDown(self):
        get_active_exclusive_events.clear()
        get_member_database.clear()
        clear_exclusive_detail_cache()
        set_jkt48_cookie("")

    @patch("core.api.USING_BROWSER_CLIENT", False)
    @patch("core.api.browser_requests.get")
    def test_admin_cookie_is_only_sent_after_waiting_room(self, get):
        waiting_room = Mock(
            status_code=200,
            headers={"content-type": "text/html"},
            text="Cloudflare Waiting Room",
        )
        live_api = Mock(status_code=200, headers={"content-type": "application/json"})
        get.side_effect = [waiting_room, live_api]

        with patch.dict(os.environ, {"JKT48_COOKIE": "__cfwaitingroom=secret"}):
            set_jkt48_cookie("__cfwaitingroom=admin")
            _http_get("https://jkt48.com/api/v1/members", 15)

        self.assertNotIn("Cookie", get.call_args_list[0].kwargs["headers"])
        self.assertEqual(get.call_args_list[1].kwargs["headers"]["Cookie"], "__cfwaitingroom=admin")
        self.assertTrue(is_waiting_room_detected())

        get.reset_mock(side_effect=True)
        get.return_value = live_api
        _http_get("https://jkt48.com/api/v1/members", 15)

        self.assertNotIn("Cookie", get.call_args.kwargs["headers"])
        self.assertFalse(is_waiting_room_detected())

    def test_waiting_room_cookie_value_builds_the_request_header(self):
        self.assertEqual(build_jkt48_cookie(" waiting== "), f"{WAITING_ROOM_COOKIE_NAME}=waiting==")
        self.assertEqual(build_jkt48_cookie("__cfwaitingroom_custom=waiting=="), "__cfwaitingroom_custom=waiting==")
        for value in ("", "__cfwaitingroom_custom", "__cfwaitingroom_custom=", "waiting; other=value", "waiting\r\nOther: value"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                build_jkt48_cookie(value)

    @patch("core.api.USING_BROWSER_CLIENT", False)
    @patch("core.api.browser_requests.get")
    def test_admin_cookie_retries_cloudflare_challenge_for_member_photos(self, get):
        challenge = Mock(
            status_code=403,
            headers={"content-type": "text/html"},
            text="Just a moment... cf-chl",
        )
        live_api = Mock(status_code=200, headers={"content-type": "application/json"})
        get.side_effect = [challenge, live_api]
        set_jkt48_cookie(build_jkt48_cookie("admin"))

        response = _http_get("https://jkt48.com/api/v1/members", 15)

        self.assertIs(response, live_api)
        self.assertNotIn("Cookie", get.call_args_list[0].kwargs["headers"])
        self.assertEqual(get.call_args_list[1].kwargs["headers"]["Cookie"], f"{WAITING_ROOM_COOKIE_NAME}=admin")

    @patch("core.api._send_http_get")
    def test_cookie_validation_checks_live_response_without_saving(self, get):
        cookie = build_jkt48_cookie("candidate")
        response = Mock(status_code=200, headers={"content-type": "application/json"})
        response.json.return_value = {"status": True, "data": []}
        get.return_value = response
        with patch("core.api.set_jkt48_cookie") as save:
            validate_jkt48_cookie(cookie)
            self.assertEqual(get.call_args.args[2]["Cookie"], cookie)
            response.headers = {"content-type": "text/html"}
            response.text = "Cloudflare Waiting Room"
            with self.assertRaisesRegex(LiveApiUnavailable, "Waiting Room"):
                validate_jkt48_cookie(cookie)
            get.side_effect = TimeoutError("Timed out")
            with self.assertRaisesRegex(LiveApiUnavailable, "Connection failed"):
                validate_jkt48_cookie(cookie)
            save.assert_not_called()

    @patch("core.api._read_cache")
    @patch("core.api._get_json", side_effect=LiveApiUnavailable("Cloudflare challenge"))
    def test_member_photos_fall_back_to_last_successful_snapshot(self, _get_json, read_cache):
        read_cache.return_value = {
            "nickname_map": {"michie": "michelle alexandra"},
            "photo_map": {"michelle alexandra": "https://example.com/michie.jpg"},
        }

        nicknames, photos = get_member_database()

        self.assertEqual(nicknames["michie"], "michelle alexandra")
        self.assertEqual(photos["michelle alexandra"], "https://example.com/michie.jpg")

    @patch("core.api._write_cache")
    @patch("core.api._get_json")
    def test_live_response_is_used_without_manual_event_list(self, get_json, write_cache):
        live_event = {
            "code": "EXNEW1",
            "category": "DIGITAL_PHOTOBOOK",
            "title": "New live event",
            "valid_date_from": "2026-08-01T13:00:00.000Z",
        }
        get_json.return_value = {"status": True, "data": [live_event]}

        events = get_active_exclusive_events()

        self.assertEqual(events, [live_event])
        write_cache.assert_called_once()

    @patch("core.api._read_cache")
    @patch("core.api._get_json", side_effect=LiveApiUnavailable("Cloudflare Waiting Room"))
    def test_event_list_falls_back_when_live_api_is_unavailable(self, _get_json, read_cache):
        read_cache.return_value = {"last_updated": "now", "data": KNOWN_EXCLUSIVE_EVENTS}

        events = get_active_exclusive_events()

        self.assertEqual(events, KNOWN_EXCLUSIVE_EVENTS)

    @patch("builtins.open", side_effect=PermissionError)
    @patch("core.api._get_json")
    def test_cache_write_failure_does_not_discard_live_detail(self, get_json, _open):
        live_detail = {"code": "EXNEW1", "session": []}
        get_json.return_value = {"status": True, "data": live_detail}

        detail = fetch_exclusive_detail("EXNEW1")

        self.assertEqual(detail, live_detail)

    @patch("core.api._set_wr_status")
    @patch("core.api._write_cache")
    @patch("core.api._get_json")
    def test_detail_request_is_shared_for_all_users(self, get_json, _write_cache, set_status):
        live_detail = {"code": "EXSHARED", "session": []}
        get_json.return_value = {"status": True, "data": live_detail}

        with ThreadPoolExecutor(max_workers=20) as executor:
            details = list(executor.map(fetch_exclusive_detail, ["EXSHARED"] * 20))

        self.assertEqual(details, [live_detail] * 20)
        self.assertEqual(get_json.call_count, 2)
        self.assertEqual(set_status.call_count, 20)

    @patch("core.api._write_cache")
    @patch("core.api._get_json")
    def test_bonus_stock_overrides_matching_slots_and_falls_back(self, get_json, write_cache):
        member = {"label": "Jalur 1", "jkt48_member_name": "Jacqueline Immanuela",
                  "tickets_sold": 10, "available_quota": 35, "quota_available": True}
        session = {"date": "2026-09-13", "start_time": "11:45:00", "label": "Sesi 1",
                   "session_detail": [member]}
        original = {"code": "EX5A08", "default_price": 120000, "session": [
            session, {**session, "date": "2026-09-14"},
        ]}
        bonus = {"date": "2026-09-13", "start_time": "11:45:00", "label": "Sesi 1",
                 "session_members": [{"label": "Jalur 1", "member_name": "Jacqueline Immanuela",
                                      "available_quota": 0}]}
        for response in ({"status": True, "data": [bonus]},
                         LiveApiUnavailable("HTTP 404"), LiveApiUnavailable("HTTP 429"),
                         {"status": True, "data": []}, {"status": True, "data": None},
                         {"status": True, "data": [bonus, {"session_members": [None]}]}):
            with self.subTest(response=response):
                clear_exclusive_detail_cache()
                get_json.side_effect = [{"status": True, "data": original}, response]
                detail = fetch_exclusive_detail("EX5A08")
                self.assertEqual(get_json.call_args.args[0], "https://jkt48.com/api/v1/exclusives/EX5A08/bonus?lang=id")
                if isinstance(response, dict) and response.get("data") == [bonus]:
                    updated = detail["session"][0]["session_detail"][0]
                    self.assertEqual(updated["available_quota"], 0)
                    self.assertFalse(updated["quota_available"])
                    self.assertEqual(updated["tickets_sold"], 10)
                    self.assertEqual(detail["session"][1], original["session"][1])
                    self.assertEqual(detail["default_price"], 120000)
                    self.assertEqual(member["available_quota"], 35)
                else:
                    self.assertEqual(detail, original)
                self.assertEqual(write_cache.call_args.args[1]["data"], detail)

    def test_every_known_event_has_bundled_detail(self):
        project_root = Path(__file__).parent.parent

        for event in KNOWN_EXCLUSIVE_EVENTS:
            cache_file = project_root / "data" / "fallback" / f"{event['code']}.json"
            with self.subTest(code=event["code"]):
                self.assertTrue(cache_file.exists())
                with cache_file.open(encoding="utf-8") as file:
                    cached_event = json.load(file)["data"]
                self.assertEqual(cached_event["code"], event["code"])
                self.assertEqual(cached_event["category"], event["category"])


if __name__ == "__main__":
    unittest.main()
