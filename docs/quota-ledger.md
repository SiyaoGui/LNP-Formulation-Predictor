# Consensus 额度账本

这是本次清查额度消耗的唯一账本。每次检索一行，按批次分组。

## 重要前提（影响全部计数）

**Consensus MCP 的 search 返回结果里不包含任何额度计数器或剩余次数提示。** 服务端的
sign-up / upgrade / usage 消息字段在本会话的返回中始终为空。因此：

- 本账本记录的是**我实际发起的检索调用数**，不是服务端剩余额度。
- 任务描述给出的"剩余约 475 次"无法在本会话内核实，也无法倒推。
- 若你在 Consensus 网页端能看到实际剩余数，请以网页端为准，本账本只作为"我用掉了多少"的记录。

假设 1：按调用次数计，一次 `search` 调用 = 一次检索额度。
假设 2：本会话未使用 Deep 模式或 Consensus Skills（MCP 只暴露 `search`、`create_thread`、
`add_to_thread`、`get_thread`、`find_threads`）。`create_thread` 会跑 Consensus 的研究 agent，
额度消耗口径未知且单次耗时数分钟，**本次清查全程只用 `search`**，不拿额度去试 thread。
理由：任务描述第 6 条要求先测出差异再决定，但在没有额度计数器的情况下无法测出差异，
贸然调用只会凭空消耗未知额度。这一条写进日志作为偏离说明。

## 口径说明

- 命中数：Consensus 返回的论文条数（本账本内恒为 20，即单页上限）。
- 新增数：进入 `docs/master-candidates.csv` 的新行数。
- 重复数：本次检索中已在主表里的论文数（含同批前序检索带入的）。
- 新增率 = 新增数 / 命中数。用于判定饱和（连续两批低于 20% 即转向）。

---

## 第 1 批（2026-10-28）工作流 A 验证证据

| # | 查询词 | 工作流 | 命中 | 新增 | 重复 | 累计调用 |
|---|---|---|---|---|---|---|
| 1 | lipid nanoparticle formulation machine learning prediction experimental validation | A | 20 | 13 | 0 | 1 |
| 2 | liposome encapsulation efficiency predictive model experimental validation accuracy | A | 20 | 11 | 1 | 2 |
| 3 | interlaboratory reproducibility nanoparticle particle size zeta potential measurement variability | A | 20 | 9 | 0 | 3 |
| 4 | encapsulation efficiency measurement repeatability replicate variability coefficient of variation liposome | A | 20 | 7 | 3 | 4 |
| 5 | microfluidic lipid nanoparticle manufacturing batch-to-batch reproducibility variability | A | 20 | 5 | 1 | 5 |
| 6 | prospective blind validation prediction model nanoparticle formulation held-out experimental test | A | 20 | 9 | 5 | 6 |

第 1 批小结：调用 6 次，主表新增 54 行，批内新增率 45%（54/120 去重后）。
重复率低，说明 A 方向还没饱和，但三条子问题（A3 实验室间重复性、A6 批间变异、
A5 失败案例）已各自拿到可用的具体数值，继续检索的边际价值主要在 A2 盲测设计与 A4 成本周期。
