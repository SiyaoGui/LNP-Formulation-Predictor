#!/usr/bin/env python3
"""
论文内部诊断，纯标准库，无需 pandas。
输入: modeling/2026-10-20_ee-feasibility/oof_predictions_G1.csv
用法: python3 -I within_paper_check.py <oof_predictions_G1.csv>

回答两个原工作没问的问题:
  A. 同一篇论文内部，模型能不能打败"这篇论文自己的均值"?
     不能 -> G1 的 +4.99 pp 主要来自论文级记忆，不是化学信号。
  B. 论文内部的排序能力 (Spearman)，扣掉 b0 的噪声地板之后还剩多少?
     注意 b0 预测常数，本应为 0，实测约 +0.11，那才是地板。
"""
import csv, collections, statistics as st, sys

path = sys.argv[1] if len(sys.argv) > 1 else "oof_predictions_G1.csv"
rows = list(csv.DictReader(open(path, encoding="utf-8-sig")))
models = sorted({r["model"] for r in rows})
seeds  = sorted({r["seed"] for r in rows})
one    = [r for r in rows if r["model"] == models[0] and r["seed"] == seeds[0]]
cnt    = collections.Counter(r["paper_doi"] for r in one)

def rank(xs):
    idx = sorted(range(len(xs)), key=lambda i: xs[i]); r = [0.0]*len(xs); i = 0
    while i < len(idx):
        j = i
        while j+1 < len(idx) and xs[idx[j+1]] == xs[idx[i]]: j += 1
        avg = (i+j)/2.0 + 1
        for k in range(i, j+1): r[idx[k]] = avg
        i = j+1
    return r

def spearman(a, b):
    if len(a) < 3: return None
    ra, rb = rank(a), rank(b)
    ma, mb = st.fmean(ra), st.fmean(rb)
    num = sum((x-ma)*(y-mb) for x, y in zip(ra, rb))
    da  = sum((x-ma)**2 for x in ra)**.5
    db  = sum((y-mb)**2 for y in rb)**.5
    return None if da == 0 or db == 0 else num/(da*db)

for MIN in (5, 10):
    big = {d for d, n in cnt.items() if n >= MIN}
    print(f"\n===== 论文内部诊断 (>= {MIN} 个单元的 {len(big)} 篇论文) =====")
    print(f"{'模型':27} {'论文内MAE':>10} {'论文均值MAE':>12} {'Spearman':>9}")
    for m in models:
        mm, bb, sp = [], [], []
        for s in seeds:
            sub = [r for r in rows if r["model"] == m and r["seed"] == s and r["paper_doi"] in big]
            bp = collections.defaultdict(list)
            for r in sub: bp[r["paper_doi"]].append((float(r["y_true"]), float(r["y_pred"])))
            a, b, c = [], [], []
            for d, v in bp.items():
                ys = [x for x, _ in v]; mu = st.fmean(ys)
                a.append(st.fmean(abs(x-y) for x, y in v))
                b.append(st.fmean(abs(x-mu) for x in ys))
                r_ = spearman(ys, [y for _, y in v])
                if r_ is not None: c.append(r_)
            mm.append(st.fmean(a)); bb.append(st.fmean(b))
            if c: sp.append(st.fmean(c))
        print(f"{m:27} {st.fmean(mm):10.3f} {st.fmean(bb):12.3f} {st.fmean(sp):+9.3f}")
    print("  提示: 以 b0 那一行的 Spearman 为噪声地板，真实信号是其它行减去它。")
