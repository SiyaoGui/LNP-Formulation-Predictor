# Khawar 2022: 辛醇/水分配系数与亨利常数预测脂质/水分配系数

| 项 | 值 |
|---|---|
| DOI | `10.1038/s41598-022-19452-6` |
| 作者 | Khawar, Muhammad Irfan; Mahmood, Azhar; Nabi, Deedar |
| 出处 | Scientific Reports 12(1), article 14936, 2022 |
| 授权 | **CC BY 4.0** |
| 授权登记 | `docs/data-licensing.md` 第二节 |

## 原始下载链接

- 文章页面：https://www.nature.com/articles/s41598-022-19452-6
- 补充材料：该页面 Supplementary Information 一节，文件 `41598_2022_19452_MOESM1_ESM.docx`

## 下载日期

2026-10-28（由用户下载并提交，文件系统时间戳为当日）。

## 需要的文件

- 含 logKlw（储存脂/水，n=305）和 logKpw（磷脂/水，n=131）实测值的表。按摘要推测在补充材料里
- 若补充材料有多个文件，全部放进来
- 需要的是**化合物名 + 实测分配系数 + 测定条件**；只有模型系数的表用不上

## 文件清单与校验值

> 由 `python3 scripts/record_raw_checksums.py` 自动生成并写入本节，不要手填。

<!-- CHECKSUMS:BEGIN -->
| 文件 | 大小（字节） | SHA-256 |
|---|---|---|
| `41598_2022_19452_MOESM1_ESM.docx` | 997,404 | `792025a44bb99ecc8d6eca63540db8f21ea889d427271357d1607bc5406d9073` |
<!-- CHECKSUMS:END -->

## 做过哪些修改

CC BY 4.0 要求标明是否对原始材料做了修改。原始 docx **未被改动**，以下修改全部发生在派生产物 `data/processed/partition_coefficients.csv` 上，由 `scripts/extract_khawar2022.py` 执行，可复现。

1. **重新组织成另一种 schema。** 原文是 19 张 Word 表格，产物是一张长表，一行等于一个（化合物 × 系数类型）
2. **合并了多张表。** Table S1 的 logKlw 与 Abraham 描述符，和 Table S10/S11 的 SMILES，按 CAS 号连接；Table S2 与 S12/S13 同理
3. **SMILES 规范化。** 用 RDKit 重新输出规范 SMILES，原文写法保留在 `smiles_as_reported` 列
4. **新增 InChIKey 列**，由 SMILES 计算，原文没有
5. **新增分子量列**，由 SMILES 计算，原文没有
6. **数值解析。** Unicode 减号（U+2212、U+2013）统一替换为 ASCII 连字符后转浮点
7. **CAS 号规范化**，去空白与非数字连字符字符
8. **未做单位换算。** 原文四个系数均为 log10 值，直接沿用
9. **未删除任何行。** 6 条因原文缺 SMILES 无法解析的记录保留在表里，标 `qc_flag = suspect`

## 备注

抽取目标表：`data/processed/partition_coefficients.csv`，schema 与抽取结论见 `docs/schema-partition-coefficients.md`。

**2026-10-28 更正**：原先写的「磷脂/水 logKpw 是主力」不准确。该文实际给了四个系数，其中 **Table S15 的 logKlipw 脂相字面就是脂质体**（36 条），比 logKpw 更贴近本项目体系。优先级：logKlipw > logKpw > logKlw，logKtw 不用。

**抽取结论（详见 schema 文档第七节）**：本数据集**不支持**当初立项时的假设。logKow 与脂相系数相关 r > 0.97，系统性偏差仅 0.19 个对数单位；且与现有 22 个化合物只重叠 1 个（propranolol），MW 中位数 128 对 415，适用域不匹配，无任何类黄酮。

该文的实测值汇集自更早的原始文献，局限写在 schema 文档第五节。
