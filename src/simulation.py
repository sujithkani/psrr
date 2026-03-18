import numpy as np
from model import compute_psrr, psrr_to_voltages, classify

def generate_freqs(settings):
    return np.logspace(np.log10(settings["f_start"]),np.log10(settings["f_stop"]),settings["points"])

def make_row(i, freq, s):
    psrr_db = compute_psrr(freq, s)
    vin_ac, vout_ac = psrr_to_voltages(psrr_db, s)
    status, code, source, severity = classify(psrr_db, s)
    return {
        "timestamp_s": round(i * 0.1, 2),
        "frequency_hz": round(freq, 2),
        "vin_dc_v": s["vin"],
        "vout_dc_v": s["vout"],
        "vin_ac_v": vin_ac,
        "vout_ac_v": vout_ac,
        "psrr_db": round(psrr_db, 2),
        "psrr_i32": int(round(psrr_db)),
        "status": status,
        "error_code": code,
        "error_source": source,
        "severity": severity
    }
