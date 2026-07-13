# -*- coding: utf-8 -*-
"""Detay sayfalari: oyuncu line-break tablolari + sut detaylari (tum PDF'ler).

 - "Line Breaks <takim>" (# Player'li tablo): oyuncu basina denenen/tamamlanan
   line break + yon (through/around/over) + tip (pas/orta/tasima).
   Dogrulama: yon toplami = denenen.
 - "Attempts at Goal <takim>" (Time Player Outcome'lu tablo): her sut icin
   sonuc + gelis tipi (Pass/Cross/Corner/Freekick/Penalty/...).
Cikti: data/player_line_breaks.csv, data/shot_details.csv
"""
import logging
import re
from pathlib import Path

import pandas as pd
import pdfplumber

logging.getLogger("pdfminer").setLevel(logging.ERROR)

FOOTBALL = Path(__file__).resolve().parents[2]
PDF_DIR = FOOTBALL / "climate_analysis" / "data" / "fifa_reports"
OUT = Path(__file__).resolve().parents[1] / "data"

def dec(ch):
    o = ord(ch)
    if 0xE071 <= o <= 0xE07A:
        return str(o - 0xE071)
    if o == 0xE094:
        return "."
    return ch

def page_lines(pg):
    rows = {}
    for w in pg.extract_words():
        txt = "".join(dec(c) for c in w["text"])
        rows.setdefault(round(w["top"] / 6), []).append((w["x0"], txt))
    return [" ".join(t for _, t in sorted(rows[k])) for k in sorted(rows)]

LB_ROW = re.compile(r"^(\d{1,2})\s+(.+?)\s+(\d+)\s+(\d+)\s+(\d+)%\s+((?:\d+\s+){14}\d+)$")
OUTCOMES = ["On Target - Goal", "On Target - Saved", "Off Target",
            "Incomplete - Blocked", "Deflected Off Target - Defensive Event",
            "Deflected On Target - Defensive Event", "Woodwork",
            "On Target - Blocked", "Incomplete"]
DELIVERIES = ["Loose Ball", "Set Play", "Pass", "Cross", "Freekick", "Corner",
              "Penalty", "Throw In", "Dribble", "Rebound", "Other"]

def parse_lb_page(lines, team):
    rows = []
    for ln in lines:
        m = LB_ROW.match(ln.strip())
        if not m:
            continue
        nums = [int(x) for x in m.group(6).split()]
        rows.append({
            "team": team, "jersey": int(m.group(1)), "player": m.group(2),
            "lb_attempted": int(m.group(3)), "lb_completed": int(m.group(4)),
            "through": nums[9], "around": nums[10], "over": nums[11],
            "via_pass": nums[12], "via_cross": nums[13], "via_carry": nums[14],
            "dir_sum_ok": int(nums[9] + nums[10] + nums[11] == int(m.group(3))),
        })
    return rows

def parse_shot_line(ln):
    s = ln.strip()
    m = re.match(r"^(\d{1,3})\s+(\d{1,2})\s*(.+)$", s)
    if not m:
        return None
    minute, rest = int(m.group(1)), m.group(3)
    delivery = next((d for d in DELIVERIES if rest.endswith(d)), None)
    if delivery is None:
        return None
    rest = rest[: -len(delivery)].strip()
    outcome = next((o for o in OUTCOMES if o in rest), None)
    if outcome is None:
        return None
    player = rest.split(outcome)[0].strip()
    return {"minute": minute, "player": player, "outcome": outcome,
            "is_goal": int(outcome == "On Target - Goal"),
            "delivery": delivery}

def main():
    lb_rows, shot_rows = [], []
    for f in sorted(PDF_DIR.glob("PMSR-*.pdf")):
        mnum = int(re.search(r"M(\d+)", f.name).group(1))
        pdf = pdfplumber.open(f)
        header = None
        for idx in range(4, min(len(pdf.pages), 24)):
            lines = page_lines(pdf.pages[idx])
            if not lines:
                continue
            if header is None:
                header = lines[0]
            title = lines[1] if len(lines) > 1 else ""
            m = re.match(r"^Line Breaks (.+)$", title.strip())
            if m and any("# Player" in l for l in lines):
                for r in parse_lb_page(lines, m.group(1).strip()):
                    r["match_number"] = mnum
                    r["header"] = header
                    lb_rows.append(r)
                continue
            m = re.match(r"^Attempts at Goal (.+)$", title.strip())
            if m and any(l.strip().startswith("Time Player Outcome") for l in lines):
                team = m.group(1).strip()
                for ln in lines:
                    r = parse_shot_line(ln)
                    if r:
                        r["match_number"] = mnum
                        r["team"] = team
                        r["header"] = header
                        shot_rows.append(r)
        pdf.close()

    lb = pd.DataFrame(lb_rows).drop_duplicates(
        subset=["match_number", "team", "player"])
    sh = pd.DataFrame(shot_rows).drop_duplicates(
        subset=["match_number", "team", "minute", "player", "outcome"])
    lb.to_csv(OUT / "player_line_breaks.csv", index=False)
    sh.to_csv(OUT / "shot_details.csv", index=False)
    print(f"line breaks: {len(lb)} oyuncu-mac, {lb['match_number'].nunique()} mac, "
          f"yon dogrulamasi: %{100 * lb['dir_sum_ok'].mean():.1f}")
    print(f"sutlar: {len(sh)} sut, {sh['match_number'].nunique()} mac, "
          f"gol: {sh['is_goal'].sum()}")
    print("gelis tipi dagilimi:")
    print(sh["delivery"].value_counts().to_string())

if __name__ == "__main__":
    main()
