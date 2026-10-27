# Khawar 2022: 辛醇/水分配系数与亨利常数预测脂质/水分配系数

| 项 | 值 |
|---|---|
| DOI | `10.1038/s41598-022-19452-6` |
| 作者 | Khawar, Muhammad Irfan; Mahmood, Azhar; Nabi, Deedar |
| 出处 | Scientific Reports 12(1), article 14936, 2022 |
| 授权 | **CC BY 4.0** |
| 授权登记 | `docs/data-licensing.md` 第二节 |

## 原始下载链接

> 待填。请写下实际下载页面的完整 URL（不是 doi.org 跳转前的链接），以及补充材料各文件的直接链接。

- 文章页面：
- 补充材料：

## 下载日期

> 待填。

## 需要的文件

- 含 logKlw（储存脂/水，n=305）和 logKpw（磷脂/水，n=131）实测值的表。按摘要推测在补充材料里
- 若补充材料有多个文件，全部放进来
- 需要的是**化合物名 + 实测分配系数 + 测定条件**；只有模型系数的表用不上

## 文件清单与校验值

> 由 `python3 scripts/record_raw_checksums.py` 自动生成并写入本节，不要手填。

<!-- CHECKSUMS:BEGIN -->
（尚无文件）
<!-- CHECKSUMS:END -->

## 做过哪些修改

CC BY 4.0 要求标明是否对原始材料做了修改。抽取过程中的每一项修改都要记在这里。

> 待填。抽取完成后由抽取脚本的报告填入。预期至少包括：重新组织成仓库 schema、单位换算、SMILES 规范化、InChIKey 计算。

## 备注

抽取目标表：`data/processed/partition_coefficients.csv`，schema 见 `docs/schema-partition-coefficients.md`。
**磷脂/水（logKpw，n=131）是主力**，对应经典脂质体；储存脂/水（logKlw，n=305）对应 SLN/NLC，留给将来。
注意：该文的实测值汇集自更早的原始文献，局限写在 schema 文档第五节。
