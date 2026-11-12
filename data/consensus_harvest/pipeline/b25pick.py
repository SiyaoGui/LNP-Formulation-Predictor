import json,re,sys
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
PICK={246:[2,3,4],247:[1,3],253:[1,2,3,4,6],255:[1,2],256:[2],257:[1,3,5,6],258:[1,3],259:[1]}
for bi in sorted(PICK):
    txt=blocks[bi]; parts=rec.split(txt)
    for i in range(1,len(parts),4):
        n=int(parts[i]); title=parts[i+1]; body=re.sub(r'\s+',' ',parts[i+3] if i+3<len(parts) else "").strip()
        if n in PICK[bi]:
            print("\n### B%d [%d] %s"%(bi,n,title))
            print(body[600:2600])
