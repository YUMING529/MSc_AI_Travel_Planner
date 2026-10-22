# AI Usage Log

**Personal review status confirmed by the project owner on 16 October 2026.**

Significant AI use during software development only. Historical dates below are retrospective estimates. The project owner confirmed all four personal-review entries on 16 October 2026; specific review actions are not recorded here.

| Date | Tool | Development task / AI assistance | My review / modification |
| --- | --- | --- | --- |
| 10 Oct 2026 | ChatGPT | Helped refine the system architecture and component boundaries. | Confirmed by the project owner on 16 Oct 2026. |
| 11 Oct 2026 | ChatGPT | Compared technologies for the MVP. | Confirmed by the project owner on 16 Oct 2026. |
| Before or on 9 Oct 2026 (exact date unconfirmed) | Codex | Assisted with implementing the React front-end prototype. | Confirmed by the project owner on 16 Oct 2026. |
| 14 Oct 2026 | ChatGPT / Codex | Assisted with Flask API planning and implementation, input validation and front-end integration. | Confirmed by the project owner on 16 Oct 2026. |

Append a short row for significant design, coding, debugging, testing or development-related prompt/schema work. Record only personal review or modifications actually completed. Exclude general Q&A, research summaries, document preparation, folder organisation and log maintenance.

Audit note (16 October 2026): the React prototype was already copied and built in this project on 9 October, so the former 12 October implementation date was inconsistent with the recorded sequence. Other retrospective dates still need owner confirmation. All four personal-review statuses were subsequently confirmed by the project owner on 16 October 2026. This confirmation does not establish exact historical dates or document specific personal checks; automated agent checks do not constitute the owner's review.

- 2026-10-21 · Codex：实现 Qwen provider、输出校验、配置模板、前端来源区分和模拟测试；13 个自动测试及构建通过；浏览器确认缺少密钥时显示配置错误，真实 API 联调及人工审阅待确认。

- 2026-10-21 · Codex：使用用户本地配置执行一次真实 Qwen 浏览器联调，验证生成、保存、刷新后读取，保存页面证据；发现事实/餐饮覆盖仍待评估，人工审阅待确认。

- 2026-10-21 · Codex：按用户反馈扩展城市/天数/人数，排查真实费用校验失败和长输出超时；加入费用差额披露、一次输出修正及分段生成；18 个测试、构建和 1/3/12 天真实样例通过，人工审阅待确认。

- 2026-10-21 · Codex：实现 Open-Meteo 日预报、降级/缓存、Qwen 天气输入和室内备选、天气卡片与快照保存；26 个自动测试及构建通过，真实天气+Qwen 浏览器生成和保存读取通过，人工审阅待确认。

- 2026-10-21 · Codex：按用户要求执行边界回归与真实 Qwen 长行程测试；增加景点名称去重及顺序修复、交通间隔与分类费用下限，修复存档和手机布局，提供本地启动与源代码交付脚本。35 个后端与 3 个前端测试通过；真实结果和限制见 docs/Testing-2026-10-21.md。人工审阅待确认。

- 2026-10-21 · Codex：按用户反馈补充 My Trips 删除/撤销、搜索排序和费用对比；通过浏览器验证恢复及刷新持久化、手机布局和构建。人工审阅待确认。

- 2026-10-21 · Codex：按用户要求继续改善长行程，改为生成前共享景点历史，修复餐饮类具名地点绕过去重的问题并减少重复整段生成；40 项后端测试、3 项前端测试及构建通过。真实实验记录见 experiments/long-trip-v5/，人工审阅待确认。

- 2026-10-22 · Codex：v5 顺序排除名单实测失败后，改为 v6 全局分配景点再并行展开，加入额外活动约束及原交通估计保留；44 项后端测试、3 项前端测试与构建通过。最终 London 14 天 99.0 秒、Manchester 7 天 50.6 秒成功，未检测到重复地点；事实准确性未核实，人工审阅待确认。

- 2026-10-22 · Codex：建立最终版本固定验收脚本与报告生成器，冻结代码运行 8 个真实 Qwen / 固定天气案例及 8 个非法输入案例；均通过对应硬性检查，平均 40.977 秒。记录两例坏天气混合活动复核项、三例保守估价和小样本局限；未修改应用代码来替换不理想结果。人工审阅待确认。
