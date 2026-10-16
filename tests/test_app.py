import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest
from streamlit.runtime.scriptrunner_utils.script_run_context import ScriptRunContext
from core.api import LiveApiUnavailable, clear_exclusive_detail_cache


class DashboardNoticesTest(unittest.TestCase):
    def test_member_search_survives_event_switch_and_tickets_lead_statistics(self):
        events = [{"code": code, "title": code, "category": "TWO_SHOT", "session": [{
            "date": "2099-01-01", "label": "Session 1", "start_time": "12:00:00",
            "session_detail": [{"jkt48_member_name": member, "available_quota": 9, "tickets_sold": 1}],
        }]} for code, member in [("EXA", "Jemima"), ("EXB", "Hagia")]]
        with patch("core.api.get_active_exclusive_events", return_value=events), \
             patch("core.api.get_member_database", return_value=({}, {})), \
             patch("core.api.fetch_exclusive_detail", side_effect=lambda code: next(e for e in events if e["code"] == code)):
            app = AppTest.from_file(str(Path(__file__).parents[1] / "app.py")).run(timeout=15)
            markdown = [m.value for m in app.markdown]
            self.assertLess(next(i for i, m in enumerate(markdown) if "laporan-container" in m),
                            next(i for i, m in enumerate(markdown) if "Entire event totals" in m))
            app.text_input(key="search_member").input("Jemima").run(timeout=15)
            next(s for s in app.selectbox if s.label == "Event").set_value("EXB").run(timeout=15)
            self.assertEqual(app.text_input(key="search_member").value, "Jemima")
            self.assertTrue(any("No schedules match" in w.value for w in app.warning))
            app.text_input(key="search_member").input("Hagia").run(timeout=15)
            self.assertTrue(any("c-member\">Hagia" in m.value for m in app.markdown))
            self.assertEqual(len(app.exception), 0)

    def test_date_selection_survives_refresh_and_search(self):
        app = AppTest.from_string('''
import streamlit as st
from ui.components import render_event_cards
query = st.text_input("Search")
event = {"code": "EXDATES", "session": [
    {"date": date, "label": "Session 1", "start_time": "12:00:00",
     "session_detail": [{"jkt48_member_name": "Member", "available_quota": 1}]}
    for date in ["2099-10-14", "2099-10-15"]
]}
render_event_cards(event, query, {}, {}, False)
''').run()
        self.assertEqual(app.radio[0].value, "14/10/2099")
        app.radio[0].set_value("15/10/2099").run()
        app.run()
        self.assertEqual(app.radio[0].value, "15/10/2099")
        app.text_input[0].input("member").run()
        self.assertEqual(len(app.radio), 0)
        app.text_input[0].input("").run()
        self.assertEqual(app.radio[0].value, "15/10/2099")
        self.assertEqual(len(app.exception), 0)

    def setUp(self):
        browser = patch("core.browser_fetch.fetch_event_json", return_value={})
        browser.start()
        self.addCleanup(browser.stop)

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

    def test_closed_detail_stops_timer_and_keeps_filters_working(self):
        event = {
            "code": "EXCLOSED",
            "title": "Closed event",
            "category": "DIGITAL_PHOTOBOOK",
            "valid_date_to": "2000-01-01T00:00:00",
            "session": [{"date": "2000-01-01", "label": "Sesi 1", "start_time": "11:45:00",
                         "session_detail": [{"label": "Jalur 1", "jkt48_member_name": "Test Member",
                                             "available_quota": 9}]}],
        }
        with patch("core.api.get_active_exclusive_events", return_value=[{**event, "valid_date_to": "2099-01-01T23:00:00"}]), \
             patch("core.api.get_member_database", return_value=({}, {})), \
             patch("core.api.fetch_exclusive_detail", return_value=event) as fetch:
            app = AppTest.from_file(str(Path(__file__).parents[1] / "app.py"))
            app.session_state["wr_status_EXCLOSED"] = {
                "is_live": True, "reason": "bonus: HTTP 404", "time": "last sync",
            }
            app.run(timeout=15)
            self.assertEqual(len(app.exception), 0)
            self.assertEqual(fetch.call_count, 1)
            self.assertTrue(any("SALES CLOSED" in markdown.value for markdown in app.markdown))
            status = next(m.value for m in app.markdown if "SALES CLOSED" in m.value)
            self.assertIn("<small>last sync</small>", status)
            self.assertNotIn("<span>", status)
            self.assertTrue(all(line.strip() for line in status.splitlines()))
            self.assertEqual(len(app.warning) + len(app.info), 0)
            self.assertFalse(any(b.key == "manual_refresh" for b in app.button))

            intervals = []
            enqueue = ScriptRunContext.enqueue

            def record_schedule(context, message):
                if message.HasField("auto_rerun"):
                    intervals.append(message.auto_rerun.interval)
                return enqueue(context, message)

            with patch.object(ScriptRunContext, "enqueue", record_schedule):
                app.run(timeout=15)
                app.toggle[0].set_value(True).run(timeout=15)
                self.assertTrue(any("Turn off Available only" in warning.value for warning in app.warning))
                app.toggle[0].set_value(False).run(timeout=15)
            self.assertEqual(intervals, [])
            self.assertEqual(fetch.call_count, 1)
            self.assertTrue(any("SALES CLOSED" in m.value for m in app.markdown))

    def test_polling_continues_without_a_final_snapshot(self):
        for closed, live_source, has_detail in [(False, True, True), (True, False, True), (True, True, False)]:
            with self.subTest(closed=closed, live_source=live_source, has_detail=has_detail):
                event = {"code": "EXPOLL", "title": "Polling event", "category": "TWO_SHOT",
                         "valid_date_to": "2000-01-01T23:00:00" if closed else "2099-01-01T23:00:00"}
                detail = {**event, "session": [{"date": "2099-01-01", "label": "Session 1",
                          "start_time": "12:00:00", "session_detail": [
                              {"jkt48_member_name": "Member", "available_quota": 9}]}]} if has_detail else None
                intervals = []
                enqueue = ScriptRunContext.enqueue

                def record_schedule(context, message):
                    if message.HasField("auto_rerun"):
                        intervals.append(message.auto_rerun.interval)
                    return enqueue(context, message)

                with patch("core.api.get_active_exclusive_events", return_value=[event]), \
                     patch("core.api.get_member_database", return_value=({}, {})), \
                     patch("core.api.fetch_exclusive_detail", return_value=detail), \
                     patch.object(ScriptRunContext, "enqueue", record_schedule):
                    app = AppTest.from_file(str(Path(__file__).parents[1] / "app.py"))
                    app.session_state["wr_status_EXPOLL"] = {"is_live": live_source, "time": "last sync"}
                    app.run(timeout=15)
                self.assertEqual(len(app.exception), 0)
                self.assertEqual(intervals, [5])

    def test_cached_status_replaces_notice_and_partial_live_data_is_compact(self):
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
                    self.assertIn("Retrying live updates", status)
                    self.assertEqual(app.session_state["event_data_EXTEST"], event)
                    continue
                self.assertEqual(len(messages), 0)
                status = next(m.value for m in app.markdown if "PARTIAL UPDATE" in m.value)
                self.assertIn('source-readout is-cached', status)
                self.assertIn("Updates automatically", status)
                self.assertNotIn("<span>Updates automatically</span>", status)
                self.assertIn("<small>last sync</small>", status)
                self.assertEqual(app.text_area(key="import_detail_EXTEST").label, "JSON detail (wajib)")
                self.assertFalse(any(button.label == "Mitigate Waiting Room" for button in app.button))


if __name__ == "__main__":
    unittest.main()
