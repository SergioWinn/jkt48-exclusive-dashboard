import json
import unittest
from unittest.mock import Mock, patch

from core import browser_fetch


class BrowserFallbackTest(unittest.TestCase):
    def tearDown(self):
        browser_fetch.clear_browser_modes()

    @patch("core.browser_fetch.shutil.which", return_value=None)
    def test_missing_browser_returns_empty_payload(self, which):
        self.assertEqual(browser_fetch.fetch_event_json("EXTEST", 12), {})
        which.assert_called_once_with("chromium")

    @patch("core.browser_fetch.subprocess.run")
    @patch("core.browser_fetch.shutil.which", return_value="installed")
    def test_browser_runs_in_isolated_process(self, _which, run):
        run.return_value = Mock(returncode=0, stdout=json.dumps({"detail": {"status": True}, "bonus": None}))

        self.assertEqual(
            browser_fetch.fetch_event_json("EXTEST", 12),
            {"detail": {"status": True}, "bonus": None},
        )
        command = run.call_args.args[0]
        self.assertEqual(command[0], browser_fetch.sys.executable)
        self.assertEqual(command[1], str(browser_fetch.Path(browser_fetch.__file__).resolve()))
        self.assertEqual(command[2:], ["EXTEST", "12"])
