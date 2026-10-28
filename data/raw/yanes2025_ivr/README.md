# Yanes 2025: 把体外释放与配方数据做成 AI-ready

| 项 | 值 |
|---|---|
| DOI | `10.1016/j.ijpx.2025.100393` |
| 作者 | Yanes, Daniel; Mead, Heather; Mann, James; Röding, Magnus; Paraskevopoulou, Vasiliki; Alexander, Cameron; Parhizkar, Maryam; Twycross, Jamie; Zelzer, Mischa |
| 出处 | International Journal of Pharmaceutics: X 10, 100393, 2025 |
| 授权 | **CC BY 4.0** |
| 授权登记 | `docs/data-licensing.md` 第二节 |

## 原始下载链接

> 待填。请写下实际下载页面的完整 URL（不是 doi.org 跳转前的链接），以及补充材料各文件的直接链接。

- 文章页面：
- 补充材料：

## 下载日期

> 待填。

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

CC BY 4.0 要求标明是否对原始材料做了修改。抽取过程中的每一项修改都要记在这里。

> 待填。抽取完成后由抽取脚本的报告填入。预期至少包括：重新组织成仓库 schema、单位换算、SMILES 规范化、InChIKey 计算。

## 备注

抽取目标：按 `docs/literature-protocol.md` 第三节 schema 抽成配方数据。
这个库正好可能补上仓库缺失的 272 条释放曲线（见 `docs/data-inventory.md` 出入三），但释放动力学本轮不作为目标，先只抽配方与表征。
