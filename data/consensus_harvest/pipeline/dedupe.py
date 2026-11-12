import csv
P="/home/user/LNP-Formulation-Predictor/docs/master-candidates.csv"
rows=list(csv.DictReader(open(P,encoding="utf-8")))
FIELDS=["doi","title","year","journal","workflows","source_type","license_status","in_zotero","priority","needs_fulltext","why_matters"]
order={"P0":0,"P1":1,"P2":2}
WF="ABCDEFGHIJK"
merged={}; seq=[]; dups=0
def norm(d): return d.strip().lower().rstrip('.')
for r in rows:
    d=norm(r["doi"])
    if d in merged:
        dups+=1
        m=merged[d]
        wf=sorted(set(m["workflows"].split(";"))|set(r["workflows"].split(";")),
                  key=lambda x: WF.index(x) if x in WF else 99)
        m["workflows"]=";".join(w for w in wf if w)
        if order[r["priority"]]<order[m["priority"]]: m["priority"]=r["priority"]
        if "Y" in (m["needs_fulltext"],r["needs_fulltext"]): m["needs_fulltext"]="Y"
        if len(r["why_matters"])>len(m["why_matters"]): m["why_matters"]=r["why_matters"]
        if len(r["license_status"])>len(m["license_status"]): m["license_status"]=r["license_status"]
        if r["source_type"]=="preprint": m["source_type"]="preprint"
    else:
        merged[d]=dict(r); merged[d]["doi"]=r["doi"].strip().rstrip('.'); seq.append(d)
out=sorted((merged[d] for d in seq), key=lambda r:(order[r["priority"]], r["workflows"], -int(r["year"])))
with open(P,"w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=FIELDS); w.writeheader(); w.writerows(out)
from collections import Counter
wc=Counter(); 
for r in out:
    for x in r["workflows"].split(";"): wc[x]+=1
print("merged duplicates:",dups,"final rows:",len(out))
print("workflows:",dict(sorted(wc.items())))
print("priority:",dict(Counter(r["priority"] for r in out)))
print("needs_fulltext Y:",sum(1 for r in out if r["needs_fulltext"]=="Y"),
      "of which P0:",sum(1 for r in out if r["needs_fulltext"]=="Y" and r["priority"]=="P0"))
print("source_type:",dict(Counter(r["source_type"] for r in out)))
print("H rows:",sum(1 for r in out if "H" in r["workflows"].split(";")))
