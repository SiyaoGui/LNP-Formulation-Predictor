# 分配系数表 schema（分子属性，非配方记录）

日期：2026-10-27
目标文件：`data/processed/partition_coefficients.csv`
来源：Khawar 2022（`10.1038/s41598-022-19452-6`，CC BY 4.0，见 `docs/data-licensing.md` 2.1）
状态：**schema 已定，等原始文件进仓库后抽取**

---

## 一、为什么单独建表

这批数据**不含任何配方信息**：没有脂质组成、没有粒径、没有包封率、没有制备工艺。它是「分子 → 在脂相与水相之间怎么分配」的属性数据。

所以：

1. **不进 `merged_formulations_v2.csv`。** 那张表一行等于一个配方记录，本表一行等于一个化合物
2. **不作为预测目标。** 它的用途是作为特征，接到现有特征矩阵上
3. 连接键是 `inchikey`，和小分子子集的 `payload_inchikey` 对齐

## 二、这一轮要检验的假设

现有特征矩阵用的是计算得到的辛醇/水 logP（`docs/data-inventory.md` 3.2 节的 LogP 列）。假设是：

> 辛醇/水 logP 对磷脂双层的分配行为存在系统性偏差，尤其对带电分子；换成磷脂/水分配系数能减小这个偏差。

Khawar 2022 摘要里的直接证据：用 logKow 加 logKaw 的线性组合去拟合 logKpw，n=131 时 R²=0.953、RMSE=0.413；拟合 logKlw，n=305 时 R²=0.971、RMSE=0.375。Bittermann 2016（`10.1016/j.chemosphere.2015.08.065`，本轮未纳入）另报：单用中性态 logKow 外推到离子，阴离子 RMSE=0.79、阳离子 RMSE=1.14。

**这一轮只建表，不做对比实验。** 对比实验等三个数据集抽完、用户确认之后再做。

## 三、两个系数分别对应仓库里的哪类载体

Khawar 2022 同时给两个量，不能混用：

| 系数 | 脂相是什么 | 对应仓库的 `carrier_subtype` | 样本数 |
|---|---|---|---|
| **logKpw**（磷脂/水） | 磷脂（膜脂） | `classic_liposome`、`ionizable_LNP` | n=131 |
| **logKlw**（储存脂/水） | 储存脂，即三酰甘油类 | `SLN`、`NLC`（基质就是甘油酯） | n=305 |

这是一个有用的对应：现有小分子子集 272 条全部是经典脂质体，所以**主力应该用 logKpw（n=131）**；logKlw 留给将来的 SLN / NLC 数据。

两列都抽，用 `coefficient_type` 区分，不要合并成一列。

## 四、字段定义

### 4.1 分子标识

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `row_id` | int | 是 | 本表内行号，从 1 递增 |
| `compound_name` | str | 是 | 原文给的化合物名，原样抄录 |
| `smiles` | str | 是 | 规范化 SMILES。原文没给则由名字反查，并在 `id_source` 标注 |
| `inchikey` | str | 是 | 由 SMILES 用 RDKit 算出。**连接键** |
| `cas` | str | 否 | |
| `id_source` | enum | 是 | `paper_smiles` / `pubchem_by_name` / `chembl_by_name` / `uncertain` |
| `pubchem_cid` | int | 否 | 名字反查时必填，使反查可复核 |

### 4.2 分配系数

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `coefficient_type` | enum | 是 | `logKpw`（磷脂/水）/ `logKlw`（储存脂/水）。**不许合并** |
| `log_value` | float | 是 | log10 值 |
| `species` | enum | 是 | `neutral` / `cation` / `anion` / `zwitterion` / `unspecified`。带电态的分配系数和中性态差一到两个数量级，混用会制造假信号 |
| `value_origin` | enum | 是 | `experimental`（原文标为实测）/ `model_predicted`（原文的模型预测值）。**预测值默认不作为特征，只作敏感性检验** |
| `temperature_c` | float | 否 | |
| `ph` | float | 否 | 带电态系数必须有 pH，否则 `species` 无意义 |
| `ionic_strength` | str | 否 | |
| `measurement_method` | str | 否 | 如 SPME、平衡透析、LEKC |

### 4.3 溯源与授权

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `source_doi` | str | 是 | 固定 `10.1038/s41598-022-19452-6` |
| `source_license` | str | 是 | 固定 `CC-BY-4.0` |
| `source_attribution` | str | 是 | 见 `docs/data-licensing.md` 第四节格式 |
| `source_location` | str | 是 | 数值在原文的位置，如 `Table S1, row 42` |
| `primary_source_doi` | str | 否 | **见第五节**。Khawar 2022 的实测值汇集自更早的原始文献，若原文给出了出处则记在这里 |
| `primary_source_available` | bool | 是 | 原文是否标明了该数值的原始出处 |

### 4.4 质控

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `qc_flag` | enum | 是 | `ok` / `suspect` / `excluded` |
| `qc_reason` | str | 条件 | 非 ok 时必填。不许静默删行 |
| `overlaps_repo_compound` | bool | 是 | `inchikey` 是否命中现有 22 个化合物之一 |

## 五、一个必须写明的局限

**Khawar 2022 的实测值是汇集自更早的原始文献的，不是该文自己测的。** 这和 `docs/literature-protocol.md` 6.4 节「不许以综述为数据出处」的精神有张力，所以把判断依据写在这里：

**认定可用的理由**：

1. Khawar 2022 不是综述，是一篇用汇集数据集做模型标定的原始研究，数据集本身是该文的交付物之一
2. 分配系数的测定有 OECD 指南，跨实验室可比性远好于包封率。这正是 `docs/data-spec-ee.md` 认定包封率跨来源不可比的那个理由在这里**不成立**的原因：包封率依赖配方、工艺、测定方法、载药比四层变量，分配系数只依赖脂相种类、温度、pH、离子强度，且这四项都是标准化报告项
3. 它的用途是**特征**，不是目标。特征的测量噪声会稀释信号，但不会像目标泄漏那样制造虚高指标

**仍然要做的防护**：

1. `primary_source_available` 必填。将来若要对外发表，没有原始出处的记录要么补齐，要么单独标注
2. `value_origin = model_predicted` 的记录默认不进特征，只作敏感性检验
3. 将来若要提高置信度，可以用 Bittermann 2016（约 303 个化合物，含 36 阳离子 + 56 阴离子）做交叉核对。该文本轮未纳入，若要用须先按 `docs/data-licensing.md` 走一遍授权核实

## 六、交付时要报的数字

抽完后报告（按用户 2026-10-27 的要求）：

1. 本表贡献多少条记录（按 `coefficient_type` 分开报）
2. 多少个唯一化合物（按 `inchikey`）
3. 和现有 22 个化合物重叠多少
4. **能连上现有小分子子集的化合物有几个**。这是决定性的数字：本表再大，连不上现有配方记录就用不上
5. 合并后唯一化合物数从 22 变成多少

第 4 项要先说清口径：本表是分子属性表，它不增加配方记录数。它对「唯一化合物数」这个瓶颈指标的贡献，取决于后续是否有配方数据能配上这些新化合物。所以第 4 项和第 5 项要分开报，不许合成一个数字。
