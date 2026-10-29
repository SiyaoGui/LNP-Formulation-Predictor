# Xu 2022: 用于脂质体远程载药的紫杉醇衍生物合成

| 项 | 值 |
|---|---|
| DOI | `10.3390/molecules27227967` |
| 作者 | Xu, Xiangwei; Liu, Yanhua; Shao, Shanshan; Li, Jinbo; Xu, Zhaochu; Yin, Yueling; Zhao, Linxiang; Wang, Yongjun; Liu, Dan |
| 出处 | Molecules 27(22), 7967, 2022 |
| 授权 | **CC BY 4.0** |
| 授权登记 | `docs/data-licensing.md` 第二节 |

## 原始下载链接

文件由用户在本地浏览器下载后提交进仓库（容器网络策略不允许直连出版社域名）。
MDPI 的开放获取页面：

- 文章页面：https://www.mdpi.com/1420-3049/27/22/7967
- 正文 PDF：同页 "Download PDF"，落地名 `molecules-27-07967.pdf`
- 补充材料：同页 "Supplementary Material"，落地名 `molecules-27-07967-s001.zip`
  （zip 里只有一个文件 `molecules-2015680-supplementary.pdf`，43 页，
  主要是核磁谱图，前 2 页有 Table S1 与 Table S2）

## 下载日期

2026-10-28（校验值记录日期同日）。

## 需要的文件

原计划要的东西和实际拿到的东西差别很大，列在一起：

| 原计划要的 | 实际情况 |
|---|---|
| 19 个衍生物的**结构** | **拿不到。** 表 1 的 R1/R2 是文字（Bz/Ac/Boc/H），但 Y、Z 两个取代基是图片。原文全篇不提供 SMILES |
| 19 个衍生物的**包封率** | **不存在。** 19 个化合物只有细胞毒性数据（表 2 的 GI50），没有逐个的包封率 |
| 脂质体配方筛选 | **有，但是单载荷。** 表 3（6 个铜梯度配方）、表 4（7 种梯度）、表 S1（6 个乙酸钙配方，全失败）全部是固定载荷 compound 4d 变配方 |

实际抽到的位置：

| 内容 | 在哪 | 条数 |
|---|---|---|
| 铜离子梯度配方筛选 | 正文 Table 3 | 6 |
| 糖类与 ATP 梯度 | 正文 Table 4 | 7（ATP 失败） |
| 乙酸钙梯度 | 补充 Table S1 | 6（全部失败） |
| 4d 最优配方表征 | 补充 Table S2 | 1 |
| 5 个化合物的 logD / pKa 与载入结果 | 正文 2.4 节 | 5 |
| 4d 的 IUPAC 名与分子式 | 正文 p11 | 1 |

## 文件清单与校验值

> 由 `python3 scripts/record_raw_checksums.py` 自动生成并写入本节，不要手填。

<!-- CHECKSUMS:BEGIN -->
| 文件 | 大小（字节） | SHA-256 |
|---|---|---|
| `molecules-27-07967-s001.zip` | 7,725,364 | `416d7f46ca2e19d060b9d6601bed970df1e06fde586e89335d052fe3497772a2` |
| `molecules-27-07967.pdf` | 3,735,568 | `87e6c5ea935a57540d5e421ddda94f3ebc52455f0b558989b6e91c607717e48c` |
<!-- CHECKSUMS:END -->

## 做过哪些修改

CC BY 4.0 要求标明是否对原始材料做了修改。抽取脚本是
`scripts/extract_xu2022_probe.py`，产物是 `data/processed/probe_xu2022.csv`（20 条）
与 `data/processed/probe_xu2022_compounds.csv`（5 条）。做过的修改：

1. **四张表合并成一张**。表 3、表 4、表 S1、表 S2 原本分开，统一成一行一个配方，
   用 `source_location` 区分出处。
2. **表 3 的合并单元格按词坐标重建**。pdfplumber 的表格识别对这个 PDF 完全失效，
   内水相与缓冲液两列是跨行合并的。改用词的 x/y 坐标分组重建行列对应，
   再用正文三处文字描述交叉验证（铜浓度越高 EE 越高、3:1:0.05 优于 19:1:0.25、
   中性葡萄糖酸铜最优），三项全部吻合。脚本每次运行都会重跑这三项验证。
3. **脂质比按原文的质量比保留，未换成摩尔比**。原文给的是 HSPC:Chol:DSPE-PEG2000
   的 w/w/w，`composition_unit_as_reported = mass_ratio`。正文另提到
   「the content of Chol was 45% (molar ratio)」，但没有给逐行的摩尔比，
   所以不自己换算。
4. **失败记录保留为失败，不当缺测**。表 S1 的 EE 列原文写 `---`，表 4 的 ATP 写 `—`，
   都置 `formation_ok = FALSE`、`encapsulation_efficiency_pct` 留空，
   并在 `qc_reason` 写明是失败而非缺测。这 7 条是有信息的负样本。
5. **未计算 SMILES 与 InChIKey**。原文不提供结构。4d 只有 IUPAC 名
   `2'-O-[2-((2-((4-boronobenzyl)oxy)-2-oxoethyl)disulfaneyl)acetyl]taxol`
   和 HR-MS 分子式 `C58H63BNO19S2`，两者都原样记录，
   `payload_id_source = name_only`。**没有从 IUPAC 名反推结构**，那是猜测。
6. **4d 的分子量由 [M+H]+ 推算**。原文只给 `[M+H]+` 计算值 1152.3523，
   减去一个质子得中性分子约 1151.34 Da，记在 `payload_mw_from_paper`。
   超过 900 Da 上限，全部标 `mw_over_default_cap = TRUE`。
7. **表 4 的脂质比是推断的**。原文说表 4 沿用铜梯度的最优配方，但没有逐行重述
   脂质比。按 3:1:0.05 填入，并置 `slot_assignment_uncertain = TRUE`，
   在 `notes` 写明是推断。
8. **表 S1 的载荷按不确定处理**。原文没说表 S1 对应哪个化合物，只说对
   4a/4d/13a/17a/17c 试过乙酸钙梯度。所以
   `payload_type = uncertain_one_of_4a_4d_13a_17a_17c`，不指定成 4d。
9. **表 S2 单独一行，没有并进表 3**。表 S2 的组分和表 3 第 2 行相同，但原文分开报，
   未说明是否同一批次，所以留成单独记录并用 `same_composition_as` 指向
   `xu2022_t3_2`，不合并。
10. **回读核对**。脚本从 PDF 文本层回读全部 28 个硬编码数字（表 3/表 4 的 EE、
    4d 的分子式与 IUPAC 名、5 个化合物的 logD 与 pKa、表 S2 的 4 个值），
    28 项全部对上。

## 备注

**外部探针集，不进训练集。** 产物与主数据表分开存放。

### 原定用途落空了

收集时的设想是：19 个分子共享单一紫杉醇骨架，正好是 `docs/data-spec-ee.md`
2.3 节警告的「在一个骨架附近密集采样」，拿来检验**同骨架内的小修饰能否被模型分辨**。

核对全文后这个用途不成立，两个前提都不满足：

1. **没有逐化合物的包封率。** 19 个化合物只有细胞毒性（GI50）。
   只有 5 个（4a, 4d, 13a, 17a, 17c）尝试过载入脂质体，
   其中 4 个失败，原文只给「obvious sedimentation」的定性描述。
   有定量包封率的只有 4d 一个。
2. **没有结构。** 表 1 的 Y、Z 取代基是图片，全篇不给 SMILES。
   就算有多个化合物的 EE，也无法算分子描述符。

所以它不能检验「同骨架内分辨力」。`scripts/report_compound_gain.py` 现在会
直接把这句话打出来，避免它被当成能用的探针集。

### 它还剩下什么用

两件事，都比原定用途弱：

1. **单载荷变配方的区组**，和 Jaki 2026 同类。12 条有定量 EE，
   变量是脂质质量比、内水相种类与浓度、梯度类型。EE 跨度 50.34 到 96.13，
   同一实验室同一方法。
2. **7 条载药失败的负样本**。表 S1 的 6 条（乙酸钙梯度）加表 4 的 ATP 一条。
   现有主数据集几乎只有成功配方，负样本稀缺。这 7 条可以用来检验
   「能否预测某个配方会不会载药失败」这个二分类问题。
   注意表 S1 的载荷不确定，用的时候要看 `payload_id_source`。

另外 5 个化合物的 logD（2.309 到 2.559）与 pKa（约 12.30）记在
`probe_xu2022_compounds.csv`。值得注意的是这 5 个化合物的 logD 与 pKa 几乎相同，
但 1 个成功 4 个失败。也就是说在这个体系里，logD 和 pKa 分辨不了载药成败。
这和 Khawar 2022 那条结论（logKow 与脂相分配系数高度相关，分不出差别）方向一致。
