import urllib.request,urllib.parse,json,csv,time,sys
M="/home/user/LNP-Formulation-Predictor/docs/master-candidates.csv"
rows=list(csv.DictReader(open(M,encoding="utf-8")))
dois=[r["doi"].strip() for r in rows if r["doi"].strip()]
print("dois:",len(dois)); sys.stdout.flush()
out={}
B="https://api.crossref.org/works"
for i in range(0,len(dois),25):
    chunk=dois[i:i+25]
    q={"filter":",".join("doi:"+d for d in chunk),"rows":100,
       "select":"DOI,license,publisher,container-title,title,type,issued",
       "mailto":"YOUR_EMAIL@example.com"}
    url=B+"?"+urllib.parse.urlencode(q)
    for a in range(4):
        try:
            with urllib.request.urlopen(url,timeout=60) as r: d=json.loads(r.read()); break
        except Exception as e:
            if a==3: print("FAIL chunk",i,e); d=None
            else: time.sleep(2*(a+1))
    if not d: continue
    for it in d["message"]["items"]:
        lic=it.get("license") or []
        urls=sorted({l.get("URL","") for l in lic})
        out[it["DOI"].lower()]={"licenses":urls,"publisher":it.get("publisher",""),
                                "journal":(it.get("container-title") or [""])[0]}
    time.sleep(0.3)
    if i%100==0: print("...",i); sys.stdout.flush()
json.dump(out,open("crossref.json","w"),ensure_ascii=False)
print("resolved:",len(out),"of",len(dois))
