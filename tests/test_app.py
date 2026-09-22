import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest
from core.api import LiveApiUnavailable, clear_exclusive_detail_cache


class DashboardNoticesTest(unittest.TestCase):
    def test_admin_import_replaces_refresh_and_recovers_during_outage(self):
        event = {"code": "EXRECOVER", "title": "Recovery event", "category": "DIGITAL_PHOTOBOOK"}
        detail = {**event, "session": [{"date": "2099-01-01", "start_time": "11:00", "label": "Sesi 1",
                  "session_detail": [{"label": "1", "jkt48_member_name": "Member", "available_quota": 7}]}]}
        with tempfile.TemporaryDirectory() as cache, \
             patch("core.api.RUNTIME_CACHE_DIR", cache), \
             patch("core.api.get_active_exclusive_events", return_value=[event]), \
             patch("core.api.get_member_database", return_value=({}, {})), \
             patch("core.api._get_json", side_effect=LiveApiUnavailable("Cloudflare challenge")):
            clear_exclusive_detail_cache()
            app = AppTest.from_file(str(Path(__file__).parents[1] / "app.py"))
            app.secrets["ADMIN_KEYS"] = ["test-key"]
            app.query_params["akses"] = "test-key"
            app.run(timeout=15)
            self.assertFalse(any(b.key == "manual_refresh" for b in app.button))
            app.text_area(key="import_detail_EXRECOVER").input("not json")
            next(b for b in app.button if b.label == "Simpan snapshot lokal").click().run(timeout=15)
            self.assertTrue(app.error)
            self.assertEqual(list(Path(cache).iterdir()), [])
            app.text_area(key="import_detail_EXRECOVER").input(json.dumps({"status": True, "data": detail}))
            next(b for b in app.button if b.label == "Simpan snapshot lokal").click().run(timeout=15)
            self.assertEqual(len(app.exception), 0)
            self.assertEqual(app.session_state["event_data_EXRECOVER"], detail)
            self.assertFalse(app.session_state["wr_status_EXRECOVER"]["is_live"])
            self.assertTrue(any("CACHED DATA" in m.value for m in app.markdown))
            self.assertEqual(json.loads((Path(cache) / "exclusive_EXRECOVER.json").read_text())["data"], detail)
            visitor = AppTest.from_file(str(Path(__file__).parents[1] / "app.py")).run(timeout=15)
            self.assertEqual(len(visitor.exception), 0)
            self.assertEqual(len(visitor.text_area), 0)
            self.assertEqual(visitor.session_state["event_data_EXRECOVER"], detail)
            clear_exclusive_detail_cache()

    def test_closed_event_uses_static_fragment_after_first_snapshot(self):
        event = {
            "code": "EXCLOSED",
            "title": "Closed event",
            "category": "DIGITAL_PHOTOBOOK",
            "valid_date_to": "2000-01-01T00:00:00",
            "session": [{"date": "2000-01-01", "label": "Sesi 1", "start_time": "11:45:00",
                         "session_detail": [{"label": "Jalur 1", "jkt48_member_name": "Test Member",
                                             "available_quota": 9}]}],
        }
        with patch("core.api.get_active_exclusive_events", return_value=[event]), \
             patch("core.api.get_member_database", return_value=({}, {})), \
             patch("core.api.fetch_exclusive_detail", return_value=event) as fetch:
            app = AppTest.from_file(str(Path(__file__).parents[1] / "app.py"))
            app.session_state["wr_status_EXCLOSED"] = {
                "is_live": True, "reason": "bonus: HTTP 404", "time": "last sync",
            }
            app.run(timeout=15)
            self.assertEqual(len(app.exception), 0)
            self.assertEqual(fetch.call_count, 1)
            self.assertTrue(any("FINAL SNAPSHOT" in markdown.value for markdown in app.markdown))
            status = next(m.value for m in app.markdown if "FINAL SNAPSHOT" in m.value)
            self.assertTrue(all(line.strip() for line in status.splitlines()))
            self.assertEqual(len(app.warning) + len(app.info), 0)
            self.assertFalse(any(b.key == "manual_refresh" for b in app.button))

    def test_cached_status_replaces_notice_but_partial_live_data_keeps_notice(self):
        event = {"code": "EXTEST", "title": "Test event", "category": "DIGITAL_PHOTOBOOK",
                 "session": [{"date": "2099-09-13", "label": "Sesi 1", "start_time": "11:45:00",
                              "session_detail": [{"label": "Jalur 1", "jkt48_member_name": "Test Member",
                                                  "available_quota": 9}]}]}
        for is_live, reason in ((False, "Cloudflare Waiting Room"), (False, "Cloudflare challenge"),
                                (True, "Cloudflare Waiting Room"), (True, "bonus: HTTP 404")):
            with self.subTest(is_live=is_live, reason=reason), \
                 patch("core.api.get_active_exclusive_events", return_value=[event]), \
                 patch("core.api.get_member_database", return_value=({}, {})), \
                 patch("core.api.fetch_exclusive_detail", return_value=event), \
                 patch("core.api.is_waiting_room_detected", return_value=True):
                app = AppTest.from_file(str(Path(__file__).parents[1] / "app.py"))
                app.secrets["ADMIN_KEYS"] = ["test-key"]
                app.query_params["akses"] = "test-key"
                app.session_state["wr_status_EXTEST"] = {
                    "is_live": is_live, "reason": reason, "time": "last sync",
                }
                app.run(timeout=15)
                self.assertEqual(len(app.exception), 0)
                messages = list(app.warning) + list(app.info)
                if not is_live:
                    self.assertEqual(len(messages), 0)
                    status = next(m.value for m in app.markdown if "CACHED DATA" in m.value)
                    self.assertIn("last sync", status)
                    self.assertEqual(app.session_state["event_data_EXTEST"], event)
                    continue
                self.assertEqual(len(messages), 1)
                self.assertEqual(messages[0].value, "Bonus belum tersedia.")
                self.assertNotIn("Jumlah terjual tidak tersedia", messages[0].value)
                self.assertEqual(app.text_area(key="import_detail_EXTEST").label, "JSON detail (wajib)")
                self.assertFalse(any(button.label == "Mitigate Waiting Room" for button in app.button))


if __name__ == "__main__":
    unittest.main()
