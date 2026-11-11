import json,re
P="/root/.claude/projects/-home-user-LNP-Formulation-Predictor/48546386-be48-52b0-9e68-6e9fe37c2f9b.jsonl"
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
import sys
lo,hi,N=int(sys.argv[1]),int(sys.argv[2]),int(sys.argv[3])
for bi in range(lo,hi+1):
    txt=blocks[bi]
    print("\n\n########## BLOCK %d ##########"%bi)
    parts=rec.split(txt)
    # parts: [pre, n, title, meta, body, n, title, meta, body, ...]
    for i in range(1,len(parts),4):
        n=parts[i]; title=parts[i+1]; meta=parts[i+2]; body=parts[i+3] if i+3<len(parts) else ""
        if int(n)>N: break
        body=re.sub(r'\s+',' ',body).strip()
        print("\n[%s] %s | %s"%(n,title,meta))
        print(body[:900])
