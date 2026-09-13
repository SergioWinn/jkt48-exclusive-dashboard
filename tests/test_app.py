import unittest
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest


class DashboardNoticesTest(unittest.TestCase):
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
            app.run(timeout=15)
            self.assertEqual(len(app.exception), 0)
            self.assertEqual(fetch.call_count, 1)
            self.assertTrue(any("FINAL SNAPSHOT" in markdown.value for markdown in app.markdown))

    def test_api_and_stock_notices_share_one_message(self):
        event = {"code": "EXTEST", "title": "Test event", "category": "DIGITAL_PHOTOBOOK",
                 "session": [{"date": "2099-09-13", "label": "Sesi 1", "start_time": "11:45:00",
                              "session_detail": [{"label": "Jalur 1", "jkt48_member_name": "Test Member",
                                                  "available_quota": 9}]}]}
        for is_live in (False, True):
            with self.subTest(is_live=is_live), \
                 patch("core.api.get_active_exclusive_events", return_value=[event]), \
                 patch("core.api.get_member_database", return_value=({}, {})), \
                 patch("core.api.fetch_exclusive_detail", return_value=event), \
                 patch("core.api.is_waiting_room_detected", return_value=True):
                app = AppTest.from_file(str(Path(__file__).parents[1] / "app.py"))
                app.secrets["ADMIN_KEYS"] = ["test-key"]
                app.query_params["akses"] = "test-key"
                app.session_state["wr_status_EXTEST"] = {
                    "is_live": is_live, "reason": "Cloudflare Waiting Room", "time": "last sync",
                }
                app.run(timeout=15)
                self.assertEqual(len(app.exception), 0)
                messages = list(app.warning) + list(app.info)
                self.assertEqual(len(messages), 1)
                self.assertIn("Cloudflare Waiting Room", messages[0].value)
                self.assertIn("Jumlah terjual tidak tersedia", messages[0].value)
                self.assertTrue(any(button.label == "Mitigate Waiting Room" for button in app.button))


if __name__ == "__main__":
    unittest.main()
