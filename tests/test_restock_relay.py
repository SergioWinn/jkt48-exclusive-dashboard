import asyncio
import json
import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import patch

from starlette.requests import Request

from core.restock_relay import collect_stock, restock


class RestockRelayTest(unittest.TestCase):
    def setUp(self):
        self.token = patch.dict("os.environ", {"RESTOCK_RELAY_TOKEN": "test-secret"})
        self.token.start()
        self.addCleanup(self.token.stop)
        self.headers = {"Authorization": "Bearer test-secret"}
        self.params = {"categories": ["PHOTOCARD"], "trackedEventCodes": []}

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
            self.assertEqual(self.post(json=self.params).status_code, 401)
            self.assertEqual(self.post(headers=self.headers, json={"categories": ["UNKNOWN"]}).status_code, 400)
            self.assertEqual(self.post(headers=self.headers, json={**self.params, "trackedEventCodes": ["../../test"]}).status_code, 400)
            self.assertEqual(self.post(headers=self.headers, content="x" * 4097).status_code, 413)
            collect.assert_not_called()

    def test_endpoint_returns_live_payload_and_refuses_cached_success_on_failure(self):
        payload = {"results": []}
        with patch("core.restock_relay.collect_stock", return_value=payload):
            response = self.post(headers=self.headers, json=self.params)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(json.loads(response.body), payload)
            self.assertEqual(response.headers["cache-control"], "no-store")
        with patch("core.restock_relay.collect_stock", side_effect=RuntimeError("403")), patch("core.restock_relay.logging.exception"):
            self.assertEqual(self.post(headers=self.headers, json=self.params).status_code, 502)

    def test_collects_only_recent_or_tracked_events_with_live_bonus(self):
        recent = {"code": "EXNEW", "category": "PHOTOCARD", "title": "New", "valid_date_from": datetime.now(timezone.utc).isoformat()}
        old = {**recent, "code": "EXOLD", "valid_date_from": "2025-01-01T00:00:00Z"}
        bonus = {"status": True, "data": [{"session_members": [{"member_name": "Member", "available_quota": 3}]}]}
        def get(url, **kwargs):
            data = {"status": True, "data": {"data": [recent, old]}} if url.endswith("exclusives?lang=id") else bonus
            return SimpleNamespace(status_code=200, headers={"content-type": "application/json"}, json=lambda: data)
        with patch("core.restock_relay.requests.Session") as session:
            session.return_value.__enter__.return_value.get.side_effect = get
            payload = collect_stock(set(), {"PHOTOCARD"})
            self.assertEqual([item["event"]["code"] for item in payload["results"]], ["EXNEW"])
            self.assertEqual(payload["results"][0]["bonus"], bonus)
            payload = collect_stock({"EXOLD"}, {"PHOTOCARD"})
            self.assertEqual(len(payload["results"]), 2)
