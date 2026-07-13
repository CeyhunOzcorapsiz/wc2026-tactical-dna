# -*- coding: utf-8 -*-
"""FIFA mac raporlarindan takim-mac taktik metriklerini cikarir.

Kaynak sayfalar:
 - "Match Summary - Key Statistics": possession, pas, line break, pres vb.
 - "Defensive Pressure": pres suresi, top geri kazanma, pres yonu.
Rakamlar PUA fontuyla gizli (0xe071-0xe07a = 0-9); climate_analysis'te
dogrulanan cozumun aynisi. Dogrulama: sayfadaki gol sayilari bilinen
skorlarla karsilastirilir.
Cikti: data/team_match_tactics.csv
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
OUT.mkdir(parents=True, exist_ok=True)

TEAMS = set(pd.read_csv(FOOTBALL / "wc2026_dataset" / "teams.csv")["team_name"])
ALIAS = {"Korea Republic": "South Korea", "United States": "USA",
         "Czech Republic": "Czechia",
         "Bosnia-Herzegovina": "Bosnia and Herzegovina"}

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

def split_teams(line):
    """'South Africa Canada' gibi satiri bilinen adlarla ikiye ayir."""
    toks = line.split()
    for i in range(1, len(toks)):
        a, b = " ".join(toks[:i]), " ".join(toks[i:])
        a, b = ALIAS.get(a, a), ALIAS.get(b, b)
        if a in TEAMS and b in TEAMS:
            return a, b
    return None, None

# (regex, [home kolonlari], [away kolonlari])
KEY_PATTERNS = [
    (r"Total ([\d.]+)% ([\d.]+)% ([\d.]+)% Total",
     ["possession_pct"], ["possession_pct"], "3way"),
    (r"^(\d+) Goals (\d+)$", ["goals"], ["goals"], "2"),
    (r"([\d.]+) xG \(Expected Goals\) ([\d.]+)", ["xg"], ["xg"], "2"),
    (r"(\d+) \((\d+)\) Attempts at Goal \(On Target\) (\d+) \((\d+)\)",
     ["attempts", "on_target"], ["attempts", "on_target"], "4"),
    (r"(\d+) \((\d+)\) Total Passes \(Complete\) (\d+) \((\d+)\)",
     ["passes", "passes_complete"], ["passes", "passes_complete"], "4"),
    (r"(\d+) % Pass Completion % (\d+) %",
     ["pass_completion_pct"], ["pass_completion_pct"], "2"),
    (r"(\d+) Completed Line Breaks (\d+)",
     ["line_breaks"], ["line_breaks"], "2"),
    (r"(\d+) Defensive Line Breaks (\d+)",
     ["def_line_breaks"], ["def_line_breaks"], "2"),
    (r"(\d+) Receptions in the Final Third (\d+)",
     ["final_third_receptions"], ["final_third_receptions"], "2"),
    (r"^(\d+) Crosses (\d+)$", ["crosses"], ["crosses"], "2"),
    (r"(\d+) Ball Progressions (\d+)",
     ["progressions"], ["progressions"], "2"),
    (r"(\d+) \((\d+)\) Defensive Pressures Applied \(Direct Pressures\) (\d+) \((\d+)\)",
     ["pressures", "direct_pressures"], ["pressures", "direct_pressures"], "4"),
    (r"(\d+) Forced Turnovers (\d+)",
     ["forced_turnovers"], ["forced_turnovers"], "2"),
    (r"(\d+) Second Balls (\d+)", ["second_balls"], ["second_balls"], "2"),
    (r"([\d.]+) km Total Distance Covered ([\d.]+) km",
     ["distance_km"], ["distance_km"], "2"),
]

PRESS_PATTERNS = [
    (r"([\d.]+)s Avg Pressure Duration ([\d.]+)s", "press_duration_s"),
    (r"([\d.]+)s Ball Recovery Time ([\d.]+)s", "recovery_time_s"),
    (r"(\d+) Pushing on into Pressing (\d+)", "push_into_press"),
    (r"(\d+) Pressing Direction Inside (\d+)", "press_inside"),
    (r"(\d+) Pressing Direction Outside (\d+)", "press_outside"),
]

def parse_report(path):
    pdf = pdfplumber.open(path)
    home = {}; away = {}
    hteam = ateam = None; header = None
    # Key Statistics genelde 3. sayfa; degilse ilk 6 sayfada ara
    for idx in [2, 1, 3, 4, 5, 0]:
        if idx >= len(pdf.pages):
            continue
        lines = page_lines(pdf.pages[idx])
        if any("Key Statistics" in l for l in lines):
            header = lines[0]
            # takim satiri: "Possession"dan onceki satir
            for j, l in enumerate(lines):
                if l.strip() == "Possession" and j > 0:
                    hteam, ateam = split_teams(lines[j - 1])
                    break
            for l in lines:
                for pat, hcols, acols, kind in KEY_PATTERNS:
                    m = re.search(pat, l)
                    if not m:
                        continue
                    g = [float(x) for x in m.groups()]
                    if kind == "3way":
                        home["possession_pct"] = g[0]
                        home["contested_pct"] = g[1]
                        away["possession_pct"] = g[2]
                        away["contested_pct"] = g[1]
                    elif kind == "2":
                        home[hcols[0]] = g[0]; away[acols[0]] = g[1]
                    elif kind == "4":
                        home[hcols[0]], home[hcols[1]] = g[0], g[1]
                        away[acols[0]], away[acols[1]] = g[2], g[3]
            break
    # Defensive Pressure sayfasi (indeks ~25-35 arasi)
    for idx in range(22, min(len(pdf.pages), 40)):
        lines = page_lines(pdf.pages[idx])
        if not any(l.strip() == "Defensive Pressure" for l in lines):
            continue
        for l in lines:
            clean = re.sub(r"\b[A-Z]\b ?", "", l).strip()
            for pat, col in PRESS_PATTERNS:
                m = re.search(pat, clean)
                if m:
                    home[col] = float(m.group(1))
                    away[col] = float(m.group(2))
        break
    pdf.close()
    return header, hteam, ateam, home, away

def main():
    rows = []
    for f in sorted(PDF_DIR.glob("PMSR-*.pdf")):
        mnum = int(re.search(r"M(\d+)", f.name).group(1))
        header, ht, at, home, away = parse_report(f)
        if ht is None:
            print(f"UYARI: takimlar cozulmedi: {f.name}")
            continue
        for team, opp, d, side in ((ht, at, home, "home"), (at, ht, away, "away")):
            r = {"match_number": mnum, "header": header, "team": team,
                 "opponent": opp, "side": side}
            r.update(d)
            rows.append(r)
    df = pd.DataFrame(rows)
    df = df.drop_duplicates(subset=["match_number", "team"], keep="first")
    df.to_csv(OUT / "team_match_tactics.csv", index=False)
    print(f"{df['match_number'].nunique()} mac, {len(df)} takim-mac satiri")
    miss = df[[c for c in df.columns if c not in
               ('match_number', 'header', 'team', 'opponent', 'side')]].isna().mean()
    print("eksik oranlari (ilk 12):")
    print(miss.sort_values(ascending=False).head(12).round(3).to_string())

if __name__ == "__main__":
    main()
