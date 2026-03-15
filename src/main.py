"""
import numpy as np
from config import banner, get_settings
from io_utils import run_batch, run_stream
def main():
    np.random.seed(None)
    banner()
    settings = get_settings()
    print("\nRunning simulation...\n")
    if settings["stream"]:
        run_stream(settings)
    else:
        run_batch(settings)
    print("\nDone")
if __name__ == "__main__":
    main()
"""

import numpy as np
from config import banner, get_settings
from io_utils import run_batch, run_stream
from plot import plot_psrr
def main():
    np.random.seed(None)
    banner()
    settings=get_settings()
    print("\nRunning simulation...\n")
    if settings["stream"]:
        run_stream(settings)
    else:
        rows = run_batch(settings)
        plot_psrr(rows)
    print("\nDone!\n")
if __name__ == "__main__":
    main()
