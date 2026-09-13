# JKT48 Global Exclusive Monitor

A Streamlit dashboard for monitoring JKT48 Global Exclusive event availability, sales progress, revenue capture, and shareable member/session reports.

This project is built as an operational tracker: it polls public event data, falls back to local snapshots when upstream access is unavailable, and provides an admin-only capture workflow for sharing selected dashboard or statistics views.

## Features

- Live JKT48 Global Exclusive event and session monitoring.
- Category, event, member search, date, and availability filters.
- Event-level totals: total tickets, sold, remaining, sold rate, captured revenue, and potential revenue.
- Member, generation, and team ranking statistics.
- Responsive statistics dialog with compact mobile member cards.
- Admin-only image capture for dashboard cards and statistics rankings.
- Waiting Room mitigation support through temporary Cloudflare cookie input.
- Local runtime cache and bundled fallback snapshots for upstream interruptions.

## Tech Stack

- Python
- Streamlit
- `curl-cffi` with browser impersonation fallback
- `requests`
- Vanilla HTML/CSS/JavaScript inside Streamlit components
- Python `unittest`

## Project Structure

```text
.
|-- app.py                    # Streamlit entry point
|-- core/
|   |-- api.py                # JKT48 API access, cache, fallback, Waiting Room handling
|   |-- refresh.py            # Refresh interval and sales-window helpers
|   `-- stats.py              # Ticket, revenue, grouping, and ranking calculations
|-- data/
|   |-- member_metadata.csv   # Member generation/team metadata
|   `-- fallback/             # Bundled event detail snapshots
|-- ui/
|   |-- components.py         # Dashboard cards, share controls, statistics dialog
|   |-- styles.py             # Streamlit CSS shell
|   `-- tokens.css            # Design tokens
|-- assets/                   # SVG assets
|-- tests/                    # Unit tests
|-- worker/                   # Optional Cloudflare Cron → Telegram close snapshot
`-- requirements.txt
```

## Local Setup

1. Create and activate a virtual environment.

```bash
python -m venv .venv
.venv\Scripts\activate
```

2. Install dependencies.

```bash
pip install -r requirements.txt
```

3. Add local Streamlit secrets.

Create `.streamlit/secrets.toml`:

```toml
ADMIN_KEYS = ["replace-with-your-local-admin-key"]
```

4. Run the app.

```bash
streamlit run app.py
```

Open the admin view with:

```text
http://localhost:8501/?akses=replace-with-your-local-admin-key
```

## Optional Environment Variables

```text
JKT48_COOKIE
```

Use this only when Cloudflare Waiting Room mitigation is required. The app also provides an admin-only dialog to set a temporary runtime cookie without storing it in the repository.

## Testing

Run all tests:

```bash
python -m unittest discover -s tests -v
```

Run a quick syntax check:

```bash
python -m compileall app.py core ui tests
```

## Deployment Notes

- Configure `ADMIN_KEYS` in the deployment secret manager, not in the repository.
- Keep `.streamlit/secrets.toml` local only.
- Ensure `data/member_metadata.csv` is updated when member generation or team data changes.
- The app can continue showing cached or fallback data when the live upstream API is blocked or unavailable.
- Admin share/capture features depend on browser clipboard support.
- Optional `worker/` can store and send a Telegram JSON snapshot exactly one minute before sales close, without an open Streamlit session. See [worker/README.md](worker/README.md).

## Disclaimer

This is an unofficial community dashboard and is not affiliated with JKT48 or its official operators. Data availability depends on upstream public endpoints and local fallback snapshots.
