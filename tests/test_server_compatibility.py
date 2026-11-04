import gzip
import unittest

from streamlit.web.server.starlette.starlette_gzip_middleware import MediaAwareGZipMiddleware


class StaticResponseCompatibilityTest(unittest.IsolatedAsyncioTestCase):
    async def test_precompressed_asset_sends_headers_before_body(self):
        body = gzip.compress(b"window.dashboardLoaded = true;")

        async def asset(scope, receive, send):
            await send({
                "type": "http.response.start", "status": 200,
                "headers": [(b"content-type", b"application/javascript"),
                            (b"content-encoding", b"gzip")],
            })
            await send({"type": "http.response.body", "body": body})

        async def receive():
            return {"type": "http.request", "body": b""}

        for encoding in (b"gzip", b"identity"):
            with self.subTest(encoding=encoding):
                messages = []

                async def send(message):
                    messages.append(message)

                await MediaAwareGZipMiddleware(asset)(
                    {"type": "http", "headers": [(b"accept-encoding", encoding)]},
                    receive, send,
                )
                self.assertEqual([message["type"] for message in messages],
                                 ["http.response.start", "http.response.body"])
                self.assertEqual(messages[-1]["body"], body)
