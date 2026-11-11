exec(open("pm.py").read().split("NORDIC=")[0])
import collections,re,json
NORDIC="(Denmark[ad] OR Sweden[ad] OR Norway[ad] OR Finland[ad])"
Q={
"E_metrology": f'(("certified reference material*"[tiab] OR "reference material*"[tiab] OR traceab*[tiab] OR interlaborator*[tiab] OR "round robin"[tiab] OR "method validation"[tiab]) AND (nanoparticle*[tiab] OR liposom*[tiab] OR "lipid nanoparticle*"[tiab] OR "particle size"[tiab] OR "zeta potential"[tiab])) AND {NORDIC} AND 2016:2026[dp]',
"F_kpuu": f'("unbound brain"[tiab] OR "Kp,uu"[tiab] OR Kpuu[tiab] OR microdialysis[tiab] OR "brain slice"[tiab] OR "brain penetration"[tiab]) AND (brain[tiab] OR CNS[tiab]) AND {NORDIC} AND 2018:2026[dp]',
}
res={}
for k,q in Q.items():
    ids,cnt=esearch(q,retmax=300); print(k,"count",cnt,"fetched",len(ids))
    res[k]=efetch(ids)
json.dump(res,open("pubmed_nordic2.json","w"),ensure_ascii=False)
NORD=re.compile(r'\b(Denmark|Sweden|Norway|Finland)\b',re.I)
EMAIL=re.compile(r'[\w.+-]+@[\w-]+\.[\w.-]+')
for k,recs in res.items():
    print("\n==== "+k+" ====")
    c=collections.Counter(); who=collections.defaultdict(lambda:{"n":0,"em":set(),"p":[]})
    for r in recs:
        n=len(r["authors"])
        for i,a in enumerate(r["authors"]):
            for aff in a["affs"]:
                if not NORD.search(aff): continue
                m=re.search(r'(Universit[^,;]*|[^,;]*Institut[^,;]*|SINTEF[^,;]*|VTT[^,;]*|Karolinska[^,;]*|Chalmers[^,;]*|RISE[^,;]*|DTU[^,;]*|NTNU)',aff,re.I)
                if m: c[m.group(1).strip()[:48]]+=1
                if i in (0,n-1):
                    w=who[a["name"]]; w["n"]+=1
                    for e in EMAIL.findall(aff): w["em"].add(e.rstrip('.'))
                    if len(w["p"])<2 and m: w["p"].append((r["year"],r["doi"],r["title"][:95],m.group(1).strip()[:40]))
    for inst,cnt in c.most_common(12): print(f"  {inst[:48]:48s} {cnt}")
    print("  -- 一作或末位作者最多的人 --")
    for name,w in sorted(who.items(),key=lambda x:-x[1]["n"])[:10]:
        print(f"  * {name} ({w['n']} 篇) {', '.join(sorted(w['em'])[:1])}")
        for y,doi,t,inst in w["p"][:1]: print(f"      {y} {doi} | {inst} | {t}")
