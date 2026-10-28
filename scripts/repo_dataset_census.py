"""普查 Zenodo 与 Figshare 上的脂质纳米粒与脂质体配方数据集。

为什么需要这个脚本：Consensus 只索引论文，不索引数据仓储条目（第 3 批已证实，
见 docs/open-datasets.md）。要知道仓储里到底有多少可用的配方级数据集，
只能直接打这两个仓储的 API。

**本环境跑不了**：云环境的网络策略拒绝 zenodo.org 与 api.figshare.com
（CONNECT 返回 403）。脚本已写好并验证过语法，需在有外网的机器上跑，
或者在云环境设置里把这两个域名加进允许列表后再跑。

用法：
    python3 -I scripts/repo_dataset_census.py            # 两个仓储都查
    python3 -I scripts/repo_dataset_census.py --only zenodo
输出：
    repo_census.json   每条记录含 仓储、标题、DOI、许可、文件数、发布日期、链接
    repo_census.csv    同上的扁平表，可直接并进 docs/open-datasets.md

两个 API 都不需要 token 做只读检索；Figshare 匿名调用有速率限制，脚本已限速。
"""
import argparse, csv, json, sys, time, urllib.parse, urllib.request

QUERIES = [
    "lipid nanoparticle formulation",
    "liposome encapsulation efficiency",
    "solid lipid nanoparticle",
    "nanostructured lipid carrier",
    "lipid nanoparticle mRNA formulation screening",
    "nanoparticle particle size zeta potential dataset",
    "microfluidic nanoparticle formulation dataset",
    "blood-brain barrier permeability dataset",
]

def fetch(url, timeout=60, tries=4):
    for a in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=timeout) as r:
                return json.loads(r.read())
        except Exception as e:
            if a == tries - 1:
                print("  FAILED %s: %s" % (url[:70], e), file=sys.stderr)
                return None
            time.sleep(2 * (a + 1))

def zenodo(q, size=100):
    # type=dataset 把结果限定为数据集而不是论文预印本
    url = "https://zenodo.org/api/records?" + urllib.parse.urlencode(
        {"q": q, "size": size, "type": "dataset", "sort": "mostrecent"})
    d = fetch(url)
    out = []
    for h in ((d or {}).get("hits", {}) or {}).get("hits", []):
        md = h.get("metadata", {})
        out.append({
            "repo": "zenodo", "query": q,
            "title": md.get("title", ""),
            "doi": md.get("doi", ""),
            "license": ((md.get("license") or {}).get("id")
                        or (md.get("license") or {}).get("identifier") or ""),
            "published": md.get("publication_date", ""),
            "files": len(h.get("files", []) or []),
            "url": h.get("links", {}).get("self_html", "") or h.get("links", {}).get("html", ""),
        })
    return out

def figshare(q, page_size=100):
    url = "https://api.figshare.com/v2/articles?" + urllib.parse.urlencode(
        {"search_for": q, "page_size": page_size, "item_type": 3, "order": "published_date"})
    d = fetch(url)
    out = []
    for h in (d or []):
        out.append({
            "repo": "figshare", "query": q,
            "title": h.get("title", ""),
            "doi": h.get("doi", ""),
            "license": "",          # 需再调 /articles/{id} 才有许可，见下
            "published": h.get("published_date", ""),
            "files": "",
            "url": h.get("url_public_html", ""),
        })
    return out

def figshare_license(article_id):
    d = fetch("https://api.figshare.com/v2/articles/%s" % article_id)
    return ((d or {}).get("license") or {}).get("name", "")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", choices=["zenodo", "figshare"])
    ap.add_argument("--licenses", action="store_true",
                    help="为 Figshare 结果逐条补许可字段（多耗一次请求每条）")
    a = ap.parse_args()
    rows, seen = [], set()
    for q in QUERIES:
        for name, fn in (("zenodo", zenodo), ("figshare", figshare)):
            if a.only and a.only != name:
                continue
            print("[%s] %s" % (name, q))
            for r in fn(q):
                k = (r["repo"], r["doi"] or r["title"])
                if k in seen:
                    continue
                seen.add(k)
                rows.append(r)
            time.sleep(1.0)
    if a.licenses:
        for r in rows:
            if r["repo"] == "figshare" and r["url"]:
                aid = r["url"].rstrip("/").split("/")[-1]
                if aid.isdigit():
                    r["license"] = figshare_license(aid)
                    time.sleep(0.5)
    json.dump(rows, open("repo_census.json", "w"), ensure_ascii=False, indent=1)
    if rows:
        with open("repo_census.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
    print("\n%d 条去重后的记录，已写入 repo_census.json 与 repo_census.csv" % len(rows))
    print("下一步：人工过一遍标题，把含配方到结果配对数据的条目并进 docs/open-datasets.md")

if __name__ == "__main__":
    main()
