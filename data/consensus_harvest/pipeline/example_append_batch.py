import json,re,csv,collections
P="/root/.claude/projects/-home-user-LNP-Formulation-Predictor/48546386-be48-52b0-9e68-6e9fe37c2f9b.jsonl"
M="/home/user/LNP-Formulation-Predictor/docs/master-candidates.csv"
rec=re.compile(r'\[(\d+)\] \[([^\]]+)\]\(https://consensus\.app[^)]*\) \((.*?)\)\n')
blocks=[]
for line in open(P,encoding='utf-8'):
    try: d=json.loads(line)
    except: continue
    m=d.get("message") or {}
    c=m.get("content")
    if not isinstance(c,list): continue
    for it in c:
        if not isinstance(it,dict) or it.get("type")!="tool_result": continue
        cc=it.get("content"); txt=""
        if isinstance(cc,str): txt=cc
        elif isinstance(cc,list):
            for x in cc:
                if isinstance(x,dict) and x.get("type")=="text": txt+=x.get("text","")
        if "consensus.app/papers" not in txt: continue
        if rec.search(txt): blocks.append(txt)

CFG={
 719:("C;D","P0","DNA 条码高通量体内筛选与定量生物分布"),
 720:("C;B","P0","机器学习预测脂质纳米粒配方性能与可电离脂质筛选"),
}
NUM=[r'\d+(?:\.\d+)?\s*±\s*\d+(?:\.\d+)?\s*nm', r'\d+(?:\.\d+)?\s*nm',
     r'(?:EE|entrapment efficiency|encapsulation efficiency)[^.;]{0,30}?\d+(?:\.\d+)?\s*%',
     r'-?\d+(?:\.\d+)?\s*mV', r'DTE[^.;,]{0,25}\d+(?:\.\d+)?', r'DTP[^.;,]{0,25}\d+(?:\.\d+)?',
     r'R[²2]\s*[=of]{1,3}\s*0?\.\d+', r'RMSE[^.;,]{0,25}\d+(?:\.\d+)?',
     r'MAE[^.;,]{0,20}\d+(?:\.\d+)?', r'\d+(?:\.\d+)?\s*(?:ng|µg|ug)/(?:g|mL|ml)',
     r'PDI[^.;,]{0,20}0?\.\d+', r'\d+(?:\.\d+)?\s*%']
def snips(ab):
    out=[]
    for pat in NUM:
        for m in re.finditer(pat,ab):
            s=re.sub(r'\s+',' ',m.group(0)).strip()
            if s not in out: out.append(s)
            if len(out)>=3: return out
    return out
PRE=re.compile(r'(?:bioRxiv|medRxiv|chemRxiv|Research Square|SSRN|Preprints|arXiv)',re.I)
rows=list(csv.DictReader(open(M,encoding="utf-8")))
F=list(rows[0].keys())
have={r["doi"].strip().lower() for r in rows}
new=[]; seen=set(); nf=0
for bi,(wf,pri,theme) in CFG.items():
    txt=blocks[bi]
    hits=list(rec.finditer(txt))
    for i,h in enumerate(hits):
        title,meta=h.group(2),h.group(3)
        end=hits[i+1].start() if i+1<len(hits) else len(txt)
        ab=txt[h.end():end]
        dm=re.search(r'DOI:\s*(\S+)',meta)
        if not dm: continue
        doi=dm.group(1).rstrip('.').strip()
        k=doi.lower()
        if k in have or k in seen: continue
        seen.add(k)
        ym=re.search(r'(\b(?:19|20)\d{2}\b)',meta)
        jm=re.search(r'citations,\s*(.*?)(?:,\s*DOI:|$)',meta)
        journal=(jm.group(1) if jm else "").strip()
        sn=snips(ab)
        if sn:
            why=theme+"；摘要数据："+"，".join(sn)
            need="N"
        else:
            why=theme+"；摘要无定量结果，需全文"
            need="Y"; nf+=1
        st="preprint" if PRE.search(journal) else ("unknown" if journal.lower().startswith("unknown") else "peer_reviewed")
        new.append({"doi":doi,"title":title.replace('"',"'"),"year":(ym.group(1) if ym else "0"),
            "journal":journal,"workflows":wf,"source_type":st,"license_status":"",
            "in_zotero":"N","priority":pri,"needs_fulltext":need,"why_matters":why})
with open(M,"a",newline="",encoding="utf-8") as f:
    csv.DictWriter(f,fieldnames=F).writerow  # noop
    w=csv.DictWriter(f,fieldnames=F); w.writerows(new)
tot=sum(len(rec.findall(blocks[b])) for b in CFG)
print("hits_total",tot,"new",len(new),"dup_or_existing",tot-len(new),"needs_fulltext",nf)
print("new_rate %.1f%%"%(100.0*len(new)/tot))
