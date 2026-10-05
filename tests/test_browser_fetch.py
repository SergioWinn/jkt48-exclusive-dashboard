import unittest
from unittest.mock import patch

from core import browser_fetch


class BrowserFallbackTest(unittest.TestCase):
    def tearDown(self):
        browser_fetch.fetch_bonus_json.clear()

    @patch("core.browser_fetch.shutil.which", return_value="installed")
    @patch("core.browser_fetch.subprocess.run", side_effect=OSError)
    def test_failed_browser_attempt_is_cached(self, run, _which):
        url = "https://jkt48.com/api/v1/exclusives/EXTEST/bonus?lang=id"
        self.assertIsNone(browser_fetch.fetch_bonus_json(url, 12))
        self.assertIsNone(browser_fetch.fetch_bonus_json(url, 12))
        run.assert_called_once()
