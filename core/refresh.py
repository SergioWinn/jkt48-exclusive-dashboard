from datetime import datetime, timedelta

ACTIVE_REFRESH_SECONDS = 5
RECOVERY_REFRESH_SECONDS = 15
CLOSED_REFRESH_SECONDS = 60


def _parse_datetime(value):
    if not value:
        return None
    try:
        is_utc = str(value).endswith("Z")
        parsed = datetime.fromisoformat(str(value).replace("Z", "").split(".")[0])
        return parsed + timedelta(hours=7) if is_utc else parsed
    except (TypeError, ValueError):
        return None


def get_sales_window(event):
    general_period = next(
        (
            period
            for period in event.get("sales_period", [])
            if period.get("label", "").lower() == "general"
        ),
        None,
    )
    if general_period:
        return (
            _parse_datetime(general_period.get("start_date")),
            _parse_datetime(general_period.get("end_date")),
        )
    return None, _parse_datetime(event.get("valid_date_to"))


def is_event_closed(event, now_wib):
    _, end_date = get_sales_window(event)
    return bool(end_date and now_wib >= end_date)


def get_detail_refresh_interval(event, is_live, now_wib):
    if not is_live:
        return RECOVERY_REFRESH_SECONDS

    _, end_date = get_sales_window(event)
    if end_date and now_wib >= end_date:
        return CLOSED_REFRESH_SECONDS
    return ACTIVE_REFRESH_SECONDS
