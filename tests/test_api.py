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
    @patch("core.api._get_json")
    def test_member_photos_survive_missing_runtime_cache_and_empty_api(self, get_json):
        for result in (LiveApiUnavailable("Cloudflare challenge"), {"status": True, "data": []}):
            with self.subTest(result=result):
                get_member_database.clear()
                get_json.side_effect = [result]
                with patch("core.api.RUNTIME_CACHE_DIR", "missing-cache-for-photo-test"):
                    nicknames, photos = get_member_database()
                self.assertEqual(nicknames["aralie"], "abigail rachel")
                self.assertTrue(photos["abigail rachel"].startswith("https://jkt48.com/"))

    @patch("core.api._read_cache")
    @patch("core.api._get_json", side_effect=LiveApiUnavailable("Cloudflare challenge"))
    def test_newer_bundled_catalogue_survives_old_runtime_cache(self, _get_json, read_cache):
        read_cache.side_effect = [
            {"last_updated": "31/07/2026 13:02:35 WIB", "data": [{"code": "EXOLD"}]},
            {"last_updated": "18/09/2026 12:13:38 WIB", "data": [{"code": "EXNEW"}]},
        ]
        self.assertEqual(get_active_exclusive_events(), [{"code": "EXNEW"}])

    def tearDown(self):
        get_active_exclusive_events.clear()
        get_member_database.clear()
        clear_exclusive_detail_cache()
        set_jkt48_cookie("")

    @patch("core.api.USING_BROWSER_CLIENT", False)
    @patch("core.api.browser_requests.Session.get")
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
    @patch("core.api.browser_requests.Session.get")
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

    @patch("core.api._read_cache")
    @patch("core.api._get_json", side_effect=LiveApiUnavailable("Cloudflare challenge"))
    def test_akb48_member_photos_are_available_as_fallback(self, _get_json, read_cache):
        read_cache.return_value = {"nickname_map": {}, "photo_map": {}}

        _, photos = get_member_database()

        self.assertEqual(photos["mizuki yamauchi"], "https://d2r1lkk9i7row.cloudfront.net/mobile/member/83100951.jpg")
        self.assertEqual(photos["miyuu mizushima"], "https://d2r1lkk9i7row.cloudfront.net/mobile/member/83101007.jpg")
        self.assertEqual(photos["yui oguri"], "https://d2r1lkk9i7row.cloudfront.net/mobile/member/83100816.jpg")

    @patch("core.api._write_cache")
    @patch("core.api._get_json")
    def test_live_response_is_used_without_manual_event_list(self, get_json, write_cache):
        get_active_exclusive_events.clear()
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
        get_active_exclusive_events.clear()
        read_cache.return_value = {"last_updated": "now", "data": KNOWN_EXCLUSIVE_EVENTS}

        events = get_active_exclusive_events()

        self.assertGreater(len(events), 0)
        self.assertIn("EXE588", [event.get("code") for event in events])

    @patch("core.api._read_cache")
    @patch("core.api._get_json", side_effect=LiveApiUnavailable("Cloudflare challenge"))
    def test_stale_manual_fallback_json_is_ignored(self, _get_json, read_cache):
        get_active_exclusive_events.clear()
        stale_payload = {
            "last_updated": "31/07/2025 13:02:35 WIB",
            "data": [{"code": "EXOLD", "valid_date_from": "2025-07-16T13:00:00.000Z", "valid_date_to": "2025-07-31T23:59:59.000Z"}],
        }
        read_cache.side_effect = [None, stale_payload]

        events = get_active_exclusive_events()

        self.assertTrue(events)
        self.assertNotIn("EXOLD", [event.get("code") for event in events])
        self.assertIn("EXE588", [event.get("code") for event in events])

    @patch("core.api._read_cache")
    @patch("core.api._get_json", side_effect=LiveApiUnavailable("Cloudflare challenge"))
    def test_active_fallback_event_with_future_end_date_is_not_dropped(self, _get_json, read_cache):
        get_active_exclusive_events.clear()
        active_payload = {
            "last_updated": "18/09/2026 12:13:38 WIB",
            "data": [{
                "code": "EXFUTURE",
                "valid_date_from": "2026-06-15T05:00:00.000Z",
                "valid_date_to": "2026-10-01T23:59:59.000Z",
            }],
        }
        read_cache.side_effect = [None, active_payload]

        events = get_active_exclusive_events()

        self.assertEqual([event["code"] for event in events], ["EXFUTURE"])

    @patch("core.api._read_cache")
    @patch("core.api._get_json", side_effect=LiveApiUnavailable("Cloudflare challenge"))
    def test_fallback_keeps_multiple_valid_events_when_live_api_is_down(self, _get_json, read_cache):
        get_active_exclusive_events.clear()
        payload = {
            "last_updated": "18/09/2026 12:13:38 WIB",
            "data": [
                {"code": "EX01", "valid_date_from": "2026-06-15T05:00:00.000Z", "valid_date_to": "2026-10-01T23:59:59.000Z"},
                {"code": "EX02", "valid_date_from": "2026-07-16T13:00:00.000Z", "valid_date_to": "2026-11-01T23:59:59.000Z"},
                {"code": "EX03", "valid_date_from": "2026-08-20T13:00:00.000Z", "valid_date_to": "2026-12-01T23:59:59.000Z"},
            ],
        }
        read_cache.side_effect = [None, payload]

        events = get_active_exclusive_events()

        self.assertEqual([event["code"] for event in events], ["EX01", "EX02", "EX03"])

    @patch("core.api.os.replace", side_effect=PermissionError)
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
    @patch("core.api._read_latest_cache", return_value=None)
    @patch("core.api._get_json")
    def test_bonus_stock_overrides_matching_slots_and_falls_back(self, get_json, _read_cache, write_cache):
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
                write_cache.reset_mock()
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
                    self.assertEqual(write_cache.call_args.args[1]["data"], detail)
                else:
                    self.assertEqual(detail, original)
                    write_cache.assert_not_called()

    @patch("core.api._set_wr_status")
    @patch("core.api._write_cache")
    @patch("core.api._read_cache")
    @patch("core.api._get_json")
    def test_bonus_refreshes_cached_stock_when_detail_is_rate_limited(self, get_json, read_cache, write_cache, status):
        clear_exclusive_detail_cache()
        cached = {"code": "EX5A08", "session": [{
            "date": "2026-09-13T00:00:00", "start_time": "11:45", "label": "Session 1 (Sunday)",
            "session_detail": [{"label": "Jalur 1", "jkt48_member_name": "Jacqueline Immanuela",
                                "quota_available": False}],
        }]}
        read_cache.return_value = {"data": cached, "last_updated": "old metadata"}
        bonus = {"status": True, "data": [{
            "date": "2026-09-13", "start_time": "11:45:00", "label": "Sesi 1",
            "session_members": [{"label": "Jalur 1", "member_name": "Jacqueline Immanuela", "available_quota": 9}],
        }]}
        for response in (bonus, LiveApiUnavailable("HTTP 429")):
            with self.subTest(response=response):
                clear_exclusive_detail_cache()
                get_json.side_effect = [LiveApiUnavailable("HTTP 429"), response]
                data = fetch_exclusive_detail("EX5A08")
                self.assertIn("/bonus?lang=id", get_json.call_args.args[0])
                if response is bonus:
                    self.assertTrue(status.call_args.args[1])
                    member = data["session"][0]["session_detail"][0]
                    self.assertEqual(member["available_quota"], 9)
                    self.assertTrue(member["quota_available"])
                    self.assertNotIn("tickets_sold", member)
                    self.assertEqual(status.call_args.args[3], "")
                    self.assertEqual(write_cache.call_args.args[1]["data"], data)
                else:
                    self.assertFalse(status.call_args.args[1])
                    self.assertEqual(data, cached)

    @patch("core.api._set_wr_status")
    @patch("core.api._write_cache")
    @patch("core.api._read_cache", return_value=None)
    @patch("core.api._get_json")
    def test_new_event_stock_works_without_detail_or_cache(self, get_json, read_cache, write_cache, status):
        get_json.side_effect = [LiveApiUnavailable("HTTP 429"), {"status": True, "data": [{
            "exclusive_session_code": "EX5A08-SNCCF4", "date": "2026-09-13",
            "start_time": "11:45:00", "end_time": "12:45:00", "label": "Sesi 1",
            "session_members": [{"label": "Jalur 1", "member_name": "Jacqueline Immanuela",
                                 "session_detail_code": "EX5A08-SNCCF4-SD3017", "available_quota": 6}],
        }]}]
        data = fetch_exclusive_detail("EX5A08")
        self.assertEqual(data["code"], "EX5A08")
        member = data["session"][0]["session_detail"][0]
        self.assertEqual(member["jkt48_member_name"], "Jacqueline Immanuela")
        self.assertEqual(member["available_quota"], 6)
        self.assertNotIn("tickets_sold", member)
        self.assertTrue(status.call_args.args[1])
        self.assertEqual(write_cache.call_args.args[1]["data"], data)

    def test_legacy_event_json_files_are_removed(self):
        project_root = Path(__file__).parent.parent
        fallback_dir = project_root / "data" / "fallback"

        remaining_files = sorted(path.name for path in fallback_dir.glob("*.json"))

        self.assertEqual(remaining_files, ["exclusive_events.json", "members.json"])


if __name__ == "__main__":
    unittest.main()
