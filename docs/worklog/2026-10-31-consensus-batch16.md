# 第 16 批：到期前清空式检索（检索 110–124）

日期：2026-10-31
模式与口径同第 12–15 批：`why_matters` 机械生成，数字全部来自 Consensus 返回的摘要原文，
没有补全或推断，也没有人工判断该数字是否是该论文最关键的数字。

## 本批 15 次检索

| # | 检索式 | 工作流 | 默认优先级 |
|---|---|---|---|
| 110 | lipid nanoparticle hydrophobic small molecule drug loading capacity limits comparison with nucleic acid | B;C | P0 |
| 111 | liposome remote loading pH gradient ammonium sulfate weak base drug encapsulation mechanism | B;D | P0 |
| 112 | in vitro release testing dialysis USP apparatus 4 nanomedicine standardization biorelevant media | A;D | P0 |
| 113 | solid lipid nanoparticle burst release drug expulsion during lipid crystallization polymorphic transition storage | A;B | P0 |
| 114 | excipient variability raw material lot to lot lipid purity impact on nanoparticle formulation performance | B;D | P0 |
| 115 | quercetin nanostructured lipid carrier brain delivery neuroprotection in vivo pharmacokinetics | B;H | P0 |
| 116 | curcumin brain delivery lipid nanoparticle quantitative brain concentration bioavailability rat | B;H | P0 |
| 117 | berberine baicalin ginkgolide natural product nanoparticle central nervous system delivery pharmacokinetics | B;H | P1 |
| 118 | epigallocatechin gallate fisetin pterostilbene nanoparticle encapsulation efficiency brain targeting | B;H | P1 |
| 119 | intranasal delivery lipid nanoparticle brain targeting nose-to-brain quantitative drug targeting efficiency | B;H | P0 |
| 120 | P-glycoprotein efflux inhibition nanoparticle brain accumulation small molecule substrate | B;H | P1 |
| 121 | transferrin receptor antibody conjugated nanoparticle brain delivery quantitative brain uptake percent injected dose | B;H | P0 |
| 122 | focused ultrasound microbubble blood brain barrier opening drug delivery quantitative brain concentration increase | D;H | P0 |
| 123 | glutathione PEGylated liposome 2B3-101 brain delivery clinical translation doxorubicin | F;H | P0 |
| 124 | lipid nanoparticle protein corona composition determines cellular uptake and biodistribution serum proteins | B;J | P0 |

## 入库结果

- 命中 298 条（2 条无 DOI 丢弃），新增 207 条，重复 91 条，**新增率 69.5%**
- 主表 1493 → **1701 行**（去重后无重复 DOI）
- 本批 114 条摘要不含定量结果，标 `needs_fulltext=Y`
- 重复率上升的原因明确：123（2B3-101）与第 15 批检索 96 几乎同题，
  119/121/122 三条脑递送检索与第 12–15 批的脑递送检索有共同的综述层
- Crossref 全表重跑 1701 条：解析 1680 条，CC 系列 816 / 仅出版商或 TDM 669 / 未列 195 / 未解析 21
- 需全文 906 条，其中 441 条为开放许可

## 一、载药与释放：小分子载荷的工程边界

- **Haran 1993（硫酸铵跨膜梯度主动载药）**：弱碱药物可达 >90% 包封，
  囊内积累约 100 倍于外相。这是小分子脂质体载药的基准方法，
  与被动包封（制备时同溶）在机制上完全不同。
- **Park 2019**：吉西他滨前药化后载药量 9.4–10.3 wt%，而常规方法 0.14–3.8 wt%。
  载药量跨两个数量级的差别来自"药物分子怎么改"，不是来自粒径或表面。
- **Yu 2019（10.1016/j.jconrel.2019.09.016）**：透析膜本身带来的滞后可以用数学方法校正，
  在 DOXIL 上做了验证。含义：不同实验室报告的"释放曲线"不经校正不可直接比较。
- **Wacker 2022（USP 专家组观点）**：纳米材料的体外释放方法尚无统一药典方法。
- **Jenning 2000 / Westesen 1997 / Bertoni 2021**：固脂纳米粒在贮存期发生 α→β 晶型转变，
  晶格致密化把药物挤出，这是 SLN 的结构性缺陷；加液态脂质（即 NLC）是针对这一点的工程解。

## 二、原料批次：第 14 批"报告标准化"结论的具体化

- **Ranjbar 2026（10.1016/j.jconrel.2026.114825）**：三家供应商的 MC3 纯度 86–99%，
  理化属性随之变化，但体外效力没有变。
- **Rubio-Prego 2026（10.1016/j.jpba.2026.117633）**：带杂质的离子化脂质转染效力下降，
  而粒径与包封率**没有**变化。
- 两条合起来说明：原料批次是一个会改变结果却不会出现在粒径/EE/zeta 三件套里的变量。
  本项目的特征表必须留"原料供应商与批号"列，否则同配方不同结果无法解释。

## 三、鼻腔到脑：DTE/DTP 不能直接当标签

本批拿到一批可比的定量数字（全部来自摘要原文）：

| 文献 | 载体 | DTE | DTP | 粒径 | EE |
|---|---|---|---|---|---|
| Yasir 2021（10.1016/j.jddst.2021.102939） | 丁螺环酮 CH-NLC | 1462.49% | 93.16% | 190.98 nm | 80.53% |
| Yasir 2022（10.1016/j.jddst.2022.103631） | 多奈哌齐 CH-NLC | 321.21% | 74.55% | 192.5 nm | 89.85% |
| Muntimadugu 2016（10.1016/j.ejps.2016.05.012） | 他伦氟比 PLGA-NP | 287.24 | 65.18 | <200 nm | 64.11% |
| 同上 | 他伦氟比 SLN | 183.15 | 45.41 | <200 nm | 57.81% |
| Fatouh 2017 | 阿戈美拉汀 SLN | 190.02 | 47.37 | 167.70 nm | 91.25% |

DTE 跨度 183%–1462%，接近 8 倍。**Pires 2018（10.1016/j.jconrel.2017.11.047）**
的系统综述直接说明了为什么不能横向比：各研究在设计、分析、报告上高度异质，
不同载体类别之间的脑靶向效率差异大多没有统计学显著性，
而且部分药物即使以溶液形式鼻腔给药也能高效入脑，使"做成纳米载体"的增益不明显。
对本项目的含义：DTE/DTP 作为标签必须同时记录对照臂（静脉还是鼻腔溶液）、
取样方式与给药体积，否则是不可用的标签。
Muntimadugu 2016 里聚合物粒子优于 SLN 这一条，也不支持"脂质载体默认更好"的叙事。

## 四、三条绕开血脑屏障的工程路线，各自的定量上限

**外排抑制**（P-gp/BCRP）：
- Minocha 2012 两篇：单独抑制 P-gp 或 BCRP 对万德他尼、帕唑帕尼的脑内浓度**没有**显著影响，
  双抑制剂 elacridar 才带来约 5 倍提升。
- Lagas 2009：达沙替尼在 P-gp 缺失小鼠脑内相对积累升高 3.6 倍（口服）/4.8 倍（腹腔），
  P-gp 与 BCRP 双敲除升到 13.2 倍 / 22.7 倍。
- Crawford 2019：把 P-gp 底物（罗丹明 6G）接到纳米粒上，脑内滞留提高 2 倍以上，
  在 mdr1a(-/-) 小鼠中该差异消失，证明机制确实是 P-gp。

**转铁蛋白受体穿梭**：
- Hultqvist 2017：双价设计但单价结合，2 小时脑内 2–3% ID/g，比未修饰抗体高 80 倍。
- Johnsen 2019：抗体密度 0.15 / 0.3 / 0.6 × 10³ antibodies/µm² 三档里最高密度最好，
  但同文报告 TfR 靶向脂质体在小鼠体内引起严重不良反应。
- Bonvicini 2025：低剂量（0.22 mg/kg）下亲和力起主导，高剂量（7.5 mg/kg）下价态起主导，
  两者结论相反。Smith 2025（mAbs）进一步指出，只要细胞表面结合强度匹配，
  双价并不劣于单价，"单价天然更优"的说法不成立。
- Clark 2015：在 Tf 与粒子核之间加酸可断连接提高入脑；同样的改造用在高亲和力抗 TfR 抗体上无效。
- Ghosh 2025：23 个带 DNA 条码的 TfR-Fab LNP 一次体内筛选，Fab 密度与脂质组成同时决定入脑分配。
- Song 2025：TfR RNA 适体-DSPE 偶联物脑/血比值可达 6.5，而文中引用的抗体偶联物与纳米囊泡 <1。

**聚焦超声开窗**：
- Jeong 2025：0.25 MPa 时阿杜卡努单抗入脑 7 倍，0.42 MPa 时 60 倍。压力是强非线性变量。
- Wei 2020：依托泊苷瘤内浓度 8 倍，瘤/血比 3.5 倍。
- Karim 2026（SonoCloud-9 I 期，临床）：卡铂 9.3 倍（8.21 vs 0.88 µM），紫杉醇 3.7 倍，
  脑/血比分别升 5.8 倍与 3.6 倍。
- Ciaffi 2026 系统综述：7 项临床研究，开窗成功率 92.4–100%，
  可直接定量的两项术前研究显示瘤内药物 2.2 倍；唯一的对照研究中位 OS 31.3 vs 19.3 个月。
- **Venugopal 2025 的 FAR 元分析（>60 项研究、37 种药物、6 个物种）是本批最重要的一条**：
  高分子量药物（>10 kDa）的增益显著高于低分子量（<1 kDa）；
  低分子量药物里，本身入脑差（CNS MPO 评分低）的增益更高；
  FAR 在物种之间没有显著差别。
  对本项目的含义：**对一个被动透过性本来就不差的小分子，聚焦超声的增益最小**，
  它是"难入脑小分子"的竞争方案，不是通用增强手段。
- Fletcher 2026：开窗后健康脑区游离多柔比星在 1 小时时比脂质体型高 42%，
  而肿瘤内 24 小时时脂质体型高 113%。载体形式与取样时间共同决定谁更高。

## 五、谷胱甘肽脂质体 2B3-101 的完整证据链（竞品 F 工作流）

- Birngruber 2014：脑开放流微灌注，脑/血比值比普通 Caelyx 高 4.8 倍，p = 0.0016，
  同时荧光素标记显示血脑屏障完整性未被破坏。
- Gaillard 2014（PLOS ONE）：9 只中 2 只肿瘤完全消退，双周给药中位生存期延长 38.5%。
- 临床：I 期到 70 mg/m² 未达 DLT，可持续剂量强度 15 mg/m²/周；
  IIa 期乳腺癌脑转移 11% PR、53% SD，高级别胶质瘤 31–54% SD。
- **Hu 2019（10.1016/j.ejpb.2019.04.004）**：GSH 修饰把甲氨蝶呤的 Kp,uu 从 0.10 提到 0.82（HSPC 基质），
  但在 EYPC 基质上完全无效。配体效应不可加，必须与基质一起报告。
- Mehrabian 2021/2023：后插法可以用比 2B3-101 少 40 倍的 GSH 胶束达到更高入脑，
  但同时心、肝、脾分布升高。
- Reginald-Opara 2022：GSH-PEG 脂质体吉西他滨 8 小时脑内 3.8% ID，对照 PEG 脂质体 2.8% ID，
  脑/血浓度比 1.27。
- 口径提示：同一技术在不同文献里报的量分别是脑/血比、Kp,uu、%ID、体外转运率，
  四个量不能互换。本项目在竞品表里必须按量分列。

## 六、蛋白冠：体外实验条件本身是一个变量

- **Voke 2025（10.1038/s41467-025-63726-2）**：密度梯度超离分离蛋白冠 + 定量质谱，
  稳定富集的是玻连蛋白、C 反应蛋白、α2-巨球蛋白；
  关键结论是**摄取增加并不等于 mRNA 表达增加**，部分原因是蛋白冠把 LNP 导向溶酶体。
- **van Straten 2025（10.3762/bjnano.16.57）**：热灭活血清降低 ApoE 的稳定性与功能，
  使 MC3 LNP 的摄取与递送下降，而 C12-200 LNP 不受影响。
  含义：体外数据表里必须记录"血清是否热灭活"，否则同配方的体外结果不可比。
- van Straten 2024：脑脊液来源的蛋白冠比血浆来源富含更多脂蛋白（尤其 ApoE），
  摄取更高，但同样没有换来更高的递送效率。
- **Grumelot 2026（10.1021/acs.nanolett.6c00689）**：冷冻电镜看不到硬颗粒那样的外周蛋白壳，
  LNP 膜发生局部增厚与致密化，机制是脂蛋白融合而不是表面吸附。
- Liu 2023（10.1038/s41467-023-39768-9）：HDL 是功能必需，且比常用的 ApoE 标记物
  更能预测体内活性。
- Tang 2023（Nature Nanotechnology）：高胆固醇状态改写蛋白冠，
  使颗粒更多进入肝、脾、**脑**，更少进入肺。
- Canchola 2025（PC-DB）：83 项研究、817 个配方、2497 种吸附蛋白的数据库，
  可解释 ML（ROC-AUC > 0.85）给出最重要的三个预测变量是粒径、zeta 电位、孵育时间。
  这是一个可以直接对接本项目特征表的外部数据集。

## 七、负面结果与缺口

- 柚皮素、槲皮素以外的黄酮（如圣草酚）仍然没有可用的制剂与药动学文献（第 12 批已记录）。
- 本批没有检到任何把"小分子载荷 + 脑递送 + 配方参数"三者同时定量报告、
  且样本量足够建模的公开数据集。第 14 批 Adzavon 2026 的结论在本批没有被推翻。
- 聚焦超声相关文献里，绝大多数定量终点是瘤内浓度或瘤/血比，
  极少有脑内游离药物浓度（Kp,uu），与本项目的标签定义不对齐。
