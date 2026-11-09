# Perplexity 提示词包 v3（2026-10-22）

## v3 为什么整个重写

v2 那十组查询，**第 1、2、3、4、5、6、8 组现在都不该跑了**。

原因是另一条线三轮建模的结论：瓶颈不是数据量，是**文献跨实验室不可比**。每篇论文几乎都是"一种药配一套工艺"，分子效应和工艺效应在数学上分不开。样本量从 73 涨到 370，按论文分组后优势每次都归零。所以"把文献堆多"这个方向被证伪了。v2 第 2 组（找综述里的汇总表）当时被我列为最高优先级，**现在是最有害的一组**，因为跨来源的包封率混在一起会把真实信号稀释掉。

同时目标变量从粒径换成了**包封率**，主题从 mRNA-LNP 换成了**小分子药物的脂质体包载**。检索词几乎没有一个能复用。

v3 只剩三个任务，范围窄得多，大概一两天能跑完，不是一周。

---

## 用法

Space 和上传文件的做法不变（界面路径我仍然没核实到，以你看到的为准）。把 `LipidLens_literature_sourcing_brief_EN.md` **换成新版**重新上传，旧版删掉，否则两份互相矛盾。

自定义指令换成下面这段（约 850 字符）：

```
You are a literature TRIAGE assistant for LipidLens. Read the uploaded file
"LipidLens_literature_sourcing_brief_EN.md" (v3) before every answer and follow it exactly.

Scope is narrow on purpose. Only three jobs: (1) 3-5 small molecules with reliably published
liposomal encapsulation efficiency, for assay cross-check; (2) a candidate pool of small molecules
with published liposomal EE, spread across scaffold, LogP, charge; (3) papers where ONE lab
encapsulated 5+ different molecules under ONE fixed process, with per-molecule EE.

Do NOT bring mRNA-LNP particle-size papers, aggregated cross-paper formulation tables, or
single-formulation papers. Volume is harmful here, not helpful.

TRIAGE, not extraction: never copy numeric values out of a paper (one exception, Job 1, where you
may report that two sources disagree and roughly by how much). Every entry needs a DOI. Report
rejections with the criterion number. Say "nothing usable found" rather than padding. End with a
one-line saturation check.
```

---

## 任务 1（最高价值）：找 3 到 5 个有可靠公开包封率的分子

**短版**
```
Find 3-5 small molecules whose LIPOSOMAL encapsulation efficiency is reported by two or more
independent research groups, so that the between-lab spread is visible. For each, the paper must
state the free-drug separation method (dialysis, ultrafiltration, SEC, or centrifugation), the
drug-to-lipid ratio, and the full lipid composition in mol%. Prefer cheap, commercially available,
well-characterised compounds. List every source per molecule and say explicitly where two sources
disagree and roughly by how much. Disagreement between labs is what I want to see, not hide.
```

这组的产出直接进 `docs/data-spec-ee.md` 第 2.3 节那一条"建议含 3 到 5 个文献里已有可靠包封率的分子，用于与外部数据对齐和方法学校验"。

## 任务 2：给 40 到 60 个分子的面板攒候选池

**短版**
```
Build a CANDIDATE POOL of small molecules that have been encapsulated in liposomes with a published
encapsulation efficiency. I need breadth of chemistry, not depth per entry: as many distinct Murcko
scaffolds as possible, LogP spread from -1 to 6 with candidates in every integer bin, TPSA 20-200,
and acids, bases and neutrals all represented, MW 200-900 Da.
Priority: eriodictyol and structurally related flavonoids (hesperetin, naringenin, taxifolin,
quercetin, luteolin). Anything on their liposomal encapsulation is top priority.
For each: name, SMILES or CAS if findable, approximate LogP, one source DOI, one line on what
chemical diversity it adds. A list is fine, no deep screening needed.
```

**这组可以分批跑**，比如先跑黄酮类，再按 LogP 区间分段补。最终选分子是用 RDKit 的 MaxMin 算法做，不是靠这个列表直接定，所以宁可宽一点。

## 任务 3：唯一还值得找的论文形态

**短版**
```
Find papers where ONE laboratory encapsulated at least 5 DIFFERENT small molecules in liposomes
using the SAME fixed formulation and the SAME process, reporting per-molecule encapsulation
efficiency in a table.
Check first and hardest: was the process actually held constant across the molecules? If different
molecules got different processes, it FAILS. This is the most common failure mode.
Also required: full lipid composition in mol%, drug-to-lipid ratio, and the free-drug separation
method stated. Say whether the table is in the main text or SI.
Expect these to be rare. If you find none, say so plainly rather than returning near-misses.
```

这是唯一一种"分子效应可识别"的文献形态。找到一篇都算赚。

---

## 三件必须知道的事

**一，这轮的产出不是训练数据。** 任务 1 是校准用的参照点，任务 2 是选分子的候选池，任务 3 是方法学参考。**都不进训练集。** 训练数据只来自你自己在固定方案下测的那批。这是这一轮建模最硬的结论。

**二，Perplexity 读 SI 的 PDF 不可靠，而且它和 Consensus 都没有任何资料说能读 Supporting Information。** 它能告诉你"有没有表"，别信它说表里是什么。Consensus 尤其不要用在这个任务上：它的检索主要由标题和摘要驱动，产出的是观点综述不是结构化数据。

**三，中文文献够不到。** Perplexity 进不了知网和万方。黄酮类脂质体包载这块中文文献量不小，而且正好是你管线最相关的那一块。这块只能你自己用知网搜，或者先放着。

---

## 结果怎么收

`screening_log.csv` 的表头要换，因为列变了：

```
doi,molecule,first_author,year,venue,n_molecules,ee_per_molecule,process_fixed,separation_method,table_location,access,licence,verdict,failed_criterion,note,job,date_added
```

`job` 填 1/2/3，`date_added` 填日期。
