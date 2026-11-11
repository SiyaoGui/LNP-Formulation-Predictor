# Consensus 文献抓取：原始数据与流水线

本目录保存了 Consensus 文献检索的**原始抓取**和**流水线脚本**。此前这些只存在于
会话临时目录（scratchpad），会话回收后即丢失；2026-11-11 交接时抢救进仓库。

策展后的成品表是 `docs/master-candidates.csv`（9464 行）。本目录是它的**上游与方法**。

## 文件

| 文件 | 说明 |
|---|---|
| `papers_all.tsv` | **原始抓取**。整个项目 746 个检索块的全部命中，带块级溯源。14124 条带 DOI 记录，9595 个去重 DOI（比成品表多约 130 个，因为含被去重或未采纳的命中）。无表头，列顺序见下。 |
| `pipeline/` | 流水线脚本。见下方「可复用」与「仅存档」两类区分。 |

### `papers_all.tsv` 列（制表符分隔，无表头）

| 列 | 含义 |
|---|---|
| 1 | `block` 检索块序号（0 起）。同一次 `search` 调用的一组结果为一个块。 |
| 2 | `rank` 该块内的排名（Consensus 返回顺序）。 |
| 3 | `doi` |
| 4 | `year` |
| 5 | `journal` |
| 6 | `title` |

`block` 是关键溯源字段：它告诉你每篇论文是从哪个检索主题命中的。成品表
`master-candidates.csv` 丢弃了块号（一篇论文可能被多个块命中，去重后只留一行），
`why_matters` 列的中文主题前缀是块主题的人读版。要还原「某主题检索到哪些论文」，
用本表。

## 流水线脚本

### 可复用（在新窗口里能直接重跑）

这几个只依赖成品 CSV（路径 `/home/user/LNP-Formulation-Predictor/docs/master-candidates.csv`
在各会话间稳定）和网络，新窗口可直接重跑：

| 脚本 | 作用 | 重跑前提 |
|---|---|---|
| `dedupe.py` | 按 DOI 去重合并（合并工作流码、取更高优先级、保留更长 why_matters）。幂等。 | 无 |
| `crossref.py` | 批量查 Crossref，拉 license / publisher / journal，写 `crossref.json`。**脚本里的 `mailto` 已改成占位符 `YOUR_EMAIL@example.com`，重跑前填你自己的邮箱**（Crossref 要求联系邮箱作为 courtesy 参数，这是该邮箱唯一允许的用途，不要写进任何别处）。 | 网络可达 `api.crossref.org` |
| `fill_license.py` | 读 `crossref.json`，把 license 分类（CC BY / CC BY-NC / 仅出版商 / 未列 / 未解析）写回 CSV `license_status` 列。 | 先跑过 `crossref.py` |
| `analyze.py` | 对成品表出统计（分布、计数）。 | 无 |

**license 刷新任务**：成品表当前有 **4173 行 `license_status` 为空**（批 50/55 的
Crossref 跑之后新增的约 4000 行没覆盖到）。刷新办法：填好 `crossref.py` 的邮箱 →
`python3 crossref.py` → `python3 fill_license.py`。两步都不消耗 Consensus 额度。

### 仅存档（新窗口无法重跑，留作方法说明）

这几个读的是**本会话的转录文件** `…/48546386-…jsonl`，该路径是会话专属的，
新会话里不存在，Consensus 额度也已耗尽，因此只能当方法文档看，不能重跑：

| 脚本 | 作用 |
|---|---|
| `dump3_harvest_extractor.py` | 从会话转录里正则提取 Consensus 命中记录，生成 `papers_all.tsv`，并打印每块首篇标题（用于核对块顺序）。 |
| `example_gen_cfg.py` | 每批次「生成器」的模板示例（原名 `gen100.py`）。把一批主题配置 `cfg_items` 写进一个 append 脚本。 |
| `example_append_batch.py` | 每批次「追加」脚本示例（原名 `append_b162.py`）。核心逻辑在这里：按块号取命中 → 正则抽 DOI/年份/期刊 → 从摘要正则抽最多 3 条定量片段（粒径/包封率/电位/DTE/R² 等）→ 有定量则 `needs_fulltext=N` 并把片段写进 `why_matters`，无定量则标 `Y`「需全文」→ 预印本按期刊名判定 → 去重后 append。 |
| `example_count_group.py` | 每组 3 批次的统计脚本示例（原名 `cnt160162.py`）。 |

**每批次的一次性脚本未保留**：整个项目约 500 个 `gen*.py` / `mk*.py` /
`append_b*.py` / `cnt*.py` 和 136 个 `old_master*.csv` 快照是逐批抛弃的中间产物，
方法已被上面四个示例完整表达，不再占仓库空间。要复现某一批，照 `example_*`
改 `cfg_items` / `CFG` 即可。

## 一批是怎么产生的（方法概述）

1. 发 3 次 Consensus `search`（每条消息最多 3 次），每次一个主题，`page_size` 大。
2. **并行结果在转录里的落位顺序与发出顺序不同**，所以先跑 `dump3` 打印每块首篇
   标题，核对块号与主题的对应，再写 append 脚本（这是反复踩过的坑）。
3. append 脚本按上表逻辑抽取并追加到 `master-candidates.csv`。
4. 每 3 批提交一次，附一篇工作记录 `docs/worklog/…` 和一条额度台账
   `docs/quota-ledger.md`。
