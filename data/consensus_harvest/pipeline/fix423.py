import csv
p='/home/user/LNP-Formulation-Predictor/docs/master-candidates.csv'
rows=list(csv.DictReader(open(p)))
fn=list(rows[0].keys())
exo="外泌体与细胞外囊泡的脑递送"
bay="贝叶斯优化、主动学习与自驱动实验室在配方开发中的应用"
n422=n423=0
for r in rows:
    w=r['why_matters']
    if bay in w and r['workflows']=='C;F':
        pass
    # locate rows by theme text
for r in rows:
    w=r['why_matters']
    if w.startswith(bay):
        # these were appended for block 422 (actually exosome block) -> swap
        r['why_matters']=w.replace(bay,exo,1); r['workflows']='H;B'; r['priority']='P1'; n422+=1
    elif w.startswith(exo):
        r['why_matters']=w.replace(exo,bay,1); r['workflows']='C;F'; r['priority']='P0'; n423+=1
with open(p,'w',newline='') as f:
    wr=csv.DictWriter(f,fieldnames=fn); wr.writeheader(); wr.writerows(rows)
print('swapped bay->exo',n422,'exo->bay',n423,'total rows',len(rows))
