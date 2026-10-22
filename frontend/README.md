> 最新范围：Qwen 支持 17 个英国城市、1–14 天、1–50 人，人数手动输入。结果页和本地保存已同步适配。较早文档和截图中的 London/两天/1–4 人仅对应历史或 sample 模式。

> 2026-10-21 更新：已支持后端 Qwen 与 sample 两种模式，结果标注来源；Qwen 已完成一次真实生成、保存及刷新读取联调。以下早期原型说明涉及固定路线的内容仅适用于 sample 模式。最新配置见 ../backend/README.md。

# TripMind React frontend

Run the Flask API first using the root README, then `npm ci` and `npm run dev` in this folder. Vite proxies `/api` to `http://127.0.0.1:5001`. Build with `npm run build`; `npm run preview` also proxies to the local Flask server.

The original responsive design is retained. Generation and regeneration now use `src/services/trips.js` with a 15-second timeout and visible error messages. The result renders server-provided days and costs. London, consecutive two-day dates, GBP and 1–4 travellers are supported. This is a fixed sample, not live AI. Notes are retained and interests highlight matches but neither changes the route. Saved plans remain in this browser; earlier saved samples are still supported through the legacy fallback data in `src/data/mockTrip.js`.

API contract and limitations: see `../backend/README.md`.

Current full-page screenshots: `previews/current-2026-10-16/`. Previous screenshots are preserved under `previews/archive/` and are not current evidence. See `previews/README.md`.
