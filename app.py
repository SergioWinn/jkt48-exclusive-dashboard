# app.py

import streamlit as st
import time
from datetime import datetime, timedelta, timezone
from html import escape
from pathlib import Path

from core.api import (
    build_jkt48_cookie,
    clear_exclusive_detail_cache,
    fetch_exclusive_detail,
    get_active_exclusive_events,
    get_jkt48_cookie,
    get_member_database,
    is_waiting_room_detected,
    set_jkt48_cookie,
)
from core.refresh import get_detail_refresh_interval, get_sales_window
from core.stats import calculate_event_stats, format_rupiah, load_member_metadata, table_rows
from ui.styles import GLOBAL_CSS
from ui.components import render_event_cards, render_share_controls, render_stats_controls, render_stats_payload

try:
    from ui.components import install_motion_observer
except ImportError:
    install_motion_observer = None

CATEGORY_LABELS = {
    "DIGITAL_PHOTOBOOK": "Video Call",
    "TWO_SHOT": "2-Shot",
    "PHOTOCARD": "Meet & Greet",
}

ASSETS_DIR = Path(__file__).parent / "assets"

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="JKT48 GLOBAL EXCLUSIVE",
    layout="wide",
    page_icon=str(ASSETS_DIR / "estrella-ticket.svg"),
)

# --- 2. APPLY CSS ---
st.markdown(GLOBAL_CSS.replace('\n', '').replace('\r', ''), unsafe_allow_html=True)
if install_motion_observer:
    install_motion_observer()

# --- RENDER MAIN HEADER ---
st.html(
    """
    <div class="ldp-header">
        <div class="ldp-wordmark">
            <div class="ldp-brand">
                <span class="ldp-brand-icon" aria-hidden="true">
                    <span class="ldp-brand-half ldp-brand-half-left"></span>
                    <span class="ldp-brand-half ldp-brand-half-right"></span>
                    <span class="ldp-brand-star"></span>
                    <span class="ldp-brand-dot"></span>
                </span>
                <h1 class="ldp-title">GLOBAL EXCLUSIVE MONITOR</h1>
            </div>
            <p class="ldp-subtitle">Choose an event and date, then scan available member slots.</p>
        </div>
        <a href="https://tako.id/Sportagame19Win" target="_blank" rel="noopener noreferrer" class="tako-btn">Support project ↗</a>
    </div>
    """
)

try:
    admin_keys = st.secrets.get("ADMIN_KEYS", [])
except Exception:
    admin_keys = []
if isinstance(admin_keys, str):
    admin_keys = [admin_keys]
access_key = st.query_params.get("akses", "")
is_admin = bool(access_key and access_key in admin_keys)


# Hallmark · pre-emit critique: P5 H5 E4 S5 R5 V4
# component: dialog · genre: modern-minimal · theme: Cobalt · contrast: native Streamlit
@st.dialog("Mitigate Waiting Room", width="medium")
def show_jkt48_cookie_dialog():
    cookie_active = bool(get_jkt48_cookie())
    if cookie_active:
        st.success("Mitigation cookie aktif untuk retry Waiting Room.")
    else:
        st.warning("Waiting Room terdeteksi. Masukkan dua value cookie dari browser yang sudah lolos.")

    st.caption("Salin kolom Value dari browser. Nama cookie akan ditambahkan otomatis.")
    with st.form("jkt48_cookie_form"):
        clearance = st.text_input(
            "cf_clearance value",
            type="password",
            placeholder="rCdyhpzrkj0S…",
            help="Boleh berupa value saja atau cf_clearance=value.",
        )
        waiting_room = st.text_input(
            "Waiting Room value",
            type="password",
            placeholder="ChhYV01zb0ZG…",
            help="Boleh berupa value saja atau __cfwaitingroom_…=value.",
        )
        apply_col, remove_col = st.columns(2)
        with apply_col:
            apply_cookie = st.form_submit_button("Apply cookie", type="primary", use_container_width=True)
        with remove_col:
            remove_cookie = st.form_submit_button(
                "Remove cookie",
                disabled=not cookie_active,
                use_container_width=True,
            )

        if apply_cookie or remove_cookie:
            try:
                cookie = "" if remove_cookie else build_jkt48_cookie(clearance, waiting_room)
            except ValueError as error:
                st.error(str(error))
            else:
                set_jkt48_cookie(cookie)
                get_member_database.clear()
                get_active_exclusive_events.clear()
                clear_exclusive_detail_cache()
                st.rerun()


@st.fragment(run_every=5)
def live_dashboard_fragment(
    selected_event,
    search_query,
    nickname_map,
    photo_map,
    member_metadata,
    available_only,
    current_event_codes,
):
    refreshed_events = get_active_exclusive_events()
    refreshed_codes = {event.get("code") for event in refreshed_events if event.get("code")}
    if refreshed_codes.difference(current_event_codes):
        st.rerun()

    event_code = selected_event.get("code")
    event_state_key = f"event_data_{event_code}"
    attempt_state_key = f"event_fetch_attempt_{event_code}"
    event_data = st.session_state.get(event_state_key) or selected_event
    wr_info = st.session_state.get(f"wr_status_{event_code}", {"is_live": True, "time": ""})
    now_wib = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=7)
    refresh_interval = get_detail_refresh_interval(event_data, wr_info.get("is_live", True), now_wib)
    last_attempt = st.session_state.get(attempt_state_key, 0.0)

    if event_code and (
        event_state_key not in st.session_state
        or time.monotonic() - last_attempt >= refresh_interval
    ):
        st.session_state[attempt_state_key] = time.monotonic()
        fetched_event_data = fetch_exclusive_detail(event_code)
        if fetched_event_data:
            st.session_state[event_state_key] = fetched_event_data
            event_data = fetched_event_data

    wr_info = st.session_state.get(f"wr_status_{event_code}", {"is_live": True, "time": ""})
    now_wib = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=7)
    refresh_interval = get_detail_refresh_interval(event_data, wr_info.get("is_live", True), now_wib)
    has_event_detail = isinstance(event_data.get("session"), list)

    if not has_event_detail:
        source_class = "is-unavailable"
        source_label = "LIST ONLY"
        source_detail = "Session details unavailable"
        sync_label = f"Retrying every {refresh_interval}s"
    elif wr_info.get("is_live"):
        source_class = "is-live"
        source_label = "LIVE DATA"
        source_detail = f"{refresh_interval}s poll interval"
        sync_label = wr_info.get("time") or "Waiting for first sync"
    else:
        source_class = "is-cached"
        source_label = "CACHED DATA"
        source_detail = f"Retrying every {refresh_interval}s"
        sync_label = wr_info.get("time") or "Unknown snapshot time"
    event_title = escape(str(event_data.get("title", "Event")))
    raw_category = str(event_data.get("category", "-"))
    event_category = escape(CATEGORY_LABELS.get(raw_category, raw_category.replace("_", " ")))
    event_price = int(event_data.get("default_price") or 0)
    st.markdown(
        f"""
        <section class="event-index-head">
            <div>
                <div class="event-meta">{event_category} · IDR {event_price:,}</div>
                <h2>{event_title}</h2>
            </div>
            <div class="source-readout {source_class}">
                <strong>{source_label}</strong>
                <span>{source_detail}</span>
                <small>{escape(str(sync_label))}</small>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    _, close_date = get_sales_window(event_data)
    is_event_closed = bool(close_date and now_wib >= close_date)

    if has_event_detail and not wr_info.get("is_live"):
        st.warning(
            f"Live API unavailable ({wr_info.get('reason', 'Waiting Room / upstream down')}). "
            f"Showing last known good data ({wr_info.get('time')}). "
            f"Retrying every {refresh_interval}s."
        )
    elif not has_event_detail and not wr_info.get("is_live"):
        st.warning(
            f"Event sessions are unavailable ({wr_info.get('reason', 'Waiting Room / upstream down')}). "
            f"No cached session data exists for this event yet. Retrying every {refresh_interval}s."
        )
    elif not has_event_detail:
        st.warning(
            f"Session and ticket details are unavailable. Showing event list information only; "
            f"retrying every {refresh_interval}s."
        )

    if is_admin and is_waiting_room_detected():
        if st.button("Mitigate Waiting Room", icon=":material/key:", key=f"wr_cookie_{event_code}"):
            show_jkt48_cookie_dialog()

    if not has_event_detail:
        return

    event_stats = calculate_event_stats(event_data, member_metadata)
    summary = event_stats["summary"]
    sales_data_available = event_stats["sales_data_available"]
    st.session_state[f"sales_stats_available_{event_code}"] = sales_data_available

    if sales_data_available:
        st.markdown(
            f"""
            <div class="metrics-scope">Entire event totals</div>
            <div class="summary-stat-grid">
                <div class="summary-stat">
                    <span class="summary-stat-label">Total Tickets</span>
                    <strong>{summary['capacity']:,}</strong>
                </div>
                <div class="summary-stat">
                    <span class="summary-stat-label">Sold</span>
                    <strong>{summary['sold']:,}</strong>
                </div>
                <div class="summary-stat">
                    <span class="summary-stat-label">Remaining</span>
                    <strong>{summary['remaining']:,}</strong>
                </div>
                <div class="summary-stat summary-stat-rate">
                    <span class="summary-stat-label">Sold Rate</span>
                    <strong>{summary['sold_rate']:.1f}%</strong>
                </div>
                <div class="summary-stat summary-stat-revenue">
                    <span class="summary-stat-label">Revenue Capture</span>
                    <strong>{format_rupiah(summary['revenue'])}</strong>
                    <small>/ {format_rupiah(summary['potential_revenue'])} potential</small>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.info("JKT48 saat ini hanya mengirim status AVAILABLE / SOLD OUT. Jumlah Sold tidak tersedia dari API.")

    render_event_cards(event_data, search_query, nickname_map, photo_map, available_only, is_event_closed)
    render_stats_payload(
        {
            "Member": table_rows(event_stats["members"]),
            "Generation": table_rows(event_stats["generations"], include_members=True),
            "Team": table_rows(event_stats["teams"], include_members=True),
        } if sales_data_available else {},
        f"{event_data.get('title', 'Event')} statistics",
        photo_map,
    )


nickname_map, photo_map = get_member_database()
member_metadata = load_member_metadata()
for member in member_metadata.values():
    full_name = member["full_name"].strip().lower()
    nickname = member["nickname"].strip().lower()
    if nickname and full_name:
        nickname_map.setdefault(nickname, full_name)
active_events = get_active_exclusive_events()

categories_dict = {}
for ev in active_events:
    cat = ev.get("category", "")
    title = ev.get("title", "Unknown Event")
    raw_open_date = ev.get("valid_date_from", "")
    open_date_str = ""
    if raw_open_date:
        try:
            dt_wib = datetime.strptime(raw_open_date.split(".")[0].replace("Z", ""), "%Y-%m-%dT%H:%M:%S") + timedelta(hours=7)
            open_date_str = f"[{dt_wib.strftime('%d/%m/%Y')}] "
        except Exception:
            pass

    dropdown_label = f"{open_date_str}{title}"
    ev_info = {"label": dropdown_label, "data": ev}

    cat_label = CATEGORY_LABELS.get(cat, "Others")

    categories_dict.setdefault(cat_label, []).append(ev_info)

for events in categories_dict.values():
    events.sort(
        key=lambda event: event["data"].get("valid_date_from", ""),
        reverse=True,
    )

category_filters = dict(sorted(
    categories_dict.items(),
    key=lambda item: max(event["data"].get("valid_date_from", "") for event in item[1]),
    reverse=True,
))
available_categories = category_filters

if available_categories:
    with st.container(border=False, key="event_filters"):
        col_cat, col_ev, col_search, col_toggle = st.columns(4, vertical_alignment="bottom")

        with col_cat:
            selected_cat = st.selectbox(
                "Category",
                list(available_categories.keys()),
            )

        with col_ev:
            events_in_cat = available_categories[selected_cat]
            events_by_code = {event["data"]["code"]: event for event in events_in_cat}
            selected_event_code = st.selectbox(
                "Event",
                list(events_by_code),
                format_func=lambda code: events_by_code[code]["label"],
            )
            selected_event = events_by_code[selected_event_code]["data"]

        with col_search:
            global_query = st.text_input("Search member", placeholder="Michie, Gracie…").lower().strip()

        with col_toggle:
            available_only = st.toggle("Available only", value=False)

    live_dashboard_fragment(
        selected_event,
        global_query,
        nickname_map,
        photo_map,
        member_metadata,
        available_only,
        tuple(event.get("code") for event in active_events if event.get("code")),
    )

    if st.session_state.get(f"sales_stats_available_{selected_event_code}"):
        render_stats_controls(can_share=is_admin)

    if is_admin:
        render_share_controls(f"share_selection_{selected_event.get('code', 'unknown')}")
else:
    st.error("No active Exclusive events found or failed to fetch data.")

st.markdown(
    """
    <footer class="index-footer">
        <span>GLOBAL EXCLUSIVE MONITOR · DATA FROM JKT48 PUBLIC API</span>
        <span>DEVELOPED BY <a href="https://x.com/estrellawin19" target="_blank" rel="noopener noreferrer">@ESTRELLAWIN19</a></span>
    </footer>
    """,
    unsafe_allow_html=True,
)
