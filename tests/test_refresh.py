import unittest
from datetime import datetime

from core.refresh import get_detail_refresh_interval, is_event_closed


class DetailRefreshIntervalTest(unittest.TestCase):
    def setUp(self):
        self.event = {
            "sales_period": [
                {
                    "label": "General",
                    "start_date": "2026-08-01T10:00:00",
                    "end_date": "2026-08-01T20:00:00",
                }
            ]
        }

    def test_active_sales_refresh_every_five_seconds(self):
        interval = get_detail_refresh_interval(
            self.event,
            True,
            datetime(2026, 8, 1, 12, 0, 0),
        )

        self.assertEqual(interval, 5)

    def test_ofc_period_before_general_still_refreshes_every_five_seconds(self):
        interval = get_detail_refresh_interval(
            self.event,
            True,
            datetime(2026, 8, 1, 9, 0, 0),
        )

        self.assertEqual(interval, 5)

    def test_closed_sales_refresh_every_sixty_seconds(self):
        interval = get_detail_refresh_interval(
            self.event,
            True,
            datetime(2026, 8, 1, 21, 0, 0),
        )

        self.assertEqual(interval, 60)
        self.assertTrue(is_event_closed(self.event, datetime(2026, 8, 1, 21, 0, 0)))

    def test_waiting_room_recovery_refresh_every_fifteen_seconds(self):
        interval = get_detail_refresh_interval(
            self.event,
            False,
            datetime(2026, 8, 1, 12, 0, 0),
        )

        self.assertEqual(interval, 15)

    def test_utc_valid_date_to_is_converted_to_wib(self):
        event = {"valid_date_to": "2026-08-01T10:00:00.000Z"}

        before_close = get_detail_refresh_interval(
            event,
            True,
            datetime(2026, 8, 1, 16, 59, 0),
        )
        after_close = get_detail_refresh_interval(
            event,
            True,
            datetime(2026, 8, 1, 17, 0, 0),
        )

        self.assertEqual(before_close, 5)
        self.assertEqual(after_close, 60)


if __name__ == "__main__":
    unittest.main()
