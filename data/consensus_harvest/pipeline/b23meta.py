import json,re
P="/root/.claude/projects/-home-user-LNP-Formulation-Predictor/48546386-be48-52b0-9e68-6e9fe37c2f9b.jsonl"
blocks=[]
for line in open(P,encoding='utf-8'):
    try: d=json.loads(line)
    except: continue
    m=d.get("message") or {}
    c=m.get("content")
    if not isinstance(c,list): continue
    for it in c:
        if not isinstance(it,dict): continue
        if it.get("type")!="tool_result": continue
        cc=it.get("content")
        txt=""
        if isinstance(cc,list):
            for x in cc:
                if isinstance(x,dict) and x.get("type")=="text": txt+=x.get("text","")
        elif isinstance(cc,str): txt=cc
        if "consensus.app/papers" in txt and rec.search(txt): blocks.append(txt)
rec=re.compile(r'\[(\d+)\] \[([^\]]+)\]\(https://consensus\.app[^)]*\) \((.*?)\)\n')
out=open('b23_meta.tsv','w',encoding='utf-8')
for bi in range(212,218):
    t=blocks[bi]
    for m in rec.finditer(t):
        out.write("%d\t%s\t%s\n"%(bi,m.group(2)[:110],m.group(3)[:160]))
out.close()
print("blocks",len(blocks))
