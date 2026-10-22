"""Summarize an existing frozen acceptance run without making API calls."""
import json,sys
from pathlib import Path
root=Path(sys.argv[1]);destination=Path(sys.argv[2])
rows=json.loads((root/'results.json').read_text());summary=json.loads((root/'summary.json').read_text());manifest=json.loads((root/'manifest.json').read_text())
weather={'clear':'晴天','rain':'大雨','mixed':'不确定/混合','alternating':'晴雨交替','wind':'强风','outage':'天气超时','out_of_range':'预报范围外','partial':'部分日期有预报'}
lines=['# 最终版本固定案例验收（2026-10-22）','',
'## 方法与范围','',
f"- 模型：{manifest['model']}；提示词版本：{manifest['promptVersion']}。每个有效案例只运行一次；失败不重跑替换。",
'- 真实 Qwen，调用 Flask 生成接口；天气 HTTP 返回值采用固定样本，并冻结天气时钟至 2026-10-22（英国时间），实际执行时间单独记录。',
'- 顺序执行案例，长行程内部按应用逻辑并行；应用内置输出修正仍启用，包含在耗时中。耗时为后端完整生成接口时间，不包含浏览器渲染。',
'- 运行前后对后端代码和测试脚本做 SHA-256 比较，确认同一版本。清单、逐例响应、校验日志、CSV 和汇总全部保留。',
'- 固定的是输入和天气条件，不是模型输出；模型随机性和供应商版本变化仍会影响复跑结果。',
'','## 汇总','',
f"- HTTP 生成成功：**{summary['generation_success']}/{summary['cases']}（{summary['generation_success_rate']:.0%}）**。",
f"- 结构与一致性检查通过：**{summary['contract_pass']}/{summary['cases']}**。",
f"- 非法输入正确拒绝：**{summary['invalid_inputs_pass']}/{summary['invalid_inputs_total']}**，未调用模型或天气服务。",
f"- 有效案例耗时（包含失败）：平均 **{summary['mean_seconds_all']:.1f} 秒**；中位数 **{summary['median_seconds_all']:.1f} 秒**；最长 **{summary['max_seconds_all']:.1f} 秒**。",
f"- 代码冻结检查：{'通过' if summary['unchanged_sources'] else '失败，不能将所有案例当同一版本'}。",
'- 这是小样本验收通过比例，不能推断生产成功率；输入拒绝率没有混入生成成功率。',
'','## 固定案例结果','',
'| 编号 | 城市 | 天数 | 人数 | 整团预算 | 天气样本 | HTTP | 秒 | 一致性检查 | 预计费用 |',
'|---|---|---:|---:|---:|---|---:|---:|---|---:|']
for r in rows:
 p=r['input'];m=r['metrics'];total=m.get('estimated_total')
 lines.append(f"| {r['id']} | {p['destination']} | {r['days']} | {p['travellers']} | £{p['budget']:,} | {weather[r['weather']]} | {r['status']} | {r['seconds']:.1f} | {'通过' if m.get('contract_pass') else '未通过'} | {'£'+format(total,',') if total is not None else '—'} |")
lines+=['','## 检查定义','',
'- 日期齐全、输出结构合法、活动时间不重叠、相邻活动留足模型估算的交通分钟。',
'- 景点名称去重及长行程每日分配一致；分类费用覆盖已列明活动的整团金额，总额/超预算标记/超预算警告一致。',
'- 天气快照保持后台样本，天气原因由后台规则提供，室外或混合活动有室内备选。',
'- 天气适配只额外记录坏天气日的室外/混合活动，作为人工复核项；不会把“有备选”直接视为活动安排最优。活动室内外属性是模型自报，未逐地点核实。',
'','## 发现与复核项','']
for r in rows:
 m=r['metrics']
 if r['status']!=200:lines.append(f"- **{r['id']} 生成失败**：{r['response'].get('error',{})}。原始失败已计入统计。")
 if m.get('bad_weather_outdoor_or_mixed'):lines.append(f"- **{r['id']} 坏天气安排需复核**："+'；'.join(m['bad_weather_outdoor_or_mixed'])+'。不等同于硬性校验失败，应结合室内备选和实际开放条件判断。')
 if m.get('over_budget'):lines.append(f"- **{r['id']} 超预算**：估计 £{m['estimated_total']:,}，预算 £{r['input']['budget']:,}；超预算提示检查{'通过' if m['over_budget_disclosed'] else '未通过'}。预算不足不是 HTTP 生成失败，应用仍不保证优化到预算以内。")
 if r['validationEvents']:lines.append(f"- **{r['id']} 捕获详情校验事件 {len(r['validationEvents'])} 条**："+'；'.join(r['validationEvents'])+'。这是详情校验日志，不是总模型调用次数（未包含所有分配阶段事件）。')
 for w in m.get('warnings',[]):
  if 'unallocated optional stops' in w:lines.append(f"- **{r['id']} 保守估价**：{w}")
verification=root/'verification.json'
if verification.exists():
 v=json.loads(verification.read_text())
 lines+=['', '## 配套检查', '',f"- 后端单元测试：{v['backend_unittest']['passed']} 项通过；前端单元测试：{v['frontend_node_test']['passed']} 项通过；生产构建：{v['frontend_build']['status']}。"]
live=root.parent/'live-weather.json'
if live.exists():
 w=json.loads(live.read_text())
 lines+=['',f"- 独立真实 Open-Meteo 检查：{w['weather']['status']}，耗时 {w['seconds']:.3f} 秒；London，{w['input']['start']} 至 {w['input']['end']}。该结果不计入固定天气案例成功率。"]
lines+=['','## 局限与后续用途','',
'- 没有核实真实票价、营业时间、交通路线、地理实体别名或备选活动质量，也没有模拟真实 iOS/Android 浏览器。',
'- 天气固定样本可复现边界，不等于实时天气服务稳定性；独立的真实天气 smoke test 单独保存，不计入固定案例成功率。',
'- 极端人数和预算属于边界校验，不证明具体餐厅或景点能承接该规模。',
'- 可用作项目验收证据和后续版本对照；研究层面的稳定性评估应对相同案例多次重复并扩大样本，不能仅凭本轮报“100%可靠”。',
'','## 复现与证据','',
'在项目根目录执行（会调用真实 Qwen 并产生费用；输出目录必须尚不存在）：',
'','```sh',
'.venv/bin/python scripts/run_acceptance.py --live --output experiments/acceptance-new-run',
'.venv/bin/python scripts/summarize_acceptance.py experiments/acceptance-new-run docs/Acceptance-new-run.md',
'```','',
f"- 本轮目录：{root.as_posix()}。",
'- manifest.json：固定输入、天气时钟、模型配置名称、源码指纹。',
'- C01.json–C08.json：逐例实际响应、耗时、检查结果及详情校验日志。',
'- results.csv / results.json / summary.json：汇总数据；invalid-inputs.json：拒绝输入的结果。',
'- 密钥没有写入报告、请求记录或清单。']
destination.write_text('\n'.join(lines)+'\n')
print(destination)
