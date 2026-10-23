# MSc AI Travel Planner

**English** | [简体中文](README.zh-CN.md)

Before starting development, read [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md) (Chinese) for the project scope, MVP, MoSCoW requirements, prototype limitations and development conventions.

## Overview

TripMind is an AI-assisted travel planning prototype developed as an MSc IT project. A React interface collects travel preferences, and a Python/Flask backend calls an LLM API, validates and normalises its output, and returns a structured itinerary.

## Project aim

Explore the use of large language models in travel planning through a complete workflow from user input and itinerary generation to output validation and presentation. Experiment records support project evaluation and dissertation writing.

## Current implementation and architecture

As of 21 October 2026, the application integrates Qwen and Open-Meteo weather forecasts, supports 17 UK cities, trips of 1–14 days and groups of 1–50 travellers, and saves trips in the browser.

```text
React → Flask input validation → Weather forecast → Qwen itinerary generation
      → Global venue allocation and parallel expansion for longer trips
      → Structure / cost / travel-gap / duplicate checks → Display and save
```

Regression evidence includes 44 passing backend tests, 3 passing frontend tests and a successful production build, plus layout checks at widths of 360, 390, 768 and 1440 pixels. Separate live checks on 22 October 2026 generated a 14-day London trip in approximately 99 seconds and a 7-day Manchester trip in approximately 51 seconds, with no duplicate venues detected. These are small samples, not reliability estimates. Generated plans remain AI estimates; name-based duplicate checks do not verify venue facts or real routes.

See [Delivery](docs/Delivery.md) for installation and launch instructions and [Testing](docs/Testing-2026-10-21.md) for evidence (the testing report is in Chinese). Once dependencies and the frontend build are ready, launch with `.venv/bin/python scripts/start.py --preview`, or double-click `Start-TripMind.command` on macOS.

Configuration is documented in [backend/README.md](backend/README.md) (English). After cloning, copy `backend/.env.example` to `backend/.env` if it does not exist, and configure it locally. The repository does not include credentials. Restart the backend after configuration changes. Never upload API keys.

## Fixed-case acceptance evaluation

On 22 October 2026, all 8 valid cases generated successfully, and all 8 invalid inputs were correctly rejected. Mean generation time was approximately 41 seconds; the 14-day case took approximately 87 seconds. Tests used real Qwen calls with fixed weather samples. Weather suitability and conservative cost estimates still require review in some cases. See the [acceptance report](docs/Acceptance-2026-10-22.md) (Chinese) for definitions, individual results and limitations. This small sample does not establish a production success rate.

## Project materials and progress

Available materials include:

- Project scope: `docs/Project_Scope_Document.pdf`.
- Background survey: `docs/Background_Survey.pdf`.
- LLM baseline experiment: `docs/LLM_Baseline_Experiment.pdf`.
- Technology selection: `docs/Technology_Selection.pdf`, distinguishing implemented and planned features.
- Architecture diagrams: `docs/diagrams/`, identifying implemented and planned components.
- Earlier connected-prototype screenshots: `frontend/previews/current-2026-10-16/`; older screenshots are historical references.
- [Progress audit](docs/Progress_Audit_2026-10-16.md).
- [AI usage log](docs/AI_Usage_Log.md), recording significant development assistance and human review status.
- Early About, Home and My Trips UI prototypes: `docs/screenshots/`.

The original React + Vite prototype was copied into `frontend/`, including source, sample data, preview images and the dependency lockfile. Experiment and acceptance evidence is stored in `experiments/`. An independent dataset, meeting records and dissertation drafts remain to be added. Successful Qwen requests can optionally be recorded in `experiments/runs/`; these local logs are excluded from version control. Baseline PDF reports remain under `docs/`.

## Repository structure

```text
MSc_AI_Travel_Planner/
├── README.md                    # English overview
├── README.zh-CN.md              # Chinese overview
├── PROJECT_CONTEXT.md           # Shared development context (Chinese)
├── docs/                        # Scope, reports, diagrams and screenshots
│   ├── Delivery.md
│   ├── Testing-2026-10-21.md
│   ├── Acceptance-2026-10-22.md
│   ├── AI_Usage_Log.md
│   ├── diagrams/
│   ├── archive/
│   └── screenshots/
├── frontend/                    # React + Vite application and frontend tests
├── backend/                     # Flask API, providers, validation and tests
├── scripts/                     # Setup, launch, packaging and evaluation tools
└── experiments/                 # Experiment records and acceptance evidence
```

Local placeholders `data/`, `dissertation/` and `docs/meetings/` are currently empty and are not tracked by Git. Use them for curated data, dissertation drafts and meeting materials when available. Date screenshot filenames where possible.

## Run locally

Requirements: Python 3.10+, a compatible Node.js release (20.19+ or 22.12+) and npm. The current verification environment is macOS; other operating systems have not been verified. On a new machine, `bash scripts/setup.sh` installs dependencies, builds the frontend and runs tests.

For manual installation, run the following from the project root. Before launching, create `backend/.env` from `backend/.env.example` if it does not exist. Set `TRIP_PROVIDER=sample` for a demo without credentials, or `TRIP_PROVIDER=qwen` with a Bailian API key for real model calls.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements.txt
.venv/bin/python -m flask --app backend.app run --host 127.0.0.1 --port 5001
```

In a second terminal, start the frontend:

```sh
cd frontend
npm ci
npm run dev
```

Open the address shown by Vite, normally http://127.0.0.1:5173. The frontend proxies API requests to Flask. Both services must be running; the interface shows a retry message when the backend is unavailable. Real Qwen calls may incur provider charges. The launcher binds services to localhost for local demonstration.

Run verification from the project root:

```sh
.venv/bin/python -m unittest discover -s backend/tests -v
cd frontend
npm test
npm run build
```

Qwen mode supports 17 UK cities, 1–14 inclusive days, GBP and 1–50 travellers. Sample mode is limited to London, two consecutive days and 1–4 travellers. Past dates are allowed for experiments. Budget and group size are validated on the server; estimates over budget produce a warning rather than a guarantee of an affordable plan. Opening hours are not verified. In sample mode, interests are highlighted and notes are retained; in Qwen mode, both are sent to the model to inform generation. Trips are stored in browser localStorage, with no accounts or server-side trip storage.

See [backend/README.md](backend/README.md) for API details, output validation and optional experiment recording. Further repeated trials and manual quality assessment are needed to evaluate reliability.

Additional live checks on 21 October 2026 covered Manchester (6 travellers, 3 days), Cardiff (8 travellers, 1 day) and London (3 travellers, 12 days). The final 12-day run took 69.2 seconds. Saving and reloading the Cardiff trip also passed. Records: [expanded verification](experiments/expanded-2026-10-21/README.md).

## Weather-aware planning

Open-Meteo supplies daily forecasts for supported dates to help Qwen suggest indoor/outdoor activities and indoor alternatives. No additional weather API key is required. Set `WEATHER_ENABLED=false` to disable it. Generation continues when dates are outside the forecast window or the weather service is unavailable. Results display the source and retrieval time; saved forecasts are snapshots and do not refresh automatically. See [backend/README.md](backend/README.md) for details.

## Limitations

This is a local academic prototype. Venue existence, actual prices, opening hours, route feasibility and weather suitability require independent verification. Name-based deduplication is not full geographic entity resolution, and plans are not guaranteed to stay within budget. Browser storage can be lost when browser data is cleared. Public hosting of the source code does not deploy the application as an online service.
