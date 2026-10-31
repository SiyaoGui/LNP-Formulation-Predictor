# 第 13 批：到期前清空式检索（检索 65–79）

日期：2026-10-31
分支：claude/epic-lamport-oyzbye
模式同第 12 批：每轮 3 次检索，批次之间不写分析，满 15 次统一抽取入库。
`why_matters` 仍为机械生成，口径见 `docs/worklog/2026-10-31-consensus-batch12.md`。

## 本批 15 次检索

| # | 检索式 | 工作流 | 默认优先级 |
|---|---|---|---|
| 65 | glioblastoma lipid nanoparticle brain tumor accumulation percent injected dose | H;J | P0 |
| 66 | transferrin receptor antibody conjugated nanoparticle brain uptake quantification | B;H | P0 |
| 67 | PEG lipid molar percentage effect on circulation time and biodistribution | B;J | P0 |
| 68 | ionizable lipid apparent pKa measurement TNS assay correlation with delivery efficiency | B | P1 |
| 69 | cholesterol analog phytosterol substitution lipid nanoparticle structure transfection | B | P1 |
| 70 | nanostructured lipid carrier liquid lipid ratio effect on drug loading and crystallinity | B;C | P0 |
| 71 | surfactant type and concentration effect on lipid nanoparticle zeta potential and stability | B;C | P0 |
| 72 | dialysis vs ultrafiltration vs ultracentrifugation free drug separation EE measurement | A;D;I | P0 |
| 73 | in vitro BBB model TEER permeability coefficient comparison across laboratories | H;I | P0 |
| 74 | nanoparticle tracking analysis versus dynamic light scattering size discrepancy | A;D;I | P0 |
| 75 | quercetin solid lipid nanoparticle oral bioavailability pharmacokinetics rat | B;I | P1 |
| 76 | resveratrol lipid nanoparticle brain delivery quantitative brain concentration | B;H | P0 |
| 77 | high pressure homogenization vs ultrasonication vs microfluidics scale-up | B;D | P0 |
| 78 | logP molecular weight correlation with encapsulation efficiency meta-analysis | A;B;C | P0 |
| 79 | FAIR data sharing nanomedicine database minimum reporting standards | C;D | P0 |

## 入库结果

- 命中 298 条，新增 245 条，重复 53 条，**新增率 82.2%**
- 主表 729 → **974 行**（去重后无重复 DOI）
- 本批 144 条摘要不含任何定量结果，标 `needs_fulltext=Y`
- 全表重跑 Crossref：CC 系列 487 / 仅出版商或 TDM 386 / 未列 98 / 未解析 4
- 需全文合计 441 条，其中 **224 条开放许可**

## 本批对项目有直接影响的几条（数据均来自摘要原文）

1. **Bethiana 2026（Nat Commun，10.1038/s41467-026-72499-1）**：同一配方用 10 种混合器制备，
   物性与生物学表现差异很大；**学术界常用的手工移液混合得到的颗粒与工业湍流混合器产物不相似**。
   这条直接影响我们对文献数据的使用：不同论文的"同一配方"可能根本不是同一产物，
   混合方式必须作为特征列或分层变量，不能忽略。
2. **Strelkova-Petersen 2023（10.1016/j.ejpb.2023.10.006）**：同一配方手工混合与微流控混合的
   递送效率相差从 1/100 到 4 倍，且混合参数会改变器官倾向性。与上一条互相印证。
3. **Vigh 2021（10.3390/mi12060685）**：TEER 测量受温度、黏度、电极几何、膜孔隙率影响，
   同一生物模型可差数倍；筷式电极比腔式电极高 3 倍。
   这是 I 工作流（异质性上限）在脑递送方向的直接证据。
4. **Ghane 2026（10.3390/biomimetics11020119）**：BBB-on-chip 的 TEER 电极构型系统综述，
   提出统一报告框架。与上一条配套，是我们写验收标准时该引的方法学依据。
5. **Langevin 2018（10.1016/j.impact.2017.12.004）**：40 家实验室的 DLS/DCS 跨实验室比对，
   19 nm 二氧化硅颗粒各实验室报告 10–50 nm。**这是粒径测量异质性最硬的一条数据。**
6. **Farkas 2021（10.1007/s11051-021-05220-6）**：DLS 反演算法默认输出与累积量 z-average
   偏差通常大于 15%，且依赖正则化参数。影响我们怎么定义"真实粒径标签"。
7. **Levy 2021（10.1208/s12248-021-00651-4）** 与 **Khodadadi 2025（10.1039/d5nr01741f）**：
   两条独立证据都把**水溶性、logP、粒径、胆固醇/磷脂摩尔比**列为包封率的首要影响因素，
   后者基于 500 条数据点并做了可解释性分析。这支持我们现有的特征集方向。
8. **Sumayli 2026（10.3389/fchem.2026.1794154）**：在 116 条 niosome 数据上做因果发现，
   结论是**药物固有性质（尤其亲脂性）是上游约束而非可干预变量，且预测重要性不等于因果影响**。
   这条对我们的建模叙事很重要：特征重要性排序不能当作配方设计建议。
9. **Yanes 2025（10.1016/j.ijpx.2025.100393）**：自建开放脂质体体外释放 + 配方数据库，
   并明确指出当前报告实践的缺口。属于 C 工作流可直接抽取的数据源。
10. **Johnsen 2019（10.1016/j.jconrel.2019.01.005）**：TfR 抗体密度三档
    （0.15 / 0.3 / 0.6 ×10³ 抗体每 μm²），最高密度入脑最好；同时在小鼠上观察到静脉给药后严重不良反应。

## 判定

新增率 82.2%（上一批 87.0%），两批都远高于 20% 的饱和线，**不触发停止条件**。
累计 79 次检索，主表 974 行。
