# 交接：文献数据采集与抽取（2026-10-26 至 10-29）

写给下一个窗口做数据工程的人。本文件只讲这一轮工作，不覆盖仓库早先的建模轮次。

- 分支：`claude/tender-franklin-m4ghya`，14 个提交，已全部推到远程
- 工作区干净，没有未提交的改动
- 起点：`56e46d3`（「合并小分子基线三轮工作到 main」）

## 零、开始之前必须知道的三件事

**1. 不要用 `main` 当基线。** 另一个账号在 `main` 上并行提交了大量内容
（Consensus 文献清查、品牌资产、HuggingFace Space 等，400 多个文件）。
本分支是从 `56e46d3` 拉出来的，和现在的 `main` 已经分叉。
我试过合并，11 个文件冲突，其中 9 个是我**根本没碰过**的基线文件
（`configs/*.yaml`、`docs/data-inventory.md`、`scripts/data_inventory.py` 等）
在两边 SHA 不同造成的 add/add 冲突，说明 `main` 的历史被重写过。
**合并要专门安排一次，不要顺手做。** 我没有合并，分支保持在原地。

**2. 这一轮的核心结论是负面的。** 四个数据集全部抽完，
唯一化合物数从 **22 变成 22**，净增 0。详见第二节。

**3. 有一件事悬而未决，涉及授权风险。** 见第五节第 1 条。

## 一、这一轮做了什么

| 阶段 | 产出 | 状态 |
|---|---|---|
| 采集协议 | `docs/literature-protocol.md`（2026-10-27 冻结） | 完成 |
| 可行性探查 | `docs/feasibility-probe.csv`，108 条候选，18 次检索 | 完成 |
| 授权登记 | `docs/data-licensing.md` | 完成 |
| 四个数据集抽取 | 见下表 | 完成 |
| 特征对比实验 | 无 | **未开始，按你的要求停下等确认** |

检索额度：本轮用掉 18 次（当时划的预算是 80 次，Consensus 月额度 1000 次）。

## 二、四个数据集的抽取结果

全部是 CC BY 4.0。每条记录都带 `source_doi`、`source_license`、`source_attribution`。

| 数据集 | 类型 | 记录 | 唯一化合物 | 与现有重叠 | 合并后 |
|---|---|---|---|---|---|
| Khawar 2022 | 分子属性表 | 490 | 423 | 能连上配方的只有 **1** | 22 |
| Yanes 2025 | 增补表 | 271 | 0 | 22（同一份数据） | 22 |
| Jaki 2026 | 配方表 | 45 | 0（载荷无结构） | 0 | 22 |
| Xu 2022 | 探针集 | 20 + 5 | 0（载荷无结构） | 不计入 | 不计入 |

产物在 `data/processed/`：

- `partition_coefficients.csv`（490）四类脂质/水分配系数 + Abraham 描述符
- `yanes2025_enrichment.csv`（271）给现有 PMC_IVR 记录补 14 列
- `formulations_jaki2026.csv`（45）DoE 配方表
- `probe_xu2022.csv`（20）+ `probe_xu2022_compounds.csv`（5）探针集

### 为什么净增是 0，逐个说

**Khawar 2022**：423 个化合物里只有 1 个能连上现有配方记录。
MW 中位数 128 Da（现有数据是 415），零个类黄酮。它是环境化学体系的分子，
和制剂学体系几乎不重叠。另外它**不支持当初立项的假设**：
logKow 与脂相分配系数的相关系数 r > 0.97，系统性偏差只有 0.19 个 log 单位。
注意这只对中性物种成立，「logP 对带电分子有偏」这个更窄的说法，
这份数据既没证实也没证伪。

**Yanes 2025**：它**就是**仓库里 PMC_IVR 的来源，不是新数据源。
三种方式验证过（22 个 InChIKey 完全相同、271 行全部按 IVR_ID 连上、
216 个粒径数值差 < 0.51 nm）。所以产物是增补表不是配方表。

**Jaki 2026 和 Xu 2022**：都是单载荷变配方。载荷原文都不给结构式，
算不出 InChIKey，无法参与按化合物分组的建模。

## 三、怎么复现

环境（云会话容器不预装，每个新窗口都要跑一遍，已写进 `README.md`）：

```
pip install scikit-learn rdkit pyarrow matplotlib tabulate pdfplumber python-docx
```

抽取脚本都在 `scripts/`，只读原始文件，不改写 `data/raw/`：

```
python3 -I scripts/extract_khawar2022.py data/raw/khawar2022_klipw/41598_2022_19452_MOESM1_ESM.docx
python3 -I scripts/extract_yanes2025.py <nanomed_IVR_data-main 解压目录>
python3 -I scripts/extract_jaki2026.py data/raw/jaki2026_doe/1-s2.0-S2590156726001477-mmc1.docx \
                                       data/raw/jaki2026_doe/1-s2.0-S2590156726001477-main.pdf
python3 -I scripts/extract_xu2022_probe.py data/raw/xu2022_ptx_probe/molecules-27-07967.pdf \
                                           <补充材料 PDF 解压后的路径>
python3 -I scripts/report_compound_gain.py       # 五个数字的汇总报告
python3 -I scripts/record_raw_checksums.py --verify   # 校验原始文件没被动过
```

Xu 的脚本自带两层自检：三项「对照正文文字描述」的交叉验证，
加 28 个硬编码数字从 PDF 文本层回读核对。不通过会返回非零退出码。

## 四、未完成的任务

按原计划的顺序排，前面没做完的不要跳过。

1. **特征对比实验。** 这是停下的地方。你当时的原话是
   「三个都抽完后停下来，等我确认再进入特征对比实验」。四个都抽完了，没有开始。
2. **在合并数据上重跑分组 CV。** 原计划里排在抽取之后。没有做。
   做之前先看第五节第 3 条，合并口径有争议。
3. **自建实验。** 你说「自建实验在这之后」。没有开始。
4. **Yanes 的 14 个增补字段要不要并进 `merged_formulations_v2.csv`。** 未决。
   增补表是独立文件，没有动主表。
5. **`main` 的合并。** 见第零节第 1 条。
6. **Consensus 的 Zotero 同步做不到。** 你最初要求「同步存入 My Library / LNP Collection」，
   Consensus MCP 不支持库管理操作（研究代理明确回复无法访问或管理 collection）。
   降级方案是导出 DOI 清单：`docs/feasibility-probe-dois-include.txt`（75 条：71 条「纳入」+ 4 条「部分纳入」）
   和 `-all.txt`（108 条全部），可以直接导进 Zotero。
   日志里记了一个没排除的可能：library 操作也许只在「检索 + 保存」同一次请求里才生效。
   验证要消耗额度，没有试。

## 五、有分歧或悬而未决的地方

这一节是重点。下一个窗口接手前，这几条最好先有结论。

### 1. 五个挂起数据集，这是最要紧的一条

**现状：五个全部挂起，未抽取、未下载进仓库。**
已核对 `data/` 下不存在它们的任何文件，`data/raw/` 下只有四个获准来源的目录。

你在 2026-10-27 给过明确口径：只处理三个 CC BY 4.0 的，
其余五个「全部挂起。不进管线，不进仓库，不做测试，不做『先抽着以后再删』。
等我拿到书面授权答复再说」。我按这个执行了。

后来你说「不，这五批文件也用，因为我大多数已经拿到了数据或者可用数据」。
我当时没有照办，理由是：**能拿到数据和有权再分发是两件事**，
而这个仓库是公开的（`"private": false`）。按风险分三档：

| 数据集 | 授权 | 问题 |
|---|---|---|
| Khodadadi 2025、Shahiwala 2023 | 无开放授权 | 最清楚的问题。不是条款限制，是**根本没有授予任何再分发权利** |
| Lavagna 2026 | CC BY-NC | NC 禁商用。LipidLens 是商业项目 |
| Buttitta 2025、Han 2023 | CC BY-NC-ND | NC 之外还有 ND。重新 schema 化很可能构成演绎 |

我给过两个选项：仓库转私有，或者原始文件不进 git、只提交抽取后的数字。
**你没有回答这个问题，话题转到别处了。** 所以挂起状态保留至今。

这是**你的决定，不是我的**。如果你判断风险可接受，或者仓库已经转私有，
那就按你的决定执行。我只是不想在你没明确拍板的情况下，
把一个公开仓库推到那个位置。记录在 `docs/data-licensing.md` 第三节，
含每个数据集解除挂起需要什么条件。

另：2026-10-28 核查过数据可获取性，五个分成两类。
Khodadadi、Shahiwala 是**数据本身也拿不到**；
Lavagna、Buttitta、Han 是数据能拿到但卡在授权。前两个就算授权解决了也没数据。

### 2. 「采集更多文献能提高模型精度」这个前提，和仓库已冻结的结论冲突

这个我在第一天就提出来了，你接受了并改成先做可行性探查，所以不算分歧，
但下一个窗口需要知道：

`docs/data-spec-ee.md` 里已经冻结了一条结论：**跨源 EE 不可比**。
而这一轮的探查结果独立支持了它。Adzavon 2026 用 18 个研究的 613 条配方
重做了一遍，分组 CV 的 R² 中位数是 **−1.53**，跨研究预测一致失败。
也就是说别人用比我们多一个数量级的数据，得到了同样的负面结果。

探查还发现：P 类区组（变载药分子、固定配方，统计上唯一站得住的那种）很稀缺，
E1 证据的只有 19 篇，每篇中位数 3 个分子；L 类区组（变脂质配方）很多，
E1 有 36 篇，从 DoE 密度推断文献里是数百到上千篇的量级。
**瓶颈是化合物多样性，不是记录条数。** 继续堆 L 类数据不会解决问题。

### 3. Jaki 和 Xu 要不要并进主表，我建议不并

我的建议是**不并进 `merged_formulations_v2.csv`，单独成块用**。
两者都是单载荷变配方，和主表的跨源结构不同，合并训练会把不可比的东西混在一起。
这条我在上一轮末尾提过，你还没回应。现状是没有并，两个文件独立存放。

### 4. schema 的 4 个脂质槽位不够用

Jaki 的 DOPG 是阴离子脂质，仓库 schema 只有
ionizable / helper / sterol / peg 四个槽位，没有它的位置，
只能和 DOPC 一起塞进 helper 槽。但 DOPG 是该文 zeta 电位的主要驱动
（阴离子份额与 zeta 的 r = −0.645；DOPG=0 组中位 −2.2 mV，DOPG>0 组 −16.3 mV）。
我的处理是额外立三列（`component_dopc_pct`、`component_dopg_pct`、
`anionic_lipid_frac_of_total`），原文四元组完整留在 `composition_raw_verbatim`。

**协议 schema 已冻结，这一轮没有改。** 但阴离子脂质（DOPG、DOPS、DSPG）
在脂质体文献里很常见，后续批量抽取时这个问题还会再撞上，
建议届时一并评估要不要加一组 `anionic_lipid_*` 槽位。

### 5. 我在收集阶段犯过两次同一类错误

两次都是**把摘要的描述当成了定量事实**，这正是协议里明令禁止的。
已经改正，`docs/feasibility-probe.csv` 里两行都加了更正说明：

- **Jaki 2026**：摘要说 "demonstrated across three distinct PROTACs"，
  我读成三个载荷各有配方数据。实际 ACBI1/ACBI3 只出现在 HPLC 方法验证的文字里
  （各 6 次提及，ACBI2 是 84 次），没有任何配方数据。`block_class` 由 `both` 改 `L`。
- **Xu 2022**：我以为 19 个衍生物各有包封率。实际 19 个只有细胞毒性数据，
  只有 5 个试过载入脂质体，4 个失败且只有定性描述，有定量 EE 的只有 compound 4d。
  `block_class` 由 `P` 改 `L`，`est_formulations` 由 19 改 12。

**含义：`feasibility-probe.csv` 里那 108 条的 `block_class` 和 `est_formulations`
是按摘要判断的，没有逐篇核对全文。** 抽到的两篇里有两篇判错。
后续用这张表排优先级时，要知道它的误差有这么大。

## 六、两件不在计划内但有用的发现

**1. 7 条载药失败的负样本。** Xu 表 S1 的 6 条（乙酸钙梯度）加表 4 的 ATP 一条。
原文 EE 列写 `---` 和 `—`，是明确失败而非缺测，已置 `formation_ok = FALSE`。
现有主数据集几乎全是成功配方，负样本稀缺。这 7 条可以支持
「预测某个配方会不会载药失败」这个比 EE 回归容易得多的二分类问题。
注意表 S1 的载荷不确定（原文没说是哪个化合物），用之前看 `payload_id_source`。

**2. 整体亲脂性参数分辨不了载药行为，两个独立证据。**

- Khawar：logKow 与脂相分配系数 r > 0.97，分不出差别
- Xu：5 个化合物 logD 极差仅 0.25、pKa 极差仅 0.005，但 1 成 4 败，
  成功的 4d 在 logD 上还排中间偏低

合起来的含义：**特征工程只堆 logP / logD / pKa 这类整体描述符，
按现有证据不太可能分辨出配方成败。** 这对第四节第 1 条的特征对比实验是直接相关的。

## 七、一个数据缺口

`data/raw/yanes2025_ivr/standardisation_nm_IVR.zip`（约 269 MB，数字化的释放曲线）
**不在仓库里，也不在容器里，只在你本地。**
原因是超过 GitHub 单文件 100 MB 硬上限，当时 push 失败（HTTP 408），
用 `git rm --cached` 撤出并加进了 `.gitignore`。

这份数据现在没有任何备份在仓库中。如果后续要用释放曲线，
需要你从本地重新提供，或者走 Git LFS / 外部存储。
目前的抽取没有用到它（`yanes2025_enrichment.csv` 只用了
`backend_data.csv`、`media_components.csv`、`quality_reporting.csv`）。

## 八、关键文件索引

| 文件 | 作用 |
|---|---|
| `docs/literature-protocol.md` | 采集协议，已冻结。纳入/排除标准、提取字段表、质量分档、去重规则 |
| `docs/data-licensing.md` | **授权的唯一权威**。四个可用 + 五个挂起，含解除挂起的条件 |
| `docs/feasibility-probe.csv` | 108 条候选。注意第五节第 5 条说的误差 |
| `docs/schema-partition-coefficients.md` | Khawar 那张表的 schema |
| `docs/compound_gain_stats.json` | 五个数字的机器可读版本 |
| `docs/worklog/` | 本轮 7 份（`2026-10-26` 起），另有更早轮次的 5 份。抽取报告是 10-28 和 10-29 那四份 |
| `data/raw/*/README.md` | 每个来源的下载链接、校验值、**做过哪些修改**（CC BY 署名要求） |
