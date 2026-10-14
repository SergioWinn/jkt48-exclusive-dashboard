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
|-- app.py                    # Streamlit ASGI entry point and authenticated stock route
|-- dashboard.py              # Dashboard UI
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

Use this only when Cloudflare Waiting Room mitigation is required. Cookies are configured through the environment; the dashboard has no cookie input dialog.

## Admin JSON import

In the admin view, select an event and open **Tempel JSON**. Open the detail API link in your browser and paste its complete successful JSON response into **JSON detail**. Optionally paste the bonus API response into **JSON bonus**, then choose **Simpan snapshot**. The detail must match the selected event code.

Imports are shown as cached data, dated at import time, and shared through the runtime snapshot. Automatic API refresh continues. Invalid input or a failed write leaves the previous snapshot intact. Imported snapshots are local to the running instance and do not provide persistent storage across redeployments.

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

### Restock relay for the Telegram notifier

`app.py` serves the dashboard and a separate `POST /api/restock` route using `st.App`. The route runs without an open dashboard tab. Set `RESTOCK_RELAY_TOKEN` in Streamlit Community Cloud **Settings > Secrets** and configure the same secret in the Cloudflare notifier. A local copy of the generated setting is in the ignored `.streamlit/restock-relay.secret.toml`; do not commit it.

Cloudflare calls this route every 5 minutes while monitoring is ON. Send `Authorization: Bearer <RESTOCK_RELAY_TOKEN>` and JSON containing `categories` and `trackedEventCodes`. The relay discovers recent/tracked events, collects successful bonus API responses with the dashboard's browser-compatible HTTP client, and uses its Chromium fallback when available. It does not substitute bundled snapshots for failed live requests; Cloudflare retains its last snapshot on failure.

Collection runs in a worker thread, is limited to one request at a time and 30 events, and has a 100-second budget. This is independent of the dashboard's 5-second UI refresh. Community Cloud may hibernate an inactive app; continuous operation and the effect of scheduled endpoint traffic must be verified after deployment. A failed relay call leaves monitoring ON but cannot generate fresh notifications.

- Configure `ADMIN_KEYS` in the deployment secret manager, not in the repository.
- Keep `.streamlit/secrets.toml` local only.
- Ensure `data/member_metadata.csv` is updated when member generation or team data changes.
- The app can continue showing cached or fallback data when the live upstream API is blocked or unavailable.
- Keep a `data/fallback/<event-code>.json` detail snapshot for every event in the bundled catalogue. These files must ship with the app so a fresh deployment can display sessions even when the API is blocked.
- `.runtime_cache` is local, ignored by Git, and may be lost when the hosting instance is replaced. Bundled snapshots retain their original update times; preserving the latest live data across instance replacement requires persistent external storage.
- Admin share/capture features depend on browser clipboard support.

## Disclaimer

This is an unofficial community dashboard and is not affiliated with JKT48 or its official operators. Data availability depends on upstream public endpoints and local fallback snapshots.
