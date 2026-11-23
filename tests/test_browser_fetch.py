import unittest
from unittest.mock import patch

from core import browser_fetch


class BrowserFallbackTest(unittest.TestCase):
    def tearDown(self):
        browser_fetch.clear_browser_modes()
        browser_fetch._get_browser.clear()

    @patch("core.browser_fetch._get_browser", return_value=None)
    def test_missing_browser_returns_empty_payload(self, get_browser):
        self.assertEqual(browser_fetch.fetch_event_json("EXTEST", 12), {})
        get_browser.assert_called_once()
