import asyncio
import json
import runpy
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from starlette.requests import Request

from core.restock_relay import LiveApiUnavailable, collect_stock, restock


class RestockRelayTest(unittest.TestCase):
    def setUp(self):
        self.token = patch.dict("os.environ", {"RESTOCK_RELAY_TOKEN": "test-secret"})
        self.token.start()
        self.addCleanup(self.token.stop)
        self.params = {"relayToken": "test-secret", "categories": ["PHOTOCARD"], "trackedEventCodes": []}

    def post(self, headers=None, json=None, content=None):
        import json as codec
        body = content.encode() if content is not None else codec.dumps(json).encode()
        scope = {"type": "http", "method": "POST", "path": "/api/restock",
                 "headers": [(key.lower().encode(), value.encode()) for key, value in (headers or {}).items()]}
        async def receive():
            return {"type": "http.request", "body": body, "more_body": False}
        return asyncio.run(restock(Request(scope, receive)))

    def test_authorization_and_validation_happen_before_fetch(self):
        with patch("core.restock_relay.collect_stock") as collect:
            for token in ("", "wrong", 123):
                self.assertEqual(self.post(json={**self.params, "relayToken": token}).status_code, 401)
            self.assertEqual(self.post(json={**self.params, "categories": ["UNKNOWN"]}).status_code, 400)
            self.assertEqual(self.post(json={**self.params, "trackedEventCodes": ["../../test"]}).status_code, 400)
            self.assertEqual(self.post(content="x" * 4097).status_code, 413)
            collect.assert_not_called()

    def test_entry_point_registers_the_hosting_prefix(self):
        for prefix, expected in (("", "/api/restock"), ("/~/+", "/~/+/api/restock")):
            with patch("streamlit.get_option", return_value=prefix), patch("streamlit.App") as app:
                runpy.run_path(str(Path(__file__).parents[1] / "app.py"))
                paths = app.call_args.kwargs["middleware"][0].kwargs["paths"]
                self.assertEqual(paths[0], expected)
                self.assertIn("/~/+/api/restock", paths)

    def test_route_trace_logs_paths_without_headers_or_query_secrets(self):
        with patch("streamlit.App"), patch("builtins.print") as log:
            module = runpy.run_path(str(Path(__file__).parents[1] / "app.py"))
            log.reset_mock()
            async def downstream(scope, receive, send):
                pass
            trace = module["RestockRelayMiddleware"](downstream, ["/~/+/api/restock"])
            scope = {"type": "http", "method": "POST", "path": "/~/+/api/restock", "root_path": "",
                     "headers": [(b"authorization", b"Bearer secret")], "query_string": b"token=secret"}
            async def receive():
                return {"type": "http.request", "body": b"{}", "more_body": False}
            sent = []
            async def send(message):
                sent.append(message)
            asyncio.run(trace(scope, receive, send))
            self.assertEqual(log.call_args_list[0].args[0], "[restock-relay] request=POST path=/~/+/api/restock root_path=")
            self.assertEqual(sent[0]["status"], 401)
            scope["method"] = "GET"
            sent.clear()
            asyncio.run(trace(scope, receive, send))
            self.assertEqual(sent[0]["status"], 405)
            scope["method"] = "POST"
            sent.clear()
            async def broken_handler(request):
                raise RuntimeError("hidden secret")
            trace.__call__.__globals__["restock"] = broken_handler
            asyncio.run(trace(scope, receive, send))
            self.assertEqual(sent[0]["status"], 503)
            self.assertNotIn("hidden secret", str(log.call_args_list))

    def test_endpoint_returns_live_payload_and_refuses_cached_success_on_failure(self):
        payload = {"results": []}
        with patch("core.restock_relay.collect_stock", return_value=payload):
            response = self.post(json=self.params)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(json.loads(response.body), payload)
            self.assertEqual(response.headers["cache-control"], "no-store")
        with patch("core.restock_relay.collect_stock", side_effect=RuntimeError("403")), patch("core.restock_relay.logging.exception"):
            self.assertEqual(self.post(json=self.params).status_code, 502)

    def test_collects_only_recent_or_tracked_events_with_live_bonus(self):
        recent = {"code": "EXNEW", "category": "PHOTOCARD", "title": "New", "valid_date_from": datetime.now(timezone.utc).isoformat()}
        old = {**recent, "code": "EXOLD", "valid_date_from": "2025-01-01T00:00:00Z"}
        bonus = {"status": True, "data": [{"session_members": [{"member_name": "Member", "available_quota": 3}]}]}
        with patch("core.restock_relay.get_active_exclusive_events", return_value=[recent, old]), patch("core.restock_relay._get_json", return_value=bonus):
            payload = collect_stock(set(), {"PHOTOCARD"})
            self.assertEqual([item["event"]["code"] for item in payload["results"]], ["EXNEW"])
            self.assertEqual(payload["results"][0]["bonus"], bonus)
            payload = collect_stock({"EXOLD"}, {"PHOTOCARD"})
            self.assertEqual(len(payload["results"]), 2)
        with patch("core.restock_relay.get_active_exclusive_events", return_value=[recent]), patch("core.restock_relay._get_json", side_effect=LiveApiUnavailable("Cloudflare challenge")), patch("core.restock_relay.fetch_event_json", return_value={}):
            with self.assertRaises(LiveApiUnavailable):
                collect_stock(set(), {"PHOTOCARD"})
