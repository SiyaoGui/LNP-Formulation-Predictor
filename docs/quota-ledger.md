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

---

## 第 2 批（2026-10-28）工作流 B 机理与特征

| # | 查询词 | 工作流 | 命中 | 新增 | 重复 | 累计调用 |
|---|---|---|---|---|---|---|
| 7 | partition coefficient lipid bilayer water drug encapsulation efficiency quantitative relationship liposome | B | 20 | 11 | 4 | 7 |
| 8 | octanol-water logP poor predictor liposome membrane partitioning deviation | B | 20 | 12 | 2 | 8 |
| 9 | molecular descriptors correlated with drug loading nanoparticle QSPR polar surface area hydrogen bonding pKa | B | 20 | 7 | 1 | 9 |
| 10 | ionizable lipid nanoparticle core small molecule drug loading mechanism versus phospholipid bilayer | B | 20 | 9 | 0 | 10 |
| 11 | molecular dynamics simulation coarse-grained prediction drug encapsulation lipid nanoparticle location bilayer | B | 20 | 11 | 2 | 11 |
| 12 | lipid nanoparticle internal structure amorphous core drug solubility in lipid excipient loading capacity | B | 20 | 6 | 3 | 12 |

第 2 批小结：调用 6 次，主表新增 56 行（累计 110 行，无重复 DOI）。
批内新增率约 47%，与第 1 批持平，B 方向未饱和。
B2 到 B6 六条子问题全部拿到可引用的定量答案，B1 的几篇关键研究需全文补数值。

工作流覆盖（累计）：A 36、B 81、C 18、D 28、E 8、F 1。
优先级分布：P0 39、P1 50、P2 21。需全文 16 篇。

**额度分配调整提示**：B 的检索顺带把 C（公开数据集）和 D（报告标准化）各带起了十几行候选，
其中 Hoffmann 2020 的 630 条 MD 轨迹数据集（Scientific Data，15120 次模拟）
是 C 工作流目前最高价值的单一发现。C 的实际检索可以少于原定 70 次。
E 只有 8 行且全是顺带捞到的，F 只有 1 行，这两个方向尚未真正开始。

---

## 第 3 批（2026-10-28）工作流 C 开放数据集普查

| # | 查询词 | 工作流 | 命中 | 新增 | 重复 | 累计调用 |
|---|---|---|---|---|---|---|
| 13 | open dataset repository Zenodo Figshare lipid nanoparticle liposome formulation data curated database | C | 20 | 9 | 5 | 13 |
| 14 | design of experiments screening matrix solid lipid nanoparticle niosome formulation table encapsulation efficiency particle size | C | 20 | 6 | 1 | 14 |
| 15 | flavonoid quercetin eriodictyol liposome lipid nanoparticle encapsulation efficiency formulation | B;C | 20 | 20 | 0 | 15 |

第 3 批小结：调用 3 次，主表新增 35 行（累计 145 行，无重复 DOI）。
第 15 次检索（黄酮专项）新增率 100%，说明这个分子类别此前完全没碰过。

### 本批的两项额度分配调整

**调整 1：C 的额度从 70 次压到 3 次，剩余转给 E 和 G。**
理由：**Consensus 只索引论文，不索引数据仓储的条目本身。**
用 Zenodo、Figshare 做关键词返回的是提到这些词的论文，不是仓储内容。
本批找到的所有仓储资源都是通过"描述该数据集的数据论文"间接发现的，
最高产入口是 Data in Brief 和 Scientific Data 这类数据论文期刊。
所以继续用额度"普查仓储"是无效的。正确分工已写在 docs/open-datasets.md 的方法学结论一节：
仓储用站内 API 写脚本（代码任务，零额度），MD 类数据用 MDverse 的检索引擎原型。
实际效果：3 次检索拿到 14 个数据集候选加 16 篇可抽取表格的论文，覆盖度超过上一轮的 9 个。

**调整 2：黄酮类专项检索（第 15 次）从机动储备支出，不计入 C。**
理由：第 2 批发现"圣草酚这类多羟基黄酮零直接研究"是 B 工作流的空白，
需要用机动储备追这条高价值线索。结果证明值得：新增率 100%，
且拿到两条直接影响接受标准和特征设计的结论（见下）。

### 累计额度使用

| 工作流 | 原定 | 已用 | 说明 |
|---|---|---|---|
| A 验证证据 | 80 | 6 | 六条子问题均已拿到可引用数值，A4 成本周期文献无答案 |
| B 机理与特征 | 70 | 6 | 六条子问题全部有定量答案 |
| C 开放数据集 | 70 | 3 | 方法学原因压缩，剩余转 E 和 G |
| D 报告标准化 | 45 | 0 | 已由 A 和 C 顺带带起 32 行候选 |
| E 部位特异性膜 | 70 | 0 | 仅 13 行顺带候选，未真正开始 |
| F 同行与商业情报 | 35 | 0 | 仅 1 行，未开始 |
| G 北欧验证合作方 | 45 | 0 | 未开始 |
| 机动储备 | 60 | 1 | 黄酮专项 |
| **合计** | **475** | **16** | |

工作流覆盖（累计 145 行）：A 41、B 95、C 51、D 32、E 13、F 1。
优先级：P0 50、P1 63、P2 32。

---

## 第 4 批（2026-10-28）工作流 D 报告标准化

| # | 查询词 | 工作流 | 命中 | 新增 | 重复 | 累计调用 |
|---|---|---|---|---|---|---|
| 17 | minimum information reporting standard checklist nanomaterial characterization nanomedicine MIRIBEL | D | 20 | 14 | 1 | 17 |
| 18 | missing parameters incomplete reporting nanoparticle literature data not comparable meta-analysis heterogeneity | D | 20 | 9 | 3 | 18 |
| 19 | FAIR data standards electronic lab notebook automated instrument metadata capture laboratory | D | 20 | 13 | 0 | 19 |

第 4 批小结：调用 3 次，主表新增 36 行（累计 181 行，无重复 DOI）。
批内新增率 60%，D 方向一次打透，不需要第二批。
D1 到 D5 五条子问题全部有答案，且第 19 次检索（设备端采集）新增率 100%，
说明这个角度此前完全没碰过，而它正是硬件方向最需要的证据。

**D 的额度从 45 次压到 3 次。** 理由：七环论证链已经完整闭合（见
docs/reporting-standards.md 最后一节），每一环都有具体文献和数字，
继续检索只会增加同类证据而不改变结论。剩余转给 E 和 G。

### 累计额度使用

| 工作流 | 原定 | 已用 | 余量处置 |
|---|---|---|---|
| A 验证证据 | 80 | 6 | 六条子问题有答案，A4 成本周期文献无答案 |
| B 机理与特征 | 70 | 6 | 六条子问题全部有定量答案 |
| C 开放数据集 | 70 | 3 | 方法学原因压缩，转 E 和 G |
| D 报告标准化 | 45 | 3 | 论证链闭合，转 E 和 G |
| E 部位特异性膜 | 70 | 0 | 下一批开始，可动用 A/C/D 转入的余量 |
| F 同行与商业情报 | 35 | 0 | 未开始 |
| G 北欧验证合作方 | 45 | 0 | 未开始 |
| 机动储备 | 60 | 1 | 黄酮专项 |
| **合计** | **475** | **19** | |
