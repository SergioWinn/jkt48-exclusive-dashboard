# core/api.py

import json
import os
from datetime import datetime, timedelta, timezone

import streamlit as st

try:
    from curl_cffi import requests as browser_requests
    USING_BROWSER_CLIENT = True
except ImportError:
    import requests as browser_requests
    USING_BROWSER_CLIENT = False

BASE_HEADERS = {
    "Accept": "application/json",
    "Referer": "https://jkt48.com/",
}
FALLBACK_HEADERS = {
    **BASE_HEADERS,
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
}
RUNTIME_CACHE_DIR = ".runtime_cache"
_runtime_jkt48_cookie = None
_waiting_room_detected = False
WAITING_ROOM_COOKIE_NAME = "__cfwaitingroom_q7VnL4xM2pK8dR5sT1wY9cB6hJ3uF0zA7eG2mN5Q8"
KNOWN_EXCLUSIVE_EVENTS = [
    {"exclusive_id": 936, "category": "PHOTOCARD", "thumbnail_image": "https://jkt48.com/api/v1/storages/media/exclusive/2026/04/ex7b6d-thumb-d71768.jpg", "preview_image": "https://jkt48.com/api/v1/storages/media/exclusive/2026/04/ex7b6d-preview-8a69c1.jpg", "code": "EXE588", "valid_date_from": "2026-04-02T11:00:00.000Z", "sort_order": 1, "title": "Personal Meet and Greet Festival: LOVE DREAM PASSION, Meet & Greet - 23 May", "short_description": ""},
    {"exclusive_id": 962, "category": "DIGITAL_PHOTOBOOK", "thumbnail_image": "https://jkt48.com/api/v1/storages/media/exclusive/2026/07/ex7f6c-thumb-a2122e.jpg", "preview_image": "https://jkt48.com/api/v1/storages/media/exclusive/2026/07/ex7f6c-preview-872f71.jpg", "code": "EX7F6C", "valid_date_from": "2026-07-16T13:00:00.000Z", "sort_order": None, "title": "JKT48 Request Hour 2026 Setlist Best 40", "short_description": ""},
    {"exclusive_id": 960, "category": "TWO_SHOT", "thumbnail_image": "https://jkt48.com/api/v1/storages/media/exclusive/2026/06/exfb66-thumb-ba1e85.jpg", "preview_image": "https://jkt48.com/api/v1/storages/media/exclusive/2026/06/exfb66-preview-bb4a0e.jpg", "code": "EXFB66", "valid_date_from": "2026-06-22T05:00:00.000Z", "sort_order": None, "title": "Team Love & Team Dream, 2shot Yogyakarta", "short_description": ""},
    {"exclusive_id": 959, "category": "PHOTOCARD", "thumbnail_image": "https://jkt48.com/api/v1/storages/media/exclusive/2026/06/exa340-thumb-bc4526.jpg", "preview_image": "https://jkt48.com/api/v1/storages/media/exclusive/2026/06/exa340-preview-c338ee.jpg", "code": "EXA340", "valid_date_from": "2026-06-22T05:00:00.000Z", "sort_order": None, "title": "Team Love & Team Dream, Meet and Greet Yogyakarta", "short_description": ""},
    {"exclusive_id": 958, "category": "TWO_SHOT", "thumbnail_image": "https://jkt48.com/api/v1/storages/media/exclusive/2026/06/ex38a5-thumb-ec17a2.jpg", "preview_image": "https://jkt48.com/api/v1/storages/media/exclusive/2026/06/ex38a5-preview-108c95.jpg", "code": "EX38A5", "valid_date_from": "2026-06-22T05:00:00.000Z", "sort_order": None, "title": "Team Passion, 2shot Surabaya", "short_description": ""},
    {"exclusive_id": 957, "category": "PHOTOCARD", "thumbnail_image": "https://jkt48.com/api/v1/storages/media/exclusive/2026/06/exafb8-thumb-26d9a3.jpg", "preview_image": "https://jkt48.com/api/v1/storages/media/exclusive/2026/06/exafb8-preview-b668a4.jpg", "code": "EXAFB8", "valid_date_from": "2026-06-22T05:00:00.000Z", "sort_order": None, "title": "Team Passion, Meet and Greet Surabaya", "short_description": ""},
    {"exclusive_id": 954, "category": "TWO_SHOT", "thumbnail_image": "https://jkt48.com/api/v1/storages/media/exclusive/2026/06/ex3773-thumb-f96b44.jpg", "preview_image": "https://jkt48.com/api/v1/storages/media/exclusive/2026/06/ex3773-preview-cbccce.jpg", "code": "EX3773", "valid_date_from": "2026-06-15T05:00:00.000Z", "sort_order": None, "title": "Team Love & Team Dream, 2shot Surabaya", "short_description": ""},
    {"exclusive_id": 953, "category": "PHOTOCARD", "thumbnail_image": "https://jkt48.com/api/v1/storages/media/exclusive/2026/06/ex9a4a-thumb-736b1c.jpg", "preview_image": "https://jkt48.com/api/v1/storages/media/exclusive/2026/06/ex9a4a-preview-792fcc.jpg", "code": "EX9A4A", "valid_date_from": "2026-06-15T05:00:00.000Z", "sort_order": None, "title": "Team Love & Team Dream, Meet and Greet Surabaya", "short_description": ""},
    {"exclusive_id": 956, "category": "TWO_SHOT", "thumbnail_image": "https://jkt48.com/api/v1/storages/media/exclusive/2026/06/excd2c-thumb-d289a4.jpg", "preview_image": "https://jkt48.com/api/v1/storages/media/exclusive/2026/06/excd2c-preview-385402.jpg", "code": "EXCD2C", "valid_date_from": "2026-06-15T05:00:00.000Z", "sort_order": None, "title": "Team Passion, 2shot Yogyakarta", "short_description": ""},
    {"exclusive_id": 955, "category": "PHOTOCARD", "thumbnail_image": "https://jkt48.com/api/v1/storages/media/exclusive/2026/06/excb75-thumb-fd9e9c.jpg", "preview_image": "https://jkt48.com/api/v1/storages/media/exclusive/2026/06/excb75-preview-03c4c8.jpg", "code": "EXCB75", "valid_date_from": "2026-06-15T05:00:00.000Z", "sort_order": None, "title": "Team Passion, Meet and Greet Yogyakarta", "short_description": ""},
    {"exclusive_id": 947, "category": "DIGITAL_PHOTOBOOK", "thumbnail_image": "https://jkt48.com/api/v1/storages/media/exclusive/2026/06/ex783d-thumb-edd92f.jpg", "preview_image": "https://jkt48.com/api/v1/storages/media/exclusive/2026/06/ex783d-preview-c1bec0.jpg", "code": "EX783D", "valid_date_from": "2026-06-09T13:00:00.000Z", "sort_order": None, "title": "JKT48 Personal Meet and Greet Festival: LOVE DREAM PASSION", "short_description": ""},
    {"exclusive_id": 946, "category": "DIGITAL_PHOTOBOOK", "thumbnail_image": "https://jkt48.com/api/v1/storages/media/exclusive/2026/05/ex3725-thumb-f9f5e7.jpg", "preview_image": "https://jkt48.com/api/v1/storages/media/exclusive/2026/05/ex3725-preview-d270de.jpg", "code": "EX3725", "valid_date_from": "2026-05-06T15:00:00.000Z", "sort_order": None, "title": "We Are Love, Dream Team, Passion On Fire!", "short_description": ""},
    {"exclusive_id": 945, "category": "DIGITAL_PHOTOBOOK", "thumbnail_image": "https://jkt48.com/api/v1/storages/media/exclusive/2026/04/ex8432-thumb-0bd15f.jpg", "preview_image": "https://jkt48.com/api/v1/storages/media/exclusive/2026/04/ex8432-preview-5bec27.jpg", "code": "EX8432", "valid_date_from": "2026-04-26T12:00:00.000Z", "sort_order": None, "title": "Love Dream Passion - Music Video Behind the Scenes (Without Bonus Video Call)", "short_description": ""},
    {"exclusive_id": 944, "category": "DIGITAL_PHOTOBOOK", "thumbnail_image": "https://jkt48.com/api/v1/storages/media/exclusive/2026/04/exbe10-thumb-37400f.jpg", "preview_image": "https://jkt48.com/api/v1/storages/media/exclusive/2026/04/exbe10-preview-98404e.jpg", "code": "EXBE10", "valid_date_from": "2026-04-10T15:00:00.000Z", "sort_order": None, "title": "Love Dream Passion - Music Video Behind the Scenes", "short_description": ""},
    {"exclusive_id": 933, "category": "TWO_SHOT", "thumbnail_image": "https://jkt48.com/api/v1/storages/media/exclusive/2026/03/ex579e-thumb-c637b9.jpg", "preview_image": "https://jkt48.com/api/v1/storages/media/exclusive/2026/03/ex579e-preview-e420c5.jpg", "code": "EX579E", "valid_date_from": "2026-04-01T11:00:00.000Z", "sort_order": None, "title": "Personal Meet and Greet Festival: LOVE DREAM PASSION, 2Shot - 23 May", "short_description": ""},
]
EMERGENCY_EXCLUSIVE_DETAILS = {
    "EX7F6C": {
        "exclusive_id": 962,
        "category": "DIGITAL_PHOTOBOOK",
        "thumbnail_image": "https://jkt48.com/api/v1/storages/media/exclusive/2026/07/ex7f6c-thumb-a2122e.jpg",
        "preview_image": "https://jkt48.com/api/v1/storages/media/exclusive/2026/07/ex7f6c-preview-872f71.jpg",
        "code": "EX7F6C",
        "default_price": 120000,
        "total_quota": 10800,
        "max_purchase": 5,
        "max_purchase_transaction": 5,
        "sort_order": None,
        "valid_date_from": "2026-07-16T13:00:00.000Z",
        "valid_date_to": None,
        "status": True,
        "title": "JKT48 Request Hour 2026 Setlist Best 40",
        "short_description": "",
        "content_body": "<div>Photobook JKT48 \"Request Hour 2026 Setlist Best 40\" menghadirkan berbagai momen spesial dari pertunjukan yang penuh semangat. Setiap halaman menampilkan kenangan indah para member di atas panggung. </div>",
        "sales_period": [
            {"label": "OFC", "start_date": "2026-07-16T20:00:00", "end_date": "2026-07-26T07:00:00", "is_ofc_only": True},
            {"label": "General", "start_date": "2026-07-17T20:00:00", "end_date": "2026-07-26T07:00:00", "is_ofc_only": False}
        ],
        "session": [
            {"label": "Sesi 1", "date": "2026-07-19", "start_time": "11:45:00", "end_time": "12:45:00", "reception_start_time": "11:30:00", "reception_end_time": "12:00:00", "prep_start_time": "11:30:00", "prep_end_time": "11:45:00", "session_detail": [{"label": "Jalur 1", "tickets_sold": 5, "jkt48_member_name": "Bong Aprilli", "available_quota": 40}, {"label": "Jalur 2", "tickets_sold": 18, "jkt48_member_name": "Mikaela Kusjanto", "available_quota": 27}, {"label": "Jalur 3", "tickets_sold": 4, "jkt48_member_name": "Maxine Faye", "available_quota": 41}, {"label": "Jalur 4", "tickets_sold": 17, "jkt48_member_name": "Sona Kalyana", "available_quota": 28}, {"label": "Jalur 5", "tickets_sold": 5, "jkt48_member_name": "Fahira Putri", "available_quota": 40}, {"label": "Jalur 6", "tickets_sold": 14, "jkt48_member_name": "Ralyne Van Irwan", "available_quota": 31}, {"label": "Jalur 7", "tickets_sold": 23, "jkt48_member_name": "Christabella Bonita", "available_quota": 22}]},
            {"label": "Sesi 2", "date": "2026-07-19", "start_time": "13:15:00", "end_time": "14:15:00", "reception_start_time": "13:00:00", "reception_end_time": "13:30:00", "prep_start_time": "13:00:00", "prep_end_time": "13:15:00", "session_detail": [{"label": "Jalur 1", "tickets_sold": 12, "jkt48_member_name": "Bong Aprilli", "available_quota": 33}, {"label": "Jalur 2", "tickets_sold": 26, "jkt48_member_name": "Mikaela Kusjanto", "available_quota": 19}, {"label": "Jalur 3", "tickets_sold": 7, "jkt48_member_name": "Maxine Faye", "available_quota": 38}, {"label": "Jalur 4", "tickets_sold": 11, "jkt48_member_name": "Sona Kalyana", "available_quota": 34}, {"label": "Jalur 5", "tickets_sold": 14, "jkt48_member_name": "Fahira Putri", "available_quota": 31}, {"label": "Jalur 6", "tickets_sold": 9, "jkt48_member_name": "Ralyne Van Irwan", "available_quota": 36}, {"label": "Jalur 7", "tickets_sold": 13, "jkt48_member_name": "Christabella Bonita", "available_quota": 32}]},
            {"label": "Sesi 3", "date": "2026-07-19", "start_time": "14:45:00", "end_time": "15:45:00", "reception_start_time": "14:30:00", "reception_end_time": "15:00:00", "prep_start_time": "14:30:00", "prep_end_time": "14:45:00", "session_detail": [{"label": "Jalur 1", "tickets_sold": 8, "jkt48_member_name": "Bong Aprilli", "available_quota": 37}, {"label": "Jalur 2", "tickets_sold": 37, "jkt48_member_name": "Mikaela Kusjanto", "available_quota": 8}, {"label": "Jalur 3", "tickets_sold": 6, "jkt48_member_name": "Maxine Faye", "available_quota": 39}, {"label": "Jalur 4", "tickets_sold": 32, "jkt48_member_name": "Sona Kalyana", "available_quota": 13}, {"label": "Jalur 5", "tickets_sold": 9, "jkt48_member_name": "Fahira Putri", "available_quota": 36}, {"label": "Jalur 6", "tickets_sold": 18, "jkt48_member_name": "Ralyne Van Irwan", "available_quota": 27}, {"label": "Jalur 7", "tickets_sold": 17, "jkt48_member_name": "Christabella Bonita", "available_quota": 28}]},
            {"label": "Sesi 4", "date": "2026-07-19", "start_time": "16:30:00", "end_time": "17:30:00", "reception_start_time": "16:15:00", "reception_end_time": "16:45:00", "prep_start_time": "16:15:00", "prep_end_time": "16:30:00", "session_detail": [{"label": "Jalur 1", "tickets_sold": 45, "jkt48_member_name": "Nur Intan", "available_quota": 0}, {"label": "Jalur 2", "tickets_sold": 45, "jkt48_member_name": "Hagia Sopia", "available_quota": 0}, {"label": "Jalur 3", "tickets_sold": 45, "jkt48_member_name": "Jemima Evodie", "available_quota": 0}, {"label": "Jalur 4", "tickets_sold": 45, "jkt48_member_name": "Jacqueline Immanuela", "available_quota": 0}, {"label": "Jalur 5", "tickets_sold": 33, "jkt48_member_name": "Astrella Virgiananda", "available_quota": 12}, {"label": "Jalur 6", "tickets_sold": 10, "jkt48_member_name": "Humaira Ramadhani", "available_quota": 35}, {"label": "Jalur 7", "tickets_sold": 19, "jkt48_member_name": "Aulia Riza", "available_quota": 26}]}
        ]
    }
}


class LiveApiUnavailable(RuntimeError):
    pass


def get_jkt48_cookie():
    return os.getenv("JKT48_COOKIE", "") if _runtime_jkt48_cookie is None else _runtime_jkt48_cookie


def set_jkt48_cookie(cookie):
    # ponytail: process-local state; use a shared secret store if the app gains multiple replicas.
    global _runtime_jkt48_cookie
    _runtime_jkt48_cookie = cookie


def is_waiting_room_detected():
    return _waiting_room_detected


def build_jkt48_cookie(waiting_room):
    waiting_room = waiting_room.strip()
    if waiting_room.startswith("__cfwaitingroom"):
        waiting_room_name, separator, waiting_room = waiting_room.partition("=")
    else:
        waiting_room_name, separator = WAITING_ROOM_COOKIE_NAME, "="
    if not waiting_room or not separator:
        raise ValueError("Value cookie Waiting Room wajib diisi.")
    if any(character in f"{waiting_room_name}{waiting_room}" for character in "\r\n;"):
        raise ValueError("Tempel value cookie tanpa titik koma atau baris baru.")
    return f"{waiting_room_name}={waiting_room}"


def _set_wr_status(code, is_live, time_label, reason=""):
    try:
        st.session_state[f"wr_status_{code}"] = {
            "is_live": is_live,
            "time": time_label,
            "reason": reason,
        }
    except Exception:
        pass


def _send_http_get(url, timeout, headers):
    kwargs = {"timeout": timeout, "headers": headers}
    if USING_BROWSER_CLIENT:
        responses = []
        last_error = None
        for browser in ("chrome136", "safari184"):
            try:
                response = browser_requests.get(url, impersonate=browser, **kwargs)
            except Exception as error:
                last_error = error
                continue
            responses.append(response)
            content_type = response.headers.get("content-type", "").lower()
            if response.status_code == 200 and "json" in content_type:
                return response
        if responses:
            return responses[-1]
        raise last_error or RuntimeError("No HTTP response")
    return browser_requests.get(url, **kwargs)


def _is_waiting_room_response(response):
    content_type = response.headers.get("content-type", "").lower()
    if "json" in content_type:
        return False
    body_start = response.text[:1000].lower()
    return "waiting room" in body_start or "__cfwaitingroom" in body_start


def _is_cloudflare_gate_response(response):
    if _is_waiting_room_response(response):
        return True
    content_type = response.headers.get("content-type", "").lower()
    if "json" in content_type:
        return False
    body_start = response.text[:1000].lower()
    return response.status_code == 403 or "just a moment" in body_start or "cf-chl" in body_start


def _http_get(url, timeout):
    global _waiting_room_detected
    response = _send_http_get(url, timeout, FALLBACK_HEADERS)
    _waiting_room_detected = _is_cloudflare_gate_response(response)
    if _waiting_room_detected and (cookie := get_jkt48_cookie()):
        response = _send_http_get(url, timeout, {**FALLBACK_HEADERS, "Cookie": cookie})
    return response


def _get_json(url, timeout):
    try:
        response = _http_get(url, timeout)
    except Exception as error:
        raise LiveApiUnavailable(f"Connection failed: {error}") from error

    content_type = response.headers.get("content-type", "").lower()
    if response.status_code != 200:
        reason = "Cloudflare challenge" if response.status_code == 403 else f"HTTP {response.status_code}"
        raise LiveApiUnavailable(reason)
    if "json" not in content_type:
        body_start = response.text[:1000].lower()
        if _is_waiting_room_response(response):
            reason = "Cloudflare Waiting Room"
        elif "just a moment" in body_start or "cf-chl" in body_start:
            reason = "Cloudflare challenge"
        else:
            reason = f"Unexpected content type: {content_type or 'unknown'}"
        raise LiveApiUnavailable(reason)

    try:
        payload = response.json()
    except Exception as error:
        raise LiveApiUnavailable("Invalid JSON response") from error
    if not isinstance(payload, dict) or payload.get("status") is not True:
        message = payload.get("message", "Invalid API response") if isinstance(payload, dict) else "Invalid API response"
        raise LiveApiUnavailable(message)
    return payload


def _write_cache(cache_file, payload):
    try:
        parent_dir = os.path.dirname(cache_file)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)
        with open(cache_file, "w", encoding="utf-8") as file:
            json.dump(payload, file)
    except OSError:
        pass


def _read_cache(cache_file):
    if not os.path.exists(cache_file):
        return None
    try:
        with open(cache_file, "r", encoding="utf-8") as file:
            return json.load(file)
    except (OSError, ValueError):
        return None


@st.cache_data(ttl=30)
def get_member_database():
    url = "https://jkt48.com/api/v1/members?lang=id"
    cache_file = os.path.join(RUNTIME_CACHE_DIR, "members.json")
    nickname_map = {}
    photo_map = {}
    try:
        res_json = _get_json(url, 15)
        if res_json.get("status") is True and "data" in res_json:
            for member in res_json["data"]:
                name = member.get("name", "").strip().lower()
                nickname = member.get("nickname", "").strip().lower()
                photo = member.get("photo", "")
                if nickname and name:
                    nickname_map[nickname] = name
                if name and photo:
                    photo_map[name] = photo
        if photo_map:
            _write_cache(cache_file, {"nickname_map": nickname_map, "photo_map": photo_map})
    except Exception:
        cached_members = _read_cache(cache_file) or {}
        nickname_map = cached_members.get("nickname_map", {})
        photo_map = cached_members.get("photo_map", {})
    return nickname_map, photo_map


@st.cache_data(ttl=30)
def get_active_exclusive_events():
    url = "https://jkt48.com/api/v1/exclusives?lang=id"
    cache_file = os.path.join(RUNTIME_CACHE_DIR, "exclusive_events.json")
    try:
        res_json = _get_json(url, 20)
        data_content = res_json.get("data", [])
        event_list = data_content if isinstance(data_content, list) else data_content.get("data", [])
        live_events = [event for event in event_list if event.get("code")]
        if not live_events:
            raise LiveApiUnavailable("Exclusive event list is empty")
        live_events.sort(key=lambda event: event.get("valid_date_from") or "", reverse=True)
        now_wib = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=7)
        _write_cache(
            cache_file,
            {"last_updated": now_wib.strftime('%d/%m/%Y %H:%M:%S WIB'), "data": live_events},
        )
        return live_events
    except LiveApiUnavailable:
        cached_events = _read_cache(cache_file)
        if cached_events and cached_events.get("data"):
            return cached_events["data"]
        return KNOWN_EXCLUSIVE_EVENTS.copy()


@st.cache_data(ttl=4, show_spinner=False)
def _fetch_exclusive_detail_shared(code):
    url = f"https://jkt48.com/api/v1/exclusives/{code}?lang=id"
    cache_file = os.path.join(RUNTIME_CACHE_DIR, f"exclusive_{code}.json")
    bundled_cache_file = os.path.join("data", "fallback", f"{code}.json")
    now_wib = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=7)
    waktu_sekarang = now_wib.strftime('%d/%m/%Y %H:%M:%S WIB')

    try:
        res_json = _get_json(url, 12)
        data = res_json.get("data")
        if not isinstance(data, dict) or not data.get("code"):
            raise LiveApiUnavailable("Exclusive detail is missing")
        _write_cache(cache_file, {"last_updated": waktu_sekarang, "data": data})
        return {
            "data": data,
            "is_live": True,
            "reason": "",
            "time": waktu_sekarang,
        }
    except LiveApiUnavailable as error:
        cache_payload = _read_cache(cache_file) or _read_cache(bundled_cache_file)
        if cache_payload and cache_payload.get("data"):
            return {
                "data": cache_payload["data"],
                "is_live": False,
                "reason": str(error),
                "time": cache_payload.get("last_updated", "Unknown"),
            }

    emergency_data = EMERGENCY_EXCLUSIVE_DETAILS.get(code)
    if emergency_data:
        return {
            "data": emergency_data,
            "is_live": False,
            "reason": "Live API unavailable",
            "time": "Bundled emergency fallback",
        }

    return {
        "data": None,
        "is_live": False,
        "reason": "Live API unavailable",
        "time": "No Cache Available",
    }


def fetch_exclusive_detail(code):
    result = _fetch_exclusive_detail_shared(code)
    _set_wr_status(
        code,
        result["is_live"],
        result["time"],
        result["reason"],
    )
    return result["data"]


def clear_exclusive_detail_cache():
    _fetch_exclusive_detail_shared.clear()
