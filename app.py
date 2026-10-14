from pathlib import Path

import streamlit as st
from starlette.routing import Route

from core.restock_relay import restock

app = st.App(Path(__file__).with_name("dashboard.py"), routes=[Route("/api/restock", restock, methods=["POST"])])
