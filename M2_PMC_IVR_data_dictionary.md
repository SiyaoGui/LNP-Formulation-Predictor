# M2 · 数据源 3：PMC IVR（诺丁汉体外释放数据库）—— 修订版

> ⚠️ 更正：早前版本说"这批数据完全没有脂质配方"，这个结论是错的，原因是当时只连接了 zip 里 data/ 下的四个子文件夹（drug_release/papers/processed/unprocessed），144MB，漏了整个 269MB 包里另外 125MB——也就是真正的 `liposome_IVR.db` 数据库本体。拿到完整数据库后确认：**配方组成数据是有的**，论文摘要里说的"lipid composition features"和 `formulation_composition` 表都在，之前是我这边访问范围不全，不是数据集本身的缺口。这次补全后重做了 M2 合并。

---

## 一、数据库真实结构：11 张表，不是之前看到的两三张 CSV

| 表名 | 行数 | 作用 |
|---|---|---|
| `formulation_composition` | 385 | **配方组成明细**——每行是"某配方里含有某个组分及其摩尔比"，长表格式，一个配方对应多行 |
| `component_name` | 31 | 脂质/辅料名录（HSPC、Cholesterol、mPEG2000-DSPE-2k 等） |
| `component_properties` | 62 | 每个组分的分子量(Mw)和相变温度(Tm) |
| `formulation` | 141 | 配方主表：配方ID → 用了哪个API(药物) → 来自哪篇论文 |
| `formulation_CPPs_CQAs` | 140 | 配方级别的关键工艺参数/质量属性：制备方法、粒径、PDI、表面电位等 |
| `IVR` | 272 | 单次释放实验：配方ID、释放方法、介质条件、时间单位等 |
| `API_name` | 22 | 药物名录+SMILES |
| `media_components` | 563 | 释放介质具体成分（长表） |
| `papers` | 34 | 来源论文 |
| `search_terms` | 28 | 作者做文献检索时用的检索词（方法学元数据，跟建模无关） |
| `sqlite_sequence` | 6 | sqlite 内部自增序号表，忽略 |

## 二、配方组成怎么读

`formulation_composition` 是长表（一个配方多行），每行 = 一个组分 + 它的摩尔比，要跟 `component_name` 关联才知道组分叫什么。**这份数据集里没有"电离脂质"这个角色**（跟 Luciani 一样，是经典脂质体，不是 pH 敏感的 LNP），31 个组分基本是磷脂（HSPC/DSPC/DPPC等）、胆固醇、PEG化脂质（名字里带"PEG"的）三类。合并时按名字关键词分了角色：含"PEG"→peg_lipid，含"Cholesterol"→sterol_lipid，其余→helper_lipid（同一个配方如果有两个磷脂类组分，比如 HSPC+HePc，两个名字合并、占比相加）。

⚠️ **数据库本身没有脂质的 SMILES**（只有药物 API 的 SMILES，脂质只有名字）——原文论文（Yanes et al., *Int J Pharm X* 2025）的方法学部分也印证了这点："APIs...stored...with their chemical identifiers (e.g., SMILES)...Components were stored in the component_name table, and their proportions were converted or recorded as molar ratios"——药物有结构式，脂质组分只有名字+摩尔比，论文没把这个当限制单独讨论，但设计上就是如此。

**已手动补全**：把这 31 个脂质/辅料组分逐一拿到 PubChem 和原始 34 篇文献里核实（结果见 `PMC_IVR_lipid_component_smiles.csv`），分四种情况：

- **16 个标准脂质，结构单一、已核实**（DSPC、DPPC、DMPC、DOPC、POPC、DEPC、DPPG、DSPG-Na、DSPE、Cholesterol、α-生育酚、Tricaprylin、DCP、MSPC、HePc、P-Lyso-PC）——已并入合并表的 SMILES 列。
- **5 个天然混合物**（HSPC、Soy PC、EPC、asolectin、Egg SM）——本质上是多种磷脂/鞘磷脂的批次化混合物，没有单一分子结构，没有勉强赋值。
- **3 个 PEG 化脂质**（mPEG2000/5K/10K-DSPE）——PEG 链长有分布，不是单一精确分子，暂留空，见下方说明。
- **5 个需要人工核实但尚未确认精确结构的定制合成脂质**（DPPGOG、疑似 Ph-DPPC、CM-DPPC、DBCO-DPPC、胆固醇-唾液酸偶联物 SA-CH）——在原始 34 篇论文里找到了这些名字的确切定义和出处论文，但因为是实验室自制/专利化合物，精确结构没有二次核实来源，没有编造 SMILES。**其中一个重要发现**：数据库里的组分名 `pH-DPPC` 很可能是 `Ph-DPPC`（phenoxy-conjugated DPPC，苯氧基修饰DPPC）的拼写/OCR 混淆——来自 *Nature Communications* 2023 论文（DOI 10.1038/s41467-023-41946-8），跟"pH敏感"没有关系，这是这次核实中顺带发现的一处数据集命名疑点。

并入合并表后的实际覆盖情况：helper_lipid_smiles 98/272（36.0%，主要是混合物和未核实定制脂质拉低了这个数）、sterol_lipid_smiles 180/272（66.2%，全部覆盖了 sterol_lipid_name，因为这类只有 Cholesterol 一种）、peg_lipid_smiles 0/272（PEG 聚合物暂未给近似结构）。

⚠️ **摩尔比总和不总是 100**：多数配方加总接近100（比如56.2+38.3+5.3=99.8），但也有个别配方（比如 formulation_ID=3 加总只有3.14）明显不是按"占比"报的，可能是绝对摩尔当量或原始论文报告方式不同。用之前建议按总和是否接近100做一次筛查。

## 三、和其他两个表的关联方式

`IVR`（272行，一次释放实验）→ 关联 `formulation`（配方是什么、用了哪个药）→ 关联 `formulation_CPPs_CQAs`（这个配方测出来的粒径/PDI/电位）→ 关联 `API_name`（药物SMILES）→ 关联 `formulation_composition`透过`component_name`（脂质组成）→ 关联 `papers`（出处DOI）。合并表里一行 = 一次 IVR 实验，同一个配方如果做了多次释放测试，会展开成多行（比如 formulation_ID=3 那个配方做了两次释放实验，分别用不同介质，就是两行）。

## 四、覆盖率（并入统一表后的实际数字）

272 行 PMC_IVR 记录里：**helper_lipid 100% 有值，sterol_lipid 66.2%，peg_lipid 46.3%**——不是所有配方都用了全部三类组分（比如有的配方没加胆固醇），这是真实数据反映的情况，不是缺失。

## 五、这次的教训

这是本项目第二次因为"没拿到完整数据就下结论"而说错话（第一次是 M1 摩尔比顺序问题）。这次的具体原因是：Cowork 环境里连接的文件夹范围是提前配置好的，我只能看到明确连接给我的目录，看不到你本地磁盘上这个 zip 解压出来的其他部分——所以下次遇到"这个数据集好像缺了点什么"的情况，先怀疑"是不是我这边没看全"，而不是急着下结论说数据集本身有缺陷。
