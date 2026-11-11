#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_calendar.py : basic consistency checks for the LipidLens funding calendar HTML.

Usage:
    python3 -I check_calendar.py lipidlens-funding-calendar.html [--now 2026-11-10T00:00] [--upcoming-days 90] [--words FILE]

What it checks (it only reads the file, it never edits it and never touches the network):
  1. Structure counts: cards, groups, countdown chips by kind, regions, action-list items.
  2. Chip dates: each countdown chip carries epoch milliseconds (data-t0, data-t1) and printed labels
     (data-abs0, data-abs1 such as "11-10 周二"). The script converts the epoch to Copenhagen time and
     compares month, day and weekday with the printed label. A label may legitimately follow the
     organiser's own time zone, so mismatches are reported for review, not as proven errors.
  3. Weekday and date pairs in the visible text ("11-05 周四", "2027-01-10 周日"): each pair is tested
     against the calendar for 2026 and 2027 (or the year printed next to it).
  4. Dash characters (em dash, en dash) in the visible text. The owner's rule is no dashes in new text.
  5. E-mail addresses and phone-like numbers in the whole file.
  6. Counts for an optional word list given with --words FILE (the list itself is kept out of the public repository).
  7. The next deadlines inside the window given by --upcoming-days, as a plain list for hand-over work.

Exit code is 0 even when findings exist, because findings need a human decision.
"""
import re
import sys
import json
import hashlib
import datetime as dt
from zoneinfo import ZoneInfo
from html import unescape
from collections import Counter

from bs4 import BeautifulSoup

CPH = ZoneInfo("Europe/Copenhagen")
# A printed label follows the organiser's own clock, so it may differ from Copenhagen time.
LABEL_ZONES = [ZoneInfo(z) for z in (
    "Europe/Copenhagen", "Europe/Helsinki", "Europe/Lisbon", "Europe/London", "Europe/Brussels",
    "Europe/Berlin", "Europe/Zurich", "Europe/Paris", "Europe/Stockholm", "Europe/Oslo", "Atlantic/Reykjavik",
    "America/Los_Angeles", "America/New_York", "America/Chicago", "America/Toronto", "UTC")]
WD = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]  # Monday first, like datetime.weekday()

# Personal-status terms are not kept in this file. Pass --words FILE (one term per line) to count them.
PRIVATE_WORDS = []


def parse_args(argv):
    path = None
    now = dt.datetime.now(CPH)
    days = 90
    words_file = None
    i = 1
    while i < len(argv):
        a = argv[i]
        if a == "--now":
            now = dt.datetime.fromisoformat(argv[i + 1]).replace(tzinfo=CPH)
            i += 2
        elif a == "--upcoming-days":
            days = int(argv[i + 1])
            i += 2
        elif a == "--words":
            words_file = argv[i + 1]
            i += 2
        else:
            path = a
            i += 1
    if not path:
        print(__doc__)
        sys.exit(2)
    return path, now, days, words_file


def cph(ms):
    return dt.datetime.fromtimestamp(ms / 1000.0, tz=dt.timezone.utc).astimezone(CPH)


def label_parts(label):
    """'11-10 周二' or '2027-01-10 周日' -> (year or None, month, day, weekday_name)."""
    m = re.match(r"\s*(?:(\d{4})-)?(\d{1,2})-(\d{1,2})\s*(周[一二三四五六日])", label or "")
    if not m:
        return None
    y = int(m.group(1)) if m.group(1) else None
    return y, int(m.group(2)), int(m.group(3)), m.group(4)


def main():
    path, now, days, words_file = parse_args(sys.argv)
    if words_file:
        PRIVATE_WORDS.extend(w.strip() for w in open(words_file, encoding="utf-8") if w.strip())
    raw = open(path, "rb").read()
    html = raw.decode("utf-8")
    print("file:", path)
    print("bytes:", len(raw), " sha256:", hashlib.sha256(raw).hexdigest())
    soup = BeautifulSoup(html, "html.parser")

    # ---------------------------------------------------------------- 1. structure
    print("\n== 1. structure")
    cards = soup.select("div.fcard")
    print("cards:", len(cards))
    groups = soup.select("details.group")
    per_group = Counter()
    for g in groups:
        per_group[g.get("data-cat")] += len(g.select("div.fcard"))
    print("cards per group:", dict(per_group), " (sum %d)" % sum(per_group.values()))
    chips = soup.select("button.cd")
    print("countdown chips:", len(chips), dict(Counter(c.get("data-k") for c in chips)))
    print("estimated chips (data-a=1):", sum(1 for c in chips if c.get("data-a") == "1"),
          " backward-planned targets (data-tg=1):", sum(1 for c in chips if c.get("data-tg") == "1"),
          " assumed clock hour (data-h=1):", sum(1 for c in chips if c.get("data-h") == "1"))
    print("regions:", dict(Counter(c.get("data-region") for c in cards)))
    print("need tags:", dict(Counter(c.get("data-need") for c in cards)))
    acts_all = soup.select("div.actbox li")
    acts = soup.select("div.actbox li[data-until]")
    print("action-list items:", len(acts_all), " of which with data-until:", len(acts))
    print("timeline details blocks:", len(soup.select("details.tl-details")))
    stats = [(s.select_one(".l").get_text(strip=True), s.select_one(".n").get_text(strip=True))
             for s in soup.select("section.stats div.stat")]
    print("header stat tiles:", stats)
    print("title:", soup.title.get_text(strip=True) if soup.title else None)

    # ---------------------------------------------------------------- 2. chip dates
    print("\n== 2. chip epoch versus printed label (any organiser time zone in LABEL_ZONES)")
    bad = []
    for c in chips:
        card = c.find_parent("div", class_="fcard")
        name = card.get("data-short") if card else "(no card)"
        lab = c.select_one(".cd-l").get_text(strip=True) if c.select_one(".cd-l") else ""
        for which in ("0", "1"):
            t = c.get("data-t" + which)
            a = c.get("data-abs" + which)
            if not t or not a:
                continue
            p = label_parts(a)
            if not p:
                bad.append((name, lab, which, a, "label not parseable", ""))
                continue
            y, mo, da, wd = p
            ok = False
            for z in LABEL_ZONES:
                d = dt.datetime.fromtimestamp(int(t) / 1000.0, tz=dt.timezone.utc).astimezone(z)
                if d.month == mo and d.day == da and WD[d.weekday()] == wd and (y is None or d.year == y):
                    ok = True
                    break
            if not ok:
                d = cph(int(t))
                bad.append((name, lab, which, a, d.strftime("%Y-%m-%d %H:%M ") + WD[d.weekday()], t))
    print("chips whose label matches no candidate time zone:", len(bad))
    for b in bad[:60]:
        print("  ", b[0], "|", b[1], "| t%s" % b[2], "| label:", b[3], "| Copenhagen:", b[4])
    if len(bad) > 60:
        print("   ... %d more" % (len(bad) - 60))
    order_bad = [(c.find_parent("div", class_="fcard").get("data-short"), c.get("data-t0"), c.get("data-t1"))
                 for c in chips if c.get("data-t0") and c.get("data-t1") and int(c["data-t1"]) < int(c["data-t0"])]
    print("chips whose end is before the start:", len(order_bad), order_bad[:5])

    # ---------------------------------------------------------------- 3. weekday pairs in text
    print("\n== 3. weekday and date pairs in the visible text")
    for s in soup(["script", "style"]):
        s.decompose()
    text = unescape(soup.get_text("\n"))
    pairs = re.findall(r"(?<![\d-])(?:(\d{4})-)?(\d{1,2})-(\d{1,2})\s*(周[一二三四五六日])", text)
    wrong = []
    for y, mo, da, wd in pairs:
        mo, da = int(mo), int(da)
        years = [int(y)] if y else [2026, 2027]
        okany = False
        for yy in years:
            try:
                if WD[dt.date(yy, mo, da).weekday()] == wd:
                    okany = True
            except ValueError:
                pass
        if not okany:
            wrong.append((y, mo, da, wd))
    print("pairs found:", len(pairs), " pairs that match neither 2026 nor 2027 (or the printed year):", len(wrong))
    for w in wrong[:40]:
        print("  ", w)

    # ---------------------------------------------------------------- 4. dashes
    print("\n== 4. dash characters in the visible text")
    em = text.count("\u2014")
    en = text.count("\u2013")
    print("em dash:", em, " en dash:", en)
    for m in list(re.finditer(r"[\u2013\u2014]", text))[:8]:
        print("   ...", text[max(0, m.start() - 30):m.end() + 30].replace("\n", " "))

    # ---------------------------------------------------------------- 5. e-mail and phones
    print("\n== 5. e-mail addresses and phone-like numbers in the whole file")
    emails = sorted(set(re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", html)))
    print("distinct e-mail addresses:", len(emails))
    for e in emails[:40]:
        print("   ", e)
    phones = sorted(set(re.findall(r"(?<![\d-])\+\d{2,3}[\d\s]{7,14}", text)))
    print("phone-like numbers:", len(phones), phones[:10])

    # ---------------------------------------------------------------- 6. private words
    print("\n== 6. words from --words FILE (count in visible text)" if PRIVATE_WORDS else "\n== 6. no --words file given, skipped")
    low = text.lower()
    for w in PRIVATE_WORDS:
        n = low.count(w.lower())
        if n:
            print("   %-22s %d" % (w, n))

    # ---------------------------------------------------------------- 7. upcoming
    print("\n== 7. next deadlines and dates, window %d days from %s" % (days, now.strftime("%Y-%m-%d %H:%M")))
    soup2 = BeautifulSoup(html, "html.parser")
    rows = []
    now_ms = int(now.timestamp() * 1000)
    end_ms = int((now + dt.timedelta(days=days)).timestamp() * 1000)
    for c in soup2.select("button.cd"):
        t0, t1 = c.get("data-t0"), c.get("data-t1")
        if not t0 or not t1:
            continue
        t0, t1 = int(t0), int(t1)
        if t1 < now_ms or t0 > end_ms:
            continue
        card = c.find_parent("div", class_="fcard")
        if card is None:
            continue  # timeline and next-box copies of a chip; the card chip is listed instead
        grp = card.find_parent("details", class_="group").get("data-cat")
        rows.append((t1, c.get("data-k"), "~" if c.get("data-a") == "1" else "=", grp,
                     card.get("data-short"), c.select_one(".cd-l").get_text(strip=True),
                     c.select_one(".cd-d").get_text(strip=True)))
    rows.sort()
    for r in rows:
        print("  %s  %-2s %s  [%-11s] %s : %s (%s)" % (cph(r[0]).strftime("%Y-%m-%d %H:%M"), r[1], r[2], r[3], r[4], r[5], r[6]))
    print("(= official date, ~ estimated date; kinds: dl deadline, ev event, op opens, rs result expected, wn window)")


if __name__ == "__main__":
    main()
