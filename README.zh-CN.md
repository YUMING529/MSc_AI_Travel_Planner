# MSc AI Travel Planner

[English](README.md) | **简体中文**

开始新任务前，请先阅读 [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md)，了解项目范围、MVP、MoSCoW 需求、原型限制与开发约定。

## 项目简介

本项目是 MSc IT 学位项目，构建了一个 AI 辅助旅行规划原型，通过 React 界面收集旅行需求，由 Python/Flask 后端调用 LLM API，并在校验和结构化处理后展示规划结果。

## 项目目标

探索大语言模型在旅行规划场景中的应用，逐步完成从用户输入、行程生成、输出校验到结果展示的完整流程，并通过实验记录支持项目评估与论文写作。

## 当前实现与架构

截至 2026-10-21，已接入 Qwen 与 Open-Meteo 天气，支持英国 17 城、1–14 天、1–50 人，以及浏览器保存。

```text
React → Flask 输入校验 → 天气预报 → Qwen 行程生成
      → 长行程全局分配景点、并行补充详情 → 结构/费用/时间间隔/去重校验 → 结果与保存
```

本轮回归：44 项后端测试、3 项前端测试及生产构建通过；检查 360/390/768/1440 四种宽度。2026-10-22 实测 London 14 天约 99 秒、Manchester 7 天约 51 秒，均未检测到重复地点（少量案例，不代表稳定成功率）。长行程仍是 AI 估算，名称去重不能替代景点事实和实际路线核验。

**启动和交付请看 [Delivery](docs/Delivery.md)，测试证据见 [Testing](docs/Testing-2026-10-21.md)。** 本机可双击 Start-TripMind.command，或运行 `.venv/bin/python scripts/start.py --preview`。

配置步骤见 [backend/README.md](backend/README.md)，模板为 `backend/.env.example`。克隆仓库后请自行复制模板并在本地配置 `backend/.env`（不包含在仓库中）；更改配置后需重启后端。不要上传密钥。

## 固定案例验收

2026-10-22：8 个有效案例全部生成成功，8 个非法输入正确拒绝；平均 41 秒，14 天案例 87 秒。天气条件使用固定样本、模型真实调用，仍有天气安排及保守估价复核项。完整定义、逐例结果与局限见 [验收报告](docs/Acceptance-2026-10-22.md)。小样本结果不代表生产成功率。

## 当前进度

目前已归档的项目材料包括：

- 项目范围文档：`docs/Project_Scope_Document.pdf`
- 背景调研文档：`docs/Background_Survey.pdf`
- LLM 基线实验文档：`docs/LLM_Baseline_Experiment.pdf`
- 技术选型：`docs/Technology_Selection.pdf`（已区分当前实现与计划）
- 架构图：`docs/diagrams/`（已标注已实现及未实现组件）
- 较早的连接原型截图：`frontend/previews/current-2026-10-16/`；旧截图仅作历史参考
- 本次一致性检查：[Progress Audit](docs/Progress_Audit_2026-10-16.md)
- AI 使用记录：[AI Usage Log](docs/AI_Usage_Log.md)（仅记录开发中的重要 AI 使用及人工审阅）
- About、Home、MyTrips 三张界面原型截图：`docs/screenshots/`

另已将 `tripmind` React + Vite 原型完整复制到 `frontend/`，包含源码、模拟数据、预览截图、依赖锁定文件及原项目说明。原项目保留不变。现有实验与验收证据保存在 `experiments/`；独立数据集、会议记录和论文草稿后续再补充；Qwen 成功请求可选择自动记录到 experiments/runs/。基线实验 PDF 统一保留在文档目录，后续实验输入、模型输出及评估记录放入 `experiments/`。

## 文件夹结构

```text
MSc_AI_Travel_Planner/
├── README.md                          # 英文说明
├── README.zh-CN.md                    # 中文说明
├── PROJECT_CONTEXT.md
├── docs/
│   ├── Project_Scope_Document.pdf
│   ├── Background_Survey.pdf
│   ├── LLM_Baseline_Experiment.pdf
│   ├── Technology_Selection.pdf
│   ├── AI_Usage_Log.md
│   ├── Progress_Audit_2026-10-16.md
│   ├── README.md                        # 文档状态与证据索引
│   ├── diagrams/                       # 当前与计划架构
│   ├── archive/                        # 更新前历史材料
│   ├── meetings/                       # 会议记录与会议材料（当前为空）
│   └── screenshots/
│       ├── UI_Prototype_About.png
│       ├── UI_Prototype_Home.png
│       └── UI_Prototype_MyTrips.png
├── frontend/                          # React + Vite 原型（含源码、模拟数据和预览图）
├── backend/                           # Flask API、输入校验、样例生成和测试
├── experiments/                       # LLM 实验记录与验收证据
├── data/                              # 精选景点与模拟数据（当前为空）
└── dissertation/                      # 学位论文草稿（当前为空）
```

会议笔记与会议材料放入 `docs/meetings/`；会议相关截图及其他项目截图放入 `docs/screenshots/`，建议在文件名中注明日期与用途。

## 运行连接原型

需要 Python 3.10+、Node.js（20.19+ 或 22.12+ 的兼容版本）及 npm；当前验证环境为 macOS。新电脑可先运行 `bash scripts/setup.sh` 安装依赖、构建并测试。

手动安装时，在项目根目录执行以下命令；若 `backend/.env` 不存在，先从 `backend/.env.example` 复制并在本地配置。设置 `TRIP_PROVIDER=sample` 可无密钥演示；设置 `TRIP_PROVIDER=qwen` 并填写密钥可调用真实模型。然后启动后端：

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements.txt
.venv/bin/python -m flask --app backend.app run --host 127.0.0.1 --port 5001
```

另开终端启动前端：

```sh
cd frontend
npm ci
npm run dev
```

打开 Vite 显示的地址（通常为 http://127.0.0.1:5173）。前端通过 Vite 代理访问 Flask；sample 模式无需密钥，qwen 模式需在后端配置百炼 API Key。两项服务都需要运行；Flask 不可用时界面显示重试提示。

验证：

```sh
.venv/bin/python -m unittest discover -s backend/tests -v
cd frontend
npm test
npm run build
```

Qwen 当前支持 17 个英国城市、1–14 天、GBP、手动输入 1–50 人；离线样例仍限定 London 两天 1–4 人；过去日期也可用于样例演示。预算与人数经过服务端校验，超预算会显示提醒。模型会依据日期生成，但不会核实当天开放情况；sample 模式兴趣仅高亮、备注仅保留；qwen 模式将兴趣与备注发送给模型参与生成。保存仍使用浏览器 localStorage。没有账户或服务端行程存储；真实调用验证记录见上述验收报告。

接口说明见 [backend/README.md](backend/README.md)。已加入 Qwen provider、输出校验和可选实验记录；下一步进行多组真实输出质量评估。

2026-10-21 扩展验证：Manchester 6 人 3 天、Cardiff 8 人单日、London 3 人 12 天真实生成均通过；12 天最终耗时 69.2 秒。Cardiff 保存并刷新读取通过。完整记录见 experiments/expanded-2026-10-21/README.md。

## 天气功能

默认从 Open-Meteo 获取日期可用的日预报，帮助 Qwen 推荐室内/室外活动并提供室内备选。无需额外 API Key；设置 WEATHER_ENABLED=false 可关闭。预报超范围或服务不可用时仍生成行程。结果页显示数据来源、获取时间；保存的预报不会自动刷新。详见 backend/README.md。

## 使用限制

本项目是本地学术原型。景点真实性、实际价格、营业时间、路线可行性与天气适配仍需独立核验；名称去重不等于完整的地理实体识别，也不保证方案始终在预算内。清除浏览器数据可能导致已保存行程丢失。GitHub 公开源码不代表应用已部署为在线服务。
