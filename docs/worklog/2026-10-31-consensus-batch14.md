# 第 14 批：到期前清空式检索（检索 80–94）

日期：2026-10-31
模式与口径同第 12、13 批（机械抽取，`why_matters` 为主题短句 + 摘要内定量片段）。

## 本批 15 次检索

| # | 检索式 | 工作流 | 默认优先级 |
|---|---|---|---|
| 80 | doxorubicin liposome Doxil generic bioequivalence physicochemical characterization | A;D;F | P0 |
| 81 | lipid nanoparticle storage stability frozen lyophilized long term size change | B;D;I | P0 |
| 82 | molecular dynamics simulation drug partitioning in lipid bilayer prediction of loading | A;B | P1 |
| 83 | protein corona composition LNP serum proteomics effect on cellular uptake | B;J | P1 |
| 84 | cryo-EM lipid nanoparticle internal structure bleb morphology mRNA localization | B;D | P1 |
| 85 | donepezil memantine rivastigmine nanoparticle brain delivery Alzheimer PK | B;H | P0 |
| 86 | temozolomide paclitaxel docetaxel lipid NP brain tumor PK brain/plasma ratio | H;J | P0 |
| 87 | PBPK model nanoparticle brain distribution simulation | A;H | P0 |
| 88 | active learning Bayesian optimization closed loop autonomous formulation screening | A;C;D | P0 |
| 89 | liquid handling robot automated high throughput nanoparticle library screening | C;D | P0 |
| 90 | microdialysis unbound brain interstitial fluid concentration nanoparticle drug | A;H | P0 |
| 91 | naringenin hesperetin apigenin luteolin nanoparticle EE characterization | B;C | P0 |
| 92 | nanoparticle size effect on BBB penetration quantitative comparison | B;H | P0 |
| 93 | reporting quality reproducibility crisis nanomedicine literature | D;I | P0 |
| 94 | LLM extraction of experimental data from materials and pharmaceutical literature | C;D | P0 |

## 入库结果

- 命中 299 条，新增 258 条，重复 41 条，**新增率 86.3%**
- 主表 974 → **1232 行**（去重后无重复 DOI）
- 本批 158 条摘要不含定量结果，标 `needs_fulltext=Y`
- 全表重跑 Crossref（1233 条）：CC 系列 610 / 仅出版商或 TDM 482 / 未列 126 / 未解析 13
- 需全文合计 599 条，其中 **308 条开放许可**

## 对项目有直接影响的条目（数据来自摘要原文）

1. **Adzavon 2026（10.1016/j.ijpharm.2026.127405）**：这是本批最重要的一条。
   对 18 项独立研究的 **613 组 LNP 配方**做储存稳定性的系统分析，结论是
   **按研究内建模预测粒径变化在 12 项合格研究里中位 R² = −1.53，0/12 达到 R² ≥ 0.70；
   跨研究预测在 4 种算法上全部失败（分组交叉验证平均 R² 在 −1.73 到 −0.27）。**
   作者的结论是：当前文献报告的分子与配方描述符不足以支撑储存不稳定性的预测，
   瓶颈是标准化、更高分辨率的数据报告，而不是更多建模。
   **这篇论文的方法与结论和我们自己的 2026-10-20 建模结论高度一致**，
   是外部独立证据，必须进我们的报告与对外材料。
   其中可用的阈值结论：冻干的保护作用只在 90 天以后才出现，90 天是生物活性保留率
   中位数跌破 80% 的临界储存时长。
2. **Ohta 2020（10.1038/s41598-020-75253-9）与 Hoch 2026（10.1148/radiol.251005）**
   两条独立证据在聚焦超声开放血脑屏障下都给出**非单调的粒径最优**：
   Ohta 的 15 nm 金颗粒最高（0.22 %ID，3 nm 与 120 nm 都更低）；
   Hoch 用定量磁化率成像测得 15 nm 比 2.3 nm 钆对比剂高 2.6 倍、23 nm 与 15 nm 相当、
   45 nm 比 23 nm 低 2.5 倍。两者独立互证"最优粒径在十几到二十几纳米"。
3. **Nowak 2019（10.1002/btm2.10153）**：在人源血脑屏障微流控下，
   **200 nm 颗粒的跨屏障通量高于 100 nm 与 500 nm**，又是一个非单调关系，
   且与上面 FUS 条件下的结论方向不同——说明"粒径最优值"依赖开放机制，不是普适常数。
4. **Kumar 2023（10.1016/j.addr.2023.114708）**：2018 组数据算出的
   纳米颗粒生物分布系数（NBC）：肝 17.56 %ID/g、脾 12.1、肿瘤 3.4、肾 3.1、肺 2.8、
   **脑 0.3 %ID/g**。这是脑递送效率天花板最硬的一条汇总数据。
5. **Cheng 2020（10.1021/acsnano.9b08142）**：376 组数据的 PBPK 荟萃，
   入瘤递送效率均值 2.23 %ID、中位 0.76 %ID（24 h 2.24/0.76，168 h 降到 1.23/0.35）。
6. **Chou 2023（10.1016/j.jconrel.2023.07.040）**：AI + PBPK 预测入瘤效率，
   24 h 的 R² = 0.83、168 h 只有 0.56，288 组数据里 133 组 R² ≥ 0.70。
   这是"纳米递送可预测性"的现状基准，可直接用于对比我们自己的指标。
7. **Errington 2021（10.7554/elife.67995）**：预期复现 193 个实验，实际只完成 50 个；
   **193 个实验里只有 4 个的统计数据是公开可得的，68% 联系原作者也拿不到；
   没有一个实验在原文里描述到足以直接复现的程度。** 这条是"文献数据底座不可靠"的硬引用。
8. **Polak 2023（ChatExtract，10.1038/s41467-024-45914-8）**：对话式 LLM 抽取材料数据，
   GPT-4 的精确率与召回率均接近 90%。**Dagdelen 2024（10.1038/s41467-024-45563-x）**、
   **Gupta 2024（10.1038/s43246-024-00708-9，从 240 万篇全文里抽出 100 万条记录）**
   以及 **Park 2026 纳米毒性多模态抽取（F1 96.1%，821 篇文章 16786 条记录）**
   共同说明：**从文献批量建库这条路现在是成熟技术，不是研究问题。**
   这对我们 C 工作流的路线选择有直接影响。
9. **Liu 2026 多目标贝叶斯优化（10.1016/j.jconrel.2026.115171）**：
   只做 22 个样品就达到多属性最优权衡；**Waibel 2025（10.1021/acs.molpharmaceut.5c00591）**
   33 个实验同时优化三项生物物理属性；**Hanna 2025（10.1021/acsnano.5c15613）**
   并行微流控每小时约 1000 个配方。闭环主动学习在制剂领域已有可复制的样本量参考。
10. **Hanada 2014、Liu 2014、Shilo 2015、Meng 2021** 四条在粒径—透过关系上给出互相矛盾的方向
    （有的越小越好，有的 70 nm 最优），进一步支持"粒径效应受模型与表面化学混杂"的判断。

## 判定

新增率 86.3%（前两批 87.0%、82.2%），**连续三批不触发饱和条件**。
累计 94 次检索，主表 1232 行。
