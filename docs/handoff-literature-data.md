# 交接：文献数据采集与抽取（2026-10-26 至 10-29）

本文件只讲这一轮的文献数据采集与抽取，不覆盖仓库早先的建模轮次。2026-11 并入 main 时按复核结果做了更正，更正清单在第十节。

- 本轮成果已并入 main。合并时只有两处冲突：`.gitignore` 保留 main 的英文注释；`README.md` 以 main 的英文版为准，原有两段中文（本文件入口、环境准备）改写成英文并入
- 合并后把三个脚本的基线路径改为 `data/raw/merged_formulations_v2.csv`。main 早先已把这个文件从仓库根目录移到 `data/raw/`

## 零、先知道的五件事

**1. 核心结论是负面的。** 四个数据集全部抽完，唯一化合物数从 22 变成 22，净增 0。详见第二节。

**2. 仓库里没有「既有结构又有包封率」的小分子记录。** 基线的 22 个化合物来自 PMC_IVR 的 272 行，这些行有粒径、PDI、zeta 和释放曲线，包封率一列全空。本轮新抽的 Jaki 与 Xu 有包封率，但载荷没有结构，分子量也都超过协议的 900 Da 上限。见第二节末。

**3. 下一步不能直接开工。** 停下的位置是特征对比实验，但它目前既缺数据也缺放行，见第四节第 1 条。

**4. 五个挂起数据集的授权问题仍未拍板。** 见第五节第 1 条。

**5. main 上另有材料与这一轮相关。** `docs/handoff-data-engineering-2026-11-11.md` 是 Consensus 文献语料（9,464 行候选表）的交接，属另一条线；`docs/handoff.md` 是三轮建模的交接；`docs/alignment-2026-10-29.md`、`docs/next-actions.md`、`docs/decisions-pending.md` 给本轮安排过后续，包括用本轮的采集协议筛候选文献、自采分子面板与 Khawar 2022 的实测化合物取交集、三臂特征对比实验。

## 一、这一轮做了什么

| 阶段 | 产出 | 状态 |
|---|---|---|
| 采集协议 | `docs/literature-protocol.md`（2026-10-27 冻结） | 完成 |
| 可行性探查 | `docs/feasibility-probe.csv`，108 条候选，18 次检索 | 完成 |
| 授权登记 | `docs/data-licensing.md` | 完成 |
| 四个数据集抽取 | 见第二节 | 完成 |
| 特征对比实验 | 无 | 未开始。按用户要求停在这里等确认，执行前提见第四节第 1 条 |

检索额度：本轮用了 18 次，当时给本轮划的预算是 80 次。协议里写的「月额度 1000 次」没有出处，以 `docs/quota-ledger.md` 为准：月上限 500 次，所有 API key 与客户端合并计算，每月 1 日重置。额度跟着 Consensus 账号走，用的是同一个 Consensus 账号，不论在哪里接手都是同一份额度。2026 年 11 月的额度已经用尽（台账记到第 491 次），12 月 1 日重置。

## 二、四个数据集的抽取结果

全部是 CC BY 4.0。每条记录都带 `source_doi`、`source_license`、`source_attribution`。

| 数据集 | 类型 | 记录 | 唯一化合物 | 与现有重叠 | 合并后 |
|---|---|---|---|---|---|
| Khawar 2022 | 分子属性表 | 490 | 423 | 能连上配方的只有 1 个 | 22 |
| Yanes 2025 | 增补表 | 271 | 0 | 22（同一份数据） | 22 |
| Jaki 2026 | 配方表 | 45 | 0（载荷无结构） | 0 | 22 |
| Xu 2022 | 探针集 | 20 + 5 | 0（载荷无结构） | 不计入 | 不计入 |

产物在 `data/processed/`：

- `partition_coefficients.csv`（490）：四张表的脂质/水分配系数加 Abraham 描述符
- `yanes2025_enrichment.csv`（271）：给现有 PMC_IVR 记录补 14 列，其中真正新增信息的是 9 列（见下）
- `formulations_jaki2026.csv`（45）：DoE 配方表
- `probe_xu2022.csv`（20）加 `probe_xu2022_compounds.csv`（5）：探针集

### 为什么净增是 0，逐个说

**Khawar 2022**：423 个化合物里只有 1 个（propranolol）能连上现有配方记录。分子量中位数按 423 个唯一化合物是 134 Da（按表 S1、S2 的 430 行不去重是 128 Da），现有数据是 415 Da；没有一个类黄酮。它是环境化学的分子，和制剂学几乎不重叠。

它和立项假设（整体亲脂性参数 logKow 不足以代表膜分配）的关系要分开看：

- 表 S1、S2 的实验脂质/水系数与 logKow 高度相关（储存脂 r = 0.98，磷脂 r = 0.97，磷脂/水平均比 logKow 高 0.19 个 log 单位）。这两张表里的 logKow 是原文的**预测值**（表题原文 "predicted values of logKow and logKaw"），实验值只有 logKlw 和 logKpw。改用表 S5、S6 里的实验 logKow，相关系数仍在 0.97 到 0.98。所以对非极性中性小分子，结论成立
- 表 S15 是脂质体/水体系，36 个化合物，多为可电离的药物类分子。原文用 logKow 与 logKaw 建的模型，预测值对实验值 r 只有 0.78，RMSE 0.57，最大残差约 1.6 个 log 单位（warfarin +1.59，quinine +1.37）。CSV 只抽了实验值，预测值与残差两列没有抽，这一层此前没有分析过
- 酚类有系统正偏差：含芳香羟基的 46 个化合物，logKpw 平均比 logKow 高 0.3 到 0.4（用预测或实验 logKow 结果相近），非酚类只高 0.05 到 0.09。方向与立项假设一致。圣草酚是多酚类黄酮，而这份数据里没有类黄酮
- 表 S14 的 logKtw 是三油酸甘油酯/水（triolein-water），抽取时误标成「组织/水」，被排除在用途之外

结论：「Khawar 不支持立项假设」只对非极性中性小分子成立。对可电离药物和酚类，这份数据反而显示出偏差，只是样本小、多为文献汇集值，只能定性。

**Yanes 2025**：它就是仓库里 PMC_IVR 的来源，不是新数据源。这一点仓库早有记录：数据字典 `archive/2026-09_first-model/docs/M2_PMC_IVR_data_dictionary.md`（2026-10-18 首次提交）已写明 PMC_IVR 来自 Yanes 等人的诺丁汉 IVR 数据库，所以 10-28 的验证是复核，不是新发现。复核结果：

- 22 个载荷的 SMILES 字符串两边逐字相同
- PMC_IVR 272 行中 271 行按 IVR_ID 连上。缺的是 IVR 104（配方 41，两性霉素 B），它不在 GitHub 快照的 `backend_data.csv` 里，只在诺丁汉存档的数据库里
- 能配对的 216 个粒径数值差值全为 0（原先写的「差小于 0.51 nm」偏保守）。这项粒径核对不在 `extract_yanes2025.py` 里，仓库里无法重跑

增补表的 14 列里，4 列是连接键或已有字段的重复（`source_row_id`、`release_curve_file`、`ivr_id_from_curve`、`API_name`），`media_temp_oC` 的内容主表 `process_notes` 里已有，真正新增的是 9 列：`drug_loading`、`media_volume_mL`、`media_components`、五个质量评级列，以及 `quality_nan`。最后这列其实是原表的 Comments 列，只有 5 行非空。

**Jaki 2026 和 Xu 2022**：都是单载荷变配方。载荷没有可用的结构式（Jaki 原文没给 ACBI2 的结构，Xu 的取代基只以图片给出），算不出 InChIKey，无法参与按化合物分组的建模。即使按协议允许的名称查询补上结构，两个载荷的分子量（ACBI2 1064 Da，Xu 的 4d 1151 Da）也都超过协议的 900 Da 上限。

### 能用来建包封率模型的记录有多少

这是比「唯一化合物数」更要紧的数字：**0**。

- 基线 22 个化合物对应 PMC_IVR 的 272 行，包封率一列全空，只有粒径 216、PDI 150、zeta 124 和释放曲线
- 主表里有包封率的 563 行全部来自 LNP_Atlas，那是核酸 LNP，按可离子化脂质记录，没有小分子载荷结构
- Jaki 与 Xu 有包封率（45 条和 12 条），但没有载荷结构，且分子量超限

所以第四节第 1、2 条要先解决数据问题。

## 三、怎么复现

依赖（`README.md` 的 Reproducing the results 一节有同样的内容）：

```
pip install scikit-learn rdkit pyarrow matplotlib tabulate pdfplumber python-docx
```

`rdkit` 是 `extract_khawar2022.py` 与 `report_compound_gain.py` 的硬依赖；`pdfplumber` 给 Jaki 和 Xu 的脚本用，`python-docx` 给 Khawar 和 Jaki 的脚本用。

抽取脚本都在 `scripts/`，只读原始文件，不改写 `data/raw/`：

```
python3 -I scripts/extract_khawar2022.py data/raw/khawar2022_klipw/41598_2022_19452_MOESM1_ESM.docx
python3 -I scripts/extract_yanes2025.py <nanomed_IVR_data-main.zip 解压后的目录>
python3 -I scripts/extract_jaki2026.py data/raw/jaki2026_doe/1-s2.0-S2590156726001477-mmc1.docx \
                                       data/raw/jaki2026_doe/1-s2.0-S2590156726001477-main.pdf
python3 -I scripts/extract_xu2022_probe.py data/raw/xu2022_ptx_probe/molecules-27-07967.pdf \
                                           <补充材料 zip 解压后的 PDF 路径>
python3 -I scripts/report_compound_gain.py       # 五个数字的汇总报告
python3 -I scripts/record_raw_checksums.py --verify   # 校验原始文件没被改动
```

`-I` 会让 Python 忽略用户目录里的包，依赖若是用 `pip install --user` 装的，去掉 `-I`。本机若留着被忽略的 `standardisation_nm_IVR.zip`，`--verify` 会把它报成一个未登记文件，属正常。

Xu 的脚本自带两层自检：三项「对照正文文字描述」的交叉验证，加 28 个硬编码数字从 PDF 文本层回读核对。不通过会返回非零退出码。

## 四、未完成的任务

按原计划的顺序排。

1. **特征对比实验。** 这是停下的位置：用户要求三个数据集抽完后停下，等确认再进入特征对比实验。四个都抽完了，没有开始。执行前要先解决三件事：
   - **没有数据。** 见第二节末，可建包封率模型的小分子记录是 0 条
   - **没有放行。** main 上的定义是三臂对比（现有特征 / 加 Klip,w / 加物理动机描述符，见 `docs/next-actions.md` 第 1.4 条与 `docs/alignment-2026-10-29.md`），要求先写进 `docs/evaluation-protocol.md` 再跑。该文件自 2026-11-01 起按用户指示冻结（`docs/decisions-pending.md`），三臂至今没有写进去
   - **第二臂缺料。** 有实测脂质体/水分配系数的只有表 S15 的 36 个化合物，能和现有配方记录对上的只有 1 个
2. **在合并数据上重跑分组 CV。** 原计划排在抽取之后，没有做。预期价值很低：Yanes 是同一份数据，Jaki 与 Xu 没有结构，合并后可建模的记录不会增加。做之前先看第五节第 3 条
3. **自建实验。** 用户说「自建实验在这之后」，没有开始。规格在 `docs/data-spec-ee.md` 与 `docs/phase1-design.md`，main 的 README 把它列为下一步主线
4. **Yanes 增补字段要不要并进 `merged_formulations_v2.csv`。** 未决。真正新增的是 9 列（第二节）。增补表是独立文件，没有动主表
5. **Khawar 数据的已知问题。** 修复要重跑抽取（需要 `python-docx`）：表 S2 有 5 个 CAS 号是 Excel 日期序列号（如 65386 对应 79-01-6），源头在补充材料；表 S11 有一行把四氯化碳的 CAS 与 SMILES 配给了四氟化碳；表 S14 被误标为组织/水；表 S15 的预测值与残差两列没有抽。缺 SMILES 的 6 条记录，在补充材料别的表里都能按名称找到结构
6. **Zotero 同步没有做成。** 用户最初要求同步存入 My Library / LNP Collection，Consensus 当时回复不能管理 collection。降级方案是导出 DOI 清单：`docs/feasibility-probe-dois-include.txt`（75 条：71 条「纳入」加 4 条「部分纳入」）和 `-all.txt`（108 条全部），可以直接导进 Zotero。注意 include 清单里包括五个挂起数据集，「纳入」只是筛选判定，能不能抽取以 `docs/data-licensing.md` 为准

## 五、有分歧或悬而未决的地方

### 1. 五个挂起数据集，这是最要紧的一条

**现状：五个全部挂起，未抽取，没有进仓库。** 2026-11-13 按文件哈希核对过：这五个数据集的任何文件都不在仓库的对象库里，包括已不可达的旧提交。

用户 2026-10-27 的口径：CC BY 4.0 的照常处理（Khawar、Yanes、Jaki 进抽取，Xu 2022 只作外部探针集），其余五个全部挂起：不进管线、不进仓库、不做测试，也不「先抽着以后再删」，等拿到书面授权答复再说。执行时按这个口径。

后来用户提出这五批也要用，理由是大多数已经拿到了数据。当时没有照办，理由是**能拿到数据和有权使用是两件事**，而且仓库是公开的。按风险分三档：

| 数据集 | 授权 | 问题 |
|---|---|---|
| Khodadadi 2025、Shahiwala 2023 | 无开放授权 | 最清楚的问题：根本没有授予再分发或再使用的权利 |
| Lavagna 2026 | CC BY-NC | NC 禁止商业使用，LipidLens 是商业项目 |
| Buttitta 2025、Han 2023 | CC BY-NC-ND | NC 之外还有 ND，抽取成另一种 schema 很可能构成演绎 |

当时给过两个选项：仓库转私有，或者原始文件不进 git、只提交抽取后的数字。用户没有答复，挂起状态保留至今。复核后补两点：

- 第二个选项解决不了问题。授权登记的规则是挂起期间不抽取；NC 与 ND 约束的正是抽取之后的使用与改编
- 仓库转私有能缓解再分发问题（两篇无开放授权的，以及 ND），但改变不了 NC 的商业使用限制。NC 限制的是用途，与仓库是否公开无关

这是用户的决定。如果用户判断风险可接受，或者拿到了书面授权，就按用户的决定执行；原始文件都在用户本机（见第七节），不用重新下载。每个数据集解除挂起的条件记录在 `docs/data-licensing.md` 第三节。

**数据可获取性要更正。** 2026-10-28 的核查认为 Khodadadi 与 Shahiwala「数据本身也拿不到」。复核发现用户本机两个文件夹里都有补充材料，含完整数据表：

- Khodadadi 2025：xlsx，503 行、27 列，含载荷名、各组分摩尔比、粒径、包封率、zeta，来自 118 篇文献、86 种载荷
- Shahiwala 2023：docx 附录 A，114 行、13 列，含包封率与粒径，但没有药物名称列，算不出载荷结构

所以五个都是数据可得、卡在授权。另外，Khodadadi 是 118 篇文献的汇总，属于第五节第 2 条说的跨来源数据，授权即使解决，对精度的帮助也有限。

### 2. 「采集更多文献能提高模型精度」这个前提，和仓库已有的结论冲突

这一点在第一天就提出过，用户接受并改成先做可行性探查，所以不算分歧，但接手的人需要知道：

`docs/data-spec-ee.md` 里已经写定一条结论：**跨源包封率不可比**。它来自第二轮建模，数据是 LNP_Atlas 里核酸 LNP 的可离子化脂质。仓库里没有小分子包封率记录，所以这条结论在小分子脂质体上没有被直接检验过。

原稿这里引用了 Adzavon 2026 作为旁证，这个引用不对题：它研究的是核酸 LNP 储存后的粒径变化，不是包封率；613 条配方对仓库包封率轮的 370 个单元只是 1.7 倍，18 个研究还少于仓库的 37 篇；R² 中位数 −1.53 是 12 个合格研究逐研究建模的结果；而且只读了摘要（`docs/worklog/2026-10-27-可行性探查.md` 自己写的是「规模大 2.3 倍」）。它不能作为「别人用多一个数量级的数据得到同样负面结果」的证据。

探查还发现：P 类区组（变载药分子、固定配方，统计上唯一站得住的那种）很稀缺，纳入的 E1 证据只有 19 篇，每篇中位数 3 个分子；L 类区组（变脂质配方）多得多，纳入的 E1 有 41 篇（原写 36 篇，是第二批检索之前的数），从 DoE 密度推断文献里是数百到上千篇的量级。19 篇来自少量定向检索，召回率未知，应视为下限。**瓶颈是化合物多样性，不是记录条数。** 继续堆 L 类数据不会解决问题。

### 3. Jaki 和 Xu 要不要并进主表：建议不并

建议**不并进 `merged_formulations_v2.csv`，单独成块用**。两者都是单载荷变配方，和主表的跨源结构不同，合并训练会把不可比的东西混在一起。这条建议用户还没有回应，现状是两个文件独立存放。

### 4. schema 的 4 个脂质槽位不够用

Jaki 的 DOPG 是阴离子脂质，仓库 schema 只有 ionizable / helper / sterol / peg 四个槽位，没有它的位置，只能和 DOPC 一起放进 helper 槽。但 DOPG 是该文 zeta 电位的主要驱动（阴离子份额与 zeta 的 r = −0.645；DOPG=0 组中位 −2.2 mV，DOPG>0 组 −16.3 mV）。处理方式是额外立三列（`component_dopc_pct`、`component_dopg_pct`、`anionic_lipid_frac_of_total`），原文四元组完整留在 `composition_raw_verbatim`。

**协议 schema 已冻结，这一轮没有改。** 但阴离子脂质（DOPG、DOPS、DSPG）在脂质体文献里很常见，后续批量抽取时还会再遇到，届时应评估要不要加一组 `anionic_lipid_*` 槽位。

### 5. 收集阶段出现过两次同一类错误

两次都是**把摘要的描述当成了定量事实**，这正是协议明令禁止的。已在 `docs/feasibility-probe.csv` 两行里加了更正说明：

- **Jaki 2026**：摘要说 "demonstrated across three distinct PROTACs"，被读成三个载荷各有配方数据。实际 ACBI1/ACBI3 只出现在 HPLC 方法验证的文字里（各 6 次提及，ACBI2 是 84 次），没有任何配方数据。`block_class` 由 `both` 改 `L`
- **Xu 2022**：原以为 19 个衍生物各有包封率。实际 19 个只有细胞毒性数据，只有 5 个试过载入脂质体，4 个失败且只有定性描述，有定量包封率的只有 compound 4d。`block_class` 由 `P` 改 `L`，`est_formulations` 由 19 改 12

Yanes 那一行的预期也落空了：表里写的是「正好补仓库缺失的 272 条释放曲线」，实际它就是 PMC_IVR 的来源，GitHub 快照里也没有释放曲线。抽到的四篇里，有三篇的摘要判断需要修正。

**含义：`feasibility-probe.csv` 里那 108 条的 `block_class` 和 `est_formulations` 是按摘要判断的，没有逐篇核对全文。** 后续用这张表排优先级时，要知道它的误差有这么大。另：该表第 34 行（Shi 2019）原先有一个字段含逗号却没加引号，并入 main 时已修正。

## 六、两件不在计划内的发现

**1. 7 条载药失败的负样本。** Xu 表 S1 的 6 条（乙酸钙梯度）加表 4 的 ATP 一条。原文包封率一栏写 `---` 和 `—`，是明确失败而非缺测，已置 `formation_ok = FALSE`。现有主数据集几乎全是成功配方，负样本稀缺，这 7 条原本被看作可以支持「预测配方会不会载药失败」的二分类问题。用之前要知道它的局限：6 条来自同一篇论文的同一种梯度法，失败与方法完全混杂；表 S1 的载荷不确定（原文没说是哪个化合物，`payload_type` 记为五个候选之一），用之前看 `payload_id_source`。

**2. 原稿写「整体亲脂性参数分辨不了载药行为，两个独立证据」，这条撤回。**

- Khawar 没有载药数据，它讲的是分配系数之间的相关，推不出载药行为；第二节也说明了，对可电离药物和酚类，它反而显示出偏差
- Xu 的 5 个化合物是同一骨架，logD 与 pKa 几乎相同（极差 0.25 和 0.005），分不出 1 成 4 败是意料之中，不能推广到一般情形

所以「特征工程只堆 logP / logD / pKa 不太可能分辨配方成败」这句话，按现有证据既不能肯定也不能否定。

## 七、原始文件在哪（含一个数据缺口）

### 7.1 用户本机

九个数据集的原始文件都在用户本机的项目文件夹里，不在仓库内；四个可用数据集另有一份提交进了 `data/raw/`。九个文件夹：

| 文件夹 | 数据集 | 授权 | 在仓库里吗 |
|---|---|---|---|
| `1. Khawar 2022` | Khawar 2022 | CC BY 4.0 | 在，`data/raw/khawar2022_klipw/` |
| `2. Yanes 2025` | Yanes 2025 | CC BY 4.0 | 在，`data/raw/yanes2025_ivr/`（大压缩包除外，见 7.2） |
| `3. Jaki 2026` | Jaki 2026 | CC BY 4.0 | 在，`data/raw/jaki2026_doe/` |
| `4. Xu 2022` | Xu 2022 | CC BY 4.0 | 在，`data/raw/xu2022_ptx_probe/` |
| `1. Khodadadi 2025` | Khodadadi 2025 | 无开放授权 | 不在，挂起 |
| `2. Lavagna 2026` | Lavagna 2026 | CC BY-NC | 不在，挂起 |
| `3. Buttitta 2025` | Buttitta 2025 | CC BY-NC-ND | 不在，挂起 |
| `4. Han 2023` | Han 2023 | CC BY-NC-ND | 不在，挂起 |
| `5. Shahiwala 2023` | Shahiwala 2023 | 无开放授权 | 不在，挂起 |

**注意编号是重复的。** 1 到 5 各出现两次：可用的四个是 `1. Khawar` / `2. Yanes` / `3. Jaki` / `4. Xu`，挂起的五个是 `1. Khodadadi` / `2. Lavagna` / `3. Buttitta` / `4. Han` / `5. Shahiwala`。上一轮拷文件时在这里出过问题，按编号匹配会把挂起的数据集拷进来。**按名字匹配，不要按编号。** 部分文件夹里还有未解压的内层压缩包。

`data/raw/jaki2026_doe/` 原先还有一份 PubMed 相关文献导出（`linked-discoveries-42598203-50rows-2026-10-28.csv`），并入 main 时删去，原因见该目录的 `README.md`。

### 7.2 一个数据缺口

`standardisation_nm_IVR.zip`（约 269 MB，诺丁汉机构库的存档）不在仓库里。它超过 GitHub 单文件 100 MB 的上限，当时推送失败，撤出后加进了 `.gitignore`。它只在用户本机：项目文件夹的 `2. Yanes 2025` 下，本地克隆的 `data/raw/yanes2025_ivr/` 里也有一份（被忽略）。

**不要把它整包放进 Git LFS 或任何公开存储。** 包里约 94% 是第三方论文：`data/papers/` 下 35 个出版社 PDF（约 135 MiB），数据库 `liposome_IVR.db` 的 papers 表还内嵌了 34 篇 PDF（约 141 MiB）。这些 PDF 出版方以 Elsevier 为主，只有 5 个带 CC 授权标记。真正需要的释放曲线是 `data/drug_release/` 下的 275 个 CSV。这份存档公开可下（DOI `10.17639/nott.7542`，见 `data/raw/yanes2025_ivr/README.md`），仓库不需要备份它；以后要用释放曲线，只提取曲线文件。目前的抽取没有用到它（`yanes2025_enrichment.csv` 只用了 `backend_data.csv`、`media_components.csv`、`quality_reporting.csv`）。

## 八、接手须知

1. **仓库与推送。** `SiyaoGui/LNP-Formulation-Predictor` 目前是公开仓库。推送规则见 `docs/funding-ops/HANDOVER.md`：只推 main，不建分支、不打标签、不强制推送；`git add` 只用精确路径
2. **原始文件。** 原始文件和五个挂起数据集只在用户本机（第七节）。联网受限的环境访问不到出版社网站与 zenodo.org，需要原始文件时由用户下载后提交
3. **Consensus 额度。** 见第一节：月上限 500 次，按 Consensus 账号计算，每月 1 日重置
4. **依赖。** 见第三节
5. **授权判断与仓库可见性。** 见第五节第 1 条：转私有能缓解再分发，改变不了 NC 的商业使用限制

## 九、关键文件索引

| 文件 | 作用 |
|---|---|
| `docs/literature-protocol.md` | 采集协议，2026-10-27 冻结，2026-11-14 修订一处字段说明。纳入/排除标准、提取字段表、质量分档、去重规则 |
| `docs/data-licensing.md` | **授权的唯一依据**。四个可用加五个挂起，含解除挂起的条件 |
| `docs/feasibility-probe.csv` | 108 条候选。注意第五节第 5 条说的误差 |
| `docs/feasibility-probe-dois-include.txt`、`docs/feasibility-probe-dois-all.txt` | 导入 Zotero 用的 DOI 清单（75 条与 108 条） |
| `docs/schema-partition-coefficients.md` | Khawar 那张表的 schema |
| `docs/compound_gain_stats.json` | 五个数字的机器可读版本 |
| `docs/worklog/` | 本轮 7 份，文件名以 2026-10-26 至 2026-10-29 开头。抽取报告是 10-28 和 10-29 那四份 |
| `data/raw/README.md` 与 `data/raw/*/README.md` | 原始文件的规则；每个来源的下载链接、校验值、做过哪些修改（CC BY 署名要求） |
| `docs/quota-ledger.md` | Consensus 额度台账 |
| `docs/handoff-data-engineering-2026-11-11.md` | Consensus 文献语料的交接（另一条线） |
| `archive/2026-09_first-model/docs/M2_PMC_IVR_data_dictionary.md` | PMC_IVR 的数据字典，写明来源是 Yanes 等人的诺丁汉 IVR 数据库 |

## 十、2026-11 复核更正

2026-11-13 用本机原始文件与仓库数据独立复算，以下内容与原稿不同：

| 位置 | 原稿 | 更正 |
|---|---|---|
| 第一节 | Consensus 月额度 1000 次，按账号算，换账号不受限 | 月上限 500 次，按 Consensus 账号合并计算，2026 年 11 月已用尽 |
| 第二节 Khawar | r 大于 0.97，不支持立项假设 | 表 S1、S2 比的是预测 logKow；表 S15（可电离药物）r 0.78；酚类有 0.3 到 0.4 的系统正偏差；表 S14 是三油酸甘油酯/水；分子量中位数按唯一化合物是 134 Da |
| 第二节 Yanes | 新验证出它是 PMC_IVR 的来源；粒径差小于 0.51 nm；补 14 列 | 仓库 2026-10-18 起已有记录；缺 IVR 104；粒径差全为 0；真正新增 9 列 |
| 第二节末 | 无 | 可建包封率模型的小分子记录是 0 条 |
| 第四节第 1 条 | 停在特征对比实验 | 执行前提：缺数据、协议冻结未放行、第二臂缺料 |
| 第五节第 1 条 | Khodadadi、Shahiwala 数据拿不到 | 用户本机有完整数据表，只卡在授权；转私有改变不了 NC |
| 第五节第 2 条 | Adzavon 2026 是同样负面结果的旁证；L 类 E1 36 篇 | 终点和对象都不同，只读了摘要；L 类 E1 41 篇 |
| 第五节第 5 条 | 抽到的两篇判错 | 四篇里有三篇的摘要判断需要修正 |
| 第六节第 2 条 | 两个独立证据说明整体亲脂性参数分辨不了载药 | 撤回 |
| 第七节 7.2 | 可走 Git LFS 或外部存储 | 存档约 94% 是第三方论文 PDF，不能公开存放；存档本身公开可下 |

并入 main 时的数据整理：删去 `data/raw/jaki2026_doe/` 下的 PubMed 相关文献导出（含第三方摘要，不在 CC BY 授权范围内）；`formulations_jaki2026.csv` 的 `extracted_by` 改为抽取脚本路径；修正 `feasibility-probe.csv` 第 34 行。
