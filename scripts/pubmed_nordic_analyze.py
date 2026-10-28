"""解析 pubmed_nordic.json，把作者单位规范化到机构，统计每个机构在四类检索中的
论文数，并列出同时具备配方能力与血脑屏障或脑递送能力的机构。

用法：先跑 pubmed_nordic_scan.py，再 python3 -I scripts/pubmed_nordic_analyze.py
输出：nordic_analysis.json（机构到 PMID、人到邮箱与代表论文）
"""
import json,re,collections
res=json.load(open("pubmed_nordic.json"))
NORD=re.compile(r'\b(Denmark|Sweden|Norway|Finland|Danmark|Sverige|Norge|Suomi)\b',re.I)
KEY=re.compile(r'(Universit[^,;]*|[^,;]*Institut[^,;]*|[^,;]*Hospital[^,;]*|[^,;]*Högskola[^,;]*|SINTEF[^,;]*|VTT[^,;]*|Karolinska[^,;]*|Chalmers[^,;]*|Åbo[^,;]*|Aalto[^,;]*|NTNU|DTU|Novo Nordisk[^,;]*|AstraZeneca[^,;]*|Lundbeck[^,;]*|Orion[^,;]*|Ferring[^,;]*|Nanovi[^,;]*|RISE[^,;]*)',re.I)
CANON=[
 (r'Technical University of Denmark|DTU','Technical University of Denmark (DTU), DK'),
 (r'University of Copenhagen|Københavns Universitet','University of Copenhagen, DK'),
 (r'Aarhus Universit','Aarhus University, DK'),
 (r'University of Southern Denmark|Syddansk','University of Southern Denmark, DK'),
 (r'Aalborg Universit','Aalborg University, DK'),
 (r'Karolinska','Karolinska Institutet, SE'),
 (r'Uppsala Universit','Uppsala University, SE'),
 (r'Lund Universit','Lund University, SE'),
 (r'Chalmers','Chalmers University of Technology, SE'),
 (r'(University of )?Gothenburg|Göteborg','University of Gothenburg, SE'),
 (r'Stockholm Universit','Stockholm University, SE'),
 (r'KTH|Royal Institute of Technology','KTH Royal Institute of Technology, SE'),
 (r'Linköping','Linköping University, SE'),
 (r'Umeå','Umeå University, SE'),
 (r'Malmö Universit','Malmö University, SE'),
 (r'RISE Research Institutes','RISE Research Institutes of Sweden, SE'),
 (r'University of Oslo|Universitetet i Oslo','University of Oslo, NO'),
 (r'Norwegian University of Science|NTNU','NTNU, NO'),
 (r'(UiT|Arctic University|Tromsø)','UiT The Arctic University of Norway, NO'),
 (r'University of Bergen|Universitetet i Bergen','University of Bergen, NO'),
 (r'SINTEF','SINTEF, NO'),
 (r'Oslo University Hospital','Oslo University Hospital, NO'),
 (r'University of Helsinki|Helsingin yliopisto','University of Helsinki, FI'),
 (r'University of Eastern Finland|Itä-Suomen','University of Eastern Finland, FI'),
 (r'Åbo Akademi','Åbo Akademi University, FI'),
 (r'Aalto','Aalto University, FI'),
 (r'University of Oulu','University of Oulu, FI'),
 (r'Tampere Universit','Tampere University, FI'),
 (r'University of Turku|Turun yliopisto','University of Turku, FI'),
 (r'VTT','VTT Technical Research Centre of Finland, FI'),
 (r'University of Jyväskylä','University of Jyväskylä, FI'),
 (r'AstraZeneca','AstraZeneca (industry), SE'),
 (r'Novo Nordisk','Novo Nordisk (industry), DK'),
 (r'Lundbeck','H. Lundbeck (industry), DK'),
 (r'Orion ','Orion Pharma (industry), FI'),
]
def canon(aff):
    for pat,name in CANON:
        if re.search(pat,aff,re.I): return name
    m=KEY.search(aff)
    if m: return m.group(1).strip()[:60]
    return None
EMAIL=re.compile(r'[\w.+-]+@[\w-]+\.[\w.-]+')
inst=collections.defaultdict(lambda: collections.defaultdict(set))   # inst -> query -> pmids
people=collections.defaultdict(lambda: {"insts":set(),"emails":set(),"queries":set(),"papers":[],"last":0})
for q,recs in res.items():
    for r in recs:
        n=len(r["authors"])
        for i,a in enumerate(r["authors"]):
            for aff in a["affs"]:
                if not NORD.search(aff): continue
                c=canon(aff)
                if not c: continue
                inst[c][q].add(r["pmid"])
                islast = (i==n-1) or (i==0)
                key=(a["name"],c)
                p=people[key]
                p["insts"].add(c); p["queries"].add(q)
                for e in EMAIL.findall(aff): p["emails"].add(e.rstrip('.'))
                if islast:
                    p["last"]+=1
                    if len(p["papers"])<4: p["papers"].append((r["year"],r["doi"],r["title"][:110],q))
rows=[]
for c,d in inst.items():
    rows.append((c,{q:len(v) for q,v in d.items()}))
def tot(x): return sum(x[1].values())
rows.sort(key=lambda x:-tot(x))
print("=== INSTITUTIONS (paper counts per query set) ===")
print(f"{'institution':52s} {'A_lnp':>6s} {'B_bbb':>6s} {'C_char':>7s} {'D_brain':>8s}")
both=[]
for c,d in rows[:45]:
    a=d.get("A_lnp_formulation",0); b=d.get("B_bbb_model",0); ch=d.get("C_characterisation",0); dd=d.get("D_brain_delivery",0)
    print(f"{c[:52]:52s} {a:6d} {b:6d} {ch:7d} {dd:8d}")
    if a>=2 and (b>=2 or dd>=2): both.append((c,a,b,ch,dd))
print()
print("=== BOTH LNP FORMULATION AND BBB/BRAIN CAPABILITY (A>=2 and (B>=2 or D>=2)) ===")
for c,a,b,ch,dd in sorted(both,key=lambda x:-(x[1]+x[2]+x[4])):
    print(f"{c[:52]:52s} A={a} B={b} C={ch} D={dd}")
json.dump({"inst":{c:{q:sorted(v) for q,v in d.items()} for c,d in inst.items()},
           "people":{f"{k[0]}||{k[1]}":{"emails":sorted(v["emails"]),"queries":sorted(v["queries"]),
                      "papers":v["papers"],"last":v["last"]} for k,v in people.items()}},
          open("nordic_analysis.json","w"),ensure_ascii=False)
print("\nsaved nordic_analysis.json; people:",len(people))
