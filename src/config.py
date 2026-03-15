def banner():
    print("\n" + "=" * 55)
    print(" PSRR Circuit Simulator — LDO Regulator Model")
    print(" For LabVIEW PSRR Monitoring System")
    print("=" * 55 + "\n")

def get_float(prompt, default, min_val=None, max_val=None):
    while True:
        try:
            raw=input(f"{prompt} [{default}]: ").strip()
            val=float(raw) if raw else default
            if min_val is not None and val < min_val:
                print(f"Must be >= {min_val}. Try again.")
                continue
            if max_val is not None and val > max_val:
                print(f"Must be <= {max_val}. Try again.")
                continue
            return val
        except ValueError:
            print("Invalid input. Enter a number.")
            
def get_int(prompt, default, min_val=None, max_val=None):
    while True:
        try:
            raw=input(f"{prompt} [{default}]: ").strip()
            val=int(raw) if raw else default
            if min_val is not None and val < min_val:
                print(f"Must be >= {min_val}. Try again.")
                continue
            if max_val is not None and val > max_val:
                print(f"Must be <= {max_val}. Try again.")
                continue
            return val
        except ValueError:
            print("Invalid input. Enter a whole number.")

def get_str(prompt, default):
    raw=input(f"{prompt} [{default}]: ").strip()
    return raw if raw else default

def get_bool(prompt, default=True):
    default_str="Y/n" if default else "y/N"
    while True:
        raw=input(f"{prompt} [{default_str}]: ").strip().lower()
        if raw == "":
            return default
        if raw in ("y", "yes"):
            return True
        if raw in ("n", "no"):
            return False
        print("Enter y or n.")

def get_settings():
    print("-- Circuit Parameters -----------------------------")
    vin=get_float("Input DC voltage Vin (V)", 5.0, 1.0, 30.0)
    vout=get_float("Output DC voltage Vout (V)", 3.3, 0.5, vin - 0.5)
    ripple=get_float("AC ripple amplitude on Vin (V)", 0.1, 0.001, 2.0)
    print("\n-- Frequency Sweep ------------------------------")
    f_start=get_float("Start frequency (Hz)", 10, 1, 1000)
    f_stop=get_float("Stop frequency (Hz)", 1e6, f_start * 10)
    points=get_int("Number of data points", 200, 10, 2000)
    print("\n-- PSRR Model ---------------------------------")
    psrr_base=get_float("PSRR at 10 Hz (dB)", -65.0, None, -10.0)
    noise_std=get_float("Measurement noise std dev (dB)", 2.5, 0.0, 10.0)
    print("\n-- Warning Thresholds ------------------------")
    print("Rule: PSRR closer to 0 dB=worse rejection")
    t_warn=get_float("WARNING threshold (dB)", -35.0, None, -5.0)
    t_crit=get_float("CRITICAL threshold (dB)", -20.0, t_warn + 1, -1.0)
    print("\n-- Output Settings -----------------------------")
    filename=get_str("Output CSV filename", "psrr_simulation.csv")
    if not filename.endswith(".csv"):
        filename+=".csv"
    stream=get_bool("Use live streaming mode (one row at a time)?", False)
    interval=0.1
    if stream:
        interval=get_float("Streaming interval (seconds per row)", 0.1, 0.01, 5.0)

    return {"vin": vin,"vout": vout,"ripple": ripple,"f_start": f_start,"f_stop": f_stop,
        "points": points,"psrr_base": psrr_base,"noise_std": noise_std,"t_warn": t_warn,"t_crit": t_crit,
        "filename": filename,"stream": stream,"interval": interval}
