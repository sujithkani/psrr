import configparser
import os
import sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from fpdf import FPDF
from datetime import datetime

# ============================================================
#  PSRR PDF Report Generator  -  Medium Blue & White Theme
#  Usage:
#    python psrr_report_bw.py                  <- picks latest INI
#    python psrr_report_bw.py psrr_run_0.ini   <- specific file
# ============================================================

# ── Colour palette ───────────────────────────────────────────
C_WHITE       = (255, 255, 255)
C_PAGE        = (248, 251, 255)   # near-white page background
C_BLUE        = (30,  100, 200)   # medium blue - primary
C_BLUE_MED    = (60,  130, 220)   # slightly lighter blue
C_BLUE_LIGHT  = (210, 228, 248)   # pale blue for card fills
C_BLUE_PALE   = (235, 243, 252)   # very pale blue rows
C_BLUE_LINE   = (170, 205, 240)   # border colour
C_TEXT_DARK   = (20,  40,  80)    # dark blue-tinted text
C_TEXT_MID    = (80,  110, 160)   # secondary text
C_TEXT_LIGHT  = (140, 170, 205)   # muted labels

def find_latest_ini():
    files = []
    for f in os.listdir("."):
        if f.startswith("psrr_run_") and f.endswith(".ini"):
            try:
                n = int(f.replace("psrr_run_","").replace(".ini",""))
                files.append((n, f))
            except ValueError:
                pass
    return sorted(files)[-1][1] if files else None

def load_ini(path):
    cfg = configparser.RawConfigParser()
    cfg.read(path)
    return cfg

def analyse(cfg):
    info   = dict(cfg["run_info"])   if cfg.has_section("run_info")   else {}
    thresh = dict(cfg["thresholds"]) if cfg.has_section("thresholds") else {}

    freqs, psrr_vals, severities = [], [], []
    i = 1
    while cfg.has_section(f"row_{i}"):
        r = dict(cfg[f"row_{i}"])
        freqs.append(float(r.get("frequency_hz", 0)))
        psrr_vals.append(float(r.get("psrr_db", 0)))
        severities.append(r.get("severity","NORMAL").strip())
        i += 1
    total  = len(psrr_vals)
    counts = {s: severities.count(s) for s in ["NORMAL","WARNING","CRITICAL"]}
    best_idx  = psrr_vals.index(min(psrr_vals))
    worst_idx = psrr_vals.index(max(psrr_vals))
    avg       = sum(psrr_vals)/total if total else 0
    crit_pct  = counts["CRITICAL"]/total*100 if total else 0
    warn_pct  = counts["WARNING"] /total*100 if total else 0

    if crit_pct > 40:
        verdict = "POOR"
        vtext   = ("The circuit shows critically degraded PSRR across a large portion "
                   "of the frequency sweep. High-frequency ripple rejection has failed. "
                   "Hardware-level intervention is required before deployment.")
    elif crit_pct > 15 or warn_pct > 30:
        verdict = "MARGINAL"
        vtext   = ("The circuit meets minimum requirements at low frequencies but degrades "
                   "significantly at higher frequencies. Suitable for low-frequency "
                   "applications only. Improvements are recommended.")
    elif warn_pct > 10:
        verdict = "ACCEPTABLE"
        vtext   = ("PSRR performance is within tolerable limits for most general-purpose "
                   "applications. Minor improvements could tighten the margin.")
    else:
        verdict = "GOOD"
        vtext   = ("The circuit demonstrates strong ripple rejection across the sweep. "
                   "Performance is within specification and suitable for mixed-signal "
                   "and audio applications.")
    recs = []
    if crit_pct > 20:
        recs.append(("Increase output capacitor value",
                     "Replace with a 47uF or 100uF low-ESR ceramic (X5R/X7R). "
                     "Larger capacitance improves high-frequency PSRR by providing "
                     "local charge storage that buffers against supply ripple."))
        recs.append(("Add feed-forward capacitor across feedback resistor R1",
                     "Place a 10-100 pF capacitor in parallel with the upper feedback "
                     "resistor. This extends PSRR bandwidth by boosting loop gain at "
                     "high frequencies (ref: TI Application Note SLVA118)."))
    if warn_pct > 15:
        recs.append(("Add input bypass capacitor",
                     "Place a 100 nF ceramic capacitor as close as possible to the "
                     "supply input pin. Pair with a 10 uF bulk capacitor for "
                     "low-frequency decoupling."))
    if float(info.get("ripple_mv",100)) > 50:
        recs.append(("Reduce source ripple amplitude",
                     f"Test used {info.get('ripple_mv','100')} mV ripple. "
                     "An LC pre-filter before the regulator reduces input ripple, "
                     "improving effective system PSRR across all frequencies."))
    if not recs:
        recs.append(("Consider a higher-performance regulator",
                     "Performance is good. For tighter margins consider TPS7A47 or "
                     "LT3045 which maintain -80 dB PSRR up to 1 MHz. Also review "
                     "PCB layout: star grounding and short output capacitor traces."))
    return dict(
        info=info, thresh=thresh,
        freqs=freqs, psrr_vals=psrr_vals, severities=severities,
        counts=counts, total=total,
        best_psrr=psrr_vals[best_idx], worst_psrr=psrr_vals[worst_idx],
        best_freq=freqs[best_idx],     worst_freq=freqs[worst_idx],
        avg=avg, crit_pct=crit_pct, warn_pct=warn_pct,
        verdict=verdict, vtext=vtext, recs=recs,
    )


def make_line_chart(a, path):
    tw = float(a["thresh"].get("warning_db",  -35))
    tc = float(a["thresh"].get("critical_db", -20))
    fig, ax = plt.subplots(figsize=(10, 3.4), facecolor="white")
    ax.set_facecolor("#f5f9ff")
    step = max(1, len(a["psrr_vals"]) // 150)
    cv   = a["psrr_vals"][::step]
    ax.plot(cv, color="#1e64c8", linewidth=1.8, zorder=3)
    ax.scatter(range(len(cv)), cv, c="#1e64c8", s=14, zorder=4)
    ax.axhline(tw, color="#3c82dc", linewidth=1.2, linestyle="--",label=f"Warning ({tw} dB)")
    ax.axhline(tc, color="#0a3070", linewidth=1.2, linestyle="--",label=f"Critical ({tc} dB)")
    ax.fill_between(range(len(cv)), cv, min(cv),alpha=0.06, color="#1e64c8")
    ax.set_xlabel("Iteration", color="#507090", fontsize=9)
    ax.set_ylabel("PSRR (dB)", color="#507090", fontsize=9)
    ax.tick_params(colors="#7090b0", labelsize=8)
    for sp in ax.spines.values():
        sp.set_edgecolor("#b0cce8")
    ax.grid(color="#d8eaf8", linewidth=0.5)
    ax.legend(fontsize=8, facecolor="white", edgecolor="#b0cce8",
              labelcolor="#3c5a8c")
    plt.tight_layout(pad=0.4)
    plt.savefig(path, dpi=140, bbox_inches="tight", facecolor="white")
    plt.close()


def make_bar_chart(a, path):
    labels = ["NORMAL","WARNING","CRITICAL"]
    values = [a["counts"][s] for s in labels]
    colors = ["#3c82dc","#1e64c8","#0a3070"]
    fig, ax = plt.subplots(figsize=(5.5, 2.8), facecolor="white")
    ax.set_facecolor("#f5f9ff")
    bars = ax.bar(labels, values, color=colors, width=0.5,
                  edgecolor="white", linewidth=1)
    for bar, val in zip(bars, values):
        ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.4,
                str(val), ha="center", va="bottom",
                fontsize=9, color="#0a3070", fontweight="bold")
    ax.set_ylabel("Count", color="#507090", fontsize=9)
    ax.tick_params(colors="#7090b0", labelsize=8)
    for sp in ax.spines.values():
        sp.set_edgecolor("#b0cce8")
    ax.grid(axis="y", color="#d8eaf8", linewidth=0.5)
    plt.tight_layout(pad=0.4)
    plt.savefig(path, dpi=140, bbox_inches="tight", facecolor="white")
    plt.close()

def make_distribution_chart(a, path):
    import numpy as np
    data = np.array(a["psrr_vals"])
    fig, ax = plt.subplots(figsize=(5.5, 2.8), facecolor="white")
    ax.set_facecolor("#f5f9ff")
    bins = min(8, max(4, len(data)//2))   # adaptive bins
    ax.hist(data, bins=bins, density=True,
            color="#1e64c8", alpha=0.5, edgecolor="white")
    mu = np.mean(data)
    sigma = np.std(data)
    x = np.linspace(min(data), max(data), 200)
    y = (1/(sigma*np.sqrt(2*np.pi))) * np.exp(-(x-mu)**2/(2*sigma**2))
    ax.plot(x, y, color="#0a3070", linewidth=2)
    ax.set_xlabel("PSRR (dB)", fontsize=9, color="#507090")
    ax.set_ylabel("Density", fontsize=9, color="#507090")
    ax.tick_params(colors="#7090b0", labelsize=8)
    for sp in ax.spines.values():
        sp.set_edgecolor("#b0cce8")
    ax.grid(axis="y", color="#d8eaf8", linewidth=0.5)
    plt.tight_layout(pad=0.4)
    plt.savefig(path, dpi=140, bbox_inches="tight")
    plt.close()

class PDF(FPDF):
    def __init__(self, run_number, generated):
        super().__init__()
        self.run_number = run_number
        self.generated  = generated
        self.set_auto_page_break(auto=True, margin=16)
        self.set_margins(18, 16, 18)

    def header(self):
        # medium blue header bar
        self.set_fill_color(*C_BLUE)
        self.rect(0, 0, 210, 10, "F")
        self.set_font("Helvetica", "", 7)
        self.set_text_color(*C_WHITE)
        self.set_xy(18, 2)
        self.cell(87, 6, "PSRR ANALYSIS REPORT", align="L")
        self.set_xy(105, 2)
        self.cell(87, 6,
                  f"Run #{self.run_number}  |  {self.generated}",
                  align="R")
        self.set_y(14)

    def footer(self):
        self.set_fill_color(*C_BLUE_LIGHT)
        self.rect(0, 287, 210, 10, "F")
        self.set_y(-10)
        self.set_font("Helvetica", "", 7)
        self.set_text_color(*C_TEXT_MID)
        self.cell(87, 6, "KCG College of Technology  |  Department of Electrical and Electronic Engineering")
        self.cell(0, 6,
                  f"Page {self.page_no()}  |  PSRR Monitor",
                  align="R")

    def section_label(self, text):
        y = self.get_y()
        # left accent line only — no filled rect
        self.set_draw_color(*C_BLUE)
        self.set_line_width(2.5)
        self.line(18, y+1, 18, y+8)
        self.set_line_width(0.2)
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*C_BLUE)
        self.set_xy(23, y)
        self.cell(0, 9, text.upper())
        self.ln(1)
        self.set_draw_color(*C_BLUE_LINE)
        self.set_line_width(0.2)
        self.line(18, self.get_y(), 192, self.get_y())
        self.ln(8)

    def metric_card(self, x, y, w, h, label, value, unit, highlight=False):
        if highlight:
            self.set_fill_color(*C_BLUE)
            txt_lbl = C_BLUE_LIGHT
            txt_val = C_WHITE
            txt_unit= C_BLUE_LIGHT
        else:
            self.set_fill_color(*C_BLUE_LIGHT)
            txt_lbl = C_TEXT_MID
            txt_val = C_TEXT_DARK
            txt_unit= C_TEXT_MID
        self.set_draw_color(*C_BLUE_LINE)
        self.set_line_width(0.2)
        self.rect(x, y, w, h, "FD")
        self.set_font("Helvetica", "", 7)
        self.set_text_color(*txt_lbl)
        self.set_xy(x+3, y+3)
        self.cell(w-6, 4, label)
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(*txt_val)
        self.set_xy(x+3, y+8)
        self.cell(w-6, 6, str(value))
        self.set_font("Helvetica", "", 7)
        self.set_text_color(*txt_unit)
        self.set_xy(x+3, y+16)
        self.cell(w-6, 4, unit)

    def sev_bar(self, label, count, total, y):
        pct = count/total*100 if total else 0
        bw  = pct/100 * 118
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(*C_TEXT_DARK)
        self.set_xy(18, y)
        self.cell(38, 7, label)
        self.set_fill_color(*C_BLUE_PALE)
        self.set_draw_color(*C_BLUE_LINE)
        self.set_line_width(0.2)
        self.rect(58, y+1.5, 118, 4.5, "FD")
        if bw > 0:
            self.set_fill_color(*C_BLUE_MED)
            self.rect(58, y+1.5, max(bw, 1.5), 4.5, "F")
            if bw > 20:
                self.set_font("Helvetica","B",6.5)
                self.set_text_color(*C_WHITE)
                self.set_xy(59, y+1.5)
                self.cell(bw-2, 4.5, f"{pct:.0f}%", align="L")
        self.set_font("Helvetica", "", 7.5)
        self.set_text_color(*C_TEXT_MID)
        self.set_xy(180, y)
        self.cell(0, 7, f"{count}  ({pct:.1f}%)")


def build_pdf(a, ini_path, line_path, bar_path, dist_path):
    info    = a["info"]
    thresh  = a["thresh"]
    counts  = a["counts"]
    now     = datetime.now().strftime("%d %B %Y, %H:%M")
    run_num = info.get("run_number","0")
    pdf = PDF(run_number=run_num, generated=now)
    # ═══════════ PAGE 1 ═══════════
    pdf.add_page()
    pdf.set_fill_color(*C_PAGE)
    pdf.rect(0, 0, 210, 297, "F")
    pdf.set_fill_color(*C_BLUE)
    pdf.rect(0, 10, 210, 28, "F")
    pdf.set_font("Helvetica", "", 7.5)
    pdf.set_text_color(*C_BLUE_LIGHT)
    pdf.set_xy(18, 13)
    pdf.cell(0, 5, "PSRR ANALYSIS REPORT")
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(*C_WHITE)
    pdf.set_xy(18, 19)
    pdf.cell(140, 8,
             f"Run #{run_num}  -  LDO Performance Analysis")
    pdf.set_font("Helvetica", "", 7.5)
    pdf.set_text_color(*C_BLUE_LIGHT)
    pdf.set_xy(18, 29)
    #pdf.cell(0, 5,f"Generated {now}   |   "f"Vin: {info.get('vin_v','?')}V    "f"Vout: {info.get('vout_v','?')}V   |   "f"{info.get('total_points','?')} data points")
    # verdict badge — white box on blue header
    pdf.set_fill_color(*C_WHITE)
    pdf.set_draw_color(*C_BLUE_LIGHT)
    pdf.set_line_width(0.3)
    pdf.rect(155, 13, 37, 18, "FD")
    pdf.set_font("Helvetica", "", 6.5)
    pdf.set_text_color(*C_TEXT_MID)
    pdf.set_xy(155, 15.5)
    pdf.cell(37, 4, "VERDICT", align="C")
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*C_BLUE)
    pdf.set_xy(155, 21)
    pdf.cell(37, 6, a["verdict"], align="C")
    pdf.set_y(44)
    pdf.section_label("Key Metrics")
    mw, mh, gap = 28, 22, 2.4
    my = pdf.get_y()
    metrics = [
        ("Best PSRR",    f"{a['best_psrr']:.1f} dB",
         f"at {a['best_freq']:.0f} Hz",     False),
        ("Worst PSRR",   f"{a['worst_psrr']:.1f} dB",
         f"at {a['worst_freq']:.0f} Hz",    True),
        ("Average PSRR", f"{a['avg']:.1f} dB",
         "across sweep",                    False),
        ("NORMAL",       str(counts["NORMAL"]),
         f"{counts['NORMAL']/a['total']*100:.0f}% of sweep", False),
        ("WARNING",      str(counts["WARNING"]),
         f"{a['warn_pct']:.0f}% of sweep",  False),
        ("CRITICAL",     str(counts["CRITICAL"]),
         f"{a['crit_pct']:.0f}% of sweep",  True),
    ]
    for i,(lbl,val,unit,hi) in enumerate(metrics):
        pdf.metric_card(18+i*(mw+gap), my, mw, mh, lbl, val, unit, hi)
    pdf.set_y(my + mh + 12)
    pdf.section_label("PSRR vs Frequency Sweep")
    cy = pdf.get_y()
    pdf.set_fill_color(*C_WHITE)
    pdf.set_draw_color(*C_BLUE_LINE)
    pdf.set_line_width(0.3)
    pdf.rect(18, cy, 174, 66, "FD")
    pdf.image(line_path, x=19, y=cy+1, w=172, h=64)
    pdf.set_y(cy + 78)
    pdf.section_label("Severity Breakdown")
    for sev in ["NORMAL","WARNING","CRITICAL"]:
        sy = pdf.get_y()
        pdf.sev_bar(sev, counts[sev], a["total"], sy)
        pdf.ln(12)
    pdf.ln(3)
    pdf.section_label("Overall Assessment")
    vy = pdf.get_y()
    vlines = pdf.multi_cell(154, 4.2, a["vtext"],dry_run=True, output="LINES")
    vbox_h = 10 + 6 + len(vlines)*4.5 + 12
    pdf.set_fill_color(*C_BLUE_LIGHT)
    pdf.set_draw_color(*C_BLUE_MED)
    pdf.set_line_width(0.3)
    pdf.rect(18, vy, 174, vbox_h, "FD")
    pdf.set_draw_color(*C_BLUE)
    pdf.set_line_width(3)
    pdf.line(18, vy, 18, vy+vbox_h)
    pdf.set_line_width(0.3)
    pdf.set_font("Helvetica", "", 6.5)
    pdf.set_text_color(*C_TEXT_MID)
    pdf.set_xy(25, vy+4)
    pdf.cell(0, 4, "CIRCUIT HEALTH VERDICT")
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*C_BLUE)
    pdf.set_xy(25, vy+9)
    pdf.cell(0, 5, a["verdict"])
    pdf.set_font("Helvetica", "", 7.5)
    pdf.set_text_color(*C_TEXT_DARK)
    pdf.set_xy(25, vy+16)
    pdf.multi_cell(154, 4.2, a["vtext"])
    pdf.set_y(vy + vbox_h + 12)
    # ═══════════ PAGE 2 ═══════════
    pdf.add_page()
    pdf.set_fill_color(*C_PAGE)
    pdf.rect(0, 0, 210, 297, "F")
    pdf.section_label("Recommendations for Improvement")
    for idx,(title,detail) in enumerate(a["recs"]):
        ry = pdf.get_y()
        lines = pdf.multi_cell(148, 4, detail,dry_run=True, output="LINES")
        rh = 12 + len(lines)*4 + 4
        if ry + rh > 272:
            pdf.add_page()
            pdf.set_fill_color(*C_PAGE)
            pdf.rect(0,0,210,297,"F")
            ry = pdf.get_y()
        # white card with blue border
        pdf.set_fill_color(*C_WHITE)
        pdf.set_draw_color(*C_BLUE_LINE)
        pdf.set_line_width(0.3)
        pdf.rect(18, ry, 174, rh, "FD")
        # left accent line only — no overlapping fill
        pdf.set_draw_color(*C_BLUE)
        pdf.set_line_width(5)
        pdf.line(18, ry, 18, ry+rh)
        pdf.set_line_width(0.3)
        # number — sits in left margin, no background box
        pdf.set_font("Helvetica","B",11)
        pdf.set_text_color(*C_BLUE_MED)
        pdf.set_xy(21, ry + rh/2 - 5)
        pdf.cell(14, 7, f"{idx+1:02d}", align="C")
        # title
        pdf.set_font("Helvetica","B",8.5)
        pdf.set_text_color(*C_TEXT_DARK)
        pdf.set_xy(38, ry+4)
        pdf.cell(0, 5, title)
        # detail
        pdf.set_font("Helvetica","",7.5)
        pdf.set_text_color(*C_TEXT_MID)
        pdf.set_xy(38, ry+11)
        pdf.multi_cell(150, 4, detail)
        pdf.ln(5)

    pdf.ln(2)
    pdf.section_label("Severity Distribution")
    by = pdf.get_y()
    pdf.set_fill_color(*C_WHITE)
    pdf.set_draw_color(*C_BLUE_LINE)
    pdf.set_line_width(0.3)
    pdf.rect(18, by, 174, 60, "FD")
    pdf.image(bar_path, x=48, y=by+3, w=116, h=54)
    pdf.set_y(by + 66)
    pdf.ln(4)
    pdf.section_label("PSRR Value Distribution")
    dy = pdf.get_y()
    pdf.set_fill_color(*C_WHITE)
    pdf.set_draw_color(*C_BLUE_LINE)
    pdf.set_line_width(0.3)
    pdf.rect(18, dy, 174, 52, "FD")
    pdf.image(dist_path, x=48, y=dy+2, w=116, h=48)
    pdf.set_y(dy + 56)
    pdf.set_font("Helvetica", "", 7.5)
    pdf.set_text_color(*C_TEXT_MID)
    return pdf

def main():
    if len(sys.argv) > 1:
        ini_path = sys.argv[1]
        if not os.path.exists(ini_path):
            print(f"\n  Error: File not found: {ini_path}\n")
            sys.exit(1)
    else:
        ini_path = find_latest_ini()
        if not ini_path:
            print("\n  No psrr_run_*.ini files found. Run psrr_simulator.py first.\n")
            sys.exit(1)
        print(f"\n  No file specified - using latest: {ini_path}")

    print(f"\n  Reading {ini_path}...")
    cfg = load_ini(ini_path)
    a   = analyse(cfg)
    print(f"  Analysing {a['total']} data rows...")

    run_num   = a["info"].get("run_number","0")
    import tempfile


    tmp_dir = tempfile.gettempdir()
    run_num = a["info"].get("run_number", "0")
    line_path = os.path.join(tmp_dir, f"psrr_line_{run_num}.png")
    bar_path  = os.path.join(tmp_dir, f"psrr_bar_{run_num}.png")
    dist_path = os.path.join(tmp_dir, f"psrr_dist_{run_num}.png")

    print("  Generating charts...")
    make_line_chart(a, line_path)
    make_bar_chart(a, bar_path)
    dist_path = os.path.join(tmp_dir, f"psrr_dist_{run_num}.png")
    make_distribution_chart(a, dist_path)

    print("  Building PDF...")
    out_path = f"psrr_report_run_{run_num}.pdf"
    pdf = build_pdf(a, ini_path, line_path, bar_path, dist_path)
    pdf.output(out_path)
    for p in [line_path, bar_path, dist_path]:
        if os.path.exists(p): os.remove(p)

    print(f"\n  Report saved: {os.path.abspath(out_path)}")
    print(f"    Verdict   : {a['verdict']}")
    print(f"    Best PSRR : {a['best_psrr']:.2f} dB  at {a['best_freq']:.0f} Hz")
    print(f"    Worst PSRR: {a['worst_psrr']:.2f} dB  at {a['worst_freq']:.0f} Hz")
    print(f"    NORMAL    : {a['counts']['NORMAL']} rows")
    print(f"    WARNING   : {a['counts']['WARNING']} rows")
    print(f"    CRITICAL  : {a['counts']['CRITICAL']} rows\n")


import tkinter as tk
from tkinter import filedialog,ttk,messagebox
import os,csv,configparser,sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from fpdf import FPDF
from datetime import datetime

#CSV LOADER
def load_csv(path):
    freqs,psrr_vals,severities=[],[],[]
    with open(path) as f:
        reader=csv.DictReader(f)
        for row in reader:
            freqs.append(float(row["frequency_hz"]))
            psrr_vals.append(float(row["psrr_db"]))
            severities.append(row["severity"])
    total=len(psrr_vals)
    counts={"NORMAL": severities.count("NORMAL"),"WARNING": severities.count("WARNING"),"CRITICAL": severities.count("CRITICAL")}
    return freqs,psrr_vals,severities,counts,total

#CHARTS
def make_psrr_chart(freqs,psrr_vals,path):
    plt.figure()
    plt.semilogx(freqs,psrr_vals)
    plt.xlabel("Frequency (Hz)")
    plt.ylabel("PSRR (dB)")
    plt.grid(True)
    plt.savefig(path)
    plt.close()

def make_pie_chart(counts,path):
    labels=counts.keys()
    sizes=counts.values()
    plt.figure()
    plt.pie(sizes,labels=labels,autopct="%1.0f%%")
    plt.savefig(path)
    plt.close()

#UI
class App:
    def __init__(self,root):
        self.root=root
        root.title("PSRR Report Generator")
        root.geometry("500x220")
        self.src=tk.StringVar()
        self.dst=tk.StringVar()
        root.grid_columnconfigure(0,weight=1)
        # INPUT
        ttk.Label(root,text="Input (.ini/.csv)").grid(row=0,column=0,padx=10,pady=(10,2),sticky="w")
        ttk.Entry(root,textvariable=self.src).grid(row=1,column=0,padx=10,sticky="ew")
        ttk.Button(root,text="Browse",command=self.pick_src).grid(row=1,column=1,padx=(0,10))
        # OUTPUT
        ttk.Label(root,text="Output PDF").grid(row=2,column=0,padx=10,pady=(10,2),sticky="w")
        ttk.Entry(root,textvariable=self.dst).grid(row=3,column=0,padx=10,sticky="ew")
        ttk.Button(root,text="Browse",command=self.pick_dst).grid(row=3,column=1,padx=(0,10))
        self.type_label=ttk.Label(root,text="Type: --")
        self.type_label.grid(row=5,column=0,columnspan=2,pady=5)
        # EXPORT
        self.btn=ttk.Button(root,text="Export",command=self.run,state="disabled")
        self.btn.grid(row=4,column=0,columnspan=2,pady=15)
        self.src.trace_add("write",self.check_enable)
        self.dst.trace_add("write",self.check_enable)

    def pick_src(self):
        path=filedialog.askopenfilename(filetypes=[("Data","*.ini *.csv")])
        if path:
            self.src.set(path)
            if path.endswith(".csv"):
                self.type_label.config(text="Type: CSV detected")
            elif path.endswith(".ini"):
                self.type_label.config(text="Type: INI detected")
            else:
                self.type_label.config(text="Type: Unknown")

    def pick_dst(self):
        path=filedialog.asksaveasfilename(defaultextension=".pdf")
        if path:
            self.dst.set(path)

    def check_enable(self,*args):
        if self.src.get() and self.dst.get():
            self.btn.config(state="normal")
        else:
            self.btn.config(state="disabled")

    def run(self):
        try:
            src = self.src.get()
            dst = self.dst.get()
            # ---- LOAD ----
            if src.endswith(".ini"):
                cfg = load_ini(src)

            elif src.endswith(".csv"):
                cfg = configparser.RawConfigParser()
                cfg.add_section("run_info")
                cfg.set("run_info", "run_number", "")

                with open(src) as f:
                    reader = csv.DictReader(f)
                    for i, row in enumerate(reader, start=1):
                        sec = f"row_{i}"
                        cfg.add_section(sec)
                        cfg.set(sec, "frequency_hz", row["frequency_hz"])
                        cfg.set(sec, "psrr_db", row["psrr_db"])
                        cfg.set(sec, "severity", row["severity"])
            else:
                messagebox.showerror("Error","Invalid file")
                return
            # ---- ANALYSE ----
            a = analyse(cfg)
            # ---- CHARTS ----
            import tempfile

            tmp_dir = tempfile.gettempdir()
            run_num = a["info"].get("run_number", "0")
            line_path = os.path.join(tmp_dir, f"psrr_line_{run_num}.png")
            bar_path  = os.path.join(tmp_dir, f"psrr_bar_{run_num}.png")
            dist_path = os.path.join(tmp_dir, f"psrr_dist_{run_num}.png")
            make_distribution_chart(a, dist_path)
            make_line_chart(a, line_path)
            make_bar_chart(a, bar_path)
            # ---- PDF ----
            pdf = build_pdf(a, src, line_path, bar_path, dist_path)
            pdf.output(dst)
            os.remove(line_path)
            os.remove(bar_path)
            os.remove(dist_path)
            messagebox.showinfo("Success","Report generated")
        except Exception as e:
            messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        main()   # CLI mode
    else:
        root = tk.Tk()
        app = App(root)
        root.mainloop()
