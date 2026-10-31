# 第 12 批：到期前清空式检索（检索 50–64）

日期：2026-10-31
分支：claude/epic-lamport-oyzbye
模式：会员次日到期，按"尽量压低 cloud 用量、不限制 Consensus 次数"执行。
每轮 3 次检索，批次之间不写分析，满 15 次统一抽取入库。

## 本批 15 次检索

| # | 检索式 | 工作流 | 默认优先级 |
|---|---|---|---|
| 50 | process analytical technology in-line monitoring liposome lipid nanoparticle manufacturing | A;D | P0 |
| 51 | quality by design critical process parameters liposome formulation design of experiments | B;D | P1 |
| 52 | microfluidic total flow rate and flow rate ratio effect on lipid nanoparticle size and encapsulation | B;D | P0 |
| 53 | real-time feedback control of nanoparticle production closed loop process control | D | P1 |
| 54 | batch-to-batch variability and reproducibility of liposome manufacturing between operators and sites | D;I | P0 |
| 55 | lyophilization freeze-drying cryoprotectant effect on lipid nanoparticle size and encapsulation retention | B;D | P1 |
| 56 | receptor mediated transcytosis quantitative transport efficiency across brain endothelial monolayer nanoparticle | H | P0 |
| 57 | focused ultrasound blood-brain barrier opening nanoparticle delivery quantitative brain concentration | H | P1 |
| 58 | P-glycoprotein efflux effect on nanoparticle encapsulated drug brain accumulation | B;H | P1 |
| 59 | eriodictyol pharmacokinetics bioavailability nanoformulation delivery | B;H | P1 |
| 60 | flavonoid nanoparticle brain delivery blood-brain barrier permeability quantitative neuroprotection | B;H | P0 |
| 61 | curcumin encapsulation efficiency variability across different lipid carriers comparison studies | B;I | P0 |
| 62 | intranasal nose-to-brain lipid nanoparticle drug delivery brain concentration quantitative | H | P1 |
| 63 | machine learning prediction of nanoparticle size and encapsulation efficiency from formulation parameters | A;C | P0 |
| 64 | solid lipid nanoparticle particle size encapsulation efficiency response surface methodology optimization | B;C | P0 |

## 入库结果

- 命中记录 300 条（15 × 20）
- 新增 261 条，重复 39 条，**新增率 87.0%**
- 主表从 469 行增至 **729 行**（去重后 730 行含表头）
- 本批有 145 条摘要不含任何定量结果（无 nm、无百分数、无 mV、无 R²、无浓度），已标 `needs_fulltext=Y`
- 许可字段对全部 730 条重跑 Crossref：CC 系列 383、仅出版商或 TDM 条款 279、未列 64、未解析 4
- 需全文合计 297 条，其中 **160 条为开放许可，可立刻合法下载**

## 抽取方式说明（与前 11 批不同，必须记录）

为压低 cloud 用量，本批 `why_matters` 不再逐条人工撰写，改为机械生成：
检索主题的中文短句 + 从该条摘要里用正则抓出的前 3 个定量片段（nm / EE% / mV / R² / RMSE / 浓度 / PDI）。
抓不到任何定量片段的，一律写"摘要无定量结果，需全文"并标 Y。
**这意味着：本批 why_matters 里出现的每个数字都来自 Consensus 返回的摘要原文，没有任何补全或推断，
但也没有人工判断该数字是否就是这篇论文最关键的数字。** 后续要用某条时仍需看摘要或全文。
DOI、标题、年份、期刊四列同前 11 批，全部来自 Consensus 返回原文，脚本直接写入，无人工转录。

## 本批值得单独记住的条目（来自摘要原文）

1. **Lee 2026，在线 PAT + 机器学习预测脂质体粒径**，RMSE 7.18 nm、外部泛化 7.53 nm
   （10.1002/smtd.70663）。这是目前检到的唯一一篇把"在线传感 + 预测模型"做成闭环并报出泛化误差的论文，
   与 `hardware/README.md` 的 L2/L3 路线直接对应。
2. **Glader 2025，SR-DLS（NanoFlowSizer）离线/在线/在线旁路三种模式对比**（10.3390/pharmaceutics17060684）。
3. **Sheybanifard 2022，连续流生产 + 在线 CQA 控制**（10.1039/d2lc00463a）。
4. **Buttitta 2025，机器学习引导的微流控脂质体优化，>300 组实验条件**（10.1016/j.ijpharm.2025.126362）。
5. **Lavagna 2026，Smart Microfluidics 跨实验室数据集，304 + 12 组配方，数据在 Zenodo**
   （10.1016/j.dib.2026.112667）。Zenodo 本容器被网络策略拦，需在浏览器侧下载。
6. **Ohta 2020，聚焦超声开放血脑屏障下的最优粒径**：15 nm 最好，入脑 0.22 %ID（10.1038/s41598-020-75253-9）。
7. **Venugopal 2025，FUS-BBBO 的 37 种药物 / 60 项研究荟萃**（10.1093/neuonc/noaf201.0621）。
8. **Youdim 2004，黄酮类原位脑灌注透过率**：柚皮素 Kin 0.145 对槲皮素 0.019 mL/min/g
   （10.1016/j.freeradbiomed.2003.11.023）。同一类分子之间差 7.6 倍，是分子面板重选的直接依据。
9. **Malvajerd 2018，姜黄素 NLC 脑 AUC 505.76 对 SLN 116.31 对游离药 0.00 ng/g·h**
   （10.1021/acschemneuro.8b00510）。
10. **圣草酚（eriodictyol）检索基本无制剂与药代数据**，只检到抗癌机制综述。
    这条是阴性结果但很重要：如果首发管线要用圣草酚，它没有可训练的制剂文献底座，
    必须自己产数据，不存在"先用文献数据冷启动"这条路。

## 判定

本批新增率 87.0%，远高于 20% 的饱和线，**不触发停止条件**。
原因明确：前 11 批在 A/B/C/D 工作流上检的是方法学与数据集，这一批转向
"工艺参数—质量属性"与"脑递送路径"两类具体题面，命中的基本是另一批论文。
下一批继续沿脑递送与工艺参数两条线推进。
