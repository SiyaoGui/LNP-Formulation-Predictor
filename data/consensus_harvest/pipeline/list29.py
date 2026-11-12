import csv
old=set()
with open('old_master54.csv',encoding='utf-8') as f:
    for r in csv.DictReader(f): old.add(r['doi'].strip().lower())
themes={}
with open('/home/user/LNP-Formulation-Predictor/docs/master-candidates.csv',encoding='utf-8') as f:
    for r in csv.DictReader(f):
        if r['doi'].strip().lower() in old: continue
        t=r['why_matters'].split('。')[0]
        themes.setdefault(t,[]).append(r)
for t,rows in themes.items():
    print("### "+t+"  ("+str(len(rows))+")")
    for r in rows:
        print("  %s | %s | %s | %s | %s | %s"%(r['doi'],r['year'],r['source_type'],r['needs_fulltext'],r['title'][:95],r['journal'][:40]))
