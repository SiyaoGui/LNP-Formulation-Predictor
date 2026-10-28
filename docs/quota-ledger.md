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
