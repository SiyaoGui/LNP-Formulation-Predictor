# Jaki 2026: DoE 双离心驱动的难溶 API 脂质体包载筛选平台

| 项 | 值 |
|---|---|
| DOI | `10.1016/j.ijpx.2026.100627` |
| 作者 | Jaki, Miriam; Köll-Weber, Monika; Lembeck, Jan; Wittmann, Maximilian; Süss, Regine |
| 出处 | International Journal of Pharmaceutics: X 12, 100627, 2026 |
| 授权 | **CC BY 4.0** |
| 授权登记 | `docs/data-licensing.md` 第二节 |

## 原始下载链接

文件由用户在本地浏览器下载后提交进仓库（容器网络策略不允许直连出版社域名）。
文件名里的 `S2590156726001477` 是 ScienceDirect 的 PII，可据此复原下载位置：

- 文章页面：https://www.sciencedirect.com/science/article/pii/S2590156726001477
- 正文 PDF：同页 "Download full issue / PDF"，落地名 `1-s2.0-S2590156726001477-main.pdf`
- 补充材料：同页 "Appendix A. Supplementary data"，落地名 `1-s2.0-S2590156726001477-mmc1.docx`
- `linked-discoveries-42598203-50rows-2026-10-28.csv` **不是本文的补充材料**，
  是以本文 PMID 42598203 为中心导出的 PubMed 引文网络（50 行，含 Cited by / Cites）。
  见下方「文件清单」说明。

## 下载日期

2026-10-28（校验值记录日期同日）。

## 需要的文件

实际用到的，以及原计划里落空的：

| 需要的内容 | 在哪 | 状态 |
|---|---|---|
| DoE 配方矩阵（6 因子、40 run） | mmc1.docx 表 8 | 已抽取 |
| DoE 响应值（粒径/PDI/zeta/DL 比/IE） | mmc1.docx 表 9 | 已抽取 |
| 5 个确认实验配方与实测均值 | 正文 PDF 表 3 | 已抽取 |
| ACBI2 分子量 | mmc1.docx 表 A.1（1064 Da） | 已抽取 |
| **3 个 PROTAC 各自的配方数据** | 不存在 | **落空，见备注** |
| HPLC 方法与原始测定值表 | 正文 2.x 节、mmc1 | 未抽取，对建模无用 |

## 文件清单与校验值

> 由 `python3 scripts/record_raw_checksums.py` 自动生成并写入本节，不要手填。

<!-- CHECKSUMS:BEGIN -->
| 文件 | 大小（字节） | SHA-256 |
|---|---|---|
| `1-s2.0-S2590156726001477-main.pdf` | 11,440,827 | `eb88e7b1c275418f5bf2f429c442ef69b22d2b371cdae649338296a50e99ffd7` |
| `1-s2.0-S2590156726001477-mmc1.docx` | 4,058,883 | `175423b92c3f878e68f1e37e31769df13a668b4d9fdc8cb48dc3cd632580dc63` |
| `linked-discoveries-42598203-50rows-2026-10-28.csv` | 93,843 | `a69d78c2fb52c3ed7bab810dedba9415a879433a3ee942d07dfdc996f6c8dde6` |
<!-- CHECKSUMS:END -->

## 做过哪些修改

CC BY 4.0 要求标明是否对原始材料做了修改。抽取脚本是 `scripts/extract_jaki2026.py`，
产物是 `data/processed/formulations_jaki2026.csv`（45 条）。做过的修改：

1. **重新组织成仓库 schema**。原文是「设计矩阵表 + 响应表」两张分开的表，按 Run 号
   对齐合并成一行一个配方；正文表 3 的 5 个确认实验追加在后面。
2. **DOPC 与 DOPG 合并进 helper 槽位**。仓库 schema 只有 4 个脂质槽位
   （ionizable / helper / sterol / peg），DOPG 没有对应槽位。
   `helper_lipid_pct` = DOPC% + DOPG%，并置 `n_components_in_helper_slot = 2`、
   `slot_assignment_uncertain = TRUE`。**原始的两个百分比没有丢**：
   完整写进 `composition_raw_verbatim`，并另立 `component_dopc_pct`、
   `component_dopg_pct`、`anionic_lipid_frac_of_total` 三列。
   这一步必要，因为 DOPG 是阴离子脂质，是本文 zeta 电位的主要驱动
   （阴离子份额与 zeta 的 r = −0.645；DOPG=0 组 zeta 中位 −2.2 mV，
   DOPG>0 组 −16.3 mV）。折叠进 helper 槽后这个信息就看不出来了。
3. **确认实验取三列中的中间列**。正文表 3 每个响应给三个数
   （`95% prediction interval low` / `Data Mean` / `high`），取中间的实测均值
   （n=3），两侧的预测区间**没有**抽进来。
4. **未做单位换算**。原文组分已是 mol%，粒径 nm，zeta mV，IE %，D/L 比 %，直接沿用。
5. **未做 SMILES 规范化、未计算 InChIKey**。原文没有给 ACBI2 的结构式，
   所以 `payload_smiles` / `payload_inchikey` 留空，`payload_id_source = uncertain`。
   不自己猜结构。
6. **负号修复**。PDF 文本层把减号渲染成 `(cid:0)`，docx 里是 Unicode 减号 `−`，
   都统一成 ASCII `-`。
7. **未填的字段保持空**。原文未报 40 个 DoE run 的重复次数与标准差，
   `n_replicates` / `value_sd` 留空（确认实验的 `n_replicates = 3` 有原文依据）。
   原文未逐个 run 报缓冲液组成（只在 CryoTEM 子集提到组氨酸/葡萄糖缓冲液），
   `aqueous_phase_buffer` 留空。

## 备注

抽取目标：按 `docs/literature-protocol.md` 第三节 schema 抽成配方数据。
ACBI2 分子量 1064 Da，超过 900 Da 上限，按协议 N1 仍提取但 45 条全部标
`mw_over_default_cap = TRUE`，默认不进主数据集。

### 它不是 P 类，只是 L 类。收集阶段判断错了

收集时根据摘要那句 "demonstrated across three distinct PROTACs" 把本文标成
「P 类（3 个 PROTAC）+ L 类」。核对全文后这个判断是错的：

- ACBI1 和 ACBI3 只出现在 HPLC 方法验证的文字里（各 6 次提及），**没有任何配方数据**
- ACBI2 提及 84 次，是唯一有配方与响应数据的载荷
- 摘要那句说的是 HPLC 方法对三个 PROTAC 都适用，不是三个载荷各有配方

所以 45 条记录是**单一载荷下变脂质配方**，`block_varies_by = multiple`
（同时变 4 个组分比例 + pH + 脂质浓度），纯 L 类。
它对「唯一化合物数」这个瓶颈指标的贡献是 0。

### study_block_id 的切分

按原文的 Block 列切成 `jaki2026_batch1`（run 1-20）、`jaki2026_batch2`（run 21-40），
确认实验单独一组 `jaki2026_confirmation`。DoE 的两个 batch 是原文自己的区组因子，
不是不同工艺。确认实验分开是因为它是 n=3 均值，而 DoE 是单次测定。

### 这批数据的实际价值

单一载荷、45 条、6 个工艺与组分因子、5 个响应全齐，并且是同一实验室同一方法
同一台仪器测的。它不能抬高唯一化合物数，但它是目前拿到的**唯一一个组分比例
连续变化且响应完整的区组**，适合用来单独检验「在固定载荷下，脂质组分比例能否
预测 EE」这个比跨源预测弱得多、但可能真能成立的问题。
