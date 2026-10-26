# 文献数据采集协议（小分子 LNP 制剂）

日期：2026-10-26
适用范围：用 Consensus 连接器系统性扩充 LipidLens 小分子 LNP 制剂数据集
状态：**待确认**。确认后冻结，不因「想多收一些数据」而放宽任何一条

本协议先于任何检索写成。确认之后，第二步到第四步的全部判定都只依据本文，不另立标准。

---

## 零、先说一件必须正视的事

仓库里已有一条冻结的结论，和「用文献数据扩充数据集来提升精度」这个思路直接冲突。写在最前面，因为它决定了本次采集的目标形态。

`docs/data-spec-ee.md` 第六节原文：

> 不能用文献的包封率数据来扩充这批数据。这是本次验证最硬的结论：跨来源的包封率不可比，混在一起会把真实信号稀释掉

支撑这条结论的数字在同一份文件第一节：包封率的分子效应按**分子**分组时是 +4.99 个百分点，按**论文**分组时掉到 **+0.01**。相似性基线的方向甚至翻转（按分子分组好 3.88，按论文分组差 1.79）。原因是测定方法、载药比、缓冲体系在论文之间都不一样，同一个分子在两个实验室可以差 20 个百分点。

`docs/data-inventory.md` 第三节给出同类证据：atenolol 和 propranolol 同配方不同工艺，粒径差 25 倍。

**这意味着什么**：把 N 篇论文的数据池化成一张大表，再按分子分组做交叉验证，是本项目已经证伪过一次的做法。继续做只会得到同样的结果。所以本次采集**不以「把记录数从 272 堆到 1000」为目标**，而以下面两件事为目标：

1. **扩大唯一化合物数**。瓶颈数字是 22 个唯一化合物（主目标口径 19 个），不是 272 条记录。
2. **优先采集论文内部的多配方对比**。同一篇论文内工艺和测定方法是固定的，分子或配方的差异因此可识别。一篇含配方筛选矩阵或 DoE 的论文，提供的是一组**组内可比**的数据点，这和跨论文池化在统计上不是一回事。

因此第二步检索的第 5 层（DoE / 筛选矩阵）不只是「一篇给的数据点多」，而是**唯一一类能绕开已证伪问题的数据**。本协议把它定为最高优先级，并为此在 schema 里强制引入 `study_block_id`（见第三节 3.6）。

**需要你决策的事项列在第七节。**

---

## 一、纳入标准

一条论文要被纳入，必须**同时**满足 N1 到 N5。任一条不满足即排除，没有「基本满足」这种判定。

### N1 载荷是小分子，且身份可确定

- 载荷必须是单一化学实体的小分子
- 必须能拿到 **SMILES**，或者能拿到可在 PubChem / ChEMBL 唯一检索到的化合物名或 CAS 号（由名字反查 SMILES 时，必须记录反查来源和 PubChem CID，并在 `payload_id_source` 标注）
- 分子量上限沿用仓库默认 **900 Da**（`docs/data-inventory.md` 第 2.3 节）。超过 900 Da 的记录仍然提取，但标记 `mw_over_default_cap = TRUE`，默认不进主数据集，只进敏感性分析
- 混合载荷（同时载两种药）排除，因为无法归因到单一分子

### N2 报告了具体的脂质组成及摩尔比

- 必须给出**每一个**脂质组分的名称
- 必须给出可换算成 mol% 的配比。接受摩尔比（如 50:10:38.5:1.5）、mol%、或「质量比 + 各组分分子量可查」。**只给质量比且分子量不可查的，排除**
- 「按文献 [12] 的标准配方」这类间接引用：追到被引论文，在被引论文里拿到具体数字才算满足；追不到则排除
- 组分名称必须具体到可查结构。写「phospholipid」「PEG-lipid」而不给具体型号的，该组分视为不可用，整条记录排除

### N3 至少有一项定量表征结果

至少一项，取自：包封率、粒径、PDI、Zeta 电位。且：

- 必须是**具体数值**。「粒径约 100 nm 左右」不算，「nanoparticles were below 200 nm」不算
- 必须能对应到具体配方。一篇论文给了 6 个配方但只报一个「代表性粒径」，那 6 个配方只能算 1 条可用记录，不是 6 条

### N4 定量数值出自正文表格、图、或补充材料，且位置可标注

- 必须记录到 `source_location`（如 `Table 2, row 4`、`Fig 3b, digitized`、`Table S1`）
- 只在摘要里出现的数字，**不纳入**，标为「需全文」进入待定池（见第五节 5.3）

### N5 全文可获取

- 利用 KU / DTU 图书馆权限能拿到全文（含补充材料）
- 拿不到全文的，标 `fulltext_status = unavailable`，进入待定池，不进主数据集

---

## 二、排除标准

命中任一条即排除，并在 `docs/screening-table.csv` 的 `exclude_reason` 写明代码。

| 代码 | 排除理由 | 说明 |
|---|---|---|
| X1 | 核酸载荷 | mRNA、siRNA、saRNA、DNA、ASO、miRNA、sgRNA、plasmid、aptamer |
| X2 | 多肽或蛋白载荷 | 含多肽、蛋白、抗体、酶、疫苗抗原 |
| X3 | 空载体 | 无载荷配方。即使表征数据完整也排除，因为没有被递送分子 |
| X4 | 非分子载荷 | 金纳米粒、量子点、氧化铁、造影剂颗粒、细胞、外泌体内容物 |
| X5 | 综述 / 观点 / 社论 | 不作为数据源。综述里的汇总表按第六节 6.4 处理（追原文，不直接提取） |
| X6 | 无定量数据 | 不满足 N3 |
| X7 | 配方不完整 | 不满足 N2 |
| X8 | 载荷身份不明 | 不满足 N1，含混合载荷 |
| X9 | 全文不可获取 | 不满足 N5。标记后进待定池，不是永久排除 |
| X10 | 仅摘要有数据 | 不满足 N4。标记后进待定池 |
| X11 | 与仓库已有数据重复 | 命中已有 34 篇小分子 DOI（见第六节 6.1） |
| X12 | 纯计算 / 模拟研究 | 分子动力学、QSPR 预测值，没有实测数据 |
| X13 | 非 LNP / 脂质体体系 | 聚合物胶束、树枝状大分子、固体分散体、无脂质双层的纳米晶 |

**关于 X13 的边界**：固体脂质纳米粒（SLN）和纳米结构脂质载体（NLC）**纳入**，但标记 `carrier_subtype`，因为它们的脂质角色划分（基质脂质 vs 液态脂质）和四槽位 schema 不是一对一映射。经典脂质体、现代可离子化 LNP、SLN、NLC 四类都收，靠 `carrier_subtype` 区分，不混为一谈。

---

## 三、提取字段表（schema）

设计原则：**能复用仓库现有列名的一律复用**，这样新数据能直接进 `merge_schema.py` 而不用改合并逻辑。现有列名见 `merged_formulations_v2.csv`（35 列）。

标记说明：`[现]` = 现有列，列名和语义完全照抄；`[新]` = 本次新增。

### 3.1 溯源

| 字段 | 标记 | 类型 | 必填 | 说明 |
|---|---|---|---|---|
| `source_dataset` | [现] | str | 是 | 本批固定填 `ConsensusLit_202610` |
| `source_row_id` | [现] | int | 是 | 本批内行号，从 1 递增 |
| `formulation_id` | [现] | int | 是 | 同一配方的多行共用一个 id |
| `paper_doi` | [现] | str | 是 | **必须来自 Consensus 返回结果**，不许凭印象补。拿不到 DOI 的标 `待核实` |
| `paper_year` | [新] | int | 是 | 来自 Consensus 返回结果 |
| `paper_first_author` | [新] | str | 是 | 来自 Consensus 返回结果 |
| `paper_journal` | [新] | str | 否 | 来自 Consensus 返回结果 |
| `source_location` | [新] | str | 是 | 数值在原文的位置，如 `Table 2, row 4` / `Fig 3b` / `Table S1`。**N4 要求** |
| `value_read_from` | [新] | enum | 是 | `table` / `text` / `figure_digitized` / `supplementary` |
| `extracted_by` | [新] | str | 是 | 提取者（本轮为 `claude` 或人名），便于回溯 |
| `extraction_date` | [新] | date | 是 | |

### 3.2 载荷分子

| 字段 | 标记 | 类型 | 必填 | 说明 |
|---|---|---|---|---|
| `payload_type` | [现] | str | 是 | 沿用现有语义：这一列放**化合物通用名**（现有 PMC_IVR 数据就是这么存的） |
| `payload_smiles` | [现] | str | 是 | 规范化 SMILES。N1 硬要求 |
| `payload_inchikey` | [新] | str | 是 | 由 SMILES 用 RDKit 算出。**跨论文去重的主键**，不靠名字匹配 |
| `payload_cas` | [新] | str | 否 | 便于人工核对 |
| `payload_id_source` | [新] | enum | 是 | `paper_smiles`（原文直接给）/ `pubchem_by_name`（名字反查）/ `chembl_by_name` / `uncertain` |
| `payload_pubchem_cid` | [新] | int | 否 | 用名字反查时必填，使反查可复核 |
| `mw_over_default_cap` | [新] | bool | 是 | MW > 900 Da 时为 TRUE |
| `is_probe` | [新] | bool | 是 | 荧光示踪剂 / 色素类（rhodamine、calcein、carboxyfluorescein 等）为 TRUE。沿用 `data-inventory.md` 问题 2 的默认做法：保留但标记 |

### 3.3 脂质组成

四槽位结构沿用现有 schema。每个槽位三列（name / smiles / pct），列名完全照抄。

| 字段 | 标记 | 必填 | 说明 |
|---|---|---|---|
| `ionizable_lipid_name` / `_smiles` / `_pct` | [现] | 条件 | 体系含可离子化脂质时必填。现有小分子子集这一组**全空**，本次采集的核心增量之一 |
| `helper_lipid_name` / `_smiles` / `_pct` | [现] | 条件 | |
| `sterol_lipid_name` / `_smiles` / `_pct` | [现] | 条件 | |
| `peg_lipid_name` / `_smiles` / `_pct` | [现] | 条件 | |
| `composition_raw_verbatim` | [新] | 是 | **原文配比字符串原样抄录**，如 `DSPC:Chol:DMG-PEG2000 = 50:38.5:1.5 molar`。所有换算都必须能从这一列复核 |
| `composition_unit_as_reported` | [新] | 是 | `mol_pct` / `molar_ratio` / `mass_ratio` / `mass_pct` |
| `composition_pct_was_renormalized` | [现] | 是 | 做过归一化则 TRUE，语义照抄现有列 |
| `ratio_order_was_ambiguous` | [现] | 是 | 原文未明确哪个数字对哪个脂质则 TRUE |
| `n_components_in_helper_slot` | [新] | 是 | helper 槽位塞了几个脂质。现有数据 141/272 行是多组分混合（`data-inventory.md` 3.6 节），这是已知的有损压缩，必须显式记录而不是埋掉 |
| `slot_assignment_uncertain` | [新] | 是 | 某脂质归哪个槽位有争议（如 DOPE 既可算 helper 也参与融合）则 TRUE |
| `carrier_subtype` | [新] | 是 | `classic_liposome` / `ionizable_LNP` / `SLN` / `NLC` / `other` |
| `total_lipid_slots_filled` | [新] | 是 | 1 到 4，用于快速筛出三组分 vs 四组分体系 |

### 3.4 载药与工艺

| 字段 | 标记 | 必填 | 说明 |
|---|---|---|---|
| `drug_to_lipid_ratio` | [新] | 否 | 数值。**现有 schema 完全没有这一列**，而它是包封率的一级决定因素 |
| `drug_to_lipid_unit` | [新] | 条件 | `molar` / `mass` / `wt_pct`。上一列非空时必填 |
| `prep_method_std` | [现] | 是 | 沿用现有取值体系（现有 16 类，如 `薄膜水化+挤出`）。新类别追加并在工作日志记录 |
| `extrusion_pore_nm` | [新] | 否 | **重点字段**。`data-inventory.md` 3.7 节认定挤出膜孔径直接决定粒径，但「孔径没有被记录成单独字段」。文献里常有，这次必须单列 |
| `extrusion_passes` | [新] | 否 | 挤出次数 |
| `device_or_chip_std` | [现] | 否 | 微流控芯片型号。现有小分子子集全空 |
| `total_flow_rate_ml_min_std` | [现] | 否 | 现有小分子子集全空 |
| `flow_ratio_imbalance` | [现] | 否 | 水相:有机相流速比。现有小分子子集全空 |
| `process_temp_c_std` | [现] | 否 | |
| `aqueous_phase_ph` | [新] | 否 | 制备时水相 pH。注意和测量介质 pH 区分 |
| `aqueous_phase_buffer` | [新] | 否 | 缓冲体系名称与浓度 |
| `organic_phase_solvent` | [新] | 否 | 乙醇 / 氯仿 / 乙醚等 |
| `loading_mode` | [新] | 是 | `passive` / `active_ph_gradient` / `active_ion_gradient` / `unknown`。被动载药和主动载药（如 doxorubicin 的硫酸铵梯度）的包封率不在一个量纲上，混用会制造假信号 |
| `process_notes` | [现] | 否 | 自由文本。**注意**：`data-inventory.md` 3.7 节已认定此列不能整体做文本特征（`structure_type` 泄漏） |

### 3.5 表征结果与测量方法

| 字段 | 标记 | 必填 | 说明 |
|---|---|---|---|
| `encapsulation_efficiency_pct` | [现] | 否 | 0 到 100。现有小分子子集**全空**，本次核心增量 |
| `ee_method` | [新] | 条件 | EE 非空时必填。`HPLC` / `UV-Vis` / `fluorescence` / `LC-MS` / `other` |
| `ee_free_drug_separation` | [新] | 条件 | EE 非空时必填。`dialysis` / `ultrafiltration` / `SEC` / `centrifugation` / `ion_exchange` / `unknown`。不同分离方式结果不可比（`data-spec-ee.md` 3.3 节） |
| `drug_loading_pct` | [新] | 否 | 载药量。和包封率不是一回事，两者都要 |
| `particle_size_nm` | [现] | 否 | |
| `size_metric` | [新] | 条件 | 粒径非空时必填。`Z_average` / `number_mean` / `volume_mean` / `TEM` / `unspecified`。现有数据没区分这个，而 Z-average 和 number mean 可以差一倍 |
| `pdi` | [现] | 否 | 0 到 1 |
| `zeta_potential_mv` | [现] | 否 | |
| `zeta_measurement_medium` | [新] | 条件 | Zeta 非空时必填。Zeta 强依赖介质和 pH（`data-inventory.md` 4.1 节 C 项） |
| `measurement_instrument_std` | [现] | 否 | 沿用现有取值。**注意**：`data-inventory.md` 3.7 节认定此列为中危泄漏通道，默认不进特征 |
| `n_replicates` | [新] | 否 | 原文报告的重复数 |
| `value_sd` | [新] | 否 | 原文给的标准差或标准误 |
| `value_sd_type` | [新] | 条件 | `SD` / `SEM`，上一列非空时必填 |
| `formation_ok` | [现] | 是 | 是否成功成粒，语义照抄现有列 |

### 3.6 分组与质量标记

这一组是本协议相对现有 schema 最重要的新增，直接对应第零节的问题。

| 字段 | 标记 | 必填 | 说明 |
|---|---|---|---|
| `study_block_id` | [新] | 是 | **同一篇论文内工艺与测定方法相同的一组记录共用一个 id**。论文内换了工艺或换了 EE 测定方法，就是不同 block。用途：支持论文内组内对比和固定效应建模，这是绕开「跨来源不可比」的唯一途径 |
| `block_varies_by` | [新] | 是 | 该 block 内部变化的是什么：`payload` / `lipid_composition` / `process_param` / `multiple`。**`payload` 的 block 价值最高**，因为它就是 `data-spec-ee.md` 2.1 节要求的单因素设计，只不过是别人做的 |
| `block_n_records` | [新] | 是 | 该 block 的记录数 |
| `is_doe_or_screening_matrix` | [新] | 是 | 该论文是否提供配方筛选矩阵或 DoE 设计 |
| `data_quality_tier` | [新] | 是 | A / B / C，见第四节 |
| `extraction_confidence` | [新] | 是 | `high` / `medium` / `low`。low 的记录不进主数据集 |
| `needs_fulltext` | [新] | 是 | TRUE 表示当前只有摘要信息，数值待全文确认 |
| `fulltext_status` | [新] | 是 | `obtained` / `available_not_yet_fetched` / `unavailable` |
| `dedup_group_id` | [新] | 是 | 见第六节 |
| `dedup_role` | [新] | 是 | `primary` / `duplicate` / `unique` |
| `qc_flag` | [新] | 是 | `ok` / `suspect` / `excluded`。沿用 `data-spec-ee.md` 3.4 节要求 |
| `qc_reason` | [新] | 条件 | 非 ok 时必填。**不许静默删除记录** |

### 3.7 明确不采集的字段

| 字段 | 原因 |
|---|---|
| `release_curve_file` | 现有列，但本批不采集释放曲线（现有 272 个曲线文件在仓库里全部不存在，见 `data-inventory.md` 出入三）。本批留空 |
| `structure_type` | 高危泄漏（`data-inventory.md` 3.7 节：SUV 定义本身就是 20 到 100 nm）。**不作为采集字段**，若原文提及只写入 `process_notes` |
| 体内数据 | 药代、肿瘤抑制率、生物分布。超出本次范围 |
| 细胞毒性 / 转染效率 | 同上 |

---

## 四、数据质量分级规则

三级。**分级在提取时判定，不事后调整**。

### A 级（高质量，进主数据集）

全部满足：

1. 数值来自正文表格或补充材料表格，不是从图里读的
2. 每个脂质槽位是**单一脂质**（`n_components_in_helper_slot = 1`）
3. 配比原文直接以 mol% 或摩尔比给出，无需从质量比换算
4. 槽位归属无争议（`slot_assignment_uncertain = FALSE`）
5. 载荷有原文 SMILES，或名字在 PubChem 唯一命中
6. 制备方法明确，且该方法的关键参数齐全（挤出法有孔径，微流控有流速比和总流速）
7. 目标值的测量方法已记录（EE 有 `ee_method` 和分离方式；粒径有 `size_metric`）

### B 级（可用，进主数据集但标记）

A 级条件中有 1 到 2 条不满足，且不满足的**不包括**第 1 条和第 5 条。典型情况：

- helper 槽位是多组分混合物（现有数据一半以上属于这类，排除它等于否定现有数据）
- 需要从质量比换算成 mol%（换算过程必须写进 `composition_raw_verbatim` 可复核）
- 制备方法的某个关键参数缺失（例如挤出但没报孔径）

### C 级（仅参考，不进主数据集）

命中任一条：

- 数值从图里数字化读出（`value_read_from = figure_digitized`）
- 载荷身份靠名字反查且 PubChem 有多个候选（`payload_id_source = uncertain`）
- 槽位归属有争议
- A 级条件不满足 3 条以上

C 级记录**保留在表里并标记**，用途是敏感性分析（「放宽到 C 级会不会改变结论」），默认不参与训练。

### 关于级别不可上调

一条记录的级别只能因为**拿到了更多原始信息**而改变（例如补到了全文、补到了补充材料），不能因为「数据量不够、放宽一下」而改变。每次级别变更在 `docs/worklog/` 记录原因。

---

## 五、与现有数据的关系

### 5.1 现有数据基线（本次采集的对照）

数字取自 `docs/data-inventory.md` 和 `merged_formulations_v2.csv`，可用 `scripts/data_inventory.py` 重跑：

| 指标 | 现值 |
|---|---|
| 小分子记录数 | 272（MW ≤ 900 时 230） |
| **唯一化合物数** | **22**（MW ≤ 900 时 20） |
| 唯一 Murcko 骨架数 | 21 |
| 小分子来源论文数 | 34 篇 DOI |
| 全表唯一 DOI | 97 篇 |
| 有包封率的小分子记录 | **0** |
| 有可离子化脂质的小分子记录 | **0** |
| 有微流控工艺参数的小分子记录 | **0** |
| 粒径的有效样本量 | 76 个独立配方 / 19 个化合物 |

### 5.2 已有 34 篇小分子 DOI（命中即判 X11）

```
10.1007/978-1-60761-609-2_14      10.1016/0378-5173(92)90015-T
10.1016/S0378-5173(97)00264-0     10.1016/j.ajps.2022.04.007
10.1016/j.bbamem.2007.05.021      10.1016/j.colsurfa.2021.126166
10.1016/j.ejpb.2018.11.010        10.1016/j.ejpb.2020.02.001
10.1016/j.ejpb.2020.03.001        10.1016/j.ejpb.2020.09.008
10.1016/j.ejpb.2021.08.013        10.1016/j.ijpharm.2016.06.117
10.1016/j.ijpharm.2020.119566     10.1016/j.ijpharm.2020.119926
10.1016/j.ijpharm.2021.120711     10.1016/j.ijpharm.2023.123710
10.1016/j.jconrel.2007.10.009     10.1016/j.jconrel.2017.02.026
10.1016/j.jconrel.2018.12.029     10.1016/j.jconrel.2020.09.032
10.1016/j.jconrel.2024.06.025     10.1016/j.jddst.2021.102351
10.1016/j.jddst.2022.103825       10.1016/j.jddst.2023.104255
10.1016/j.molliq.2021.115405      10.1016/j.nano.2015.06.007
10.1021/acs.molpharmaceut.1c00820 10.1038/s41467-023-41946-8
10.1208/s12248-016-9958-2         10.1208/s12249-017-0877-z
10.1208/s12249-021-01940-z        10.1208/s12249-022-02489-1
10.2147/IJN.S109547               10.2147/IJN.S339979
```

全表另有 63 篇 DOI 来自 LNP_Atlas 和 Luciani（大分子与空载），命中这些的论文若含小分子配方，**不判重复**，因为现有提取只取了其中的大分子记录。此类论文标 `partially_extracted_before = TRUE`。

### 5.3 待定池

不满足 N4 或 N5 的论文不直接丢弃，进待定池，记录在 `docs/screening-table.csv` 里 `初筛结论 = 待定`。待定池的用途：

- `needs_fulltext` 的论文构成「优先获取全文清单」（第三步交付物）
- `fulltext_status = unavailable` 的论文列出来，供你用 KU / DTU 权限人工尝试

**待定池里的论文在拿到全文前，一律不计入第四节的数据点估计。** 估计只基于已确认的数值。

### 5.4 现有 22 个化合物（用于判断新增是否真的新增）

doxorubicin, amphotericin B, bupivacaine, rhodamine B, carboxyfluorescein, atenolol, propranolol, BAY 87-2243, sulforhodamine B, calcein, vincristine sulfate, budesonide, fraxetin, tetrodotoxin, hydrocortisone, amoxicillin, methotrexate, temoporfin, gemcitabine, hydroxy-alpha-sanshool, paclitaxel, 5-fluorouracil carbonate

新采集的化合物按 `payload_inchikey` 和这 22 个比对。InChIKey 相同即为已有化合物，**它贡献的是新配方记录，不是新化合物**。第四节的汇总必须把这两件事分开报。

---

## 六、去重规则

去重的目的不是删行，是**让模型划分时知道哪些行不独立**。所以规则产出的是分组 id，不是删除操作。

### 6.1 第一层：与仓库现有数据去重

1. 按 `paper_doi` 比对 5.2 节的 34 篇。命中即 X11 排除，不重复提取
2. DOI 不同但 `payload_inchikey` + 组成向量 + `prep_method_std` 与现有记录一致：保留，标 `dedup_role = duplicate`，`dedup_group_id` 指向现有记录的 `formulation_id`

### 6.2 第二层：跨论文同一配方

典型情况是经典配方被反复复现（如 Doxil 的 HSPC:Chol:PEG-DSPE = 56.3:38.4:5.3，`data-inventory.md` 3.3 节已记录其在多篇文章里重复出现）。

规则：

1. 去重键 = `payload_inchikey` + 组成向量（各槽位 mol% 四舍五入到 **0.1**）+ `prep_method_std` + `loading_mode`
2. 键相同的记录归入同一 `dedup_group_id`，**全部保留**
3. 组内选 `primary`：优先 `data_quality_tier` 高的；同级则优先 `value_read_from = table`；再同级则优先年份新的（工艺描述通常更完整）
4. 建模时的用法写死：**同一 `dedup_group_id` 内的记录不得跨训练集和测试集**。这一条和现有 `docs/evaluation-protocol.md` 的分组原则一致

### 6.3 第三层：同一论文内同一配方的多次测量

现有数据的主要重复来源（`data-inventory.md` 3.3 节：216 条有粒径的记录只对应 76 个唯一组合，14 个组合的粒径值在所有行里完全相同）。

规则：

1. 对**配方固有属性**（粒径、PDI、Zeta、EE）：同一配方在同一 block 内多次报告且数值相同，**只保留一行**，`block_n_records` 记录原始行数
2. 数值不同（例如不同储存时间点、不同介质）：保留多行，但 `qc_flag` 标 `suspect` 并在 `qc_reason` 写明差异来源。**配方固有属性在同配方下出现多个不同值，说明有未记录的变量，这类记录不进主数据集**
3. 同一配方在不同 block（论文内换了工艺）：是不同记录，不去重，这正是有价值的组内对比

### 6.4 第四层：综述汇总表

综述本身判 X5 排除。但综述里的汇总表是高效的论文发现渠道。处理方式：

1. 从综述汇总表拿到的是**原始论文线索**，不是数据
2. 必须追到原始论文，在原始论文里按 N1 到 N5 重新判定并提取
3. 追不到原始论文的，整条丢弃，**不许以综述为出处录入数据**
4. 综述本身记在 `docs/worklog/` 的发现来源里，不进 `screening-table.csv` 的纳入行

### 6.5 冲突处理

同一配方在两篇论文报了差异很大的数值（例如粒径差一倍以上）：

1. 两条都保留，同一 `dedup_group_id`
2. 两条都标 `qc_flag = suspect`，`qc_reason` 写明冲突对象
3. **不许挑一个「看起来对的」保留**。冲突本身是「跨来源不可比」的证据，要在第四步的报告里统计这类冲突的数量和幅度

---

## 七、需要你决策的事项

### 决策 1：这次采集的目标是什么（最重要）

第零节说明了：池化文献数据按分子分组建模，是本项目已经证伪过的做法。三个选项：

**A. 按原计划采集，目标是扩大唯一化合物数（22 → 尽可能多）**
接受「跨来源不可比」的限制，把新数据当作更宽的化学空间覆盖，建模时必须用论文级固定效应或只做组内对比。能回答「化学空间铺开后，分子效应是否浮现」。

**B. 只采集论文内多配方对比，特别是 `block_varies_by = payload` 的 block**
数量会少很多，但每个 block 内部工艺固定，等于「别人做过的单因素实验」。这是文献里唯一和 `data-spec-ee.md` 要求的自建实验设计同构的数据。质量最高，量最少。

**C. 先做一次小规模可行性探查（约 50 到 80 次检索），只回答「文献里到底有多少个 `block_varies_by = payload` 的 block」**
再决定投入。成本最低，但要多花一轮。

**我的建议是 B 为主、A 为辅**：主力采集论文内多配方 block，同时把顺带发现的新化合物按 A 收进来标记好，但在报告里分开报两类数据的量。理由是 A 单独做下去，大概率复现 `+0.01` 那个结果。这件事取决于你要拿这批数据回答什么问题，我不替你定。

### 决策 2：包封率要不要作为采集重点

现有小分子子集 EE 是 0 条，所以采集 EE 是纯增量。但 `data-spec-ee.md` 明确说文献 EE 不能用来扩充自建数据。两者不矛盾（一个是扩充文献集，一个是扩充自建集），但要确认 EE 数据的用途：

- 用途一：做「文献 EE 在组内是否可学」的检验，为自建实验设计提供先验
- 用途二：和未来自建数据做方法学对齐（`data-spec-ee.md` 2.3 节建议含 3 到 5 个文献已有可靠 EE 的分子）

两个用途都成立，但都不是「直接混进训练集」。确认按这个定位采集。

### 决策 3：Consensus Library 的 collection 名称

你要求同步到 `My Library / LNP Collection`。我还没有列过你的 collection 列表（列 collection 要跑一次 thread，会消耗检索额度，所以放到第二步开始时做）。需要确认：

- 如果 `LNP Collection` 已存在，直接存入
- 如果不存在，是否授权我创建一个同名 collection
- 是否要按检索层次分成多个 collection（如 `LNP-DoE`、`LNP-SmallMol`），还是全部进一个

### 决策 4：MW 上限和荧光探针

沿用 `data-inventory.md` 的默认（900 Da 上限、探针保留但标记），还是本次改口径。我默认沿用，因为改口径会让新旧数据不可比。

### 决策 5：检索额度分配

每月 1000 次，每次返回 20 篇。第二步的五层检索按本协议大约需要 **120 到 180 次检索**（每层 20 到 40 个互不重叠的检索式）。确认这个额度量级可以接受，还是要压缩到更少。

---

## 八、执行与记录要求

### 8.1 检索日志

每层检索后在 `docs/worklog/` 写一份日志，文件名 `2026-10-DD-检索第N层.md`，必须包含：

1. 每个检索式的**完整查询词原文**
2. 该检索式**想覆盖什么**，以及**为什么和前面的不重复**
3. 命中数（Consensus 返回的实际条数）
4. 其中新论文数、已见过的论文数
5. 初筛通过数
6. 累计已用检索次数

### 8.2 不许做的事

1. **不许把摘要里的描述当定量数据**。摘要无具体数字的，标 `needs_fulltext = TRUE`，不猜
2. **不许凭印象补 DOI、年份、作者**。全部来自 Consensus 返回结果，不确定的标 `待核实`
3. **不许为了凑数放宽纳入标准**。本协议确认后冻结
4. **不许静默删除记录**。排除的保留在 screening-table 并写明理由
5. **不许以综述为数据出处**

### 8.3 交付物清单

| 步骤 | 交付物 | 状态 |
|---|---|---|
| 第一步 | `docs/literature-protocol.md`（本文） | 待确认 |
| 第二步 | `docs/worklog/` 下 5 份分层检索日志 | 未开始 |
| 第三步 | `docs/screening-table.csv` + 优先全文清单 + DoE 论文清单 | 未开始 |
| 第四步 | `docs/literature-report.md` | 未开始 |

---

## 九、本协议的已知局限

写在这里，避免事后被当成疏漏：

1. **本协议无法解决「跨来源不可比」这个根本问题**，只能通过 `study_block_id` 把可比的子集标出来。如果文献里 `block_varies_by = payload` 的 block 很少，那么结论就是文献数据解决不了精度问题，这个结论本身是第四步要诚实写出的
2. **Consensus 的语义检索不等于系统性文献综述**。它不是 PRISMA 流程，没有检索式的布尔完备性保证，召回率未知。本协议产出的是「一个有记录、可复现的扩充过程」，不是「穷尽式综述」。报告里不得表述为 systematic review
3. **提取靠读全文，本轮由我做，没有第二人独立复核**。标准的数据提取要求双人独立提取再比对。本轮做不到，所以 `extraction_confidence` 和 `source_location` 两列是唯一的事后复核手段，必须填全
4. **图里数字化读数的误差没有量化**。C 级记录的误差幅度未知
5. **`block_varies_by = payload` 的 block 也只在该论文的单一配方下成立**，换配方是否还成立无法从文献回答
