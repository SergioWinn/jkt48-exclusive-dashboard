from pathlib import Path

import streamlit as st
from starlette.routing import Route

from core.restock_relay import restock

base_path = st.get_option("server.baseUrlPath").strip("/")
restock_path = f"/{base_path}/api/restock" if base_path else "/api/restock"
print(f"[restock-relay] endpoint={restock_path}", flush=True)
# Hosting proxies may strip the base path before forwarding custom routes.
paths = [restock_path] if not base_path else [restock_path, "/api/restock"]
app = st.App(Path(__file__).with_name("dashboard.py"), routes=[Route(path, restock, methods=["POST"]) for path in paths])
