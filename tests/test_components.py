import unittest
from unittest.mock import patch

from core.api import LiveApiUnavailable, _apply_bonus_stock
from core.stats import calculate_event_stats
from ui.components import render_event_cards


class EventCardsTest(unittest.TestCase):
    @patch("ui.components.st.markdown")
    def test_bonus_remaining_is_shown_without_sales_counts(self, markdown):
        session = {"date": "2099-09-13", "start_time": "11:45:00", "label": "Sesi 1"}
        event = {"code": "EX5A08", "category": "TWO_SHOT", "session": [{
            **session, "session_detail": [{"label": "Jalur 1", "jkt48_member_name": "Jacqueline Immanuela",
                                          "quota_available": True}],
        }]}
        for quota in (9, 3, 0, None):
            with self.subTest(quota=quota):
                data = event if quota is None else _apply_bonus_stock(event, [{
                    **session, "session_members": [{"label": "Jalur 1", "member_name": "Jacqueline Immanuela",
                                                    "available_quota": quota}],
                }])
                render_event_cards(data, "", {}, {}, False)
                html = markdown.call_args.args[0]
                self.assertNotIn("Sold:&nbsp;", html)
                if quota is None:
                    self.assertIn("Status:&nbsp;<b>AVAILABLE</b>", html)
                    self.assertNotIn("0 remaining", html)
                else:
                    self.assertIn(f"Remaining:&nbsp;<b>{quota}</b>", html)
                    self.assertIn(f"{quota}&nbsp;LEFT" if quota else "SOLD&nbsp;OUT", html)

    @patch("ui.components.st.markdown")
    def test_video_call_uses_capacity_45_for_sales_and_stats(self, markdown):
        session = {"date": "2099-09-13", "start_time": "11:45:00", "label": "Sesi 1"}
        event = {"code": "EX5A08", "category": "DIGITAL_PHOTOBOOK", "default_price": 120000,
                 "session": [{**session, "session_detail": [
                     {"label": "Jalur 1", "jkt48_member_name": "Jacqueline Immanuela", "tickets_sold": 1},
                 ]}]}
        for quota in (0, 9, 45, 46):
            with self.subTest(quota=quota):
                bonus = [{**session, "session_members": [
                    {"label": "Jalur 1", "member_name": "Jacqueline Immanuela", "available_quota": quota},
                ]}]
                if quota > 45:
                    with self.assertRaises(LiveApiUnavailable):
                        _apply_bonus_stock(event, bonus)
                    continue
                data = _apply_bonus_stock(event, bonus)
                render_event_cards(data, "", {}, {}, False)
                self.assertIn(f"Sold:&nbsp;<b>{45 - quota}</b>", markdown.call_args.args[0])
                stats = calculate_event_stats(data)
                self.assertTrue(stats["sales_data_available"])
                self.assertEqual(stats["summary"]["capacity"], 45)
                self.assertEqual(stats["summary"]["remaining"], quota)
                self.assertEqual(stats["summary"]["revenue"], (45 - quota) * 120000)


if __name__ == "__main__":
    unittest.main()
