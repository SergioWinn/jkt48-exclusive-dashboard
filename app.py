# app.py

import streamlit as st
import time
from datetime import datetime, timedelta, timezone
from html import escape
from pathlib import Path

from core.api import (
    clear_exclusive_detail_cache,
    fetch_exclusive_detail,
    get_active_exclusive_events,
    get_member_database,
)
from core.refresh import get_detail_refresh_interval, is_event_closed
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


def _humanize_api_reason(reason):
    raw_reason = (reason or "").strip()
    normalized = raw_reason.lower()
    if "waiting room" in normalized or "__cfwaitingroom" in normalized:
        return "Situs JKT48 sedang dalam antrean keamanan Cloudflare (Waiting Room). Kami menampilkan data terakhir yang tersedia sementara proses verifikasi berjalan."
    if "cloudflare challenge" in normalized or "just a moment" in normalized or "cf-chl" in normalized:
        return "Situs JKT48 sedang menjalani verifikasi keamanan Cloudflare. Data terbaru mungkin tertunda sementara sistem memvalidasi akses."
    if "connection failed" in normalized:
        return "Koneksi ke server JKT48 terganggu. Kami menampilkan data terakhir yang berhasil disimpan."
    if "bonus:" in normalized:
        return "Sisa stok bonus belum bisa dimuat. Menampilkan data API utama yang tersedia."
    if raw_reason:
        return raw_reason
    return "Layanan JKT48 sedang tidak dapat diakses saat ini."


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
                <h1 class="ldp-title">Global Exclusive Monitor</h1>
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

def _render_dashboard(
    selected_event,
    search_query,
    nickname_map,
    photo_map,
    member_metadata,
    available_only,
    current_event_codes,
):
    event_code = selected_event.get("code")
    event_state_key = f"event_data_{event_code}"
    attempt_state_key = f"event_fetch_attempt_{event_code}"
    event_data = st.session_state.get(event_state_key) or selected_event
    wr_info = st.session_state.get(f"wr_status_{event_code}", {"is_live": True, "time": ""})
    now_wib = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=7)
    closed = is_event_closed(event_data, now_wib)
    if not closed:
        refreshed_events = get_active_exclusive_events()
        refreshed_codes = {event.get("code") for event in refreshed_events if event.get("code")}
        if refreshed_codes.difference(current_event_codes):
            st.rerun()
    refresh_interval = get_detail_refresh_interval(event_data, wr_info.get("is_live", True), now_wib)
    last_attempt = st.session_state.get(attempt_state_key, 0.0)
    manual_refresh = st.session_state.pop("manual_refresh_requested", False)

    should_fetch = manual_refresh or event_state_key not in st.session_state or (
        (not closed or not wr_info.get("is_live", True)) and time.monotonic() - last_attempt >= refresh_interval
    )
    if event_code and should_fetch:
        st.session_state[attempt_state_key] = time.monotonic()
        fetched_event_data = fetch_exclusive_detail(event_code)
        if fetched_event_data:
            fetched_event_data = {**selected_event, **fetched_event_data}
            st.session_state[event_state_key] = fetched_event_data
            event_data = fetched_event_data

    wr_info = st.session_state.get(f"wr_status_{event_code}", {"is_live": True, "time": ""})
    now_wib = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=7)
    closed = is_event_closed(event_data, now_wib)
    refresh_interval = get_detail_refresh_interval(event_data, wr_info.get("is_live", True), now_wib)
    has_event_detail = isinstance(event_data.get("session"), list)

    if closed and wr_info.get("is_live"):
        source_class = "is-cached"
        source_label = "FINAL SNAPSHOT"
        source_detail = "Auto refresh stopped"
        sync_label = ""
    elif not has_event_detail:
        source_class = "is-unavailable"
        source_label = "LIST ONLY"
        source_detail = "Session details unavailable"
        sync_label = "Waiting for session data"
    elif wr_info.get("is_live"):
        source_class = "is-live"
        source_label = "LIVE DATA"
        source_detail = "Auto refresh"
        sync_label = wr_info.get("time") or "Waiting for first sync"
    else:
        source_class = "is-cached"
        source_label = "CACHED DATA"
        source_detail = "Last snapshot"
        sync_label = wr_info.get("time") or "Unknown snapshot time"
    event_title = escape(str(event_data.get("title", "Event")))
    raw_category = str(event_data.get("category", "-"))
    event_category = escape(CATEGORY_LABELS.get(raw_category, raw_category.replace("_", " ")))
    event_price = int(event_data.get("default_price") or 0)
    sync_markup = f"<small>{escape(str(sync_label))}</small>" if sync_label else ""
    with st.container(horizontal=True, vertical_alignment="center"):
        title_slot = st.container()
        with st.container(horizontal=True, vertical_alignment="center", width="content", gap="small"):
            if is_admin:
                with st.container(width="content", gap=None):
                    if st.button(
                        "Refresh", icon=":material/refresh:", type="tertiary",
                        help="Refresh data sekarang", key="manual_refresh",
                    ):
                        print(f"[sync] event={event_code} manual refresh requested", flush=True)
                        get_member_database.clear()
                        get_active_exclusive_events.clear()
                        clear_exclusive_detail_cache()
                        st.session_state["manual_refresh_requested"] = True
                        st.rerun()
                    result = "\u00a0"
                    if manual_refresh:
                        succeeded = has_event_detail and wr_info.get("is_live") and not wr_info.get("reason")
                        result = ":green[Successful]" if succeeded else ":orange[Failed]"
                        if has_event_detail and wr_info.get("is_live") and wr_info.get("reason"):
                            result = ":orange[Partial]"
                    st.caption(result, width="content")
            st.markdown(
                f'<div class="source-readout {source_class}">'
                f'<strong>{source_label}</strong>'
                f'<span>{source_detail}</span>{sync_markup}</div>',
                unsafe_allow_html=True, width="content",
            )
    title_slot.markdown(
        f"""
        <section class="event-index-head">
            <div>
                <div class="event-meta">{event_category} · IDR {event_price:,}</div>
                <h2>{event_title}</h2>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    event_closed = closed

    event_stats = calculate_event_stats(event_data, member_metadata)
    summary = event_stats["summary"]
    sales_data_available = event_stats["sales_data_available"]
    st.session_state[f"sales_stats_available_{event_code}"] = sales_data_available
    notices = []

    friendly_reason = _humanize_api_reason(wr_info.get("reason"))

    if not has_event_detail and not wr_info.get("is_live") and not event_closed:
        notices.append(
            f"{friendly_reason} "
            "Belum ada data sesi yang tersimpan untuk event ini."
        )
    elif not has_event_detail and not event_closed:
        notices.append(
            "Detail sesi dan stok belum tersedia. Kami menampilkan daftar event saja sementara proses sinkronisasi berjalan."
        )

    if not event_closed and wr_info.get("is_live") and wr_info.get("reason"):
        notices.append(friendly_reason)

    if notices:
        show_notice = st.warning if not wr_info.get("is_live") or not has_event_detail else st.info
        show_notice("\n\n".join(notices))

    if not has_event_detail:
        return

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

    render_event_cards(event_data, search_query, nickname_map, photo_map, available_only, event_closed)
    render_stats_payload(
        {
            "Member": table_rows(event_stats["members"]),
            "Generation": table_rows(event_stats["generations"], include_members=True),
            "Team": table_rows(event_stats["teams"], include_members=True),
        } if sales_data_available else {},
        f"{event_data.get('title', 'Event')} statistics",
        photo_map,
    )


@st.fragment(run_every=5)
def live_dashboard_fragment(*args):
    _render_dashboard(*args)


@st.fragment(run_every=5)
def closed_dashboard_fragment(*args):
    _render_dashboard(*args)


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

    fragment = closed_dashboard_fragment if is_event_closed(
        selected_event,
        datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=7),
    ) else live_dashboard_fragment
    fragment(
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
