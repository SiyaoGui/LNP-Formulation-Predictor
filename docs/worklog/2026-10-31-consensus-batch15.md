# 第 15 批：到期前清空式检索（检索 95–109）

日期：2026-10-31
模式与口径同第 12–14 批。

## 本批 15 次检索

| # | 检索式 | 工作流 | 默认优先级 |
|---|---|---|---|
| 95 | angiopep-2 peptide modified nanoparticle LRP1 brain targeting efficiency | B;H | P0 |
| 96 | glutathione PEGylated liposome 2B3-101 clinical trial brain delivery | F;H | P0 |
| 97 | polysorbate 80 coated nanoparticle apolipoprotein adsorption brain uptake | B;H | P0 |
| 98 | clinical trial nanoparticle failure translation lack of efficacy phase II | F;I;K | P0 |
| 99 | intra-arterial / intrathecal / ICV administration nanoparticle brain distribution | D;H | P1 |
| 100 | glymphatic clearance perivascular transport nanoparticle brain penetration | B;H | P1 |
| 101 | LNP mRNA delivery to brain neurons astrocytes after systemic administration | B;H | P0 |
| 102 | organ-on-chip microphysiological system predictive validity regulatory acceptance | D;I | P1 |
| 103 | DLS SOP ISO 22412 cumulant z-average reporting requirement | A;D | P0 |
| 104 | zeta potential standardization electrophoretic mobility ionic strength reporting | A;D | P0 |
| 105 | encapsulation efficiency RiboGreen assay method validation accuracy | A;D | P0 |
| 106 | transfer learning domain adaptation small dataset property prediction | A;C | P0 |
| 107 | leave-one-study-out cross validation data leakage ML evaluation pitfalls | A;I | P0 |
| 108 | nab-paclitaxel Abraxane formulation attributes vs other nanomedicines | B;F | P1 |
| 109 | continuous manufacturing ICH Q13 real time release testing implementation | D;K | P0 |

## 入库结果

- 命中 300 条，新增 261 条，重复 39 条，**新增率 87.0%**
- 主表 1232 → **1493 行**（去重后无重复 DOI）
- 本批 193 条摘要不含定量结果，标 `needs_fulltext=Y`
- 全表重跑 Crossref（1494 条）：CC 系列 727 / 仅出版商或 TDM 583 / 未列 160 / 未解析 21
- 需全文合计 792 条，其中 **391 条开放许可**

## 对项目有直接影响的条目

1. **He 2019（10.1021/acs.accounts.9b00228）**：75 个肿瘤纳米药、190 项临床试验的统计：
   **一期成功率约 94%，二期降到约 48%，三期只有约 14%**；二期失败里 15/19 是疗效不足，
   只有 4/19 是毒性。这条是"纳米制剂能做出来不等于能过临床"的硬数据。
2. **Fayez 2026（10.2147/ijn.s618407）**：847 项临床试验（2010–2020）的漏斗分析，
   以及 23 项研究、412 名患者的 EPR 异质性比较；到 2025 年全球获批纳米药估计只有 50–80 个。
3. **Kapoor 2023（10.1016/j.patter.2023.100804）**：**17 个领域、294 篇论文存在数据泄漏**，
   并给出 8 类泄漏的分类法；纠正错误后复杂模型并不优于几十年前的逻辑回归。
   **Bernett 2024（10.1038/s41592-024-02362-y）**给出 7 个必问问题。
   **Asiaee 2026（10.64898/2026.02.05.704016）**在 265 种药、1462 个细胞系上量化：
   无泄漏交叉验证的 MSE 平均高 16.6%，**32 篇已发表方法里 23 篇（72%）有泄漏**。
   这三条直接支撑我们在验收标准里要求"按研究/按实验室分组的交叉验证"。
4. **Austin 2025（10.1126/sciadv.adx6976）**：证明留一法交叉验证本身引入"分布偏倚"
   （训练折平均标签与测试样本标签负相关），会系统性低估性能并偏向弱正则化。
   我们的小样本评估方案必须避开朴素留一法。
5. **Leinonen 2024（10.1016/j.compbiomed.2024.109271）**：多源数据上
   **K 折交叉验证系统性高估跨源泛化，留一源法偏差接近零但方差更大**。
   这与我们"按实验室分层"的方案一致，可直接引用。
6. **Lindsay 2025（10.3390/vaccines13040339）**：四种可电离脂质的 LNP 理化性质相近，
   体外 SM-102 显著最好，**体内却是 ALC-0315 与 SM-102 并列，排序与体外不一致**。
   这是"体外-体内相关性断裂"在 LNP 上的直接证据。
7. **Wang 2025（Nat Mater，10.1038/s41563-024-02114-5）**：72 种跨血脑屏障脂质合成筛选，
   静脉给药后可转染全脑的神经元与星形胶质细胞，效率高于已获批 LNP。
   **Xue 2025（10.1002/adma.202417097）**鞘内给药后 GFP 表达覆盖 29.6% 神经元、38.1% 星形胶质细胞。
   **Han 2026（10.1021/acsnano.5c19138）**用 mRNA 条形码做大库体内筛选，
   找到 C14-306 既提高脑转染又降低肝转染。这三条说明脑递送的"可工程化入口"确实存在，
   但都在核酸载荷上，**小分子入脑仍无对应的高通量筛选体系**。
8. **Gaillard 2014（10.1371/journal.pone.0082331）与 Birngruber 2014（10.1002/jps.23994）**：
   2B3-101 的脑血比比 Caelyx 高 4.8 倍（cOFM 测定，p = 0.0016），临床一期 28 例最高到 70 mg/m²
   未达剂量限制毒性，二期 a 期 BCBM 11% 部分缓解、53% 疾病稳定。
   **这是"脑靶向脂质体做到临床二期"的完整证据链，可作为管线里程碑的外部参照。**
9. **Hu 2019（10.1016/j.ejpb.2019.04.004）**：同样加谷胱甘肽，
   **GSH-PEG-HSPC 把甲氨蝶呤的 Kp,uu 从 0.10 提到 0.82（4 倍），
   但 GSH 加在 PEG-EYPC 上完全没有额外增益**（该配方本身 Kp,uu 已 1.5）。
   靶向配体的效果强依赖基础配方，不是可加性的。
10. **Langevin 2018 两篇（10.1016/j.impact.2017.12.004、10.1016/j.impact.2018.04.002）
    与 Varenne 2015（10.1016/j.colsurfa.2015.08.044）**：
    DLS 与 zeta 的 SOP 验证给出明确的不确定度数字——
    粒径 60 nm 时 7.0%、203 nm 时 3.8%；zeta 负电 14%、正电 12%。
    **这是我们两档验收标准里"普通实验室档"可以引用的测量不确定度来源。**
11. **Tsalmpouris 2025（10.1021/acs.analchem.5c03299）**：30 个 mRNA-LNP 样品上
    阴离子交换色谱与 RiboGreen 的包封率结果**显著不一致**，原因是两者测的不是同一个量
    （RiboGreen 测染料可及的 mRNA，AEX 测与 LNP 解离的 mRNA 并能看到表面结合态）。
    **Klusek 2026（10.3390/cimb48080805）**进一步证明 LNP 本身的浊度会压低 RiboGreen 信号。
    这意味着文献里的 EE 数值本身带方法学系统偏差，必须在特征表里记录测定方法。

## 判定

新增率 87.0%（前三批 87.0% / 82.2% / 86.3%），**连续四批不触发饱和**。
累计 109 次检索，主表 1493 行。
