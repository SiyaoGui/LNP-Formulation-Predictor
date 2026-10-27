# Xu 2022: 用于脂质体远程载药的紫杉醇衍生物合成

| 项 | 值 |
|---|---|
| DOI | `10.3390/molecules27227967` |
| 作者 | Xu, Xiangwei; Liu, Yanhua; Shao, Shanshan; Li, Jinbo; Xu, Zhaochu; Yin, Yueling; Zhao, Linxiang; Wang, Yongjun; Liu, Dan |
| 出处 | Molecules 27(22), 7967, 2022 |
| 授权 | **CC BY 4.0** |
| 授权登记 | `docs/data-licensing.md` 第二节 |

## 原始下载链接

> 待填。请写下实际下载页面的完整 URL（不是 doi.org 跳转前的链接），以及补充材料各文件的直接链接。

- 文章页面：
- 补充材料：

## 下载日期

> 待填。

## 需要的文件

- 19 个紫杉醇硼酸衍生物的结构与包封率/载药量数据
- 脂质体配方（原文说对活性化合物做了配方筛选）

## 文件清单与校验值

> 由 `python3 scripts/record_raw_checksums.py` 自动生成并写入本节，不要手填。

<!-- CHECKSUMS:BEGIN -->
（尚无文件）
<!-- CHECKSUMS:END -->

## 做过哪些修改

CC BY 4.0 要求标明是否对原始材料做了修改。抽取过程中的每一项修改都要记在这里。

> 待填。抽取完成后由抽取脚本的报告填入。预期至少包括：重新组织成仓库 schema、单位换算、SMILES 规范化、InChIKey 计算。

## 备注

**外部探针集，不进训练集。** 19 个分子共享单一 Murcko 骨架，正是 `docs/data-spec-ee.md` 2.3 节警告的「在一个骨架附近密集采样」。
用途：检验同骨架内的小修饰能否被模型分辨。抽取产物写到 `data/processed/probe_xu2022.csv`，与主数据表分开。
