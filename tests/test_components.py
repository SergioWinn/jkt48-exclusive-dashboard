import unittest
import re
import shutil
import subprocess
from unittest.mock import patch

from core.api import _apply_bonus_stock
from core.stats import calculate_event_stats
from ui.components import install_motion_observer, render_event_cards, render_share_controls
from ui.styles import GLOBAL_CSS


class EventCardsTest(unittest.TestCase):
    @patch("ui.components.st.iframe")
    def test_cards_are_not_hidden_until_scrolled_into_view(self, iframe):
        install_motion_observer()
        script = iframe.call_args.args[0]
        self.assertNotIn("IntersectionObserver", script)
        self.assertNotIn('classList.add("ex48-reveal")', script)
        self.assertNotIn(".ex48-reveal", GLOBAL_CSS)
        self.assertIn("values.get(key) !== value", script)
        render_share_controls("test")
        capture = iframe.call_args.args[0]
        self.assertIn('image.loading = "eager"', capture)
        self.assertIn("await waitForCaptureAssets(state.target)", capture)

    @unittest.skipUnless(shutil.which("node"), "Node is needed to check share JavaScript")
    @patch("ui.components.st.iframe")
    def test_share_snapshot_survives_live_cards_disappearing(self, iframe):
        render_share_controls("test")
        html = iframe.call_args.args[0]
        functions = "\n".join(re.search(
            rf"        function {name}\([^)]*\).*?\n        }}", html, re.S
        ).group(0) for name in ("openPicker", "refreshData", "selectedCardCount", "buildShareParts"))
        script = r'''
const assert = require('node:assert/strict');
let shareSnapshot = null, selectionInitialized = false;
let shareParts = [], activePart = -1;
let selectedSessions = new Set(), selectedMembers = new Set(), sessionItems = [], memberItems = [];
const card = {dataset: {shareSession: 'one', shareSessionLabel: 'Session 1', shareMember: 'Member'}, stock: 7};
let liveCards = [card];
const source = {cloneNode() {
    const cards = structuredClone(liveCards);
    return {querySelectorAll: () => cards};
}};
let liveSource = source;
const window = {parent: {document: {getElementById: () => liveSource}}};
const dialog = {open: false, showModal() {this.open = true;}, querySelector() {return null;}};
const requestAnimationFrame = callback => callback();
const normalizeCaptureColors = () => ({background: 'black', tokens: {}});
const getCaptureBackground = () => 'black';
const setFeedback = () => {};
const renderPicker = () => {};
const loadSaved = (_, available) => new Set(available);
''' + functions + r'''
openPicker();
assert.equal(selectedCardCount(), 1);
card.stock = 0;
liveCards = [];
liveSource = null;
refreshData();
assert.equal(selectedCardCount(), 1);
assert.equal(shareSnapshot.source.querySelectorAll()[0].stock, 7);
assert.deepEqual(sessionItems, [{value: 'one', label: 'Session 1'}]);
dialog.open = false;
liveSource = source;
liveCards = [{...card, stock: 2}];
openPicker();
assert.equal(shareSnapshot.source.querySelectorAll()[0].stock, 2);
for (const [count, sizes] of [[4, [4]], [5, [3, 2]], [6, [3, 3]], [7, [4, 3]], [8, [4, 4]], [9, [3, 3, 3]], [10, [4, 3, 3]]]) {
    const items = Array.from({length: count}, (_, i) => ({value: String(i), label: `18/09/2026 - Session ${i + 1}`}));
    const parts = buildShareParts(items);
    assert.deepEqual(parts.map(p => p.values.length), sizes);
    assert.deepEqual(parts.flatMap(p => p.values), items.map(i => i.value));
}
const days = buildShareParts([{value: 'a', label: '18/09/2026 - Session 1'}, {value: 'b', label: '19/09/2026 - Session 1'}]);
assert.deepEqual(days.map(p => p.values), [['a'], ['b']]);
'''
        subprocess.run([shutil.which("node"), "-e", script], check=True, capture_output=True, text=True)
        capture = html.split("function siapkanTarget()", 1)[1].split("function setCopyState", 1)[0]
        self.assertIn("const source = shareSnapshot?.source", capture)
        self.assertNotIn('getElementById("laporan-container")', capture)

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
                    self.assertIn("&mdash;&nbsp;LEFT", html)
                else:
                    self.assertIn(f"Status:&nbsp;<b>{'AVAILABLE' if quota else 'SOLD OUT'}</b>", html)
                    self.assertNotIn("Remaining:&nbsp;", html)
                    self.assertIn(f"{quota}&nbsp;LEFT", html)
                    self.assertNotIn("SOLD&nbsp;OUT", html)
                closed_event = {**data, "valid_date_to": "2000-01-01T00:00:00"}
                render_event_cards(closed_event, "", {}, {}, False)
                closed_html = markdown.call_args.args[0]
                if quota is None:
                    self.assertIn('<div class="c-prog-text">CLOSED</div>', closed_html)
                else:
                    self.assertIn(f"{quota}&nbsp;LEFT&nbsp;AT&nbsp;CLOSE", closed_html)
                self.assertNotIn("purchase-card", closed_html)

    @patch("ui.components.st.markdown")
    def test_video_call_shows_remaining_without_estimating_sales(self, markdown):
        session = {"date": "2099-09-13", "start_time": "11:45:00", "label": "Sesi 1"}
        event = {"code": "EX5A08", "category": "DIGITAL_PHOTOBOOK", "default_price": 120000,
                 "session": [{**session, "session_detail": [
                     {"label": "Jalur 1", "jkt48_member_name": "Jacqueline Immanuela"},
                 ]}]}
        for quota in (0, 9, 45, 46):
            with self.subTest(quota=quota):
                bonus = [{**session, "session_members": [
                    {"label": "Jalur 1", "member_name": "Jacqueline Immanuela", "available_quota": quota},
                ]}]
                data = _apply_bonus_stock(event, bonus)
                render_event_cards(data, "", {}, {}, False)
                html = markdown.call_args.args[0]
                self.assertIn(f"Status:&nbsp;<b>{'AVAILABLE' if quota else 'SOLD OUT'}</b>", html)
                self.assertIn(f"{quota}&nbsp;LEFT", html)
                self.assertNotIn("Remaining:&nbsp;", html)
                self.assertNotIn("Sold:&nbsp;", html)
                self.assertNotIn("c-prog-fill", html)
                self.assertNotIn("tickets_sold", data["session"][0]["session_detail"][0])
                stats = calculate_event_stats(data)
                self.assertFalse(stats["sales_data_available"])
                self.assertEqual(stats["summary"]["remaining"], quota)
                render_event_cards(data, "", {}, {}, False, is_event_closed=True)
                closed_html = markdown.call_args.args[0]
                self.assertIn(f"{quota}&nbsp;LEFT&nbsp;AT&nbsp;CLOSE", closed_html)
                self.assertNotIn("purchase-card", closed_html)


if __name__ == "__main__":
    unittest.main()
