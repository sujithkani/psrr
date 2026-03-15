import numpy as np

def compute_psrr(freq, s):
    A0 = s["psrr_base"]
    fp1 = 200
    fz_esr = 30000
    fp2 = 500000
    term1 = -20*np.log10(np.sqrt(1 + (freq/fp1)**2))
    term2 =  20*np.log10(np.sqrt(1 + (freq/fz_esr)**2))
    term3 = -20*np.log10(np.sqrt(1 + (freq/fp2)**2))
    psrr = A0 + term1 + term2 + term3
    esr_peak = 3*np.exp(-((np.log10(freq)-4.5)**2)/0.18)
    psrr += esr_peak
    noise_scale = s["noise_std"]*(1+np.log10(freq))
    noise_scale = min(noise_scale, s["noise_std"]*4)
    psrr += np.random.normal(0, noise_scale)
    return np.clip(psrr, -120, 0)

def psrr_to_voltages(psrr_db, s):
    vin_ripple = s["ripple"]
    ratio = 10 ** (psrr_db / 20.0)
    vout_ripple = abs(vin_ripple * ratio)
    return round(vin_ripple, 6), round(vout_ripple, 6)

def classify(psrr_db, s):
    if psrr_db > s["t_crit"]:
        return True, 2001, "PSRR_CRITICAL_HighFreqDegradation", "CRITICAL"
    elif psrr_db > s["t_warn"]:
        return True, 1001, "PSRR_WARNING_BelowThreshold", "WARNING"
    else:
        return False, 0, "OK", "NORMAL"
