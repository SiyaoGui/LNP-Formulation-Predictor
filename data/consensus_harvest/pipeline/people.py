import json
d=json.load(open("nordic_analysis.json"))
P=d["people"]
def show(title,pred,minlast=1,limit=28):
    rows=[]
    for k,v in P.items():
        name,inst=k.split("||")
        if not pred(set(v["queries"])): continue
        if v["last"]<minlast: continue
        rows.append((v["last"],name,inst,v["emails"],v["papers"],sorted(v["queries"])))
    rows.sort(key=lambda x:-x[0])
    print("\n==== "+title+f"  (n={len(rows)}) ====")
    for last,name,inst,em,papers,qs in rows[:limit]:
        print(f"- {name} | {inst} | 一作或末位作者 {last} 篇 | {','.join(q[0] for q in qs)}")
        if em: print(f"    email: {', '.join(em[:2])}")
        for y,doi,t,q in papers[:2]:
            print(f"    [{q[0]}] {y} {doi} {t}")
show("个人层面同时具备配方与脑/BBB能力（A 且 (B 或 D)）",
     lambda q: ("A_lnp_formulation" in q) and ({"B_bbb_model","D_brain_delivery"} & q), minlast=2)
show("个人层面配方加表征方法学（A 且 C）",
     lambda q: {"A_lnp_formulation","C_characterisation"} <= q, minlast=3, limit=18)
show("个人层面 BBB 模型能力为主（B 或 D，且无 A）",
     lambda q: ({"B_bbb_model","D_brain_delivery"} & q) and "A_lnp_formulation" not in q, minlast=5, limit=14)
