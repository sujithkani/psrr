import csv
import time
import os
from constants import FIELDNAMES
from simulation import make_row, generate_freqs
from network_stream import PSRRStreamer

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
RESULT_DIR = os.path.join(BASE_DIR, "result")
os.makedirs(RESULT_DIR, exist_ok=True)

def run_batch(s):
    freqs=generate_freqs(s)
    rows=[]
    counts={"NORMAL":0,"WARNING":0,"CRITICAL":0}
    for i,f in enumerate(freqs):
        row=make_row(i,f,s)
        rows.append(row)
        counts[row["severity"]] += 1
    filepath=os.path.join(RESULT_DIR,s["filename"])
    with open(filepath, "w", newline="") as f:
        writer=csv.DictWriter(f,fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nWritten {len(rows)} rows -> {filepath}")
    print("\nResults:")
    print(f"NORMAL   : {counts['NORMAL']}")
    print(f"WARNING  : {counts['WARNING']}")
    print(f"CRITICAL : {counts['CRITICAL']}")
    return rows
"""
def run_stream(s):

    freqs=generate_freqs(s)
    print(f"\nLIVE STREAMING — writing every {s['interval']} seconds")
    print(f"LabVIEW file: {os.path.abspath(s['filename'])}\n")
    with open(s["filename"],"w",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=FIELDNAMES)
        writer.writeheader()
        for i,freq in enumerate(freqs):
            row=make_row(i,freq,s)
            writer.writerow(row)
            f.flush()
            print(
                f"[{i+1}/{s['points']}] "
                f"{freq:>10.1f} Hz "
                f"PSRR: {row['psrr_db']:>7.2f} dB "
                f"[{row['severity']}]"
            )
            time.sleep(s["interval"])
    print("\nStream complete.")
"""
def run_stream(s):
    freqs=generate_freqs(s)
    streamer=PSRRStreamer()
    print(f"\nLIVE STREAMING - writing every {s['interval']} seconds")
    print(f"LabVIEW file: {filepath}\n")
    filepath = os.path.join(RESULT_DIR, s["filename"])
    with open(filepath, "w", newline="") as f:
        writer=csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for i, freq in enumerate(freqs):
            row=make_row(i, freq, s)
            writer.writerow(row)
            #UDP SEND
            streamer.send_row(row)
            f.flush()
            print(
                f"[{i+1}/{s['points']}] "
                f"{freq:>10.1f} Hz "
                f"PSRR: {row['psrr_db']:>7.2f} dB "
                f"[{row['severity']}]"
            )
            time.sleep(s["interval"])
    streamer.close()
    print("\nStream complete.")
