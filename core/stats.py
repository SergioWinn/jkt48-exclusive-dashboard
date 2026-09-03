import csv
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent
MEMBER_METADATA_FILE = PROJECT_ROOT / "data" / "member_metadata.csv"


def _as_int(value):
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _key(value):
    return str(value or "").strip().lower()


def format_rupiah(value):
    return f"Rp {int(value):,}".replace(",", ".")


def format_revenue_pair(revenue, potential_revenue, separator="\n/ "):
    return f"{format_rupiah(revenue)}{separator}{format_rupiah(potential_revenue)}"


def load_member_metadata(path=MEMBER_METADATA_FILE):
    if not Path(path).exists():
        return {}

    with Path(path).open(encoding="utf-8-sig", newline="") as file:
        metadata = {}
        for row in csv.DictReader(file):
            full_name = str(row.get("full_name") or "").strip()
            if not full_name:
                continue
            metadata[_key(full_name)] = {
                "full_name": full_name,
                "nickname": str(row.get("nickname") or "").strip(),
                "status": str(row.get("status") or "").strip(),
                "generation": str(row.get("generasi") or "").strip(),
            }
    return metadata


def _empty_bucket(name):
    return {
        "name": name,
        "sold": 0,
        "remaining": 0,
        "capacity": 0,
        "revenue": 0,
        "potential_revenue": 0,
        "members": set(),
    }


def _add_ticket(bucket, sold, remaining, price, member_name=None):
    bucket["sold"] += sold
    bucket["remaining"] += remaining
    bucket["capacity"] += sold + remaining
    bucket["revenue"] += sold * price
    bucket["potential_revenue"] += (sold + remaining) * price
    if member_name:
        bucket["members"].add(member_name)


def _finalize(bucket):
    capacity = bucket["capacity"]
    bucket["sold_rate"] = (bucket["sold"] / capacity * 100) if capacity else 0.0
    bucket["members"] = sorted(bucket["members"])
    return bucket


def _ranked_buckets(buckets):
    ranked = sorted(
        (_finalize(bucket) for bucket in buckets.values()),
        key=lambda bucket: (-bucket["sold_rate"], -bucket["sold"], bucket["name"]),
    )
    previous_rate = None
    previous_rank = 0
    for index, bucket in enumerate(ranked, start=1):
        rate = round(bucket["sold_rate"], 10)
        if rate != previous_rate:
            previous_rank = index
            previous_rate = rate
        bucket["rank"] = previous_rank
    return ranked


def calculate_event_stats(event, member_metadata=None):
    member_metadata = member_metadata or {}
    price = _as_int(event.get("default_price"))
    summary = _empty_bucket("Event")
    by_member = {}
    by_generation = {}
    by_team = {}
    details = [detail for session in event.get("session", []) for detail in session.get("session_detail", [])]
    sales_data_available = bool(details) and all(
        "tickets_sold" in detail and "available_quota" in detail for detail in details
    )

    for detail in details:
        member_name = str(detail.get("jkt48_member_name") or "Unknown").strip() or "Unknown"
        sold = _as_int(detail.get("tickets_sold"))
        remaining = _as_int(detail.get("available_quota"))
        metadata = member_metadata.get(_key(member_name), {})
        generation = metadata.get("generation") or "Unknown"
        team = metadata.get("status") or "Unknown"

        _add_ticket(summary, sold, remaining, price, member_name)
        member_bucket = by_member.setdefault(member_name, _empty_bucket(member_name))
        member_bucket["generation"] = generation
        member_bucket["team"] = team
        _add_ticket(member_bucket, sold, remaining, price)
        _add_ticket(by_generation.setdefault(generation, _empty_bucket(generation)), sold, remaining, price, member_name)
        _add_ticket(by_team.setdefault(team, _empty_bucket(team)), sold, remaining, price, member_name)

    return {
        "summary": _finalize(summary),
        "members": _ranked_buckets(by_member),
        "generations": _ranked_buckets(by_generation),
        "teams": _ranked_buckets(by_team),
        "sales_data_available": sales_data_available,
    }


def table_rows(buckets, include_members=False):
    rows = []
    for bucket in buckets:
        row = {
            "Rank": bucket["rank"],
            "Name": bucket["name"],
            "Sold": f"{bucket['sold']:,}",
            "Remaining": f"{bucket['remaining']:,}",
            "Sold %": f"{bucket['sold_rate']:.1f}%",
            "Revenue": format_revenue_pair(bucket["revenue"], bucket["potential_revenue"]),
        }
        if "generation" in bucket:
            row["Generation"] = bucket["generation"]
        if "team" in bucket:
            row["Team"] = bucket["team"]
        if include_members:
            row["Members"] = ", ".join(bucket.get("members") or ["-"])
        rows.append(row)
    return rows
