# LNP Formulation Predictor

AI驱动的脂质纳米粒(LNP)/脂质体配方预测项目。目标是根据所载药物的分子性质预测配方与性能。

> **先读这两份**：`docs/handoff.md`（交接文档，结论和下一步）和 `docs/glossary.md`（术语表）。
> 给导师或评审看：`docs/algorithm-results-en.md`（英文版三轮结果汇总）。

---

## 当前状态（2026-10-22，这是最新的结论，取代了下方「历史」一节里的旧说法）

**现有的粒径预测模型在严格评估下不成立。** 这一轮用在跑模型之前就冻结的评估协议做了三轮建模，结论如下：

| 轮次 | 数据 | 目标 | 结论 |
|---|---|---|---|
| 第一轮 | 73 个配方 / 15 个小分子药 / 26 篇论文 | 粒径 | **不成功**，没有任何模型打败「永远预测平均值」的常数基线 |
| 第二轮 | 370 个单元 / 197 个可离子化脂质 / 37 篇论文 | 包封率 | **可学**（5/5 种子打败常数基线），但信号只在论文内部成立 |
| 第三轮 | 322 个单元 / 5 类 payload / 55 篇论文 | 粒径（大分子） | 所有模型都比常数基线更差 |

三条核心结论：

1. **粒径主要由制备工艺决定，不是由药物分子决定。** 删掉全部分子特征性能几乎不变（0.192 → 0.198），只用分子特征还不如常数基线（0.257 vs 0.253）。数据里 atenolol 和 propranolol 同配方不同工艺，粒径差 25 倍。
2. **换成包封率后，四条诊断全部反转**，分子成为主导信号。机制上说得通：包封率取决于分子的亲脂性、电荷、氢键能力。
3. **真正的瓶颈是跨实验室不可比，不是样本量。** 三轮、两个目标变量、样本量从 73 到 370，按论文分组后优势每次都归零。

**下一步**：自己在一套固定方案下采包封率数据，不要继续从文献聚合。规格见 `docs/data-spec-ee.md`。

---

## 目录结构

### 本轮产出

| 路径 | 内容 |
|---|---|
| `docs/handoff.md` | **交接文档：结论、判断、下一步、所有材料索引** |
| `docs/algorithm-results-en.md` | 英文版三轮结果汇总 |
| `docs/data-spec-ee.md` | 包封率数据采集规格 |
| `docs/glossary.md` | 术语表（B0/B1/B2/B3、分组划分、pp、5/5 等） |
| `docs/evaluation-protocol.md` | 第一轮评估协议，**在跑模型之前冻结** |
| `docs/ee-feasibility-protocol.md` | 第二轮评估协议，**在跑模型之前冻结** |
| `docs/data-inventory.md` | 数据盘点 |
| `docs/feature-engineering.md` | 特征说明与泄漏检查 |
| `docs/worklog/` | 四份过程日志 |
| `modeling/INDEX.md` | 建模总表 |
| `modeling/2026-10-19_smallmol-baseline/` | 第一轮完整产出（5 张图、metrics.json、逐条预测） |
| `modeling/2026-10-20_ee-feasibility/` | 第二轮完整产出 |
| `modeling/2026-10-20_largemol-sideproduct/` | 第三轮 + 跨子集对比 |
| `lnp/` | 可复用模块：子集定义、特征、数据集、评估 |
| `scripts/` | 八个入口脚本，每一步可单独重跑 |
| `configs/` | 配置文件，换子集只改一行 |
| `data/processed*/` | 特征矩阵与分析单元表 |

### 数据与历史产出

| 路径 | 内容 |
|---|---|
| `merged_formulations_v2.csv` | 三源合并后的主数据表，1934 行 |
| `LNP_Atlas_DB_202509_v1_utf8.csv` | LNP Atlas 原始数据 |
| `M1_*.md` 到 `M6_*.md` | 早期各阶段技术文档，按编号读可还原技术演进 |
| `HF_upload/`、`M5_streamlit_app/` | 早期部署的 Streamlit 应用 |
| `train_m4.py`、`featurize_m3.py`、`merge_schema.py` 等 | 早期脚本 |
| `专利文献数据源调研报告.md`、`预印本数据搜索_进展记录_按数据形态.md` | 数据扩充的两条调研线 |

---

## 环境准备（每个新的云会话都要先跑一遍）

**云会话的容器不预装这些依赖。** 容器是临时的，上一个会话装过的下一个会话里没有，所以每开一个新会话，动手前先跑：

```bash
pip install scikit-learn rdkit pyarrow matplotlib tabulate
```

`rdkit` 是硬依赖，不装的话这几个脚本会直接 `ModuleNotFoundError`：

| 脚本 | 用途 |
|---|---|
| `scripts/data_inventory.py` | 数据盘点 |
| `scripts/build_features.py` | 特征工程（描述符 + Morgan 指纹） |
| `scripts/report_compound_gain.py` | 外部数据集的唯一化合物增量报告 |

容器里 `pypi.org` 和 `files.pythonhosted.org` 在网络策略的放通名单内，所以 pip 能直接装。但 `zenodo.org`、各出版商域名、PubMed、Europe PMC 都是拦住的，只有 `api.crossref.org` 通，外部原始数据文件要在容器外下载再提交进仓库（见 `data/raw/README.md`）。

版本记录：`docs/data-inventory.md` 的数字是用 RDKit 2026.09.1 算的。后续会话用 pip 当前版本，唯一化合物数与骨架数已核对能对上（见 `docs/worklog/2026-10-27-抽取准备.md` 第三、四节）。若哪天对不上，以新脚本输出为准并在工作日志记录。

---

## 怎么重跑

先按上面「环境准备」装好依赖，然后：

```bash
# 第一轮
python3 scripts/build_features.py --config configs/smallmol_baseline.yaml
python3 scripts/run_modeling.py   --config configs/smallmol_baseline.yaml --out modeling/<新日期>_<说明>
python3 scripts/render_tables.py  --dir   modeling/<新日期>_<说明>
python3 scripts/make_figures.py   --dir   modeling/<新日期>_<说明>

# 第二轮（包封率）
python3 scripts/run_ee_feasibility.py --groups G1 --out modeling/<新日期>_<说明>
```

完整的环境注意事项见 `docs/handoff.md` 第六节。

---

## 规则

- 每次建模新建 `modeling/YYYY-MM-DD_<简短说明>/`，**不覆盖、不修改以前的文件夹**
- 评估协议冻结后不许为了结果好看而修改；确需修改必须单独提交并写明原因和当时已有的结果
- 每个结果都要带置信区间和跨种子波动，不许只报最好的种子

---

## 历史记录（下面是本轮之前的说法，已被上面的结论取代，保留以便追溯）

早期版本报告过「粒径预测按论文分组交叉验证 R²=−0.135」「PDI 分组 R²=−0.033」，并把瓶颈判断为「样本量/数据多样性不足」。

本轮的修正是：样本量确实不足，但那不是主要原因。更根本的问题是**目标变量选错**（粒径是工艺的函数）和**文献数据跨来源不可比**（每篇论文一种药一套工艺，分子效应不可识别）。样本量从 73 涨到 370 没有改变按论文分组后优势归零这个事实。

另外，更早的版本曾报告过 R²=0.43 的「好成绩」，那是行级随机划分造成的，同一篇论文的数据同时出现在训练和测试里。严格分组后掉到 0 附近。这个教训记录在 `docs/handoff.md` 第九节。

## 说明

这个仓库只包含代码、训练数据、模型文件和技术文档。原项目文件夹里的个人文件（证件、签名、简历）和商务文件（基金申请草稿、外联邮件、合作意向书模板等）按要求不包含在内。
