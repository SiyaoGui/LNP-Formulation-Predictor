# Yanes 2025: 把体外释放与配方数据做成 AI-ready

| 项 | 值 |
|---|---|
| DOI | `10.1016/j.ijpx.2025.100393` |
| 作者 | Yanes, Daniel; Mead, Heather; Mann, James; Röding, Magnus; Paraskevopoulou, Vasiliki; Alexander, Cameron; Parhizkar, Maryam; Twycross, Jamie; Zelzer, Mischa |
| 出处 | International Journal of Pharmaceutics: X 10, 100393, 2025 |
| 授权 | **CC BY 4.0** |
| 授权登记 | `docs/data-licensing.md` 第二节 |

## 原始下载链接

来源见本目录 `补充数据.txt`（用户下载时记录的数据可用性声明原文）：

- 文章页面：https://www.sciencedirect.com/science/article/pii/S2590156725000787
- 数据库 GitHub：https://github.com/danielyanes22/nanomed_IVR_data.git
- 诺丁汉研究数据管理存储库：http://doi.org/10.17639/nott.7542
- 补充材料：文章页面 Appendix A，文件 `1-s2.0-S2590156725000787-mmc1.docx`

## 下载日期

2026-10-28（由用户下载并提交）。

## 需要的文件

- 文中所称的开放脂质体数据库本体。摘要说它含配方参数、IVR 测试条件、数字化释放曲线
- 若数据库托管在仓库外（GitHub / Zenodo / 机构库），把下载到的文件放进来，并在上面的链接一节写明托管地址
- 补充材料里的数据标准与数据库结构说明也放进来，抽取时要照它对齐字段

## 文件清单与校验值

> 由 `python3 scripts/record_raw_checksums.py` 自动生成并写入本节，不要手填。

<!-- CHECKSUMS:BEGIN -->
| 文件 | 大小（字节） | SHA-256 |
|---|---|---|
| `1-s2.0-S2590156725000787-mmc1.docx` | 135,884 | `014ede2f588acd3dbd28b3d8007a1fe6482e7065b27030aaa2e6e99a69d1a887` |
| `nanomed_IVR_data-main.zip` | 4,395,115 | `73632455ac272066131ff86c264ef2e46b1bda7f53cb1b390cf26c92d7dd95cb` |
| `补充数据.txt` | 478 | `17984cb9d7e5ac1c3b92fe1cc219b047f482cbf4aafbb5f4341d0944e7f82a92` |
<!-- CHECKSUMS:END -->

## 做过哪些修改

CC BY 4.0 要求标明是否对原始材料做了修改。原始 zip 与 docx **未被改动**，以下修改全部发生在派生产物 `data/processed/yanes2025_enrichment.csv` 上，由 `scripts/extract_yanes2025.py` 执行，可复现。

1. **抽取范围缩小。** 只取 `backend_data.csv`、`media_components.csv`、`quality_reporting.csv` 三张表，图表与分析代码未使用
2. **重新组织成增补表。** 一行等于一个 IVR 实验，带到仓库记录的连接键
3. **修了 `quality_reporting.csv` 的表头。** 原文件第 0 行是分组标题、第 1 行才是真表头，脚本把第 1 行提升为列名
4. **折叠了释放介质组分。** `media_components.csv` 的长表（563 行）按 IVR_ID 折叠成分号分隔的一列
5. **质量评级列重命名**，加 `quality_` 前缀并转小写下划线
6. **新增连接列**：`ivr_id_from_curve`（从仓库 `release_curve_file` 解析出的数字）、`linked_to_repo`、`name_matches_repo`
7. **未做单位换算**，未删除任何行

## 备注

**2026-10-28 重大更正：这不是一个新数据源，它就是仓库里 PMC_IVR 的来源。**

验证过程（`scripts/extract_yanes2025.py` 的文档字符串里有完整记录）：

- 22 个化合物与仓库 PMC_IVR 的 22 个完全相同，InChIKey 交集 22，两侧各自独有 0
- 用仓库 `release_curve_file` 的数字对 Yanes `IVR_ID` 连接，**271 行全部连上**
- 化合物名 **271/271 一致**
- 粒径两边都有值的 216 条，**216/216 数值完全相同**（差 < 0.51 nm）

所以它贡献 **0 个新化合物、0 个新配方**。抽取形态因此从「配方表」改为「增补表」，产物是 `data/processed/yanes2025_enrichment.csv`，不是 `formulations_yanes2025.csv`。

**实际价值**：给已有的 272 条记录补上仓库 schema 里没有的字段，其中 `drug_loading`（249/271 非空）填的正是 `docs/literature-protocol.md` 3.4 节标出的那个空缺（「现有 schema 完全没有这一列，而它是包封率的一级决定因素」）。

**释放曲线不在这个包里。** 4.4 MB 的 GitHub 快照只有后端数据库、介质组分、质量评级和分析代码，数字化的释放曲线应该在 269 MB 的诺丁汉机构库存档（`standardisation_nm_IVR.zip`）里。释放动力学本轮不作为目标，暂不追。
