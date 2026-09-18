# core/api.py

import json
import os
import tempfile
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
MAX_FALLBACK_AGE_DAYS = 365
AKB48_PHOTO_MAP = {
    "saho iwatate": "https://d2r1lkk9i7row.cloudfront.net/mobile/member/83100622.jpg",
    "seina fukuoka": "https://d2r1lkk9i7row.cloudfront.net/mobile/member/83100790.jpg",
    "yui oguri": "https://d2r1lkk9i7row.cloudfront.net/mobile/member/83100816.jpg",
    "yurina gyoten": "https://d2r1lkk9i7row.cloudfront.net/mobile/member/83100840.jpg",
    "narumi kuranoo": "https://d2r1lkk9i7row.cloudfront.net/mobile/member/83100846.jpg",
    "hiyuka sakagawa": "https://d2r1lkk9i7row.cloudfront.net/mobile/member/83100997.jpg",
    "miu shitao": "https://d2r1lkk9i7row.cloudfront.net/mobile/member/83100838.jpg",
    "ayane takahashi": "https://d2r1lkk9i7row.cloudfront.net/mobile/member/83100814.jpg",
    "remi tokunaga": "https://d2r1lkk9i7row.cloudfront.net/mobile/member/83100993.jpg",
    "serika nagano": "https://d2r1lkk9i7row.cloudfront.net/mobile/member/83100828.jpg",
    "haruna hashimoto": "https://d2r1lkk9i7row.cloudfront.net/mobile/member/83100824.jpg",
    "erii chiba": "https://d2r1lkk9i7row.cloudfront.net/mobile/member/83100927.jpg",
    "haruka kurosu": "https://d2r1lkk9i7row.cloudfront.net/mobile/member/83100937.jpg",
    "ayami nagatomo": "https://d2r1lkk9i7row.cloudfront.net/mobile/member/83100943.jpg",
    "orin muto": "https://d2r1lkk9i7row.cloudfront.net/mobile/member/83100949.jpg",
    "mizuki yamauchi": "https://d2r1lkk9i7row.cloudfront.net/mobile/member/83100951.jpg",
    "suzuha yamane": "https://d2r1lkk9i7row.cloudfront.net/mobile/member/83100952.jpg",
    "yuki ota": "https://d2r1lkk9i7row.cloudfront.net/mobile/member/83100998.jpg",
    "airi sato": "https://d2r1lkk9i7row.cloudfront.net/mobile/member/83101000.jpg",
    "eriko hashimoto": "https://d2r1lkk9i7row.cloudfront.net/mobile/member/83101001.jpg",
    "nozomi hatakeyama": "https://d2r1lkk9i7row.cloudfront.net/mobile/member/83101003.jpg",
    "yuki hirata": "https://d2r1lkk9i7row.cloudfront.net/mobile/member/83101004.jpg",
    "moka hotei": "https://d2r1lkk9i7row.cloudfront.net/mobile/member/83101005.jpg",
    "mayuu masai": "https://d2r1lkk9i7row.cloudfront.net/mobile/member/83101006.jpg",
    "miyuu mizushima": "https://d2r1lkk9i7row.cloudfront.net/mobile/member/83101007.jpg",
    "sora yamazaki": "https://d2r1lkk9i7row.cloudfront.net/mobile/member/83101008.jpg",
    "yuna akiyama": "https://d2r1lkk9i7row.cloudfront.net/hashiranokai/member/83101009.jpg",
    "sae arai": "https://d2r1lkk9i7row.cloudfront.net/hashiranokai/member/83101010.jpg",
    "kasumi kudo": "https://d2r1lkk9i7row.cloudfront.net/hashiranokai/member/83101011.jpg",
    "hinano kubo": "https://d2r1lkk9i7row.cloudfront.net/hashiranokai/member/83101012.jpg",
    "yumemi sako": "https://d2r1lkk9i7row.cloudfront.net/hashiranokai/member/83101013.jpg",
    "kohina narita": "https://d2r1lkk9i7row.cloudfront.net/hashiranokai/member/83101014.jpg",
    "azuki yagi": "https://d2r1lkk9i7row.cloudfront.net/hashiranokai/member/83101015.jpg",
    "yui yamaguchi": "https://d2r1lkk9i7row.cloudfront.net/hashiranokai/member/83101016.jpg",
    "momoka ito": "https://d2r1lkk9i7row.cloudfront.net/hashiranokai/member/83101017.jpg",
    "kairi okumoto": "https://d2r1lkk9i7row.cloudfront.net/hashiranokai/member/83101018.jpg",
    "yui kawamura": "https://d2r1lkk9i7row.cloudfront.net/hashiranokai/member/83101019.jpg",
    "saki oga": "https://d2r1lkk9i7row.cloudfront.net/hashiranokai/member/83101022.jpg",
    "saki kondo": "https://d2r1lkk9i7row.cloudfront.net/hashiranokai/member/83101023.jpg",
    "hinata maruyama": "https://d2r1lkk9i7row.cloudfront.net/hashiranokai/member/83101024.jpg",
    "mao takahashi": "https://d2r1lkk9i7row.cloudfront.net/hashiranokai/member/83101025.jpg",
    "sayuri tanaka": "https://d2r1lkk9i7row.cloudfront.net/hashiranokai/member/83101026.jpg",
    "ema makito": "https://d2r1lkk9i7row.cloudfront.net/hashiranokai/member/83101027.jpg",
    "yu morikawa": "https://d2r1lkk9i7row.cloudfront.net/hashiranokai/member/83101028.jpg",
    "kiko watanabe": "https://d2r1lkk9i7row.cloudfront.net/hashiranokai/member/83101029.jpg",
}
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
    kwargs = {"timeout": min(timeout, 5), "headers": headers}
    if USING_BROWSER_CLIENT:
        return browser_requests.get(url, impersonate="chrome136", **kwargs)
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
    return response.headers.get("cf-mitigated") == "challenge" or "just a moment" in body_start or "cf-chl" in body_start


def _http_get(url, timeout):
    global _waiting_room_detected
    response = _send_http_get(url, timeout, FALLBACK_HEADERS)
    _waiting_room_detected = _is_cloudflare_gate_response(response)
    if _waiting_room_detected and (cookie := get_jkt48_cookie()):
        response = _send_http_get(url, timeout, {**FALLBACK_HEADERS, "Cookie": cookie})
    return response


def validate_jkt48_cookie(cookie):
    _get_json("https://jkt48.com/api/v1/exclusives?lang=id", 12, cookie=cookie)


def _get_json(url, timeout, cookie=None):
    try:
        response = (
            _http_get(url, timeout) if cookie is None
            else _send_http_get(url, timeout, {**FALLBACK_HEADERS, "Cookie": cookie})
        )
    except Exception as error:
        raise LiveApiUnavailable(f"Connection failed: {error}") from error

    content_type = response.headers.get("content-type", "").lower()
    if response.status_code != 200:
        reason = "Cloudflare challenge" if _is_cloudflare_gate_response(response) else f"HTTP {response.status_code}"
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
    temporary = None
    try:
        parent_dir = os.path.dirname(cache_file) or "."
        os.makedirs(parent_dir, exist_ok=True)
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=parent_dir, delete=False) as file:
            temporary = file.name
            json.dump(payload, file)
        os.replace(temporary, cache_file)
    except OSError:
        pass
    finally:
        if temporary and os.path.exists(temporary):
            try:
                os.unlink(temporary)
            except OSError:
                pass


def _read_cache(cache_file):
    if not os.path.exists(cache_file):
        return None
    try:
        with open(cache_file, "r", encoding="utf-8") as file:
            payload = json.load(file)
            return payload if isinstance(payload, dict) else None
    except (OSError, ValueError):
        return None


def _read_latest_cache(runtime_file, bundled_file):
    candidates = [_read_cache(runtime_file), _read_cache(bundled_file)]

    def updated(payload):
        try:
            return datetime.strptime(payload.get("last_updated", ""), "%d/%m/%Y %H:%M:%S WIB")
        except (TypeError, ValueError):
            return datetime.min

    return max((p for p in candidates if isinstance(p, dict) and p.get("data")),
               key=updated, default=None)


@st.cache_data(ttl=300, show_spinner=False)
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
            photo_map = {**AKB48_PHOTO_MAP, **photo_map}
            _write_cache(cache_file, {"nickname_map": nickname_map, "photo_map": photo_map})
        else:
            raise LiveApiUnavailable("Member photos are empty")
    except Exception:
        bundled_members = _read_cache(os.path.join("data", "fallback", "members.json")) or {}
        cached_members = _read_cache(cache_file) or {}
        nickname_map = {**bundled_members.get("nickname_map", {}), **cached_members.get("nickname_map", {})}
        photo_map = {**AKB48_PHOTO_MAP, **bundled_members.get("photo_map", {}), **cached_members.get("photo_map", {})}
    return nickname_map, photo_map


def _filter_recent_fallback_events(events, now_wib=None):
    now_wib = now_wib or (datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=7))
    filtered = []
    for event in events or []:
        if not isinstance(event, dict) or not event.get("code"):
            continue

        valid_from = event.get("valid_date_from")
        valid_to = event.get("valid_date_to")
        parsed_from = None
        parsed_to = None

        if valid_from:
            try:
                parsed_from = datetime.fromisoformat(str(valid_from).replace("Z", "").split(".")[0]) + timedelta(hours=7)
            except ValueError:
                parsed_from = None

        if valid_to:
            try:
                parsed_to = datetime.fromisoformat(str(valid_to).replace("Z", "").split(".")[0]) + timedelta(hours=7)
            except ValueError:
                parsed_to = None

        if parsed_to is not None:
            if now_wib >= parsed_to:
                continue
            filtered.append(event)
            continue

        if parsed_from is not None and now_wib - parsed_from > timedelta(days=MAX_FALLBACK_AGE_DAYS):
            continue

        filtered.append(event)
    return filtered


@st.cache_data(ttl=30, show_spinner=False)
def get_active_exclusive_events():
    url = "https://jkt48.com/api/v1/exclusives?lang=id"
    cache_file = os.path.join(RUNTIME_CACHE_DIR, "exclusive_events.json")
    now_wib = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=7)
    try:
        res_json = _get_json(url, 20)
        data_content = res_json.get("data", [])
        event_list = data_content.get("data") if isinstance(data_content, dict) else data_content
        if not isinstance(event_list, list):
            raise LiveApiUnavailable("Invalid event list")
        live_events = [event for event in event_list if isinstance(event, dict) and isinstance(event.get("code"), str) and event["code"]]
        if not live_events:
            raise LiveApiUnavailable("Exclusive event list is empty")
        live_events.sort(key=lambda event: event.get("valid_date_from") or "", reverse=True)
        _write_cache(
            cache_file,
            {"last_updated": now_wib.strftime('%d/%m/%Y %H:%M:%S WIB'), "data": live_events},
        )
        return live_events
    except LiveApiUnavailable:
        cached_events = _read_latest_cache(cache_file, os.path.join("data", "fallback", "exclusive_events.json"))
        if cached_events and cached_events.get("data"):
            fresh_cached = _filter_recent_fallback_events(cached_events["data"], now_wib)
            if fresh_cached:
                return fresh_cached
        fallback_events = _filter_recent_fallback_events(KNOWN_EXCLUSIVE_EVENTS.copy(), now_wib)
        return fallback_events


def _validate_detail(data, code):
    if not isinstance(data, dict) or data.get("code") != code:
        raise LiveApiUnavailable("Exclusive detail is missing")
    sessions = data.get("session", [])
    if not isinstance(sessions, list):
        raise LiveApiUnavailable("Invalid event sessions")
    for session in sessions:
        if not isinstance(session, dict) or not isinstance(session.get("session_detail", []), list):
            raise LiveApiUnavailable("Invalid event session")
        if any(not isinstance(member, dict) for member in session.get("session_detail", [])):
            raise LiveApiUnavailable("Invalid event member")
    return data


def _bonus_stock_key(session, label, member_name):
    return (str(session.get("date") or "")[:10], str(session.get("start_time") or "")[:5],
            str(label or "").strip().casefold(), str(member_name or "").strip().casefold())


def _apply_bonus_stock(data, bonus_sessions):
    if not isinstance(bonus_sessions, list) or not bonus_sessions:
        raise LiveApiUnavailable("Invalid bonus sessions")
    sessions = {
        _bonus_stock_key(session, "", "")[:2]: session
        for session in data.get("session", [])
    }
    has_stock = False
    for session in bonus_sessions:
        if not isinstance(session, dict) or not isinstance(session.get("session_members"), list):
            raise LiveApiUnavailable("Invalid bonus session")
        session_key = _bonus_stock_key(session, "", "")[:2]
        previous = sessions.get(session_key, {})
        members = {
            _bonus_stock_key(previous, member.get("label"), member.get("jkt48_member_name")): member
            for member in previous.get("session_detail", [])
        }
        for member in session["session_members"]:
            if not isinstance(member, dict):
                raise LiveApiUnavailable("Invalid bonus member")
            quota = member.get("available_quota")
            identity = _bonus_stock_key(session, member.get("label"), member.get("member_name"))
            if not all(isinstance(value, str) and value for value in identity) or type(quota) is not int or quota < 0:
                raise LiveApiUnavailable("Invalid bonus stock")
            has_stock = True
            members[identity] = {
                **members.get(identity, {}), **member,
                "jkt48_member_name": member["member_name"], "quota_available": quota > 0,
            }
        sessions[session_key] = {
            **previous, **{key: value for key, value in session.items() if key != "session_members"},
            "session_detail": list(members.values()),
        }
    if not has_stock:
        raise LiveApiUnavailable("Bonus stock is empty")
    return {**data, "session": list(sessions.values())}


@st.cache_data(ttl=4, show_spinner=False)
def _fetch_exclusive_detail_shared(code):
    url = f"https://jkt48.com/api/v1/exclusives/{code}?lang=id"
    cache_file = os.path.join(RUNTIME_CACHE_DIR, f"exclusive_{code}.json")
    bundled_cache_file = os.path.join("data", "fallback", f"{code}.json")
    now_wib = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=7)
    waktu_sekarang = now_wib.strftime('%d/%m/%Y %H:%M:%S WIB')
    is_live, reason, time_label = True, "", waktu_sekarang
    try:
        data = _validate_detail(_get_json(url, 12).get("data"), code)
    except LiveApiUnavailable as error:
        is_live, reason = False, str(error)
        cache_payload = _read_latest_cache(cache_file, bundled_cache_file)
        if cache_payload and cache_payload.get("data"):
            try:
                data = _validate_detail(cache_payload["data"], code)
            except LiveApiUnavailable:
                data = None
            time_label = cache_payload.get("last_updated", "Unknown")
        else:
            data = EMERGENCY_EXCLUSIVE_DETAILS.get(code)
            time_label = "Bundled emergency fallback" if data else "No Cache Available"

    try:
        bonus = _get_json(f"https://jkt48.com/api/v1/exclusives/{code}/bonus?lang=id", 12)
        data = _apply_bonus_stock(data or {"code": code}, bonus.get("data"))
        is_live, reason, time_label = True, "", waktu_sekarang
    except LiveApiUnavailable as error:
        reason = f"{reason}; bonus: {error}" if reason else f"Bonus: {error}"
        if is_live:
            cached = _read_latest_cache(cache_file, bundled_cache_file)
            if cached and cached.get("data"):
                try:
                    cached_data = _validate_detail(cached["data"], code)
                except LiveApiUnavailable:
                    cached_data = None
                if cached_data:
                    data = cached_data
                    is_live = False
                    time_label = cached.get("last_updated", "Unknown")
    if is_live:
        _write_cache(cache_file, {"last_updated": time_label, "data": data})
    return {"data": data, "is_live": is_live, "reason": reason, "time": time_label}


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
