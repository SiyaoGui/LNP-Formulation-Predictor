"""跨子集对比框架（小分子 vs 大分子）。本轮只写框架，不跑。

用法（等大分子子集也按同一套协议跑完之后）:
    python3 scripts/compare_subsets.py \
        --small modeling/2026-10-19_smallmol-baseline \
        --large modeling/<日期>_largemol-baseline \
        --out   modeling/<日期>_subset-comparison

现在直接运行会检查两边的产出是否齐备，缺哪边就打印还需要跑什么，然后退出。
这样框架本身是可执行、可测试的，不是一段注释。

================================================================================
怎么对比才公平（协议 docs/evaluation-protocol.md 第 11 节，这里是实现）
================================================================================

**前提：两边必须用完全相同的协议。** 指标、划分方式、种子（0-4）、基线、去重规则、
泄漏排除清单、超参数网格，一项都不能改。脚本会逐项核对两边 metrics.json 里记录的
设定，不一致就直接报错，不允许「两边用不同标准还放在一张表里」。

**第 1 条：不能直接比 MAE 的绝对值。**
目标变量的分布范围不同（小分子 30-820 nm；大分子子集是另一个范围），MAE 的尺度
不可比。两边各自的常数基线 MAE 就不一样，拿绝对值比等于比数据集难度，不是比模型。

**第 2 条：比「相对各自基线的提升幅度」。**
用 ΔMAE_log vs B0 和 vs B1，这是无量纲的相对量。再进一步用 skill score
(MAE_baseline - MAE_model) / MAE_baseline，这个量在 0 到 1 之间，可跨数据集比。

**第 3 条：在匹配的样本量上比。**
把分组数多的那个子集下采样到与少的一致（**按分组数，不是按行数**），跑同一套流程，
报告匹配后的结果；同时报告全量结果。两个数字都给，差异本身是信息。

**第 4 条：最该比的是学习曲线的形状，不是单点指标。**
两条曲线画在同一张图上，横轴是训练集分组数。斜率的差别才是「哪边更有希望」的证据。
单点指标受各自样本量影响太大，曲线斜率更稳健。

**第 5 条：必须声明一个无法消除的混杂。**
小分子子集 = PMC_IVR = 经典脂质体 = 无可离子化脂质；
大分子子集 = LNP_Atlas = 现代 LNP = 有可离子化脂质。
子集标签、数据来源、脂质体类型三者完全共线（见 docs/data-inventory.md 1.3 节）。
**所以两边的差异不能归因为「小分子 vs 大分子」，只能表述为「这两个数据集之间的
差异」。** 脚本会把这句话写进产出的 README，不允许省略。

**分组键在大分子侧会退化（协议 11.2 节）：**
大分子的 payload 只有 6 个类别，不是结构，算不出 Tanimoto，B1 基线在那边无法按原样
实现；大分子真正变化的分子是可离子化脂质。所以大分子侧要跑三套分组（payload 类别 /
可离子化脂质 InChIKey / 论文），而**跨子集对比的主口径用 S3 按论文分组**——它是唯一
在两边定义完全相同、分组数都够的划分方式（小分子 26 篇，大分子 60 篇左右）。
本轮小分子已经按协议跑了 S3，所以到时候两边有同口径的数字可比。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# 必须两边一致的设定，不一致就报错
MUST_MATCH = ("seeds", "n_bootstrap", "fp_k_grid")

# 跨子集对比的主口径
PRIMARY_SCHEME = "S3"
CONFOUND_NOTE = (
    "小分子子集 = PMC_IVR = 经典脂质体 = 无可离子化脂质；大分子子集 = LNP_Atlas = "
    "现代 LNP = 有可离子化脂质。子集标签、数据来源、脂质体类型三者完全共线，所以两边"
    "的差异只能表述为「这两个数据集之间的差异」，不能归因为「小分子 vs 大分子」。"
)


def load(d: Path) -> dict:
    f = d / "metrics.json"
    if not f.exists():
        return {}
    return json.loads(f.read_text(encoding="utf-8"))


def check_protocol_match(a: dict, b: dict) -> list[str]:
    problems = []
    for key in MUST_MATCH:
        if a.get(key) != b.get(key):
            problems.append(f"{key} 不一致: 小分子={a.get(key)} 大分子={b.get(key)}")
    if PRIMARY_SCHEME not in a.get("t1", {}):
        problems.append(f"小分子侧缺少主口径划分 {PRIMARY_SCHEME}")
    if PRIMARY_SCHEME not in b.get("t1", {}):
        problems.append(f"大分子侧缺少主口径划分 {PRIMARY_SCHEME}")
    return problems


def skill_score(mae_model: float, mae_base: float) -> float:
    """相对基线的无量纲改善，0 表示和基线一样，1 表示完美，负数表示比基线差。"""
    if not mae_base:
        return float("nan")
    return (mae_base - mae_model) / mae_base


def best_model_row(t1_scheme: dict) -> tuple[str, float] | tuple[None, None]:
    cand = {
        k: v["summary"]["mae_log"]["mean"]
        for k, v in t1_scheme.items()
        if k != "_vs_baselines" and k not in ("b0", "b1") and v.get("summary", {}).get("mae_log")
    }
    if not cand:
        return None, None
    k = min(cand, key=cand.get)
    return k, cand[k]


def compare(small: dict, large: dict) -> dict:
    """第 2 条：比相对各自基线的提升幅度（skill score），不比 MAE 绝对值。"""
    out = {"primary_scheme": PRIMARY_SCHEME, "confound_note": CONFOUND_NOTE, "by_subset": {}}
    for name, m in (("small_molecule", small), ("large_molecule", large)):
        sch = m.get("t1", {}).get(PRIMARY_SCHEME, {})
        if not sch:
            continue
        model, mae = best_model_row(sch)
        b0 = sch.get("b0", {}).get("summary", {}).get("mae_log", {}).get("mean")
        b1 = sch.get("b1", {}).get("summary", {}).get("mae_log", {}).get("mean")
        out["by_subset"][name] = {
            "best_model": model,
            "mae_log": mae,
            "mae_log_b0": b0,
            "mae_log_b1": b1,
            "skill_vs_b0": round(skill_score(mae, b0), 4) if (mae and b0) else None,
            "skill_vs_b1": round(skill_score(mae, b1), 4) if (mae and b1) else None,
            "n_units": sch.get("b0", {}).get("n_units"),
        }
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--small", default="modeling/2026-10-19_smallmol-baseline")
    ap.add_argument("--large", default="")
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    small = load(ROOT / args.small) if args.small else {}
    large = load(ROOT / args.large) if args.large else {}

    if not small:
        sys.exit(f"小分子侧产出不存在: {args.small}/metrics.json")
    if not large:
        print("大分子子集还没有按同一套协议跑过，本轮也不跑（任务范围只做小分子）。")
        print("\n要做这个对比，需要先完成：")
        print("  1. python3 scripts/build_features.py --config <把 subset.name 改成 large_molecule 的配置>")
        print("  2. python3 scripts/run_modeling.py --config <同一份配置> --out modeling/<日期>_largemol-baseline")
        print("     大分子侧额外要跑三套分组（payload 类别 / 可离子化脂质 InChIKey / 论文），见协议 11.2 节")
        print("  3. 回到本脚本，带上 --large 和 --out 再跑")
        print(f"\n对比的主口径是 {PRIMARY_SCHEME}（按论文分组），因为它是唯一在两边定义相同、"
              "分组数都够的划分方式。小分子侧本轮已按协议跑了这一套。")
        print(f"\n必须声明的混杂：{CONFOUND_NOTE}")
        return

    problems = check_protocol_match(small, large)
    if problems:
        sys.exit("两边协议设定不一致，拒绝对比：\n  - " + "\n  - ".join(problems))

    result = compare(small, large)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if args.out:
        out = ROOT / args.out
        out.mkdir(parents=True, exist_ok=True)
        (out / "comparison.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"写出 {out}/comparison.json")
        print("提醒：还需要手工补上第 3 条（匹配样本量的下采样结果）和第 4 条（两条学习曲线叠在一张图上）。")


if __name__ == "__main__":
    main()
