#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
export_cards.py : turn the calendar HTML into a JSON index of its cards.

Usage:
    python3 -I export_cards.py lipidlens-funding-calendar.html cards_index.json

The HTML is the master copy; the JSON is only a convenient read-only view of it, so a person or a
script can search the cards without parsing 800 KB of markup. Never edit the JSON and expect the
page to change.

Each card becomes one object:
    i          position in the file, starting at 0
    group      data-cat of the enclosing group (submitted, action, events, investor, ecosystem,
               competition, wait, verify, excluded, appendix)
    region     data-region (dk, eu, se, no, fi, is, nordic, us, ca, gb, ie, ...), may be null
    need       data-need tags (S single founder can apply, K needs a co-founder, C needs a CVR,
               E event, ? eligibility to be checked)
    short      data-short, the short name used in the filters and the next-deadline box
    name, org  the card heading
    pill       the status pill text
    chips      countdown chips of the card: kind (dl deadline, ev event, op opens, rs result expected,
               wn window), label, shown (the printed date text), start and end as epoch milliseconds,
               start_cph and end_cph in Copenhagen time, approx (estimated date), target (planned backwards
               from another deadline), hour_assumed (clock hour was assumed), abs0 and abs1 (printed labels)
    grid       the label and value pairs of the card body (amount, submission, cycle, ...)
    note       the verification note, as plain text
    link       the official page the card points to
"""
import sys
import json
import datetime as dt
from zoneinfo import ZoneInfo
from bs4 import BeautifulSoup

CPH = ZoneInfo("Europe/Copenhagen")


def cph(ms):
    return dt.datetime.fromtimestamp(int(ms) / 1000.0, tz=dt.timezone.utc).astimezone(CPH).strftime("%Y-%m-%d %H:%M")


def text(el):
    return el.get_text(" ", strip=True) if el else ""


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)
    src, dst = sys.argv[1], sys.argv[2]
    soup = BeautifulSoup(open(src, encoding="utf-8").read(), "html.parser")
    out = []
    for i, card in enumerate(soup.select("div.fcard")):
        grp = card.find_parent("details", class_="group")
        name_el = card.select_one(".fcard-name")
        org_el = card.select_one(".fcard-name .org")
        org = text(org_el).lstrip("· ").strip()
        # heading without the region tag and the organisation
        name = ""
        if name_el:
            parts = []
            for node in name_el.children:
                if getattr(node, "name", None) == "span":
                    continue
                parts.append(node.get_text() if hasattr(node, "get_text") else str(node))
            name = "".join(parts).strip()
        chips = []
        for b in card.select("button.cd"):
            t0, t1 = b.get("data-t0"), b.get("data-t1")
            chips.append({
                "kind": b.get("data-k"),
                "label": text(b.select_one(".cd-l")),
                "shown": text(b.select_one(".cd-d")),
                "start": int(t0) if t0 else None,
                "end": int(t1) if t1 else None,
                "start_cph": cph(t0) if t0 else None,
                "end_cph": cph(t1) if t1 else None,
                "approx": b.get("data-a") == "1",
                "target": b.get("data-tg") == "1",
                "hour_assumed": b.get("data-h") == "1",
                "abs0": b.get("data-abs0"),
                "abs1": b.get("data-abs1"),
            })
        grid = {}
        for dt_el in card.select("dl.fcard-grid dt"):
            dd = dt_el.find_next_sibling("dd")
            grid[text(dt_el)] = text(dd)
        link = card.select_one("a.fcard-link")
        out.append({
            "i": i,
            "group": grp.get("data-cat") if grp else None,
            "region": card.get("data-region"),
            "need": card.get("data-need"),
            "short": card.get("data-short"),
            "name": name,
            "org": org,
            "pill": text(card.select_one(".pill")),
            "chips": chips,
            "grid": grid,
            "note": text(card.select_one(".fcard-note")),
            "link": link.get("href") if link else None,
        })
    with open(dst, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("cards written:", len(out), " chips:", sum(len(c["chips"]) for c in out), " ->", dst)


if __name__ == "__main__":
    main()
