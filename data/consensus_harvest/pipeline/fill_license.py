import json,csv,collections
M="/home/user/LNP-Formulation-Predictor/docs/master-candidates.csv"
cr=json.load(open("crossref.json"))
rows=list(csv.DictReader(open(M,encoding="utf-8")))
F=list(rows[0].keys())
def classify(urls):
    u=" ".join(urls).lower()
    if "creativecommons.org/licenses/by/" in u: return "CC BY（Crossref）"
    if "creativecommons.org/licenses/by-nc-sa" in u: return "CC BY-NC-SA（Crossref）"
    if "creativecommons.org/licenses/by-nc-nd" in u: return "CC BY-NC-ND（Crossref）"
    if "creativecommons.org/licenses/by-nc" in u: return "CC BY-NC（Crossref）"
    if "creativecommons" in u: return "其他 CC（Crossref）"
    if urls: return "仅出版商或 TDM 条款，需订阅"
    return "Crossref 未列许可"
stat=collections.Counter()
for r in rows:
    k=r["doi"].strip().lower()
    if k in cr:
        r["license_status"]=classify(cr[k]["licenses"])
    else:
        r["license_status"]="DOI 未在 Crossref 解析到，需人工核实"
    stat[r["license_status"]]+=1
with open(M,"w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=F); w.writeheader(); w.writerows(rows)
for k,v in stat.most_common(): print(v,"|",k)
# 开放获取的需全文篇数
oa=sum(1 for r in rows if r["needs_fulltext"]=="Y" and r["license_status"].startswith(("CC","其他 CC")))
print("\n需全文且为开放许可:",oa,"/",sum(1 for r in rows if r["needs_fulltext"]=="Y"))
