"""记录 data/raw/ 下各外部数据集原始文件的 SHA-256 校验值与大小。

校验值写两处：
1. 每个源文件夹 README.md 里 CHECKSUMS:BEGIN / CHECKSUMS:END 之间的表格
2. data/raw/checksums.json（机器可读，供抽取脚本在运行前核对）

抽取脚本应当在开始前调用 verify()，确认原始文件自上次登记以来没有变过。

用法:
    python3 scripts/record_raw_checksums.py            # 登记并写入
    python3 scripts/record_raw_checksums.py --verify    # 只核对，不写入，有差异则非零退出

原始文件是外部下载的数据，本脚本只读取其字节做哈希，不解析内容、不执行其中任何代码。
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
MANIFEST = RAW / "checksums.json"

# 每个源文件夹里属于说明文档、不计入校验的文件
META_FILES = {"README.md", "LICENSE.txt"}

BEGIN = "<!-- CHECKSUMS:BEGIN -->"
END = "<!-- CHECKSUMS:END -->"


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def scan() -> dict:
    """扫描 data/raw/<源>/ 下的全部非说明文件，返回 {源: [{path, sha256, bytes}]}。"""
    out = {}
    if not RAW.is_dir():
        return out
    for src_dir in sorted(p for p in RAW.iterdir() if p.is_dir()):
        entries = []
        for f in sorted(src_dir.rglob("*")):
            if not f.is_file() or f.name in META_FILES:
                continue
            entries.append(
                {
                    "path": f.relative_to(src_dir).as_posix(),
                    "sha256": sha256_of(f),
                    "bytes": f.stat().st_size,
                }
            )
        out[src_dir.name] = entries
    return out


def render_table(entries: list) -> str:
    if not entries:
        return "（尚无文件）"
    lines = ["| 文件 | 大小（字节） | SHA-256 |", "|---|---|---|"]
    for e in entries:
        lines.append(f"| `{e['path']}` | {e['bytes']:,} | `{e['sha256']}` |")
    return "\n".join(lines)


def write_readme_block(src_dir: Path, entries: list) -> bool:
    """把校验值表写进 README.md 的标记块之间。返回是否改动了文件。"""
    readme = src_dir / "README.md"
    if not readme.is_file():
        print(f"  [跳过] {src_dir.name}/README.md 不存在")
        return False
    text = readme.read_text(encoding="utf-8")
    if BEGIN not in text or END not in text:
        print(f"  [跳过] {src_dir.name}/README.md 没有 CHECKSUMS 标记块")
        return False
    head, rest = text.split(BEGIN, 1)
    _, tail = rest.split(END, 1)
    new = f"{head}{BEGIN}\n{render_table(entries)}\n{END}{tail}"
    if new == text:
        return False
    readme.write_text(new, encoding="utf-8")
    return True


def verify() -> int:
    """核对当前文件与 checksums.json 是否一致。返回差异数。"""
    if not MANIFEST.is_file():
        print(f"没有 {MANIFEST.relative_to(ROOT)}，无法核对。先不带 --verify 跑一次。")
        return 1
    recorded = json.loads(MANIFEST.read_text(encoding="utf-8"))["sources"]
    current = scan()
    diffs = 0
    for src in sorted(set(recorded) | set(current)):
        rec = {e["path"]: e["sha256"] for e in recorded.get(src, [])}
        cur = {e["path"]: e["sha256"] for e in current.get(src, [])}
        for path in sorted(set(rec) | set(cur)):
            if path not in rec:
                print(f"  [新增] {src}/{path}")
                diffs += 1
            elif path not in cur:
                print(f"  [缺失] {src}/{path}")
                diffs += 1
            elif rec[path] != cur[path]:
                print(f"  [变更] {src}/{path}")
                print(f"         登记 {rec[path]}")
                print(f"         当前 {cur[path]}")
                diffs += 1
    print(f"核对完成，差异 {diffs} 处。")
    return diffs


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--verify", action="store_true", help="只核对，不写入")
    args = ap.parse_args()

    if args.verify:
        return 1 if verify() else 0

    sources = scan()
    if not sources:
        print(f"{RAW.relative_to(ROOT)} 下没有源文件夹。")
        return 0

    total_files = 0
    for src, entries in sources.items():
        print(f"{src}: {len(entries)} 个文件")
        for e in entries:
            print(f"  {e['path']}  {e['bytes']:,} 字节  {e['sha256'][:16]}…")
        total_files += len(entries)
        changed = write_readme_block(RAW / src, entries)
        if changed:
            print(f"  已更新 {src}/README.md")

    MANIFEST.write_text(
        json.dumps({"sources": sources}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print()
    print(f"共 {total_files} 个文件，已写入 {MANIFEST.relative_to(ROOT)}")
    if total_files == 0:
        print("提示：原始文件还没进仓库，现在登记的是空清单。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
