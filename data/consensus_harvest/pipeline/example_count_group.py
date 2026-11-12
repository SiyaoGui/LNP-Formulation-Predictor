import csv,collections
p='/home/user/LNP-Formulation-Predictor/docs/master-candidates.csv'
rows=list(csv.DictReader(open(p)))
themes=["眼与视网膜的核酸递送与临床试验","体内免疫细胞靶向递送与原位 CAR 生成","寡核苷酸肝肾毒性血小板减少与补体激活机制",
"骨与软骨的核酸递送与骨质疏松骨关节炎","抗 PEG 抗体加速血液清除与补体激活假过敏","脂肪组织靶向寡核苷酸治疗肥胖与代谢病",
"DNA 条码高通量体内筛选与定量生物分布","机器学习预测脂质纳米粒配方性能与可电离脂质筛选"]
c=collections.Counter(); nf=collections.Counter()
for r in rows:
    for t in themes:
        if r['why_matters'].startswith(t):
            c[t]+=1
            if r['needs_fulltext']=='Y': nf[t]+=1
            break
for t in themes: print(t, c[t], nf[t])
print('TOTAL ROWS', len(rows))
print(collections.Counter(r['source_type'] for r in rows))
for w in ['A','B','C','D','E','J','K']:
    print(w,'rows', sum(1 for r in rows if w in r['workflows'].split(';')))
print(collections.Counter(r['needs_fulltext'] for r in rows))
d=collections.Counter(r['doi'] for r in rows if r['doi'])
print('dup dois', sum(1 for k,v in d.items() if v>1))
