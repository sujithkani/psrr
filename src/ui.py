import tkinter as tk
from tkinter import ttk
import socket
import os
import csv
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from simulation import generate_freqs, make_row
from config_loader import load_network_config
from config_loader import save_network_config
import sys
FIXED_INTERVAL_MS = 100

def get_base_path():
    if getattr(sys, 'frozen', False):
        # Running as EXE
        return os.path.dirname(sys.executable)
    else:
        # Running as script
        return os.path.dirname(os.path.dirname(__file__))

class PSRR_GUI:
    def __init__(self, root):
        self.root=root
        root.title("PSRR Simulator")
        root.geometry("950x650")
        root.rowconfigure(1, weight=1)
        root.columnconfigure(0, weight=1)
        self.streaming=False
        net = load_network_config()
        self.default_ip = net["ip"]
        self.default_port = net["port"]

        #UDP NETWORK SETTINGS
        self.sock=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        #NOTEBOOK
        notebook=ttk.Notebook(root)
        notebook.grid(row=0, column=0, sticky="ew")
        self.tab_psrr=ttk.Frame(notebook)
        self.tab_stream=ttk.Frame(notebook)
        notebook.add(self.tab_psrr, text="PSRR Config")
        notebook.add(self.tab_stream, text="Stream Settings")
        self.build_psrr_page()
        self.build_stream_page()

        #PLOT
        plot_frame=ttk.Frame(root)
        plot_frame.grid(row=1, column=0, sticky="nsew")
        plot_frame.rowconfigure(0, weight=1)
        plot_frame.columnconfigure(0, weight=1)
        self.fig=Figure(figsize=(6,4))
        self.ax=self.fig.add_subplot(111)
        self.canvas=FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")

        #LIVE MONITOR
        monitor_frame=ttk.Frame(root)
        monitor_frame.grid(row=2, column=0, pady=5)
        self.freq_var=tk.StringVar(value="Frequency: -- Hz")
        self.psrr_var=tk.StringVar(value="PSRR: -- dB")
        self.severity_var=tk.StringVar(value="Status: --")
        ttk.Label(monitor_frame,textvariable=self.freq_var).grid(row=0,column=0,padx=10)
        ttk.Label(monitor_frame,textvariable=self.psrr_var).grid(row=0,column=1,padx=10)
        ttk.Label(monitor_frame,textvariable=self.severity_var).grid(row=0,column=2,padx=10)

        #COUNTERS
        counter_frame=ttk.Frame(root)
        counter_frame.grid(row=3, column=0)
        self.normal_var=tk.StringVar(value="NORMAL:0")
        self.warn_var=tk.StringVar(value="WARNING:0")
        self.crit_var=tk.StringVar(value="CRITICAL:0")
        ttk.Label(counter_frame,textvariable=self.normal_var,foreground="green").grid(row=0,column=0,padx=15)
        ttk.Label(counter_frame,textvariable=self.warn_var,foreground="orange").grid(row=0,column=1,padx=15)
        ttk.Label(counter_frame,textvariable=self.crit_var,foreground="red").grid(row=0,column=2,padx=15)

        #BUTTONS
        button_frame=ttk.Frame(root)
        button_frame.grid(row=4, column=0, pady=10)
        self.sim_btn=ttk.Button(button_frame,text="Simulate",command=self.simulate)
        self.sim_btn.grid(row=0,column=0,padx=10)
        self.stream_btn=ttk.Button(button_frame,text="Stream",command=self.stream)
        self.stream_btn.grid(row=0,column=1,padx=10)
        self.stop_btn=ttk.Button(button_frame,text="Stop",command=self.stop_stream,state="disabled")
        self.stop_btn.grid(row=0,column=3,padx=10)
        
        #PROGRESS BAR
        self.progress=ttk.Progressbar(root,orient="horizontal",length=500,mode="determinate")
        self.progress.grid(row=5,column=0,pady=10)
        
    #UDP SENDER
    """
    def send_udp(self, row, idx, total):
        packet=(f"{idx+1}/{total},"
            f"{row['frequency_hz']},"
            f"{row['psrr_db']},"
            f"{row['vin_ac_v']},"
            f"{row['vout_ac_v']},"
            f"{row['severity']}"
        )
        self.sock.sendto(packet.encode(),(self.settings["ip"],self.settings["port"]))
    """
    def send_udp(self, row, idx, total):
        packet = (f"{idx+1}/{total},"
                  f"{row['frequency_hz']},"
                  f"{row['psrr_db']},"
                  f"{row['vin_ac_v']},"
                  f"{row['vout_ac_v']},"
                  f"{row['severity']}")
        #self.sock.sendto(packet.encode(), (self.settings["ip"], self.settings["port"]))
        try:
            self.sock.sendto(packet.encode(), (self.settings["ip"], self.settings["port"]))
        except Exception as e:
            print("UDP ERROR:", e)
    
    #INPUT FIELD
    def add_field(self,parent,label,default,row):
        var=tk.StringVar(value=default)
        ttk.Label(parent,text=label).grid(row=row,column=0,sticky="w",padx=5,pady=4)
        ttk.Entry(parent,textvariable=var,width=15).grid(row=row,column=1)
        return var

    #PSRR PAGE
    def build_psrr_page(self):
        self.vin=self.add_field(self.tab_psrr,"Vin (V)","5",0)
        self.vout=self.add_field(self.tab_psrr,"Vout (V)","3.3",1)
        self.ripple=self.add_field(self.tab_psrr,"Ripple (V)","0.1",2)
        self.fstart=self.add_field(self.tab_psrr,"Start Frequency (Hz)","10",3)
        self.fstop=self.add_field(self.tab_psrr,"Stop Frequency (Hz)","1000000",4)
        self.points=self.add_field(self.tab_psrr,"Points","200",5)
        self.psrr_base=self.add_field(self.tab_psrr,"PSRR Base (dB)","-55",6)
        self.noise=self.add_field(self.tab_psrr,"Noise Std","3",7)
        self.warn=self.add_field(self.tab_psrr,"Warning Threshold","-35",8)
        self.crit=self.add_field(self.tab_psrr,"Critical Threshold","-20",9)

    #STREAM PAGE
    def build_stream_page(self):
        self.filename=self.add_field(self.tab_stream,"CSV Filename","psrr_simulation.csv",0)
        #self.interval=self.add_field(self.tab_stream,"Stream Interval (s)","0.1",1)
        #self.ip=self.add_field(self.tab_stream,"Target IP","127.0.0.1",2)
        #self.port=self.add_field(self.tab_stream,"Target Port","6006",3)
        self.ip = self.add_field(self.tab_stream, "Target IP", self.default_ip, 2)
        self.port = self.add_field(self.tab_stream, "Target Port", str(self.default_port), 3)

    #SETTINGS
    def collect_settings(self):
        save_network_config(self.ip.get(), int(self.port.get()))
        return {
            "vin":float(self.vin.get()),
            "vout":float(self.vout.get()),
            "ripple":float(self.ripple.get()),
            "f_start":float(self.fstart.get()),
            "f_stop":float(self.fstop.get()),
            "points":int(self.points.get()),
            "psrr_base":float(self.psrr_base.get()),
            "noise_std":float(self.noise.get()),
            "t_warn":float(self.warn.get()),
            "t_crit":float(self.crit.get()),
            "filename":self.filename.get(),
            "interval":FIXED_INTERVAL_MS,
            "ip":self.ip.get(),
            "port":int(self.port.get())
        }

    #SIMULATE
    def simulate(self):
        self.settings=self.collect_settings()
        s=self.settings
        freqs=generate_freqs(s)
        psrr=[]
        normal=warn=crit=0
        for i,f in enumerate(freqs):
            row=make_row(i,f,s)
            self.send_udp(row, i, len(freqs))
            #self.send_udp(row)
            psrr.append(row["psrr_db"])
            if row["severity"]=="NORMAL":
                normal+=1
            elif row["severity"]=="WARNING":
                warn+=1
            else:
                crit+=1
        self.ax.clear()
        self.ax.semilogx(freqs,psrr,color="blue")
        self.ax.axhline(s["t_warn"],linestyle="--")
        self.ax.axhline(s["t_crit"],linestyle="--")
        self.ax.set_xlabel("Frequency (Hz)")
        self.ax.set_ylabel("PSRR (dB)")
        self.ax.grid(True)
        self.canvas.draw()
        self.normal_var.set(f"NORMAL:{normal}")
        self.warn_var.set(f"WARNING:{warn}")
        self.crit_var.set(f"CRITICAL:{crit}")

    #STREAM
    def stream(self):
        self.settings=self.collect_settings()
        from constants import FIELDNAMES
        BASE_DIR = get_base_path()
        RESULT_DIR = os.path.join(BASE_DIR, "result")
        os.makedirs(RESULT_DIR, exist_ok=True)
        self.filepath = os.path.join(RESULT_DIR, self.settings["filename"])
        self.csv_file = open(self.filepath, "w", newline="")
        self.writer = csv.DictWriter(self.csv_file, fieldnames=FIELDNAMES)
        self.writer.writeheader()
        self.freqs=generate_freqs(self.settings)
        self.index=0
        self.xdata=[]
        self.ydata=[]
        self.normal=0
        self.warn_count=0
        self.crit_count=0
        self.streaming=True
        self.progress["value"]=0
        self.progress["maximum"]=len(self.freqs)
        self.ax.clear()
        self.ax.set_xscale("log")
        self.sim_btn.config(state="disabled")
        self.stream_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.update_stream()

    def update_stream(self):
        if not self.streaming:
            return
        if self.index>=len(self.freqs):
            self.sim_btn.config(state="normal")
            self.stream_btn.config(state="normal")
            self.stop_btn.config(state="disabled")
            try:
                self.csv_file.close()
            except:
                pass
            return
        f=self.freqs[self.index]
        row=make_row(self.index,f,self.settings)
        self.writer.writerow(row)
        self.csv_file.flush()
        self.send_udp(row, self.index, len(self.freqs))
        #self.send_udp(row)
        self.xdata.append(f)
        self.ydata.append(row["psrr_db"])
        if row["severity"]=="NORMAL":
            self.normal+=1
        elif row["severity"]=="WARNING":
            self.warn_count+=1
        else:
            self.crit_count+=1
        self.normal_var.set(f"NORMAL:{self.normal}")
        self.warn_var.set(f"WARNING:{self.warn_count}")
        self.crit_var.set(f"CRITICAL:{self.crit_count}")
        self.freq_var.set(f"Frequency: {round(f,2)} Hz")
        self.psrr_var.set(f"PSRR: {row['psrr_db']} dB")
        self.severity_var.set(f"Status: {row['severity']}")
        self.ax.clear()
        self.ax.semilogx(self.xdata,self.ydata,color="blue")
        self.ax.axhline(self.settings["t_warn"],linestyle="--")
        self.ax.axhline(self.settings["t_crit"],linestyle="--")
        self.ax.set_xlabel("Frequency (Hz)")
        self.ax.set_ylabel("PSRR (dB)")
        self.ax.grid(True)
        self.canvas.draw()
        self.progress["value"]=self.index+1
        self.index+=1
        self.root.after(FIXED_INTERVAL_MS, self.update_stream)

    #STOP
    def stop_stream(self):
        self.streaming=False
        self.sim_btn.config(state="normal")
        self.stream_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        try:
            self.sock.close()
        except:
            pass
        if hasattr(self, "csv_file"):
            try:
                self.csv_file.close()
            except:
                pass
        self.sock=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

root=tk.Tk()
app=PSRR_GUI(root)
root.mainloop()
