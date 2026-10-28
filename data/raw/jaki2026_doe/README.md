# Jaki 2026: DoE 双离心驱动的难溶 API 脂质体包载筛选平台

| 项 | 值 |
|---|---|
| DOI | `10.1016/j.ijpx.2026.100627` |
| 作者 | Jaki, Miriam; Köll-Weber, Monika; Lembeck, Jan; Wittmann, Maximilian; Süss, Regine |
| 出处 | International Journal of Pharmaceutics: X 12, 100627, 2026 |
| 授权 | **CC BY 4.0** |
| 授权登记 | `docs/data-licensing.md` 第二节 |

## 原始下载链接

> 待填。请写下实际下载页面的完整 URL（不是 doi.org 跳转前的链接），以及补充材料各文件的直接链接。

- 文章页面：
- 补充材料：

## 下载日期

> 待填。

## 需要的文件

- DoE 配方矩阵表（各脂质组分与摩尔比、D/L 比、包载结果）
- 3 个 PROTAC 的身份信息。ACBI2 以外另两个的名称或结构
- 补充材料里的 HPLC 方法与原始测定值表

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

CC BY 4.0 要求标明是否对原始材料做了修改。抽取过程中的每一项修改都要记在这里。

> 待填。抽取完成后由抽取脚本的报告填入。预期至少包括：重新组织成仓库 schema、单位换算、SMILES 规范化、InChIKey 计算。

## 备注

抽取目标：按 `docs/literature-protocol.md` 第三节 schema 抽成配方数据。
**PROTAC 分子量通常超过 900 Da**，按协议 N1 仍提取但标 `mw_over_default_cap = TRUE`，默认不进主数据集。
该文同时是 P 类（3 个 PROTAC）和 L 类（多种脂质基质），抽取时 `study_block_id` 要按工艺与测定方法是否相同来切分。
