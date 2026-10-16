import unittest
import re
import shutil
import subprocess
from datetime import datetime, timezone
from unittest.mock import patch

from core.api import _apply_bonus_stock
from core.stats import calculate_event_stats
from ui.components import install_motion_observer, render_event_cards, render_share_controls, render_stats_controls
from ui.styles import GLOBAL_CSS


class EventCardsTest(unittest.TestCase):
    @unittest.skipUnless(shutil.which("node"), "Node is needed to check statistics feedback")
    @patch("ui.components.st.iframe")
    def test_statistics_copy_feedback_covers_all_states(self, iframe):
        render_stats_controls(can_share=True)
        html = iframe.call_args.args[0]
        function = re.search(r'        function setStatsShareState\(.*?\n        }', html, re.S).group(0)
        script = r'''
const assert = require('node:assert/strict');
const feedback = {};
const dialog = {querySelector: () => feedback};
const shareButton = {dataset: {}, setAttribute() {}};
''' + function + r'''
setStatsShareState('loading');
assert.equal(shareButton.disabled, true);
assert.equal(feedback.hidden, false);
assert.match(feedback.textContent, /Preparing/);
setStatsShareState('success');
assert.equal(shareButton.disabled, false);
assert.equal(feedback.textContent, 'Copied to clipboard.');
setStatsShareState('error', 'Allow clipboard access, then try again.');
assert.equal(feedback.textContent, 'Allow clipboard access, then try again.');
setStatsShareState('error');
assert.match(feedback.textContent, /Try again/);
setStatsShareState('idle');
assert.equal(feedback.hidden, true);
assert.equal(feedback.textContent, '');
'''
        subprocess.run([shutil.which("node"), "-e", script], check=True, capture_output=True, text=True)

    @patch("ui.components.st.markdown")
    def test_date_defaults_and_existing_selections(self, markdown):
        cases = [
            ([14, 15, 17], "", "15/10/2026 (Today)"),
            ([14, 17, 18], "", "17/10/2026"),
            ([12, 14], "", "14/10/2026"),
            ([14, 15, 17], "14/10/2026", "14/10/2026"),
            ([14, 15, 17], "15/10/2026 (Tomorrow)", "15/10/2026 (Today)"),
            ([14, 15, 17], "12/10/2026", "15/10/2026 (Today)"),
        ]
        for days, previous, expected in cases:
            with self.subTest(days=days, previous=previous):
                state = {"filter_date_EXDATES": previous} if previous else {}
                event = {"code": "EXDATES", "session": [
                    {"date": f"2026-10-{day}", "label": "Session 1", "start_time": "12:00:00",
                     "session_detail": [{"jkt48_member_name": "Member", "available_quota": 1}]}
                    for day in days
                ]}
                with patch("ui.components.datetime", wraps=datetime) as clock, \
                     patch("ui.components.st.session_state", state), \
                     patch("ui.components.st.radio", side_effect=lambda *args, **kwargs: state[kwargs["key"]]):
                    clock.now.return_value = datetime(2026, 10, 15, 5, tzinfo=timezone.utc)
                    render_event_cards(event, "", {}, {}, False)
                self.assertEqual(state["filter_date_EXDATES"], expected)

    @unittest.skipUnless(shutil.which("node"), "Node is needed to check statistics keyboard behavior")
    @patch("ui.components.st.iframe")
    def test_stats_tabs_preserve_focus_and_support_keyboard(self, iframe):
        render_stats_controls()
        html = iframe.call_args.args[0]
        render = html.split("        function render() {", 1)[1].split(
            '        generationFilter.addEventListener("change"', 1
        )[0]
        script = r'''
const assert = require('node:assert/strict');
let focused = null, activeTab = '', selectedGeneration = 'All', selectedTeam = 'All';
const rowsByTab = () => ({Member: [], Generation: [], Team: []});
let payload = {rowsByTab: rowsByTab(), title: 'Statistics'};
const getStatsPayload = () => payload;
const attrs = {};
const body = {setAttribute(k,v) {attrs[k]=v;}, removeAttribute(k) {delete attrs[k];}, querySelectorAll() {return [];}};
const dialog = {querySelector() {return {};}};
const filters = {classList: {toggle() {}}};
const generationFilter = {}, teamFilter = {};
const fillSelect = () => {}, filteredRows = () => [], renderRows = () => '', renderGroupRows = () => '';
const tabList = {children: [], replaceChildren(...buttons) {this.children=buttons;}, addEventListener(_, fn) {this.keydown=fn;}};
const window = {parent: {getComputedStyle: () => ({direction: 'ltr'}), document: {createElement() {
    return {attributes: {}, setAttribute(k,v) {this.attributes[k]=v;}, addEventListener(_, fn) {this.click=fn;}, focus() {focused=this;}};
}}}};
''' + "function render() {" + render + r'''
render();
const buttons = [...tabList.children];
buttons[1].focus(); buttons[1].click();
assert.equal(focused, buttons[1]);
assert.equal(tabList.children[1], buttons[1]);
assert.equal(buttons[1].attributes['aria-selected'], 'true');
assert.equal(buttons[1].tabIndex, 0);
assert.equal(buttons[0].tabIndex, -1);
assert.equal(attrs['aria-labelledby'], buttons[1].id);
assert.equal(buttons[1].attributes['aria-controls'], 'event-stats-panel');
function key(key) {tabList.keydown({target: focused, key, preventDefault() {}});}
key('ArrowRight'); assert.equal(focused, buttons[2]);
key('ArrowRight'); assert.equal(focused, buttons[0]);
key('ArrowLeft'); assert.equal(focused, buttons[2]);
key('Home'); assert.equal(focused, buttons[0]);
key('End'); assert.equal(focused, buttons[2]);
window.parent.getComputedStyle = () => ({direction: 'rtl'});
key('ArrowRight'); assert.equal(focused, buttons[1]);
payload = {rowsByTab: {}, title: 'Empty'}; render();
assert.equal(tabList.children.length, 0);
assert.equal(attrs['aria-labelledby'], undefined);
'''
        subprocess.run([shutil.which("node"), "-e", script], check=True, capture_output=True, text=True)

    @patch("ui.components.st.markdown")
    def test_available_only_preserves_session_groups_and_matching_members(self, markdown):
        members = lambda available: [
            {"label": f"Jalur {index}", "jkt48_member_name": f"Member {index}", "available_quota": int(index <= available)}
            for index in range(1, 5)
        ]
        event = {"code": "EXCOMPACT", "category": "TWO_SHOT", "session": [
            {"date": "2099-09-13", "start_time": "11:00:00", "label": "Sesi 1", "session_detail": members(1)},
            {"date": "2099-09-13", "start_time": "12:00:00", "label": "Sesi 2", "session_detail": members(2)},
        ]}

        render_event_cards(event, "", {}, {}, True)

        html = markdown.call_args.args[0]
        self.assertIn('id="laporan-container" class="available-only-layout"', html)
        self.assertEqual(html.count('class="session-group"'), 2)
        self.assertEqual(html.count('class="ldp-card purchase-card'), 3)
        self.assertNotIn('class="ldp-card sold', html)

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
        self.assertIn('const group = grid.closest(".session-group");', capture)

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
                self.assertIn("Status:&nbsp;<b>CLOSED</b>", closed_html)
                self.assertNotIn("Status:&nbsp;<b>AVAILABLE</b>", closed_html)
                self.assertIn('<div class="c-prog-text">CLOSED</div>', closed_html)
                self.assertNotIn("&nbsp;LEFT", closed_html)
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
                self.assertIn('<div class="c-prog-text">CLOSED</div>', closed_html)
                self.assertIn("Status:&nbsp;<b>CLOSED</b>", closed_html)
                self.assertNotIn("purchase-card", closed_html)

    @patch("ui.components.st.markdown")
    def test_expired_session_is_closed_even_when_stock_remains(self, markdown):
        event = {"code": "EXPAST", "valid_date_to": "2099-01-01T23:00:00", "session": [{
            "date": "2000-01-01", "label": "Session 1", "start_time": "12:00:00",
            "session_detail": [{"jkt48_member_name": "Member", "available_quota": 9}],
        }]}
        render_event_cards(event, "", {}, {}, False)
        html = markdown.call_args.args[0]
        self.assertIn("Status:&nbsp;<b>CLOSED</b>", html)
        self.assertIn('<div class="c-prog-text">CLOSED</div>', html)
        self.assertNotIn("purchase-card", html)

    @patch("ui.components.st.markdown")
    @patch("ui.components.st.info")
    @patch("ui.components.st.warning")
    def test_empty_results_explain_how_to_recover(self, warning, info, markdown):
        event = {"code": "EXEMPTY", "session": [{
            "date": "2099-01-01", "label": "Session 1", "start_time": "12:00:00",
            "session_detail": [{"jkt48_member_name": "Member", "available_quota": 0}],
        }]}
        for query, available_only, recovery in [
            ("nobody", False, "Try another member name"),
            ("member", True, "Turn off Available only"),
            ("", True, "Turn off Available only"),
        ]:
            with self.subTest(query=query, available_only=available_only):
                warning.reset_mock()
                info.reset_mock()
                render_event_cards(event, query, {}, {}, available_only)
                self.assertIn(recovery, warning.call_args.args[0])
                info.assert_not_called()


if __name__ == "__main__":
    unittest.main()
