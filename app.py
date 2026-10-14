from pathlib import Path

import streamlit as st
from starlette.middleware import Middleware
from starlette.routing import Route

from core.restock_relay import restock


class RelayRouteTrace:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http" and "restock" in scope.get("path", ""):
            print(f"[restock-relay] request={scope['method']} path={scope['path']} root_path={scope.get('root_path', '')}", flush=True)
        await self.app(scope, receive, send)

base_path = st.get_option("server.baseUrlPath").strip("/")
restock_path = f"/{base_path}/api/restock" if base_path else "/api/restock"
# Community Cloud forwards some requests with its runtime prefix intact.
paths = list(dict.fromkeys([restock_path, "/api/restock", "/~/+/api/restock"]))
print(f"[restock-relay] endpoints={','.join(paths)}", flush=True)
app = st.App(Path(__file__).with_name("dashboard.py"), routes=[Route(path, restock, methods=["POST"]) for path in paths], middleware=[Middleware(RelayRouteTrace)])
