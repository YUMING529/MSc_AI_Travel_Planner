# TripMind Setup and Delivery

Updated: 23 October 2026 (English translation). This delivery supports a local MSc project demonstration. It is not a production deployment.

## Run a local demonstration

On macOS, double-click **Start-TripMind.command** in the project root, or run the following from the project root:

```sh
.venv/bin/python scripts/start.py --preview
```

Open http://127.0.0.1:5173. Keep the terminal open; press Ctrl+C to stop both the frontend and backend. If a required port is already in use, the launcher reports an error without terminating the existing service. Omit `--preview` for development mode. After changing frontend source files, run `npm run build` in `frontend/` before using preview mode.

If credentials are already configured on your machine, you do not need to enter them again. Credentials are not included in the repository or source archive. Restart the services after editing `backend/.env`. The `/api/health` endpoint confirms that the API is running and reports the configured provider mode; it does not check Qwen connectivity or available credit.

## Install on a new computer

Requirements: Python 3.10+, a Node.js version compatible with Vite (20.19+ or 22.12+), npm and an internet connection. The recorded verification environment was macOS / Python 3.14.7 / Node 26.12.0. Other operating systems have not been verified. The setup script targets macOS/Linux.

1. Clone the repository or extract the source archive into a writable directory, then open a terminal in that directory.
2. Run `bash scripts/setup.sh` to create a virtual environment, install dependencies from the lockfiles, build the frontend and run tests. An existing `backend/.env` file will not be overwritten.
3. Edit `backend/.env` locally and set your Alibaba Cloud Bailian `DASHSCOPE_API_KEY`. Ensure that the API key and endpoint belong to the same region. Keep credentials in the backend configuration; never put them in frontend code or upload them.
4. Run the launch command above and open http://127.0.0.1:5173.

To demonstrate the application without a model API key, run:

```sh
.venv/bin/python scripts/start.py --preview --sample
```

Sample mode supports London, two consecutive days and 1–4 travellers. It does not call Qwen. In the current implementation, sample generation also skips the weather lookup. In Qwen mode, weather availability depends on `WEATHER_ENABLED`, the forecast window and service availability; unavailable forecasts do not prevent itinerary generation.

## Supported scope and acceptance checks

Qwen mode supports 17 UK cities, trips of 1–14 days inclusive, groups of 1–50 travellers and a whole-group budget in GBP. Itemised activity costs are per person; category totals are for the whole group. Travel to and from the destination is excluded from the budget. If dates fall outside the forecast window or the weather request fails, the interface indicates that weather is unavailable and still allows itinerary generation.

For trips longer than three days, Qwen first generates a global venue allocation with two main venues per day. After checking name uniqueness, the system expands the plan in segments of up to three days, with up to three segments generated in parallel. Each segment adds activity times, meals, costs and weather guidance, and must cover the venues allocated to its dates.

Extra standalone stops introduced by the model are removed. The system preserves travel estimates through the omitted stops and checks the resulting time gaps again. Original category allowances remain as conservative estimates, with a visible warning. Missing main venues or combined activities that cannot be safely separated trigger an output repair attempt.

A 14-day itinerary normally requires six model calls: one venue allocation and five detail segments. Each call allows one output repair attempt, giving a maximum of twelve calls. Each network attempt has a timeout of up to 120 seconds within an approximately 420-second generation budget; the browser timeout is 450 seconds. Quota limits, network problems or unsuccessful output repairs can still cause generation to fail.

If validation still detects duplicate venues, the request fails explicitly. Name checks include some common aliases but do not establish geographic entity identity. Estimates above the budget are clearly flagged; the system does not guarantee a plan within budget.

Suggested acceptance walkthrough:

1. Generate an itinerary.
2. Check the number of days and estimated costs.
3. Select **Save Trip**.
4. Refresh the page.
5. Open **My Trips**, then select **View Plan**.

Saved trips exist only in the current browser's localStorage and may be lost when browser data is cleared. `localhost` and `127.0.0.1` use separate storage origins; consistently use http://127.0.0.1:5173.

## Delivery contents

`dist/TripMind-source.zip` contains rebuildable frontend and backend source, dependency lockfiles, tests, launch scripts and selected documentation. To regenerate the archive, run:

```sh
python3 scripts/package_delivery.py
```

The archive excludes credentials, the virtual environment, `node_modules`, personal browser saves and raw model logs. Recipients must install dependencies and configure their own credentials. This is a source archive, not a desktop application that runs without installation.

The final fixed-case evaluation is documented in [Acceptance-2026-10-22.md](Acceptance-2026-10-22.md), including observed acceptance results, timings, issues and reproduction commands. Earlier regression evidence is in [Testing-2026-10-21.md](Testing-2026-10-21.md). These reports are currently in Chinese. Screenshots and local synthetic test inputs and outputs are stored in `experiments/hardening-2026-10-21/` in the repository and are not included in the source archive.

Public deployment would require a production WSGI server, TLS, access control, rate limiting and cost protection, deployment configuration and further verification. The current launcher binds services to localhost only. Venue facts, prices, opening hours, routes and indoor/outdoor classifications still require independent review.
