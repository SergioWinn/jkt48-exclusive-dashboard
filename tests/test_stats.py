import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from core.stats import calculate_event_stats, format_revenue_pair, format_rupiah, table_rows
from core.stats import load_member_metadata


class EventStatsTest(unittest.TestCase):
    def test_member_metadata_handles_utf8_bom(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "members.csv"
            path.write_text("full_name,nickname,status,generasi\nHeidi Suyangga,Heidi,TRAINEE,14\n", encoding="utf-8-sig")

            metadata = load_member_metadata(path)

        self.assertEqual(metadata["heidi suyangga"]["generation"], "14")
        self.assertEqual(metadata["heidi suyangga"]["status"], "TRAINEE")

    def test_event_stats_include_revenue_and_grouping(self):
        event = {
            "default_price": 120000,
            "session": [
                {
                    "session_detail": [
                        {"jkt48_member_name": "Freya Jayawardana", "tickets_sold": 8, "available_quota": 2},
                        {"jkt48_member_name": "Alya Amanda", "tickets_sold": 5, "available_quota": 5},
                    ]
                },
                {
                    "session_detail": [
                        {"jkt48_member_name": "Freya Jayawardana", "tickets_sold": 10, "available_quota": 0},
                    ]
                },
            ],
        }
        metadata = {
            "freya jayawardana": {"generation": "7", "status": "DREAM"},
            "alya amanda": {"generation": "11", "status": "LOVE"},
        }

        stats = calculate_event_stats(event, metadata)

        self.assertEqual(stats["summary"]["sold"], 23)
        self.assertTrue(stats["sales_data_available"])
        self.assertEqual(stats["summary"]["remaining"], 7)
        self.assertEqual(stats["summary"]["revenue"], 2760000)
        self.assertEqual(stats["summary"]["potential_revenue"], 3600000)
        self.assertAlmostEqual(stats["summary"]["sold_rate"], 76.6666, places=3)
        self.assertEqual(stats["members"][0]["name"], "Freya Jayawardana")
        self.assertEqual(stats["members"][0]["rank"], 1)
        self.assertEqual(stats["generations"][0]["name"], "7")
        self.assertEqual(stats["generations"][0]["members"], ["Freya Jayawardana"])
        self.assertEqual(stats["teams"][0]["name"], "DREAM")

    def test_equal_sold_rate_shares_the_same_rank(self):
        event = {
            "default_price": 100000,
            "session": [
                {
                    "session_detail": [
                        {"jkt48_member_name": "A", "tickets_sold": 5, "available_quota": 0},
                        {"jkt48_member_name": "B", "tickets_sold": 5, "available_quota": 2},
                        {"jkt48_member_name": "C", "tickets_sold": 3, "available_quota": 0},
                    ]
                }
            ],
        }

        rows = table_rows(calculate_event_stats(event)["members"])

        self.assertEqual([row["Name"] for row in rows], ["A", "C", "B"])
        self.assertEqual([row["Rank"] for row in rows], [1, 1, 3])

    def test_missing_metadata_is_grouped_as_unknown(self):
        event = {
            "default_price": 100000,
            "session": [{"session_detail": [{"jkt48_member_name": "New Member", "tickets_sold": 0, "available_quota": 0}]}],
        }

        stats = calculate_event_stats(event)

        self.assertEqual(stats["summary"]["sold_rate"], 0.0)
        self.assertEqual(stats["generations"][0]["name"], "Unknown")
        self.assertEqual(stats["teams"][0]["name"], "Unknown")

    def test_capped_video_call_stock_hides_exact_sales_statistics(self):
        event = {"category": "DIGITAL_PHOTOBOOK", "default_price": 100000,
                 "session": [{"session_detail": [
                     {"jkt48_member_name": "A", "tickets_sold": 10, "available_quota": 5},
                 ]}]}
        self.assertFalse(calculate_event_stats(event)["sales_data_available"])
        event["session"][0]["session_detail"][0]["available_quota"] = 4
        self.assertTrue(calculate_event_stats(event)["sales_data_available"])

    def test_capped_meet_greet_stock_does_not_claim_exact_totals(self):
        event = {"category": "PHOTOCARD", "availability_only": True,
                 "session": [{"session_detail": [{"jkt48_member_name": "A", "tickets_sold": 10,
                                                   "available_quota": 20}]}]}
        self.assertFalse(calculate_event_stats(event)["sales_data_available"])
        event["session"][0]["session_detail"][0]["available_quota"] = 1
        stats = calculate_event_stats(event)
        self.assertEqual(stats["summary"]["remaining"], 1)
        self.assertTrue(stats["sales_data_available"])

    def test_availability_only_api_does_not_claim_zero_sales(self):
        stats = calculate_event_stats({
            "session": [{"session_detail": [{"jkt48_member_name": "A", "quota_available": False}]}],
        })

        self.assertFalse(stats["sales_data_available"])

    def test_binary_cached_counts_do_not_become_sales_statistics(self):
        event = {"default_price": 200000, "session": [{"session_detail": [
            {"jkt48_member_name": "A", "available_quota": 0, "tickets_sold": 20},
            {"jkt48_member_name": "B", "available_quota": 1, "tickets_sold": 10},
        ]}]}
        stats = calculate_event_stats(event)
        self.assertFalse(stats["sales_data_available"])
        self.assertEqual(stats["summary"]["revenue"], 0)
        self.assertEqual(stats["summary"]["remaining"], 0)

    def test_table_rows_format_money_percentage_and_members(self):
        rows = table_rows([
            {
                "name": "DREAM",
                "rank": 1,
                "sold": 3,
                "remaining": 1,
                "sold_rate": 75.0,
                "revenue": 360000,
                "potential_revenue": 480000,
                "members": ["Freya Jayawardana"],
            }
        ], include_members=True)

        self.assertEqual(rows[0]["Sold %"], "75.0%")
        self.assertEqual(rows[0]["Rank"], 1)
        self.assertEqual(rows[0]["Revenue"], "Rp 360.000\n/ Rp 480.000")
        self.assertEqual(rows[0]["Members"], "Freya Jayawardana")
        self.assertEqual(format_rupiah(1234567), "Rp 1.234.567")
        self.assertEqual(format_revenue_pair(1, 2, separator=" / "), "Rp 1 / Rp 2")


if __name__ == "__main__":
    unittest.main()
