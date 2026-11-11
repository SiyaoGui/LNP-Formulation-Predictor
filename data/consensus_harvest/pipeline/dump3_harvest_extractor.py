import json,re,csv
p="/root/.claude/projects/-home-user-LNP-Formulation-Predictor/48546386-be48-52b0-9e68-6e9fe37c2f9b.jsonl"
rec=re.compile(r'\[(\d+)\] \[([^\]]+)\]\(https://consensus\.app[^)]*\) \((.*?)\)\n')
blocks=[]
for line in open(p,encoding='utf-8'):
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
        h=rec.findall(txt)
        if h: blocks.append(h)
print("total blocks:",len(blocks))
out=[]
for bi in range(0,len(blocks)):
    for n,title,meta in blocks[bi]:
        ym=re.search(r'(\b(?:19|20)\d{2}\b)',meta)
        dm=re.search(r'DOI:\s*(\S+)',meta)
        jm=re.search(r'citations,\s*(.*?)(?:,\s*DOI:|$)',meta)
        out.append([bi,n,dm.group(1).rstrip('.') if dm else "",ym.group(1) if ym else "",(jm.group(1) if jm else "").strip(),title.replace("\t"," ")])
with open("papers_all.tsv","w",newline="",encoding="utf-8") as f:
    csv.writer(f,delimiter="\t").writerows(out)
print("rows",len(out),"nodoi",sum(1 for r in out if not r[2]))
for bi in range(0,len(blocks)):
    print("=== block",bi,"first title:",blocks[bi][0][1][:70])
