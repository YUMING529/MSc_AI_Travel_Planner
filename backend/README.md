# TripMind Flask API

## Qwen setup (2026-10-21)

Install dependencies from the project root:

```sh
.venv/bin/python -m pip install -r backend/requirements.txt
```

Copy `backend/.env.example` to `backend/.env` if it does not exist. Set `DASHSCOPE_API_KEY` locally to your Alibaba Cloud Bailian key. `TRIP_PROVIDER=qwen` enables Qwen; `sample` selects the deterministic offline demo. Missing credentials produce an explicit 503 error, never a sample fallback. Restart Flask after configuration changes. Shell environment variables override `.env`.

Default model: `qwen-plus`, non-thinking JSON Object mode. Default endpoint: Beijing `https://dashscope.aliyuncs.com/compatible-mode/v1`. You can set `QWEN_BASE_URL` to the workspace-specific endpoint shown in your Bailian console. The key and endpoint must belong to the same region. Requests go directly to Alibaba via Python HTTP; no OpenAI account, model or SDK is used.

```sh
.venv/bin/python -m flask --app backend.app run --host 127.0.0.1 --port 5001
```

This is a local development service, with no authentication or production rate limiting. Keep it bound to localhost. Vite proxies `/api` to port 5001.

## Contract

- `GET /api/health`: `{"status":"ok","mode":"qwen"}` (or `sample`). Reports configured mode, not live provider connectivity.
- `POST /api/trips/generate`: normalized preferences in, `{"trip": ...}` out.

```json
{"destination":"London","start":"2026-11-02","end":"2026-11-03","currency":"GBP","budget":500,"travellers":1,"interests":["History","Food"],"notes":"Relaxed pace"}
```

Qwen supports 17 UK cities (see validation.py), GBP, 1–14 inclusive days, 1–50 travellers, finite budget 1–100000, known interest labels, and notes up to 2000 characters. Requests are limited to 16 KiB. Past dates remain allowed for experiments.

The trip contains preferences, an ID, and itinerary fields `mode`, `days`, `costs`, `total`, `checks`, `warnings`. Qwen also returns configured `model` and `promptVersion`. Activity costs are per person; the five category costs are whole-group totals. The server calculates total/budget comparison and always sets `factsVerified=false`.

Qwen output validation checks fields/types, requested dates, 1–8 activities per day, ordered non-overlapping 24h intervals, known tags, nonnegative finite costs, unique categories, and that Food + Activities allowances cover listed activity/meal costs for the group. Qwen v4 also requires canonical places, costCategory and travelMinutes; validates estimated travel gaps; normalizes each cost category to its own itemized group minimum. This does not verify actual routes, prices, opening hours, or preference satisfaction. Qwen v2 excludes travel to/from the destination because no origin is supplied. Lodging covers duration minus one nights, assuming one room per two people. The prompt requires food allowances for every day. Sample mode retains its historical London/two-day/1–4-person scope and rejects other requests.

Provider socket timeout is up to 120 seconds per attempt within an approximately 420-second generation budget; browser timeout is 450 seconds. Output failures receive one repair attempt; auth/quota/network failures are not retried. Trips over three days first request a globally unique allocation of two named venues per date. The server validates date coverage and name uniqueness, then expands segments of at most three days with up to three in parallel. Each expansion must cover exactly the allocated venues on each date; generic meals may be added. Extra standalone stops are removed before validation, preserving estimated travel legs through omitted stops and disclosing conservative unchanged category allowances; missing venues and mixed allocated/unallocated bundles still fail. A 14-day trip needs six normal calls (one allocation and five expansions), at most twelve with one output retry per call, within the shared deadline. Final duplicate checks reject known repeats. Common aliases, punctuation and venue-area suffixes are normalized, but this is not full entity resolution. Segment costs and boundary nights are included in the merge. Output tokens scale with trip length (up to 16384). Safe validation reasons are logged without notes or credentials. Errors use `{"error":{"code":"...","message":"..."}}`: 400 invalid input, 413 oversized input, 415 content type, 502 provider/output errors, 503 missing key/auth/quota/network issues, 504 timeout. Provider error bodies and credentials are not returned to the browser.

## Experiments and verification

`RECORD_LLM_EXPERIMENTS=true` opts into saving successful requests, system prompt, raw response, usage/model metadata and normalized trip to ignored `experiments/runs/`. These contain user notes; no authorization headers or API keys are saved. Failed calls are not recorded yet. Logging failure leaves the trip usable with a warning. Recording is off by default.

```sh
.venv/bin/python -m unittest discover -s backend/tests -v
```

44 tests pass after the 2026-10-21 hardening round (see ../docs/Testing-2026-10-21.md for current live evidence); the following browser evidence is from the earlier integration round, including variable durations, larger groups, bounded repair and segmented merging/night accounting. Qwen unit tests mock HTTP. A separate real browser request succeeded on 2026-10-21 (HTTP 200, GBP 335 total); save, reload and reopen also passed. Evidence: experiments/live-2026-10-21/. This single smoke test does not establish output quality or reliability.

Official references checked on 2026-10-21:
- https://help.aliyun.com/zh/model-studio/compatibility-of-openai-with-dashscope
- https://help.aliyun.com/zh/model-studio/qwen-structured-output

V2 normalization: harmless period aliases and unsupported display tags are normalized. If listed per-person costs times group size exceed Food + Activities, those allowances are raised by the exact shortfall, the total is recomputed, and a visible warning discloses the adjustment. This is an estimate floor, not price verification. Negative/nonfinite values, missing dates and overlapping activity intervals still fail validation.

## Weather-aware planning (2026-10-21)

WEATHER_ENABLED defaults to true. No extra API key is needed. The server queries Open-Meteo using city-centre coordinates for the 17 supported cities, Europe/London timezone, Celsius and km/h. Only coordinates and weather fields are sent to Open-Meteo, never travel notes or Qwen credentials.

A daily forecast snapshot (source, fetchedAt, status and days) is returned as itinerary.weather. Requests outside today through today+15 days skip the network. Missing/null daily fields remain unavailable. Timeout, malformed response and network errors degrade to planning without a forecast. Positive responses are cached in memory per city/UK date for 30 minutes. Network timeout: 8 seconds. Restarting clears the cache.

Product rules: rain probability >=60%, heavy rain, strong wind >=40 km/h or selected storm/snow/ice codes favour indoors. Rain <30%, wind <25 km/h and clear/cloudy codes allow outdoor options; other conditions favour mixed activities. These heuristics are not official weather warnings or safety guarantees.

Weather is fetched once before Qwen generation and supplied to date segments. Qwen v3 adds activity setting, weatherReason and indoorAlternative. Outdoor/mixed alternatives are optional swaps, with unverified cost and availability. The backend supplies forecast numbers directly, never using model-generated weather data. Saved trips retain their original snapshot; generating again fetches a current/cached snapshot. Old trips show Weather not recorded.

Sources: https://open-meteo.com/en/docs and https://open-meteo.com/en/pricing. The free endpoint is for non-commercial use; UI attribution links to Open-Meteo. This is a daily forecast feature, not hourly scheduling or an official weather-alert integration.
