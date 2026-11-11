import urllib.request, urllib.parse, json, time, re, sys, xml.etree.ElementTree as ET
BASE="https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
TOOL={"tool":"lnp-partner-scan","email":"YOUR_EMAIL@example.com"}
def get(ep,params):
    p=dict(params); p.update(TOOL)
    url=BASE+ep+"?"+urllib.parse.urlencode(p)
    for a in range(4):
        try:
            with urllib.request.urlopen(url,timeout=60) as r: return r.read()
        except Exception as e:
            if a==3: raise
            time.sleep(2*(a+1))
def esearch(q,retmax=400):
    d=json.loads(get("esearch.fcgi",{"db":"pubmed","term":q,"retmax":retmax,"retmode":"json"}))
    return d["esearchresult"]["idlist"], d["esearchresult"]["count"]
def efetch(ids):
    out=[]
    for i in range(0,len(ids),150):
        chunk=ids[i:i+150]
        xml=get("efetch.fcgi",{"db":"pubmed","id":",".join(chunk),"retmode":"xml"})
        root=ET.fromstring(xml)
        for art in root.iter("PubmedArticle"):
            pmid=art.findtext(".//PMID") or ""
            title="".join(art.find(".//ArticleTitle").itertext()) if art.find(".//ArticleTitle") is not None else ""
            journal=art.findtext(".//Journal/ISOAbbreviation") or art.findtext(".//Journal/Title") or ""
            year=art.findtext(".//JournalIssue/PubDate/Year") or art.findtext(".//JournalIssue/PubDate/MedlineDate") or ""
            doi=""
            idlist=art.find("./PubmedData/ArticleIdList")
            if idlist is not None:
                for aid in idlist.findall("ArticleId"):
                    if aid.get("IdType")=="doi" and not doi: doi=(aid.text or "").strip()
            if not doi:
                for el in art.findall("./MedlineCitation/Article/ELocationID"):
                    if el.get("EIdType")=="doi" and not doi: doi=(el.text or "").strip()
            auths=[]
            for a in art.iter("Author"):
                ln=a.findtext("LastName") or ""; fn=a.findtext("ForeName") or ""
                affs=[ (x.findtext("Affiliation") or "") for x in a.iter("AffiliationInfo") ]
                auths.append({"name":(fn+" "+ln).strip(),"affs":affs})
            out.append({"pmid":pmid,"doi":doi,"title":title,"journal":journal,"year":year,"authors":auths})
        time.sleep(0.4)
    return out
NORDIC="(Denmark[ad] OR Sweden[ad] OR Norway[ad] OR Finland[ad] OR Danmark[ad] OR Sverige[ad] OR Norge[ad] OR Suomi[ad])"
QUERIES={
 "A_lnp_formulation": f'("lipid nanoparticle*"[tiab] OR liposom*[tiab] OR "solid lipid nanoparticle*"[tiab] OR "nanostructured lipid carrier*"[tiab]) AND (formulat*[tiab] OR encapsulat*[tiab] OR "drug loading"[tiab] OR microfluidic*[tiab]) AND {NORDIC} AND 2021:2026[dp]',
 "B_bbb_model": f'("blood-brain barrier"[tiab] OR "blood brain barrier"[tiab]) AND (model*[tiab] OR "in vitro"[tiab] OR transwell[tiab] OR "on-a-chip"[tiab] OR microfluidic*[tiab] OR organoid*[tiab] OR hiPSC[tiab] OR "iPSC"[tiab]) AND {NORDIC} AND 2021:2026[dp]',
 "C_characterisation": f'(("dynamic light scattering"[tiab] OR "zeta potential"[tiab] OR "particle size"[tiab] OR "asymmetric flow field-flow fractionation"[tiab] OR "small-angle"[tiab] OR cryo-EM[tiab] OR "reference material*"[tiab]) AND (nanoparticle*[tiab] OR liposom*[tiab] OR "lipid nanoparticle*"[tiab])) AND {NORDIC} AND 2021:2026[dp]',
 "D_brain_delivery": f'(nanoparticle*[tiab] OR liposom*[tiab] OR "lipid nanoparticle*"[tiab] OR nanocarrier*[tiab]) AND (brain[tiab] OR cerebral[tiab] OR "central nervous system"[tiab] OR CNS[tiab]) AND (deliver*[tiab] OR target*[tiab] OR transport[tiab]) AND {NORDIC} AND 2021:2026[dp]',
}
res={}
for k,q in QUERIES.items():
    ids,cnt=esearch(q)
    print(k,"count",cnt,"fetched",len(ids)); sys.stdout.flush()
    res[k]=efetch(ids)
    time.sleep(0.5)
json.dump(res,open("pubmed_nordic.json","w"),ensure_ascii=False)
print("saved")
