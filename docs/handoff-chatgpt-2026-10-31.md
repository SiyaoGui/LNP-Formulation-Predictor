# 交接文档：分给 ChatGPT 的工作与完整提示词

日期：2026-10-31
我方当前状态：主表 `docs/master-candidates.csv` 共 3352 行，Consensus 累计检索 232 次（名义额度 475 次，已用 48.8%）。
交接目的：Consensus 额度即日到期，额度只能由我方消耗；把**不需要 Consensus、也不需要我方累积上下文**的工作并行交给 ChatGPT，避免浪费任何一方的产能。

---

## 一、结论先说：该交接哪一部分

**交给 ChatGPT：专利配方实例（主）+ 监管审评文件与注册登记（次）。合称「非文献证据层」。**

**不交给 ChatGPT：任何血脑屏障与脑递送的学术文献检索。** 这一层留在我方。

### 为什么是这两块

| 判据 | 专利配方实例 | 监管审评文件 | 血脑屏障文献（不交接） |
| --- | --- | --- | --- |
| Consensus 是否索引 | **不索引** | **不索引** | 索引，且是我方额度的最佳用途 |
| 是否需要项目累积上下文 | 低（格式化抄录为主） | 低 | **高**（3352 行去重、12 批矛盾清单、工作流分类） |
| 幻觉风险是否可控 | **可控**，专利号与实施例号可逐一核验 | **可控**，机构文件有固定 URL | **不可控**，DOI 一旦编造会污染主表 |
| 对项目的边际价值 | **最高**，主表现有 0 条专利记录 | 高，直接补齐规格与验收标准 | 已有 3352 行基础 |
| 产出可验证性 | 高 | 高 | 需要领域判断 |

三条具体理由：

1. **专利说明书是「配方到结果」配对数据密度最高的来源，而且不在任何学术数据库里。** 一份 LNP 专利的实施例表格通常直接给出可电离脂质种类与 mol%、辅助脂质、胆固醇、PEG 脂质、N/P 比、工艺参数，以及对应的粒径、PDI、包封率、体内表达量。这正是本项目预测模型需要的训练样本形态。批 22 已记录 Han 2024 的现成数据集（2994 项专利、265 个配方、7674 个化合物、28789 个片段），可作为 ChatGPT 的起点而不是从零开始。
2. **主表的 `source_type` 字段设计了三类来源（同行评议 / 预印本 / 公司宣称），但「公司宣称」至今 0 行。** 专利与监管文件正是这一类的主体，缺了它整个来源分层是空的。
3. **幻觉风险的结构性差异。** 学术文献的 DOI 是 ChatGPT 最容易编造的东西之一，一条假 DOI 进了 3352 行的主表就很难再找出来。专利号与监管文件不同：US11471525B2 这类编号可以直接打开核验，实施例编号与页码也能定位，错了立刻暴露。把高幻觉风险的工作留在有额度、有真实检索返回的我方，把可核验的抄录工作交给 ChatGPT，是风险最小的切法。

### 明确不交接的其它候选（说明原因，避免你以后重复考虑）

- **中文、日文、韩文文献的工艺数据**：价值高（批 21 已验证中文期刊确有 Consensus 不索引的工艺数据），但 ChatGPT 对 CNKI、万方、J-STAGE、KCI 的可达性不稳定，且这些库多数需要机构订阅，很容易变成「它读不到却仍然给你一个条目」。等专利线跑顺、反幻觉契约验证有效之后再追加。
- **三个公开数据集的实际复现**（B3DB、Abdulai 2026、Zou 2025）：这是代码与数据工程任务，有明确的数值验收标准（R² ≈ 0.60 / AUC ≈ 0.91），更适合在本仓库里由我方直接做，而不是隔着对话转述。
- **临床试验注册库**（ClinicalTrials.gov 等）：可以做，但信息密度远低于专利，放在监管线的末位。

---

## 二、分工边界（写死，避免两边重复劳动）

| | 我方（Claude，有 Consensus 额度） | ChatGPT（无额度消耗，需联网） |
| --- | --- | --- |
| 血脑屏障与脑递送文献 | **全部** | 不做 |
| 脂质纳米颗粒配方的学术文献 | **全部** | 不做 |
| 专利说明书配方实例 | 不做 | **全部** |
| FDA / EMA / PMDA 审评文件与说明书 | 不做 | **全部** |
| ICH 与药典条款 | 不做 | **全部** |
| 临床试验注册库条目 | 不做 | 低优先级，有余力再做 |
| 主表合并与去重 | **我方独占** | 不要碰，只交付独立文件 |
| 矛盾裁决与优先级判定 | **我方独占** | 只标注，不裁决 |

去重机制：ChatGPT 交付**独立文件**（见下方 schema），由我方在本仓库内合并进主表。专利没有 DOI，所以按**专利族（simple family / 优先权号）**去重，不是按公开号。这就是为什么下面的 schema 要求它必须填 `family_id` 或 `priority_number`。

---

## 三、ChatGPT 的交付物（两个文件，schema 固定）

### 文件 1（主）：`patent-formulations.csv`

一行等于**一个专利实施例**，不是一个专利。一份专利有 12 个实施例就写 12 行。

```
patent_number,family_id_or_priority,title,assignee,priority_date,pub_date,jurisdiction,legal_status_if_stated,url,example_no,payload_type,ionizable_or_cationic_lipid,helper_lipid,sterol,peg_lipid,molar_ratios,n_to_p_ratio,process,size_nm,pdi,zeta_mv,encapsulation_pct,dose_and_species,outcome_metric,outcome_value,target_organ,bbb_relevant,quote_locator,verification_status,notes
```

字段说明（关键几个）：
- `molar_ratios`：按 `可电离:辅助:胆固醇:PEG` 顺序，例如 `50:10:38.5:1.5`。原文若用重量比，照抄并在 `notes` 注明单位。
- `process`：`microfluidic` / `ethanol_injection` / `T-mixer` / `thin_film` / `high_pressure_homogenization` / `other`，原文没写就填 `not_stated`。
- `outcome_metric` 与 `outcome_value`：例如 `luciferase_expression_liver` 与 `1.2e7 RLU/mg`；或 `%ID/g_brain` 与 `0.42`。**原文没有数值就两列都填 `not_stated`，不要用定性描述填数值列。**
- `bbb_relevant`：`Y` 仅当该实施例明确涉及脑、中枢神经系统、血脑屏障或脑靶向配体；否则 `N`。
- `quote_locator`：该行数据在原文中的位置，例如 `Example 7, Table 3, para [0142]`。**这一列为空的行一律作废。**
- `verification_status`：`VERIFIED`（我打开了该页面并逐项核对）/ `UNVERIFIED`（有任何一项没核对上）。

### 文件 2（次）：`regulatory-specs.csv`

```
doc_id,agency,product,inn_or_code,doc_type,doc_date,url,parameter,stated_value,acceptance_criterion,test_method,quote_locator,verification_status,notes
```

优先抓这些已获批的脂质与纳米制剂产品的审评与质量部分：Onpattro（patisiran）、Comirnaty、Spikevax、mRESVIA、Doxil / Caelyx、AmBisome、Abraxane、Vyxeos、Marqibo、Onivyde、Arikayce、Feraheme（ferumoxytol）、Zolgensma、Spinraza（nusinersen）、Qalsody（tofersen）。
重点字段是 `parameter` 与 `acceptance_criterion`：粒径规格范围、PDI 上限、包封率下限、残留溶剂限度、游离药物比例、内毒素限度、无菌保证、储存条件与效期、在用稳定性。这些是本项目「验收标准」一章目前完全空缺的部分。

---

## 四、可以直接整段粘贴给 ChatGPT 的提示词

> 下面整块复制给 ChatGPT。它没有本项目的记忆，所以提示词里包含了它需要的全部背景、格式、禁令与验收标准。开新对话，第一条消息就发这个。

```text
你的任务是为一个「脂质纳米颗粒（LNP）配方预测」项目建立两份可核验的结构化数据表。你没有这个项目的历史记忆，本条消息包含你需要的全部信息，不要去猜测没有写明的内容。

## 项目背景（只需知道这些）

这个项目要做一个预测模型：输入配方组成与工艺参数，预测颗粒的粒径、PDI、包封率、以及体内递送结果。首发应用方向是「血脑屏障脑递送、小分子载荷」。
项目已经有一个 3352 行的学术文献候选表，由另一个助手负责，覆盖同行评议论文与预印本。那部分**不需要你做，也不要做**。
你负责的是学术数据库索引不到的两类来源：**专利说明书里的配方实施例**，以及**监管机构审评文件里的质量规格**。这两类是目前完全空缺的。

## 为什么是你做这个

专利实施例的表格通常直接给出「可电离脂质种类与摩尔百分比、辅助脂质、胆固醇、PEG 脂质、N/P 比、工艺、粒径、PDI、包封率、体内结果」这一整套配对数据，是这个项目最需要的训练样本形态，而任何学术数据库都不索引专利。监管审评文件同理，它们包含真实的放行规格与验收标准，论文里没有。

## 绝对禁令（最重要的一节，违反任何一条整批作废）

1. **每一行数据必须来自你实际打开过的网页。** 不允许凭记忆、凭印象、凭「通常是这样」生成任何一行。
2. **不允许编造或补全任何编号。** 专利号必须是完整格式（例如 US11471525B2、WO2021/030701A1、EP3673898A1、CN114206463A），不允许写成「US1147152x」或只写「某辉瑞专利」。监管文件必须给出可打开的 URL。
3. **不允许把定性描述写进数值列。** 原文写「粒径较小」就在 size_nm 填 not_stated，不要写一个数字。原文写「包封率高」就填 not_stated。
4. **每一个数字都必须能在原文中逐字找到，并且你要在 quote_locator 列写出它的位置**（例如 `Example 7, Table 3, para [0142]`）。这一列为空的行作废。
5. **任何一项核对不上，该行 verification_status 填 UNVERIFIED，并在 notes 写明是哪一项核对不上。** 宁可交 30 行全部 VERIFIED，也不要交 200 行里混着编造的。
6. **不要做血脑屏障或 LNP 的学术文献检索，不要给出任何论文 DOI。** 那部分由另一个助手用专门的检索额度做，你给的论文条目会造成重复和污染。
7. 如果某个来源你打不开（付费墙、区域限制、站点拒绝抓取），**明确说「打不开」并跳过**，不要用别处的信息替代它。

## 任务 A（主线）：专利配方实例

**可用的检索入口**（优先用能给出全文的）：
- Google Patents（patents.google.com）：全文与实施例表格可读，支持 CPC 分类与申请人筛选
- Espacenet（worldwide.espacenet.com）
- WIPO PATENTSCOPE（patentscope.wipo.int）
- FPO（freepatentsonline.com）
- 美国 Patent Public Search（ppubs.uspto.gov）

**建议的检索策略**（你可以调整，但要把实际用过的检索式记录下来交回）：
- 按申请人：Moderna、BioNTech、Pfizer、Arbutus、Acuitas、Alnylam、Genevant、Translate Bio、CureVac、Generation Bio、Beam、Intellia、Verve、Capstan、Suzhou Abogen（艾博生物）、Stemirna（斯微生物）、RNAimmune
- 按分类号：A61K9/127（脂质体与脂质囊泡）、A61K9/51（纳米颗粒）、A61K47/54、A61K48/00、C12N15/88
- 按关键词组合：`ionizable lipid` + `molar ratio` + `encapsulation efficiency`；`lipid nanoparticle` + `blood-brain barrier`；`lipid nanoparticle` + `brain` + `example`
- 优先选取**含有实施例数据表**的专利，跳过只有权利要求没有实施例数据的

**优先级排序**（额度与时间有限时按此顺序）：
1. 实施例中同时给出「组成 + 粒径 + 包封率 + 体内结果」四项的专利（最高价值）
2. 明确涉及脑、中枢神经系统、血脑屏障、脑靶向配体的 LNP 专利（与项目首发方向直接相关）
3. 给出「组成 + 粒径 + 包封率」三项的专利
4. 只给出组成与粒径的专利

**输出格式**，CSV，表头必须逐字一致：

```
patent_number,family_id_or_priority,title,assignee,priority_date,pub_date,jurisdiction,legal_status_if_stated,url,example_no,payload_type,ionizable_or_cationic_lipid,helper_lipid,sterol,peg_lipid,molar_ratios,n_to_p_ratio,process,size_nm,pdi,zeta_mv,encapsulation_pct,dose_and_species,outcome_metric,outcome_value,target_organ,bbb_relevant,quote_locator,verification_status,notes
```

填写规则：
- **一行等于一个实施例，不是一个专利。** 一份专利有 12 个带数据的实施例就写 12 行，example_no 分别填 1 到 12。
- `family_id_or_priority`：填 Google Patents 页面上的 simple family 编号，或优先权申请号。**这一列必填**，项目方要用它去重（同一配方常有 US、EP、CN、WO 多个公开号，按族去重才不会重复计数）。
- `molar_ratios`：按 `可电离:辅助:胆固醇:PEG` 的顺序写，例如 `50:10:38.5:1.5`。原文若用重量比或其它顺序，照抄原文并在 notes 注明。
- `process`：只能填 microfluidic / ethanol_injection / T-mixer / thin_film / high_pressure_homogenization / other / not_stated
- `size_nm`、`pdi`、`zeta_mv`、`encapsulation_pct`：只填数字或区间（例如 `78` 或 `70-85`）。没有就填 not_stated。
- `outcome_metric` 与 `outcome_value`：成对出现，例如 `luciferase_expression_liver` 与 `1.2e7 RLU/mg`，或 `%ID/g_brain` 与 `0.42`，或 `protein_knockdown_pct` 与 `85`。没有数值就两列都填 not_stated。
- `bbb_relevant`：Y 仅当该实施例明确涉及脑、中枢神经系统、血脑屏障或脑靶向；否则 N。
- `notes`：写任何需要人工注意的事情，包括你的怀疑。

**目标产量**：第一批交 40 到 80 行 VERIFIED 数据，覆盖 8 到 15 个专利族。宁少勿假。

## 任务 B（次线）：监管审评文件里的质量规格

**可用入口**：
- FDA Drugs@FDA 与 accessdata.fda.gov（审评包、说明书、化学审评部分）
- EMA 欧洲公众评估报告（EPAR，ema.europa.eu）
- 日本 PMDA 审查报告（pmda.go.jp）
- ICH 指导原则官方 PDF（ich.org）
- 各国药典公开条款

**目标产品清单**（按此顺序）：Onpattro（patisiran）、Comirnaty、Spikevax、Doxil / Caelyx、AmBisome、Abraxane、Vyxeos、Marqibo、Onivyde、Arikayce、Feraheme（ferumoxytol）、Spinraza（nusinersen）、Qalsody（tofersen）。

**要抓的参数**（这是重点，不要泛泛摘录全文）：粒径规格范围、PDI 上限、包封率下限、游离药物比例限度、残留溶剂限度、内毒素限度、无菌保证方式、储存条件与效期、在用稳定性时限、以及任何写明了「acceptance criterion」的条目。

**输出格式**，CSV：

```
doc_id,agency,product,inn_or_code,doc_type,doc_date,url,parameter,stated_value,acceptance_criterion,test_method,quote_locator,verification_status,notes
```

**目标产量**：第一批交 30 到 60 行 VERIFIED 数据。

## 交付时必须同时给我这四样

1. 两个 CSV 的**完整内容**（直接贴在对话里，或给可下载文件，不要只给摘要）
2. **你实际打开过的 URL 清单**，一行一个
3. **你实际用过的检索式清单**
4. 一段**自查报告**，包含：总行数、VERIFIED 行数、UNVERIFIED 行数及原因分类、你打不开的来源清单、你自己觉得最可能有问题的 3 行及原因

## 风格要求

- 用中文回答，直接具体，不要用破折号
- 不要写鼓励性的套话，不要复述我的指令
- 不确定就说不确定，并说明不确定的是哪一项
- 聊天里只给进度与需要我决策的事，详细数据放在 CSV 里
```

---

## 五、我方拿到交付后的验收清单

按顺序做，任何一项不通过就退回重做而不是自己补：

1. **抽样核验专利号**：随机取 10 行，逐个打开 Google Patents，确认专利号存在、申请人与优先权日一致。出现 1 个不存在的编号，整批退回。
2. **抽样核验数值**：随机取 10 行，按 `quote_locator` 定位到实施例与表格，确认 `size_nm`、`encapsulation_pct`、`molar_ratios` 三项逐字一致。错 1 项退回该专利的全部行。
3. **检查 `quote_locator` 空值率**：空值行直接删除，不计入产量。
4. **检查数值列是否被定性描述污染**：`grep` 数值列里的非数字内容，只允许 `not_stated` 与区间格式。
5. **按 `family_id_or_priority` 去重**，再与主表交叉检查（专利无 DOI，但同一配方可能已通过论文进入主表，需按申请人与脂质名称人工比对）。
6. **合并**：专利表与监管表作为独立文件放在 `docs/external/`，**不直接并入 `docs/master-candidates.csv`**，而是在 `docs/quota-ledger.md` 里单列一节记录来源与行数，保持主表「学术文献」的单一来源属性。

---

## 六、如果 ChatGPT 这条线跑顺，第二批可以追加的任务

按价值排序，到时再决定：
1. **中文专利与中文期刊的工艺数据**（CNIPA 全文、CNKI、万方）。批 21 已验证中文期刊确有 Consensus 不索引的固体脂质纳米粒工艺数据。
2. **日文与韩文来源**（J-STAGE、KCI、PMDA 日文审查报告）。
3. **企业公开披露**（10-K、S-1、投资者材料里的产能、成本、时间线数据）。这能填补工作流 K（成本与时间线）目前几乎只有学术估算的缺口。
4. **临床试验注册库**（ClinicalTrials.gov、EUCTR、jRCT、CTIS）中 LNP 与脑递送相关试验的设计参数与终点。
