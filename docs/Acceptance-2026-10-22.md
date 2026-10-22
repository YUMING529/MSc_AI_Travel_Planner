# 最终版本固定案例验收（2026-10-22）

## 方法与范围

- 模型：qwen-plus；提示词版本：qwen-travel-v6。每个有效案例只运行一次；失败不重跑替换。
- 真实 Qwen，调用 Flask 生成接口；天气 HTTP 返回值采用固定样本，并冻结天气时钟至 2026-10-22（英国时间），实际执行时间单独记录。
- 顺序执行案例，长行程内部按应用逻辑并行；应用内置输出修正仍启用，包含在耗时中。耗时为后端完整生成接口时间，不包含浏览器渲染。
- 运行前后对后端代码和测试脚本做 SHA-256 比较，确认同一版本。清单、逐例响应、校验日志、CSV 和汇总全部保留。
- 固定的是输入和天气条件，不是模型输出；模型随机性和供应商版本变化仍会影响复跑结果。

## 汇总

- HTTP 生成成功：**8/8（100%）**。
- 结构与一致性检查通过：**8/8**。
- 非法输入正确拒绝：**8/8**，未调用模型或天气服务。
- 有效案例耗时（包含失败）：平均 **41.0 秒**；中位数 **37.6 秒**；最长 **86.6 秒**。
- 代码冻结检查：通过。
- 这是小样本验收通过比例，不能推断生产成功率；输入拒绝率没有混入生成成功率。

## 固定案例结果

| 编号 | 城市 | 天数 | 人数 | 整团预算 | 天气样本 | HTTP | 秒 | 一致性检查 | 预计费用 |
|---|---|---:|---:|---:|---|---:|---:|---|---:|
| C01 | London | 1 | 1 | £500 | 晴天 | 200 | 19.4 | 通过 | £83 |
| C02 | Edinburgh | 2 | 2 | £600 | 大雨 | 200 | 31.1 | 通过 | £422 |
| C03 | Manchester | 7 | 3 | £2,200 | 不确定/混合 | 200 | 53.7 | 通过 | £1,389 |
| C04 | London | 14 | 2 | £4,000 | 晴雨交替 | 200 | 86.6 | 通过 | £3,196 |
| C05 | Cardiff | 1 | 50 | £1 | 强风 | 200 | 17.7 | 通过 | £1,575 |
| C06 | Belfast | 3 | 8 | £100,000 | 天气超时 | 200 | 41.9 | 通过 | £2,192 |
| C07 | Bath | 2 | 4 | £800 | 预报范围外 | 200 | 33.4 | 通过 | £622.0 |
| C08 | York | 4 | 1 | £500 | 部分日期有预报 | 200 | 44.0 | 通过 | £335.5 |

## 检查定义

- 日期齐全、输出结构合法、活动时间不重叠、相邻活动留足模型估算的交通分钟。
- 景点名称去重及长行程每日分配一致；分类费用覆盖已列明活动的整团金额，总额/超预算标记/超预算警告一致。
- 天气快照保持后台样本，天气原因由后台规则提供，室外或混合活动有室内备选。
- 天气适配只额外记录坏天气日的室外/混合活动，作为人工复核项；不会把“有备选”直接视为活动安排最优。活动室内外属性是模型自报，未逐地点核实。

## 发现与复核项

- **C02 坏天气安排需复核**：Edinburgh Castle。不等同于硬性校验失败，应结合室内备选和实际开放条件判断。
- **C03 保守估价**：1 unallocated optional stops were omitted. Category allowances remain conservative estimates; travel estimates retain the original route.
- **C04 保守估价**：1 unallocated optional stops were omitted. Category allowances remain conservative estimates; travel estimates retain the original route.
- **C05 坏天气安排需复核**：St Fagans National Museum of History。不等同于硬性校验失败，应结合室内备选和实际开放条件判断。
- **C05 超预算**：估计 £1,575，预算 £1；超预算提示检查通过。预算不足不是 HTTP 生成失败，应用仍不保证优化到预算以内。
- **C08 保守估价**：1 unallocated optional stops were omitted. Category allowances remain conservative estimates; travel estimates retain the original route.

## 配套检查

- 后端单元测试：44 项通过；前端单元测试：3 项通过；生产构建：passed。

- 独立真实 Open-Meteo 检查：available，耗时 2.266 秒；London，2026-10-23 至 2026-10-25。该结果不计入固定天气案例成功率。

## 局限与后续用途

- 没有核实真实票价、营业时间、交通路线、地理实体别名或备选活动质量，也没有模拟真实 iOS/Android 浏览器。
- 天气固定样本可复现边界，不等于实时天气服务稳定性；独立的真实天气 smoke test 单独保存，不计入固定案例成功率。
- 极端人数和预算属于边界校验，不证明具体餐厅或景点能承接该规模。
- 可用作项目验收证据和后续版本对照；研究层面的稳定性评估应对相同案例多次重复并扩大样本，不能仅凭本轮报“100%可靠”。

## 复现与证据

在项目根目录执行（会调用真实 Qwen 并产生费用；输出目录必须尚不存在）：

```sh
.venv/bin/python scripts/run_acceptance.py --live --output experiments/acceptance-new-run
.venv/bin/python scripts/summarize_acceptance.py experiments/acceptance-new-run docs/Acceptance-new-run.md
```

- 本轮目录：experiments/acceptance-2026-10-22/run-01。
- manifest.json：固定输入、天气时钟、模型配置名称、源码指纹。
- C01.json–C08.json：逐例实际响应、耗时、检查结果及详情校验日志。
- results.csv / results.json / summary.json：汇总数据；invalid-inputs.json：拒绝输入的结果。
- 密钥没有写入报告、请求记录或清单。
