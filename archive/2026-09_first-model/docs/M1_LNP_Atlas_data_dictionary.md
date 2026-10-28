# M1 产出：LNP Atlas Data Dictionary

> 数据来源：LNP Atlas（KISTI, Song, Baek & Seo, *Scientific Data* 2026, 13:139, 论文DOI: 10.1038/s41597-025-06456-w；数据集Zenodo DOI: 10.5281/zenodo.17243732），CC BY 4.0（论文正文为CC BY-NC-ND 4.0）。作者顺序及论文DOI已于2026-09-10核对论文原文修正（此前误记为"Seo/Song/Baek"且缺少论文自身DOI）。
> 文件：`LNP_Atlas_DB_202509_v1.csv`，**1092 行 × 28 列**，覆盖 62 篇论文（论文声称 63 篇，1 篇 DOI 缺失未计入，不影响使用）。
> 已重新导出一份 UTF-8 编码的副本：`LNP_Atlas_DB_202509_v1_utf8.csv`，原因见下方"踩坑记录"第 1 条。

---

## 一、踩坑记录（先看这个，能省你不少时间）

1. **文件编码不是 UTF-8，是 `cp949`（韩文编码）**。用 `pd.read_csv()` 默认参数会直接报 `UnicodeDecodeError`；`±`、`°C` 这类符号如果强行用 latin-1 读会变成乱码（比如 `108.0 ¡¾ 2.1`）。正确读法：`pd.read_csv(path, encoding='cp949')`。我已经导出了一份转成 UTF-8 的副本，之后可以直接用那份，不用每次都记着传 encoding 参数。
2. **`lipid_molar_ratio` 的组分顺序，论文正文明确写的是 `ionizable lipid : peg lipid : sterol lipid : helper lipid`**（与列顺序一致），不要自己按"典型 LNP 配方 PEG 占比最小"这种经验去猜顺序——我一开始也猜错了一次，后来在论文 Data standardization 一节查到了官方说明，才改回来。这是本轮最容易踩的坑：**遇到不确定的字段含义，优先去找原始文档核实，不要凭经验猜**，M1 的意义就在这。
3. **不是所有行的 `lipid_molar_ratio` 都是 4 段**：1041 行是 3 个冒号（4 段，正常情况），50 行是 6 个冒号（5+ 段，说明这些配方组分数量本身超过 4 种），1 行只有 2 个冒号（3 段）。M2 写解析脚本时不能假设"永远 split 出 4 个数字"，要做健壮性处理（比如先按冒号数分流，非 4 段的单独标记待人工看）。

---

## 二、逐列字典

| 列名 | 含义 | 格式/单位 | 缺失率 | 备注 |
|---|---|---|---|---|
| `lnp_id` | 行唯一标识符 | int | 0% | 1092 个值全部唯一，等同主键 |
| `ionizable_lipid` | 电离脂质标准化简称 | 文本，如 `C12-200` | 0.7% | ⚠️ **404 行（37%）值是占位符 `"Custom lipid"`**，代表论文里没有通用简称的新脂质（多来自 AGILE 这类组合筛选文库），这些行的真实化学身份要看 `ionizable_lipid_original` 和 `ionizable_lipid_smiles`，不能把 `"Custom lipid"` 当成一个有意义的分类特征去用 |
| `peg_lipid` | PEG 化脂质标准化简称 | 文本，如 `DMG-PEG2000` | 4.2% | — |
| `sterol_lipid` | 固醇类脂质标准化简称 | 文本，如 `cholesterol` | 4.2% | — |
| `helper_lipid` | 辅助脂质标准化简称 | 文本，如 `DOPE` | 4.3% | — |
| `lipid_molar_ratio` | 四组分摩尔比 | 文本 `"a:b:c:d"`，顺序=ionizable:peg:sterol:helper | 0% | ⚠️ 段数不总是 4，见踩坑记录第 3 条 |
| `particle_size_nm_std` | 粒径 | `均值 ± 标准差` 或纯数值，单位 nm | 3.9% | 论文自己的合理性校验范围是 10–1000 nm |
| `pdi_std` | 多分散指数 (PDI) | 同上格式 | 31.9% | 合理范围 0–1 |
| `zeta_potential_mv_std` | 表面电位 | 数值，单位 mV | **70.1%** | 非常稀疏，不建议作为 M4 的首选 target |
| `encapsulation_efficiency_percent_std` | 包封率 | 百分比 | 41.5% | ⚠️ 69 行不是纯数字，是 `<60`、`>90`、`~88` 这类不等式/约数表达（原始文件里 `<` 被编码成了乱码 `?`），不能直接转 float，要单独处理或排除这批 |
| `loading_capacity_std` | 载药量 | 文本 | 14.6% | ⚠️ **列名跟实际内容对不上**：933 个非空值里只有 5 个是真正的载药量数值（如 `0.029 mg DNA per μmol lipid`），其余 928 个其实是配方投料比——`N/P 比`（如 `NP:6(molar)`）或`重量比`（如 `WR:10(wt/wt)[ionizable_lipid:mRNA]`）。用之前必须先按内容模式把"真载药量"和"投料比"分开 |
| `target_type` | 目标载荷类型 | 分类 | 0% | 分布：mRNA 678 / siRNA 178 / DNA 135 / empty 53（无载荷对照组）/ ASO 36 / gold_nanoparticles 6 ⚠️ / mRNA+siRNA 组合 3 / protein 3 ⚠️。后两个标了⚠️的类别**不是核酸载荷**，如果你的建模范围是"核酸递送"，这 9 行要单独处理或排除 |
| `nucleic_acid_sequence` | 具体载荷/报告基因名 | 文本，如 `firefly_luciferase` | 0% | 不是真实碱基序列，是报告基因/载荷名称 |
| `peg_lipid_original` | 原始论文报告的 PEG 脂质名称（未标准化） | 文本 | 4.2% | — |
| `ionizable_lipid_original` | 原始论文报告的电离脂质名称（常是 IUPAC 式全称） | 文本 | 0.7% | 对 `"Custom lipid"` 行来说，这是唯一能看出化学身份的文字字段 |
| `helper_lipid_original` | 原始辅助脂质名称 | 文本 | 4.2% | — |
| `sterol_lipid_original` | 原始固醇名称 | 文本 | 3.9% | — |
| `synthesis_info` | 合成工艺信息 | 分号分隔的 `key: value` 文本块 | 0% | 子字段包括 synthesis_method / device_used / total_flow_rate_ml_min / flow_rate_ratio / aqueous_phase_composition / organic_phase_composition / mixing_time_sec / temperature_condition / post_processing / sterilization / storage_buffer。⚠️ 需要写解析函数拆成独立列才能用于建模，现在是一整块文本 |
| `bioactivity_profile` | 生物活性数据 | 同上格式 | 14.8% | 子字段包括 cell_line / animal_model / administration_route / dose / gene_expression_result 等，同样需要拆解 |
| `paper_title` | 来源论文标题 | 文本 | 0% | — |
| `paper_authors` | 作者列表 | 字符串形式的 Python list | 0% | — |
| `paper_doi` | 论文 DOI | 文本 | 0.5% | — |
| `paper_journal` | 期刊名 | 文本 | 0.5% | — |
| `paper_year` | 发表年份 | float | 0.5% | 范围 2005–2025 |
| `ionizable_lipid_smiles` | 电离脂质 SMILES | 文本 | 13.9% | M3 做 RDKit 特征化时，这批缺失行会自动损失，需要提前决定丢弃还是想办法补 |
| `peg_lipid_smiles` | PEG 脂质 SMILES | 文本 | 17.3% | 同上 |
| `sterol_lipid_smiles` | 固醇 SMILES | 文本 | 4.5% | 同上 |
| `helper_lipid_smiles` | 辅助脂质 SMILES | 文本 | 7.1% | 同上 |

---

## 三、给 M4 选 target 的一点提示

`encapsulation_efficiency_percent_std`（58.5% 覆盖，论文里也提到这个覆盖率）和 `particle_size_nm_std`（96.1% 覆盖）是数据量最充足的两个数值型读数，比 `zeta_potential`（70% 缺失）更适合作为 baseline 的目标变量。`loading_capacity_std` 目前不能直接用，要先完成上面提到的拆分清洗。

---

## 四、M1 状态

Data dictionary 已产出，可以视为 **M1 完成**。下一步进入 M2（引入 Luciani CSV + PMC IVR，统一 schema），按排期是 07-17 主战场——你现在做完 M1 时间上还在缓冲窗口内，没有落后。
