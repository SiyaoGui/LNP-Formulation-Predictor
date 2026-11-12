import csv,collections
D="/home/user/LNP-Formulation-Predictor/docs/"
rows=list(csv.DictReader(open(D+"master-candidates.csv",encoding="utf-8")))
po={"P0":0,"P1":1,"P2":2}
# 1) 全部 DOI 清单
with open(D+"doi-list-all.txt","w",encoding="utf-8") as f:
    f.write("# 本次清查全部候选论文的 DOI（%d 条，按优先级加工作流排序）\n"%len(rows))
    f.write("# 可直接粘进 Zotero 的 Add Item by Identifier 批量导入框\n")
    for r in sorted(rows,key=lambda r:(po[r["priority"]],r["workflows"],-int(r["year"]))):
        f.write(r["doi"]+"\n")
# 2) 需全文优先清单：脑递送优先
def key(r):
    wf=set(r["workflows"].split(";"))
    brain = 0 if "H" in wf else 1
    return (brain, po[r["priority"]], 0 if r["license_status"].startswith(("CC","其他")) else 1, -int(r["year"]))
need=[r for r in rows if r["needs_fulltext"]=="Y"]
need.sort(key=key)
with open(D+"doi-list-fulltext-priority.txt","w",encoding="utf-8") as f:
    f.write("# 需全文获取的论文 DOI（%d 条）\n"%len(need))
    f.write("# 排序：脑递送专项(H) 优先 -> 优先级 P0/P1/P2 -> 开放许可优先 -> 年份新优先\n")
    f.write("# 可直接粘进 Zotero 的 Add Item by Identifier 批量导入框\n")
    for r in need: f.write(r["doi"]+"\n")
# 3) 获取清单 markdown
def licshort(s):
    for t in ("CC BY-NC-ND","CC BY-NC-SA","CC BY-NC","CC BY","其他 CC"):
        if s.startswith(t): return t
    if s.startswith("仅出版商"): return "需订阅"
    if s.startswith("Crossref 未列"): return "许可未列"
    return "需核实"
with open(D+"fulltext-acquisition-list.md","w",encoding="utf-8") as f:
    f.write("""# 全文获取清单

本清单列出主表里标为「需全文」的 %d 篇论文，按**脑递送专项优先**排序，
并用 Crossref 返回的许可字段标出哪些可以立刻合法下载。

## 怎么用

1. **先批量导入**：`docs/doi-list-fulltext-priority.txt` 里的 DOI 可直接粘进 Zotero 的
   Add Item by Identifier 批量导入框，顺序已按本清单排好。
2. **先拿开放许可的那 %d 篇**，它们不需要订阅，Zotero 多半能直接抓到 PDF。
3. 需订阅的那部分，先按下面的「为什么需要全文」判断值不值得单独买或走馆际互借。

## 汇总

| 类别 | 篇数 |
|---|---|
| 需全文合计 | %d |
| 其中开放许可（CC 系列，可立刻下载） | %d |
| 其中仅出版商或 TDM 条款（需订阅） | %d |
| 其中 Crossref 未列许可（需人工核实） | %d |
| 其中脑递送专项（工作流 H） | %d |
| 其中 P0 级 | %d |

许可字段全部取自 Crossref API，不是我的判断。Crossref 未列许可不等于不开放，
只说明出版商没在元数据里声明，需要到页面上看。

---

""" % (len(need),
       sum(1 for r in need if licshort(r["license_status"]).startswith(("CC","其他"))),
       len(need),
       sum(1 for r in need if licshort(r["license_status"]).startswith(("CC","其他"))),
       sum(1 for r in need if licshort(r["license_status"])=="需订阅"),
       sum(1 for r in need if licshort(r["license_status"])=="许可未列"),
       sum(1 for r in need if "H" in r["workflows"].split(";")),
       sum(1 for r in need if r["priority"]=="P0")))
    cur=None
    for r in need:
        wf=set(r["workflows"].split(";"))
        grp=("一、脑递送专项（工作流 H）" if "H" in wf else "二、其余工作流")+" / "+r["priority"]
        if grp!=cur:
            cur=grp; f.write("\n## "+grp+"\n\n| DOI | 年 | 期刊 | 工作流 | 许可 | 为什么需要全文 |\n|---|---|---|---|---|---|\n")
        why=r["why_matters"].replace("|","／")
        why=why[:150]+("…" if len(why)>150 else "")
        f.write("| %s | %s | %s | %s | %s | %s |\n"%(r["doi"],r["year"],r["journal"][:28],r["workflows"],licshort(r["license_status"]),why))
print("wrote 3 files; need_fulltext:",len(need))
