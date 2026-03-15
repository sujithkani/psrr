import matplotlib.pyplot as plt

def plot_psrr(rows):
    freqs=[r["frequency_hz"] for r in rows]
    psrr=[r["psrr_db"] for r in rows]
    plt.figure()
    plt.semilogx(freqs, psrr)
    plt.xlabel("Frequency (Hz)")
    plt.ylabel("PSRR (dB)")
    plt.title("LDO PSRR vs Frequency")
    plt.grid(True)
    plt.show(block=True)
