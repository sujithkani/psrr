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

#INI LOADER
def load_ini(path):
    cfg=configparser.RawConfigParser()
    cfg.read(path)
    freqs,psrr_vals,severities=[],[],[]
    i=1
    
    while cfg.has_section(f"row_{i}"):
        r=cfg[f"row_{i}"]
        freqs.append(float(r.get("frequency_hz",0)))
        psrr_vals.append(float(r.get("psrr_db",0)))
        severities.append(r.get("severity","NORMAL"))
        i += 1

    total=len(psrr_vals)
    counts={"NORMAL": severities.count("NORMAL"),"WARNING": severities.count("WARNING"),"CRITICAL": severities.count("CRITICAL")}
    return freqs,psrr_vals,severities,counts,total

#ANALYSIS
def analyse(freqs,psrr_vals,counts,total):
    best_idx=psrr_vals.index(min(psrr_vals))
    worst_idx=psrr_vals.index(max(psrr_vals))
    avg=sum(psrr_vals)/total if total else 0
    warn_pct=counts["WARNING"]/total * 100 if total else 0
    crit_pct=counts["CRITICAL"]/total * 100 if total else 0

    if crit_pct>40:
        verdict="POOR"
    elif crit_pct>15 or warn_pct>30:
        verdict="MARGINAL"
    elif warn_pct>10:
        verdict="ACCEPTABLE"
    else:
        verdict="GOOD"

    return {"best_psrr": psrr_vals[best_idx],"worst_psrr": psrr_vals[worst_idx],"best_freq": freqs[best_idx],"worst_freq": freqs[worst_idx],"avg": avg,"warn_pct": warn_pct,"crit_pct": crit_pct,"verdict": verdict}

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

#PDF
class PDF(FPDF):
    pass

def build_pdf(stats,counts,chart_path,pie_path,output):
    pdf=PDF()
    pdf.add_page()
    pdf.set_font("Arial","B",16)
    pdf.cell(0,10,"PSRR Report",ln=True)
    pdf.set_font("Arial","",10)
    pdf.cell(0,8,f"Generated: {datetime.now()}",ln=True)
    pdf.ln(5)
    pdf.cell(0,8,f"Best PSRR: {stats['best_psrr']:.2f} dB",ln=True)
    pdf.cell(0,8,f"Worst PSRR: {stats['worst_psrr']:.2f} dB",ln=True)
    pdf.cell(0,8,f"Average: {stats['avg']:.2f} dB",ln=True)
    pdf.cell(0,8,f"Verdict: {stats['verdict']}",ln=True)
    pdf.ln(10)
    pdf.image(chart_path,w=180)
    pdf.ln(5)
    pdf.image(pie_path,w=100)
    pdf.output(output)

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
        src=self.src.get()
        dst=self.dst.get()
        try:
            if src.endswith(".csv"):
                freqs,psrr_vals,sev,counts,total=load_csv(src)
            elif src.endswith(".ini"):
                freqs,psrr_vals,sev,counts,total=load_ini(src)
            else:
                messagebox.showerror("Error","Invalid file")
                return
            stats=analyse(freqs,psrr_vals,counts,total)
            make_psrr_chart(freqs,psrr_vals,"chart.png")
            make_pie_chart(counts,"pie.png")
            build_pdf(stats,counts,"chart.png","pie.png",dst)
            os.remove("chart.png")
            os.remove("pie.png")
            messagebox.showinfo("Success","PDF Generated!")

        except Exception as e:
            messagebox.showerror("Error",str(e))

root=tk.Tk()
app=App(root)
root.mainloop()
