from pathlib import Path

import streamlit as st
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from core.restock_relay import restock


class RestockRelayMiddleware:
    def __init__(self, app, paths):
        self.app = app
        self.paths = set(paths)

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http" and scope.get("path") in self.paths:
            print(f"[restock-relay] request={scope['method']} path={scope['path']} root_path={scope.get('root_path', '')}", flush=True)
            response = await restock(Request(scope, receive)) if scope["method"] == "POST" else JSONResponse({"error": "Method not allowed"}, status_code=405, headers={"Allow": "POST"})
            await response(scope, receive, send)
            return
        await self.app(scope, receive, send)

base_path = st.get_option("server.baseUrlPath").strip("/")
restock_path = f"/{base_path}/api/restock" if base_path else "/api/restock"
# Community Cloud forwards some requests with its runtime prefix intact.
paths = list(dict.fromkeys([restock_path, "/api/restock", "/~/+/api/restock"]))
print(f"[restock-relay] endpoints={','.join(paths)}", flush=True)
app = st.App(Path(__file__).with_name("dashboard.py"), middleware=[Middleware(RestockRelayMiddleware, paths=paths)])
