# Qwen 真实端到端联调 — 2026-10-21

## 结果

用户在 backend/.env 配置密钥后，重启 Flask，通过 React 页面发起一次真实请求。后端使用 Qwen provider，返回 HTTP 200；前端展示 Qwen · AI itinerary。没有使用测试 mock 或 sample fallback。

输入：London，2026-11-02 至 2026-11-03，GBP 500，1 人；History / Food / Photography；备注要求 10:00 之后开始、包含 British Museum 和素食午餐、节奏放松。

输出：两天共 7 个活动，总计 GBP 335（城际交通 120、住宿 140、餐饮 45、活动 0、市内交通 30），预算余额 165。第一天 10:00 开始，第二天 10:30 开始；包含 British Museum、Vegetarian Lunch in Covent Garden。

验证：服务端输出校验通过；浏览器正常展示；Save Trip 成功；刷新后从 My Trips 重新打开，Qwen 标识、日期、预算和活动仍在。原有保存条目保留。仅进行一次真实生成，没有额外重新生成请求。

## 证据与局限

- result-accessibility.txt：实际结果页的可访问性文本。
- qwen-result.png：刷新后重新打开已保存行程的截图。
- 本次未开启原始模型响应记录；本文件是联调记录，不是包含 token usage、完整原始 JSON 的可复现实验数据集。
- 一次成功不证明模型稳定性、整体偏好满足率或真实旅行可行性。
- 模型输出包含尚未核实的市场开放时间和交通描述。餐饮估算仅覆盖列出的餐饮活动，不足以证明两天所有用餐均已覆盖。这些属于后续质量评估和约束完善事项。
- 这是代理执行的验证，人工审阅待确认。
