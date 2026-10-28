# 外部数据集授权登记

日期：2026-10-27
状态：**生效中**。这份文件是外部数据能否进入管线的唯一依据
授权事实来源：Crossref API（`https://api.crossref.org/works/{DOI}`），字段 `license`，取 `content-version = vor`（版本记录）那一条

---

## 一、这份文件的作用

仓库里任何来自外部文献的数据，进管线之前必须在本表里有一条「可用」记录。**没有记录的，不许进 `data/`、不许进特征矩阵、不许用于任何实验，包括临时测试。**

两条硬规则：

1. **挂起的数据集不做「先抽着以后再删」。** 不抽取、不下载进仓库、不跑测试。挂起期间它在仓库里应当完全不存在
2. **授权状态只能因为拿到新的书面依据而改变**，不能因为「实验需要」而改变。每次变更在本文件末尾的变更记录里写明依据

本项目按 `AGENTS.md` 是商业管线（AI 驱动的皮肤渗透递送平台，首发管线为圣草酚毛囊递送）。因此 **NonCommercial（NC）条款是实际约束，不是形式问题。**

---

## 二、可用：CC BY 4.0（3 个，本轮执行）

CC BY 4.0 允许商业使用与改编，条件是署名、保留授权声明、标明是否做了修改。三个数据集的署名信息如下，抽取时必须逐条写入记录的 `source_attribution` 字段。

### 2.1 Khawar 2022（脂质/水分配系数，优先级最高）

| 项 | 值 |
|---|---|
| DOI | `10.1038/s41598-022-19452-6` |
| 标题 | Exploring the role of octanol-water partition coefficient and Henry's law constant in predicting the lipid-water partition coefficients of organic chemicals |
| 作者 | Khawar, Muhammad Irfan; Mahmood, Azhar; Nabi, Deedar |
| 出处 | Scientific Reports 12(1), article 14936, 2022 |
| 出版方 | Springer Science and Business Media LLC |
| 授权 | **CC BY 4.0**（`https://creativecommons.org/licenses/by/4.0`，vor 与 tdm 两版一致） |
| 商用 | 允许 |
| 改编 | 允许，需标明已修改 |
| 内容 | logKlw n=305，logKpw n=131 |
| 用途 | **分子属性，不是配方记录。** 单独建表，见 `docs/schema-partition-coefficients.md` |
| `data/raw/` 目录 | `data/raw/khawar2022_klipw/` |

### 2.2 Yanes 2025（脂质体体外释放与配方开放库）

| 项 | 值 |
|---|---|
| DOI | `10.1016/j.ijpx.2025.100393` |
| 标题 | Making in vitro release and formulation data AI-ready: A foundation for streamlined nanomedicine development |
| 作者 | Yanes, Daniel; Mead, Heather; Mann, James; Röding, Magnus; Paraskevopoulou, Vasiliki; Alexander, Cameron; Parhizkar, Maryam; Twycross, Jamie; Zelzer, Mischa |
| 出处 | International Journal of Pharmaceutics: X 10, 100393, 2025 |
| 出版方 | Elsevier BV |
| 授权 | **CC BY 4.0**（`http://creativecommons.org/licenses/by/4.0/`，vor） |
| 商用 | 允许 |
| 内容 | 配方参数 + 体外释放（IVR）测试条件 + 数字化释放曲线 |
| 用途 | 按仓库现有 schema 抽成配方数据 |
| `data/raw/` 目录 | `data/raw/yanes2025_ivr/` |

### 2.3 Jaki 2026（DoE 双离心筛选，3 个 PROTAC）

| 项 | 值 |
|---|---|
| DOI | `10.1016/j.ijpx.2026.100627` |
| 标题 | A DoE-Dual centrifugation-driven screening platform for liposomal incorporation of poorly soluble APIs: Application to the PROTAC ACBI2 |
| 作者 | Jaki, Miriam; Köll-Weber, Monika; Lembeck, Jan; Wittmann, Maximilian; Süss, Regine |
| 出处 | International Journal of Pharmaceutics: X 12, 100627, 2026 |
| 出版方 | Elsevier BV |
| 授权 | **CC BY 4.0**（`http://creativecommons.org/licenses/by/4.0/`，vor） |
| 商用 | 允许 |
| 内容 | DoE 配方矩阵，3 个 PROTAC，多种脂质基质，含 D/L 比 |
| 用途 | 按仓库现有 schema 抽成配方数据 |
| **注意** | PROTAC 分子量通常超过 900 Da 上限。按协议 N1，超限记录仍提取但标 `mw_over_default_cap = TRUE`，默认不进主数据集 |
| `data/raw/` 目录 | `data/raw/jaki2026_doe/` |

### 2.4 Xu 2022（外部探针集，不进训练集）

| 项 | 值 |
|---|---|
| DOI | `10.3390/molecules27227967` |
| 标题 | Synthesis of Paclitaxel Derivatives for Remote Loading into Liposomes and Improved Therapeutic Effect |
| 作者 | Xu, Xiangwei; Liu, Yanhua; Shao, Shanshan; Li, Jinbo; Xu, Zhaochu; Yin, Yueling; Zhao, Linxiang; Wang, Yongjun; Liu, Dan |
| 出处 | Molecules 27(22), 7967, 2022 |
| 出版方 | MDPI AG |
| 授权 | **CC BY 4.0**（`https://creativecommons.org/licenses/by/4.0/`，vor） |
| 商用 | 允许 |
| 内容 | 19 个紫杉醇硼酸衍生物，同一脂质体配方下筛选 |
| 用途 | **外部探针集，不进训练集。** 19 个分子共享单一 Murcko 骨架，正是 `docs/data-spec-ee.md` 2.3 节警告的「在一个骨架附近密集采样」。用途是检验「同骨架内的小修饰能否被模型分辨」 |
| `data/raw/` 目录 | `data/raw/xu2022_ptx_probe/` |

---

## 三、挂起：等用户书面授权答复（5 个）

**以下数据集全部不进管线、不进仓库、不做测试。** 挂起期间不抽取任何内容。

| 数据集 | DOI | 授权 | 挂起原因 | 解除挂起需要什么 |
|---|---|---|---|---|
| **Khodadadi 2025**（500 个包封率数据点） | `10.1039/d5nr01741f` | 仅 RSC terms of use（接受稿版本），无开放授权 | 付费墙后，没有任何条款允许再分发其数据集。KU / DTU 权限只解决「能读」，不解决「能用」 | 以下任一：(a) RSC 或通讯作者的书面许可；(b) 法务确认按丹麦 / 欧盟研究用途 TDM 例外可提取事实性数值，且确认商业管线是否在例外范围内；(c) 作者直接提供数据集并附授权 |
| **Lavagna 2026**（304 个微流控配方 + Zenodo） | `10.1016/j.dib.2026.112667` | **CC BY-NC 4.0** | NC 条款禁止商业使用，本项目是商业管线 | 以下任一：(a) 权利人书面同意商业使用；(b) 法务确认本项目当前阶段（研究阶段、未商业化）不构成 NC 所禁止的商业使用，并写明该判断的有效边界；(c) 若将来仅用于非商业的学术发表，可在限定范围内启用，但必须和商业管线的数据物理隔离 |
| Buttitta 2025（300+ 实验条件） | `10.1016/j.ijpharm.2025.126362` | CC BY-NC-ND 4.0 | NC 禁商用，ND 禁改编。抽取成另一种 schema 很可能构成 ND 所禁止的改编 | 同 Lavagna，且需额外处理 ND |
| Han 2023（ML 配方预测） | `10.1016/j.ajps.2023.100811` | CC BY-NC-ND 4.0 | 同上 | 同上 |
| Shahiwala 2023（114 个 niosome 配方） | `10.1208/s12249-023-02547-2` | 仅 Springer TDM 条款，无开放授权 | 付费墙后，无开放授权 | 同 Khodadadi |

### 2026-10-28 数据可获取性核查结果（用户执行）

用户去查了这 5 篇的 Data Availability。结果和预期相反：

| 数据集 | 核查结果 | 对解除挂起的影响 |
|---|---|---|
| Khodadadi 2025 | **未找到可获取的数据集** | 原本这是最值得查的一篇（500 个包封率数据点，与本项目目标最接近）。数据拿不到，授权问题就是次要的了。**实际状态从「等授权」变成「数据本身不可得」** |
| Shahiwala 2023 | **未找到可获取的数据集** | 同上。114 个 niosome 配方的表没有公开出来 |
| Lavagna 2026 | 数据可获取 | 但卡在 CC BY-NC，仍挂起 |
| Buttitta 2025 | 数据可获取 | 但卡在 CC BY-NC-ND，仍挂起 |
| Han 2023 | 数据可获取 | 但卡在 CC BY-NC-ND，仍挂起 |

**这意味着挂起名单实际上分成了两类，解除条件不同：**

- **Khodadadi、Shahiwala：数据不可得。** 授权许可解决不了这个问题。唯一的路是直接联系通讯作者索要数据集（Khodadadi 的通讯作者是 Haeri, Azadeh；Shahiwala 的是 Shahiwala, Aliasgar F.）。在拿到数据之前，授权谈判没有意义
- **Lavagna、Buttitta、Han：数据可得，卡授权。** 这三篇才是「一封邮件可能解决」的。其中 Lavagna 与 Buttitta 是同一个十人团队（只是第一作者互换），一次申请可以覆盖两篇

待补充的细节（用户若方便可回填）：Khodadadi 与 Shahiwala 是完全没有 Data Availability 声明，还是声明写了「data available on request」。后者意味着写信索要是作者预期内的流程，成功率高得多。

### 挂起不影响的事

挂起只约束**数据的使用**，不约束**引用与讨论**。这些论文：

- 仍然保留在 `docs/feasibility-probe.csv` 的候选表里（标记了授权状态）
- 仍然可以在报告与工作日志里引用其结论和数字（引用是合理使用）
- 仍然在 `docs/feasibility-probe-dois-all.txt` 里，可以导入 Zotero 作为文献管理

本文件约束的是：不把它们的数据提取成仓库里的数据表。

---

## 四、每条记录必须带的授权字段

抽取时在数据表里新增以下三列（在 `docs/literature-protocol.md` 第三节的 schema 之外）：

| 字段 | 说明 |
|---|---|
| `source_doi` | 来源 DOI。与协议的 `paper_doi` 相同语义，为显式起见单列 |
| `source_license` | 授权标识符，取值 `CC-BY-4.0`。本轮只允许这一个取值 |
| `source_attribution` | 完整署名串，格式：`作者列表. 标题. 期刊 卷(期), 文章号, 年. DOI: xxx. Licensed under CC BY 4.0.` |

CC BY 4.0 还要求「标明是否做了修改」。因为抽取本身就是改编（重新组织成另一种 schema、做单位换算、做归一化），所以：

- 每个数据集在 `data/raw/<源>/README.md` 里写明做了哪些修改
- 若将来对外发布合并数据集，必须在发布物里保留全部署名串，并声明「数据经重新组织与单位换算，非原始形式」

---

## 五、原始文件的处理约定

**容器的网络策略拦掉了 zenodo.org 与各出版商域名，只放通 `api.crossref.org`。本轮不再尝试绕过。** 原始文件由用户用浏览器下载并提交到仓库。

目录约定（每个源一个文件夹）：

```
data/raw/
  khawar2022_klipw/     README.md  LICENSE.txt  <原始文件>
  yanes2025_ivr/        README.md  LICENSE.txt  <原始文件>
  jaki2026_doe/         README.md  LICENSE.txt  <原始文件>
  xu2022_ptx_probe/     README.md  LICENSE.txt  <原始文件>
```

每个文件夹的 `README.md` 必须记录：原始下载链接、下载日期、授权、文件清单与校验值、做过哪些修改。校验值用 `python3 scripts/record_raw_checksums.py` 生成，不手填。

原始文件一律**只读**。抽取脚本不许改写 `data/raw/` 下的任何文件。

---

## 六、变更记录

| 日期 | 变更 | 依据 |
|---|---|---|
| 2026-10-27 | 建立本文件。4 个 CC BY 4.0 数据集标为可用（其中 Xu 2022 限定为外部探针集），5 个标为挂起 | Crossref `license` 字段（见第一节）；用户 2026-10-27 的授权口径决定 |
