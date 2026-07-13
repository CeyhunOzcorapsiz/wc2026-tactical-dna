# -*- coding: utf-8 -*-
"""Taktik haritanin animasyonlu veri hikayesi (MP4, 1080p, ~42 sn).

Akis: baslik -> eksen aciklamasi -> dort ekol sirayla haritaya duser
(isim + tek cumle karti) -> yari finalistler parlar -> kapanis mesaji.
Cikti: output/tactical_map_story_tr.mp4 ve _en.mp4
"""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import FFMpegWriter
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "output"

INK = "#1a1d21"; MUTED = "#6b7280"; GRID = "#e5e7eb"; SURFACE = "#ffffff"
COLORS = {0: "#0ea5e9", 3: "#059669", 2: "#f97316", 1: "#7c3aed"}
SEMIS = {"France", "Spain", "England", "Argentina"}
FPS = 30

TEXT = {
    "tr": {
        "title": "2026 Dünya Kupası'nın Taktik Haritası",
        "sub": "FIFA'nın resmî taktik verisi · 100 maç · 10 stil metriği · 48 takım",
        "xlab": "← topsuz bekleyen / topu geç kazanan            topa ve sahaya hükmeden →",
        "ylab": "← sabırlı hücum          dikine, hızlı hücum →",
        "schools": {
            0: ("Top hakimiyeti + yüksek pres",
                "Topu rakip yarı sahada kazanıp oyunu orada kuranlar"),
            3: ("Dengeli, maça göre oynayanlar",
                "Plan A'sı da B'si de olan pragmatikler — Brezilya, Hollanda, Japonya"),
            2: ("Geçiş oyunu + ön alan presi",
                "Kaybettiği an boğan, kazanınca dikine oynayanlar — Türkiye burada"),
            1: ("Alçak blok + kontra",
                "Kapanıp kontrayı bekleyenler — çoğu grupta veda etti"),
        },
        "semis": "Yarı finalistlerin 4'ü de aynı ekolden:\ntop hakimiyeti + yüksek pres",
        "end1": "Kupaya giden yol topa hükmetmekten geçti",
        "end2": "Yöntem, kod ve veri: github.com/CeyhunOzcorapsiz/wc2026-tactical-dna",
        "team_tr": {"Spain": "İspanya", "France": "Fransa", "England": "İngiltere",
                    "Argentina": "Arjantin", "Germany": "Almanya", "Brazil": "Brezilya",
                    "Netherlands": "Hollanda", "Japan": "Japonya", "USA": "ABD",
                    "Canada": "Kanada", "Morocco": "Fas", "Portugal": "Portekiz",
                    "Mexico": "Meksika", "South Africa": "Güney Afrika",
                    "South Korea": "Güney Kore", "Czechia": "Çekya",
                    "Bosnia and Herzegovina": "Bosna Hersek", "Qatar": "Katar",
                    "Switzerland": "İsviçre", "Australia": "Avustralya",
                    "Scotland": "İskoçya", "Côte d'Ivoire": "Fildişi Sahili",
                    "Ecuador": "Ekvador", "Tunisia": "Tunus", "Sweden": "İsveç",
                    "Saudi Arabia": "Suudi Arabistan", "Egypt": "Mısır",
                    "IR Iran": "İran", "New Zealand": "Yeni Zelanda",
                    "Belgium": "Belçika", "Croatia": "Hırvatistan", "Ghana": "Gana",
                    "Congo DR": "DR Kongo", "Uzbekistan": "Özbekistan",
                    "Colombia": "Kolombiya", "Norway": "Norveç", "Iraq": "Irak",
                    "Jordan": "Ürdün", "Algeria": "Cezayir", "Austria": "Avusturya"},
        "file": "tactical_map_story_tr.mp4",
    },
    "en": {
        "title": "The Tactical Map of the 2026 World Cup",
        "sub": "FIFA's official tactical data · 100 matches · 10 style metrics · 48 teams",
        "xlab": "← sitting off / slow to regain            dominating ball & territory →",
        "ylab": "← patient build-up          direct, vertical attacking →",
        "schools": {
            0: ("Possession + high press",
                "Winning the ball high and living in the opposition half"),
            3: ("Pragmatic, adaptable sides",
                "A plan A and a plan B — Brazil, Netherlands, Japan"),
            2: ("Transition game + counter-press",
                "Suffocating on the loss, direct on the regain — Türkiye lives here"),
            1: ("Low block + counters",
                "Sitting deep, waiting to break — most went home in the groups"),
        },
        "semis": "All four semi-finalists come from one school:\npossession + high press",
        "end1": "The road to the trophy ran through the ball",
        "end2": "Method, code & data: github.com/CeyhunOzcorapsiz/wc2026-tactical-dna",
        "team_tr": {},
        "file": "tactical_map_story_en.mp4",
    },
}

def ease(t):
    return 1 - (1 - np.clip(t, 0, 1)) ** 3

def make_video(lang):
    T = TEXT[lang]
    df = pd.read_csv(DATA / "team_clusters.csv")

    # sahne zamanlari (saniye)
    t_title, t_axes = 3.0, 3.0
    t_school, t_semis, t_end = 5.0, 6.0, 5.0
    order = [0, 3, 2, 1]
    total = t_title + t_axes + 4 * t_school + t_semis + t_end
    frames = int(total * FPS)

    fig, ax = plt.subplots(figsize=(12.8, 7.2), dpi=150)
    fig.subplots_adjust(top=0.86, bottom=0.10, left=0.06, right=0.97)
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.grid(color=GRID, linewidth=0.8)
    ax.tick_params(length=0, labelleft=False, labelbottom=False)
    pad_x = (df["pc1"].max() - df["pc1"].min()) * 0.10
    pad_y = (df["pc2"].max() - df["pc2"].min()) * 0.14
    ax.set_xlim(df["pc1"].min() - pad_x, df["pc1"].max() + pad_x)
    ax.set_ylim(df["pc2"].min() - pad_y, df["pc2"].max() + pad_y)

    # kalici ogeler
    title = fig.text(0.5, 0.60, T["title"], fontsize=26, fontweight="bold",
                     color=INK, ha="center", alpha=0)
    sub = fig.text(0.5, 0.53, T["sub"], fontsize=13, color=MUTED,
                   ha="center", alpha=0)
    xlab = ax.set_xlabel(T["xlab"], fontsize=11, color=MUTED)
    ylab = ax.set_ylabel(T["ylab"], fontsize=11, color=MUTED)
    xlab.set_alpha(0); ylab.set_alpha(0)

    dots, labels = {}, {}
    for _, r in df.iterrows():
        d = ax.scatter([r["pc1"]], [r["pc2"]], s=0, color=COLORS[r["cluster"]],
                       edgecolor=SURFACE, linewidth=1.5, zorder=3)
        name = T["team_tr"].get(r["team"], r["team"])
        l = ax.annotate(name, (r["pc1"], r["pc2"]), xytext=(0, 8),
                        textcoords="offset points", ha="center", fontsize=7.5,
                        color=MUTED, alpha=0, zorder=4)
        dots[r["team"]] = (d, r["cluster"])
        labels[r["team"]] = l

    card_name = fig.text(0.055, 0.905, "", fontsize=17, fontweight="bold", color=INK)
    card_desc = fig.text(0.055, 0.868, "", fontsize=11.5, color=MUTED)
    semis_txt = fig.text(0.985, 0.90, "", fontsize=14, fontweight="bold",
                         color=COLORS[0], ha="right", va="top")
    end1 = fig.text(0.5, 0.52, "", fontsize=22, fontweight="bold",
                    color=INK, ha="center")
    end2 = fig.text(0.5, 0.45, "", fontsize=12, color=MUTED, ha="center")
    veil = fig.add_axes([0, 0, 1, 1], zorder=10)
    veil.axis("off")
    veil_patch = veil.add_patch(plt.Rectangle((0, 0), 1, 1, color=SURFACE, alpha=0))

    writer = FFMpegWriter(fps=FPS, bitrate=4000,
                          extra_args=["-pix_fmt", "yuv420p"])
    path = OUT / T["file"]
    with writer.saving(fig, path, dpi=150):
        for f in range(frames):
            t = f / FPS
            # 1: baslik
            if t < t_title:
                a = ease(t / 0.8) if t < t_title - 0.8 else ease((t_title - t) / 0.8)
                title.set_alpha(a); sub.set_alpha(a * 0.9)
            else:
                title.set_alpha(0); sub.set_alpha(0)
            # 2: eksenler
            if t >= t_title:
                a = ease((t - t_title) / 1.2)
                xlab.set_alpha(a); ylab.set_alpha(a)
            # 3: ekoller
            for i, c in enumerate(order):
                t0 = t_title + t_axes + i * t_school
                if t < t0:
                    continue
                prog = (t - t0) / 1.0
                sub_df = df[df["cluster"] == c].reset_index(drop=True)
                for j, r in sub_df.iterrows():
                    tj = prog - j * 0.06
                    a = ease(tj)
                    dots[r["team"]][0].set_sizes([90 * a])
                    labels[r["team"]].set_alpha(a * 0.9)
                if t < t0 + t_school - 0.3:
                    card_name.set_text(T["schools"][c][0])
                    card_name.set_color(COLORS[c])
                    card_desc.set_text(T["schools"][c][1])
            # 4: yari finalistler
            t4 = t_title + t_axes + 4 * t_school
            if t >= t4:
                a = ease((t - t4) / 1.0)
                card_name.set_text(""); card_desc.set_text("")
                semis_txt.set_text(T["semis"]); semis_txt.set_alpha(a)
                for team, (d, c) in dots.items():
                    if team in SEMIS:
                        d.set_sizes([90 + 130 * a])
                        d.set_edgecolor(INK)
                        labels[team].set_fontsize(7.5 + 3 * a)
                        labels[team].set_fontweight("bold")
                        labels[team].set_color(INK)
                        labels[team].set_alpha(1)
                    else:
                        d.set_alpha(1 - 0.75 * a)
                        labels[team].set_alpha(0.9 - 0.75 * a)
            # 5: kapanis
            t5 = t4 + t_semis
            if t >= t5:
                a = ease((t - t5) / 1.0)
                veil_patch.set_alpha(0.92 * a)
                end1.set_text(T["end1"]); end1.set_alpha(a)
                end2.set_text(T["end2"]); end2.set_alpha(a)
                end1.set_zorder(11); end2.set_zorder(11)
                semis_txt.set_alpha(1 - a)
            writer.grab_frame()
    plt.close(fig)
    print("Yazildi:", path)

if __name__ == "__main__":
    for lang in ("tr", "en"):
        make_video(lang)
