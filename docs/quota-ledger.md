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

---

## 第 5 批（2026-10-28）工作流 E 部位特异性膜

| # | 查询词 | 工作流 | 命中 | 新增 | 重复 | 累计调用 |
|---|---|---|---|---|---|---|
| 20 | selective organ targeting SORT lipid nanoparticle mechanism liver lung spleen tissue tropism | E | 20 | 17 | 1 | 20 |
| 21 | blood brain barrier lipid nanoparticle targeting formulation composition in vivo biodistribution | E | 20 | 8 | 0 | 21 |
| 22 | cell membrane lipid composition organ specific lipidomics quantitative mapping to liposome formulation design | E | 20 | 16 | 1 | 22 |

第 5 批小结：调用 3 次，主表新增 41 行（累计 222 行，无重复 DOI）。
批内新增率 68%，E 方向此前基本没碰过。

**本批触发了任务描述第九节第 1 条（结果直接推翻项目的某个基本假设），
已在 docs/membrane-specific.md 开头和末节写明，并在聊天里提出决策问题。**
E 的后续检索在该决策做出之前暂停，不继续消耗额度，
因为"按哪个问题表述建模"直接决定后续该检索什么。

工作流覆盖（累计 222 行）：A 42、B 102、C 53、D 68、E 54、F 3。

---

## 第 6 批（2026-10-28）工作流 F 同行商业情报 与 G 北欧验证合作方

| # | 查询词 | 工作流 | 命中 | 新增 | 重复 | 累计调用 |
|---|---|---|---|---|---|---|
| 23 | Mana.bio AI-driven lipid nanoparticle formulation company machine learning platform publication | F | 20 | 9 | 8 | 23 |
| 24 | Denmark Sweden Norway Finland liposome lipid nanoparticle formulation microfluidic research group characterization | G | 20 | 5 | 3 | 24 |
| 25 | Technical University of Denmark DTU liposome nanomedicine drug delivery characterization methodology validation | G | 20 | 6 | 2 | 25 |
| 26 | liposome lipid nanoparticle formulation characterization microfluidic（country=dk,se,no,fi；year_min=2022） | G | 20 | 0 | 0 | 26 |
| 27 | small angle X-ray neutron scattering lipid nanoparticle structure Lund Chalmers Copenhagen Aarhus | G | 20 | 4 | 2 | 27 |
| 28 | interlaboratory validation round robin liposome characterization method reference material metrology institute | A;G;D | 20 | 6 | 3 | 28 |

第 6 批小结：调用 6 次，主表新增 25 行，去重后累计 **246 行**（有 1 条与第 2 批重复，已合并）。
第 26 次检索**新增 0**，这是本次清查唯一一次零新增，原因见下。

### 第三次额度分配调整：G 从 45 次压到 3 次

**原因是工具的结构性限制：Consensus 不提供作者单位字段，也无法按机构检索。**

两次失败的尝试已记入 `docs/validation-partners.md`：
1. **第 26 次检索用 country=dk,se,no,fi 过滤器，新增 0 行。**
   返回的全是真正有地理属性的研究类型（芬兰血浆脂质组 GWAS、瑞典 PFAS 纵向队列、
   挪威干眼症泪液囊泡、瑞典矿洞生物膜），配方学论文被过滤掉了。
   原因：该过滤器过滤的是"country of study"（流行病学意义上的研究所在国），
   对配方学论文这个属性不存在或被错误填充。
2. **第 24、25 次把机构名写进查询词**，但 Consensus 做的是对论文内容的语义匹配，
   机构名不在被匹配内容里，所以只起了噪声作用。

替代方案（零 Consensus 额度）已写进 `docs/next-actions.md`：
用 OpenAlex API（免费，有 institutions 端点，可按 country_code 过滤）写脚本。

### 本次清查三次调整分配的共同原因

| 调整 | 工作流 | 原定 | 实用 | 原因 |
|---|---|---|---|---|
| 第一次 | C 开放数据集 | 70 | 3 | Consensus 不索引数据仓储条目，只索引论文 |
| 第二次 | D 报告标准化 | 45 | 3 | 七环论证链已闭合，继续检索只增同类证据 |
| 第三次 | G 北欧合作方 | 45 | 3 | Consensus 无作者单位字段，无法按机构检索 |
| 附带 | F 专利格局 | 35 的一部分 | 0 | **Consensus 完全不覆盖专利** |

**三次调整里有三次源于同一个认识：Consensus 是论文语义检索工具，
不是机构检索工具、不是仓储索引、也不覆盖专利。**
这是本次清查最重要的方法学教训，决定了剩余额度不该投向哪里。

### 累计额度使用（截至第 6 批）

| 工作流 | 原定 | 已用 | 状态 |
|---|---|---|---|
| A 验证证据 | 80 | 6 | 六条子问题有答案；第 6 批又补上 CRM 与三实验室验证两条重要修正 |
| B 机理与特征 | 70 | 6 | 六条子问题全部有定量答案 |
| C 开放数据集 | 70 | 3 | 工具原因压缩 |
| D 报告标准化 | 45 | 3 | 论证链闭合 |
| E 部位特异性膜 | 70 | 3 | **因触发决策条件而暂停**，待方向确认 |
| F 同行与商业情报 | 35 | 1 | 学术格局已清；专利无法用本工具查 |
| G 北欧验证合作方 | 45 | 3 | 工具原因压缩 |
| 机动储备 | 60 | 3 | 黄酮专项 1 次、实验室间验证与参考物质 2 次 |
| **合计** | **475** | **28** | |

主表 246 行（去重后，无重复 DOI），已按优先级加工作流加年份排序。
工作流覆盖：A 51、B 110、C 53、D 80、E 55、F 13、G 11。
优先级：P0 92、P1 100、P2 54。需全文 36 篇，其中 P0 级需全文 14 篇。

---

## 第 7 批（2026-10-28）脑递送专项（新工作流 H）

**方向更正**：用户确认首发管线是血脑屏障脑递送、载荷为小分子，毛囊与皮肤线基本放弃。
本批按用户给的六条必查问题执行，新建工作流代号 **H（脑递送专项）**，
主表 `workflows` 列与排序键同步扩展为 A 到 H。

| # | 查询词 | 工作流 | 命中 | 新增 | 重复 | 累计调用 |
|---|---|---|---|---|---|---|
| 29 | apolipoprotein E adsorption LDL receptor mediated transcytosis brain delivery nanoparticle quantitative mechanism | H;B | 20 | 17 | 0 | 29 |
| 30 | small molecule drug liposome solid lipid nanoparticle brain concentration brain to plasma ratio quantitative outcome | H | 20 | 14 | 0 | 30 |
| 31 | in vitro blood brain barrier model transwell co-culture microfluidic chip correlation with in vivo permeability predictive validity | H;A | 20 | 12 | 0 | 31 |
| 32 | brain to plasma ratio Kp,uu microdialysis unbound drug interlaboratory variability reproducibility measurement | H;A | 20 | 14 | 0 | 32 |
| 33 | machine learning prediction blood brain barrier permeability dataset curated compounds logBB | H;B | 20 | 4 | 0 | 33 |
| 34 | protein corona composition lipid nanoparticle brain endothelial targeting proteomics dataset organ specific | H;B | 19 | 12 | 2 | 34 |
| 35 | machine learning prediction of nanoparticle brain delivery efficiency dataset of formulations | H;C | 20 | 12 | 5 | 35 |
| 36 | effect of PEG density and particle size on liposome brain uptake quantitative formulation parameters | H;B | 19 | 14 | 2 | 36 |
| 37 | interlaboratory variability and reproducibility of brain-to-plasma ratio measurement nanoparticle brain concentration | A;H | 20 | 12 | 8 | 37 |
| | **本批合计** | | **178** | **111** | **17** | **37** |

本批新增率 62%，重复率 9.6%。

### 第 33 次检索的新增数偏低（4/20），原因不是重复

命中的 20 篇全部是**小分子本身的血脑屏障渗透性 QSAR 模型**（logBB、B3DB 类数据集、
各种分类器比较），与配方学无关：它们预测的是分子能不能过屏障，
不是配方参数如何改变过屏障的量。本项目要的是后者。
因此只选入 4 篇方法学上可借用的，其余不计入主表。
这一条不构成饱和信号，而是**查询词把方向带偏了**：
`blood brain barrier permeability` 这个短语在文献里几乎被小分子 QSAR 垄断，
要查配方学必须带上载体词（liposome、lipid nanoparticle、SLN、formulation）。

### 第四次额度分配调整：新增工作流 H，并确认 E 的处置

| 工作流 | 原定 | 现状 | 说明 |
|---|---|---|---|
| H 脑递送专项 | 新增，约 200 | 已用 9 | 按六条必查问题执行 |
| E 部位特异性膜 | 70 | 停在 3 | 器官倾向性问题并入 H 与 A；膜脂质组到配方（原选项 D）仍否决，配对数据为零 |
| 淋巴靶向 | 曾列为候选 | 0 | 用户决定跳过，与脑递送无关 |

### 本批未能回答的问题（工具能力所限）

**问题一（PC-DB 的脑或 CNS 记录数、小分子载荷数）在 Consensus 内无解。**
PC-DB 摘要只给总计数（83 项研究、817 配方、2497 蛋白、脂质基 14.8%），
没有器官或载荷拆分。这与第 3 批 C 工作流撞的是同一道墙：
Consensus 索引论文，不索引数据仓储条目或库内字段。
已转为零额度任务：直接下载 PC-DB 数据表统计。

### 累计额度使用（截至第 7 批）

| 工作流 | 原定 | 已用 | 状态 |
|---|---|---|---|
| A 验证证据 | 80 | 8 | 第 7 批又补上 VAMAS 五十实验室与 NTA 双仪器两条关键测量不确定度证据 |
| B 机理与特征 | 70 | 6 | 六条子问题全部有定量答案 |
| C 开放数据集 | 70 | 3 | 工具原因压缩 |
| D 报告标准化 | 45 | 3 | 论证链闭合 |
| E 部位特异性膜 | 70 | 3 | 方向更正后并入 H |
| F 同行与商业情报 | 35 | 1 | 学术格局已清；专利无法用本工具查 |
| G 北欧验证合作方 | 45 | 3 | 工具原因压缩，待按论文优先策略重做约 120 次 |
| **H 脑递送专项（新）** | **约 200** | **9** | 六条问题已有五条有答案，问题一需直接访问数据库 |
| 机动储备 | 60 | 3 | |
| **合计** | **475** | **37** | |

主表 357 行（去重后，无重复 DOI），按优先级加工作流加年份排序。
工作流覆盖：A 91、B 164、C 73、D 80、E 55、F 13、G 11、H 105。
优先级：P0 133、P1 152、P2 72。需全文 102 篇，其中 P0 级 36 篇。
来源类型：同行评议 354、预印本 3。

---

## 第 8 批（2026-10-28）验收标准双档化、异质性上限、器官倾向性

本批按用户第 8 批决策执行三件事：核查 EE/PDI/Zeta 是否有参考物质、
把槲皮素异质性做实、把 A 路线的定量发现提取成申请材料。
新建两个工作流代号：**I（异质性上限）** 与 **J（器官倾向性）**，
主表排序键扩展为 A 到 J。

| # | 查询词 | 工作流 | 命中 | 新增 | 重复 | 累计调用 |
|---|---|---|---|---|---|---|
| 38 | certified reference material for liposome encapsulation efficiency and drug loading measurement standardization | A;I | 20 | 7 | 7 | 38 |
| 39 | zeta potential reference material certified standard measurement traceability nanoparticle | A | 20 | 13 | 3 | 39 |
| 40 | polydispersity index dynamic light scattering reference material ISO standard uncertainty | A | 19 | 11 | 0 | 40 |
| 41 | selective organ targeting SORT lipid nanoparticle quantitative biodistribution spleen liver lung tropism | J;B | 20 | 4 | 16 | 41 |
| 42 | barcoded lipid nanoparticle library high throughput in vivo screening organ tropism DNA barcode | J;C | 20 | 18 | 1 | 42 |
| 43 | quercetin liposome nanoparticle encapsulation efficiency effect of lipid composition and preparation method | I | 20 | 9 | 11 | 43 |
| | **本批合计** | | **119** | **62** | **38** | **43** |

本批新增率 52.1%，重复率 31.9%。

### 两条饱和信号

1. **SORT 与蛋白冠这条线已饱和。** 第 41 次检索 20 篇里 **16 篇已在主表**（重复率 80%，
   新增率 20%），因为第 2 批的 B 工作流已经把这条线查过一遍。
   结论：器官倾向性的机理文献不必再查，剩余问题是**小分子载荷的器官倾向性数据**，
   而那个在文献里基本不存在（见 `docs/organ-tropism-evidence.md` 的限制第 1 条）。
2. **槲皮素这条线接近饱和。** 第 43 次检索重复率 55%，但新增的 9 篇里有 2 篇
   是归因分析的关键对照（共载使 EE 降 32 个百分点、磷脂饱和度同配方对照），
   所以这次检索是值得的。再查一次大概率只增同类。

### 第 42 次检索（条码高通量筛选）是本批回报最高的一次

20 篇里 18 篇新增，且其中 5 篇直接改变方案设计：

- 281 个 LNP 的体外体内平行对比，结论是**体外不能预测体内**
- 条码质粒证明**转染水平高的器官不一定是累积水平高的器官**
- 用肽编码条码**只用 9 只小鼠评估 400 多个配方**
- 同一配方做 1%、16%、26% 三档**载药量会改变器官分布**（唯一的小分子类比）
- 23 个不同 Fab 密度的 LNP 做**脑**递送的条码筛选（脑线上唯一的配方库）

教训：检索词里加"high throughput""library""screening"这类**方法学词**，
比加生物学词更容易找到配方级数据集。这一条与第 7 批第 33 次检索的教训互补。

### 本批回答了一个此前标为未知的问题

第 1 批曾把「EE、PDI、Zeta 是否也有参考物质」列为待办。本批查清：

| 指标 | 结论 |
|---|---|
| Zeta | **有完整认证参考物质**（SRM 1992/ERM-FD305、SRM 1993/ERM-FD306），明确可用于校准 |
| PDI | **有认证值**（ALIPO-1 等三个 CRM 同时认证 PDI），但指标本身被证明不可靠，故降级为协变量 |
| EE | **完全没有**，既无 CRM 也无任何多实验室互比研究 |

据此已把 `docs/validation-evidence.md` 的验收标准改写为双档，
并新增独立可读的分档理由章节与完整前提清单。

### 累计额度使用（截至第 8 批）

| 工作流 | 原定 | 已用 | 状态 |
|---|---|---|---|
| A 验证证据 | 80 | 11 | 验收标准双档化已完成，参考物质问题已查清 |
| B 机理与特征 | 70 | 6 | 六条子问题全部有定量答案 |
| C 开放数据集 | 70 | 3 | 工具原因压缩 |
| D 报告标准化 | 45 | 3 | 论证链闭合，本批又补上拉曼在线定量这一环 |
| E 部位特异性膜 | 70 | 3 | 方向更正后并入 H 与 J |
| F 同行与商业情报 | 35 | 1 | 专利无法用本工具查 |
| G 北欧验证合作方 | 45 | 3 | 待按论文优先策略重做约 120 次 |
| H 脑递送专项 | 约 200 | 9 | 六条问题五条有答案 |
| **I 异质性上限（新）** | 并入机动 | 2 | 槲皮素跨度做实为 36% 到 97.5% |
| **J 器官倾向性（新）** | 并入机动 | 2 | SORT 线已饱和，条码线回报最高 |
| 机动储备 | 60 | 3 | |
| **合计** | **475** | **43** | |

主表 419 行（去重后，无重复 DOI）。
工作流覆盖：A 126、B 176、C 89、D 82、E 55、F 13、G 11、H 110、I 19、J 33。
优先级：P0 162、P1 174、P2 83。需全文 120 篇，其中 P0 级 45 篇。
来源类型：同行评议 416、预印本 3。

---

## 第 9 批（2026-10-28）G 北欧合作方：零 Consensus 额度完成

**本批 Consensus 额度消耗为 0。** 原定给 G 的约 120 次检索一次没用，
因为换工具后这件事根本不需要语义检索。

### 为什么不花这 120 次

G 的任务是「按论文反推课题组，记录机构、通信作者、代表论文、具体能力、匹配度」。
Consensus 不返回作者单位，所以用它做这件事只能靠猜，第 6 批已经撞过这道墙。
本批改用 **PubMed E-utilities**，它的 `[ad]` 字段直接检索作者单位，
返回的 XML 里每位作者都带完整单位字符串与（若论文公开了的）通信邮箱。

| 工具 | 是否可用 | 说明 |
|---|---|---|
| Consensus `search` | 做不了 | 无作者单位字段；`country` 指研究所在国 |
| OpenAlex API | **不可达** | 本环境网络策略拒绝 `api.openalex.org`，CONNECT 返回 403 |
| **PubMed E-utilities** | **可用** | `[ad]` 单位检索加完整单位字符串与邮箱 |
| Crossref API | 可用 | 本批未使用，留作备用 |

### 本批实际工作量

6 条 PubMed 检索式，命中 1526 条、解析 1478 条、提取 3351 个北欧单位作者条目。
产出写入 `docs/validation-partners.md`：机构层面 17 家、个人层面 9 位、
方法学与表征方向另 6 位，全部**单位已核实**。

另新增 17 行到主表（`why_matters` 以 `[PubMed]` 标明来源不是 Consensus）。

### 一条意外收获

**本项目脑递送证据里最关键的两个定量结果，出自同一个北欧课题组。**
Uppsala 的 Hammarlund-Udenaes 与 Loryan 组既是 Kp,uu,brain 概念的源头，
也是甲氨蝶呤 GSH-PEG 脂质体 Kp,uu 系列与苯海拉明包封后 Kp,uu 从 3.0 降到 1.5
这两篇的作者组。而我们在 `docs/brain-delivery-evidence.md` 里恰好标出了
该组两篇论文之间一处 5 倍的 Kp,uu 差异需要澄清。
这给了一个具体、有专业含量、对方有动机回答的接洽理由。

### 累计额度使用（截至第 9 批）

| 工作流 | 原定 | 已用 | 状态 |
|---|---|---|---|
| A 验证证据 | 80 | 11 | 验收标准双档化完成 |
| B 机理与特征 | 70 | 6 | 完成 |
| C 开放数据集 | 70 | 3 | 工具原因压缩 |
| D 报告标准化 | 45 | 3 | 论证链闭合 |
| E 部位特异性膜 | 70 | 3 | 并入 H 与 J |
| F 同行与商业情报 | 35 | 1 | 专利无法用本工具查 |
| **G 北欧验证合作方** | 45 后改约 120 | **3（第 6 批）加 0（第 9 批）** | **已完成，改用 PubMed** |
| H 脑递送专项 | 约 200 | 9 | 五条问题有答案 |
| I 异质性上限 | 并入机动 | 2 | 完成 |
| J 器官倾向性 | 并入机动 | 2 | SORT 线饱和 |
| 机动储备 | 60 | 3 | |
| **合计** | **475** | **43** | 未变，本批零消耗 |

主表 435 行。工作流覆盖：A 139、B 177、C 89、D 84、E 55、F 13、G 25、H 119、I 23、J 33。
优先级：P0 171、P1 181、P2 83。需全文 135 篇，其中 P0 级 53 篇。

### 剩余额度的重新打算

G 不再需要额度，原计划给 G 的约 120 次可以释放。剩余 432 次的用法：

1. **成本与周期专项，约 40 次**（低预期，零命中即如实记录"文献无答案"）
2. **脑递送追加检索**，按六条问题里仍有空白的方向补
3. 不为了用掉额度而检索（用户已明确）
