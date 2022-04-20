from pathlib import Path
import numpy as np
from tqdm import trange

from datalib import ShepherdReader, ShepherdWriter

if __name__ == "__main__":

    file_path = Path("./hrv_artificial_sawtooth_1h.h5")

    with ShepherdWriter(file_path, compression=1) as file:

        duration_s = 60
        repetitions = 60
        timestamp_vector = np.arange(0.0, duration_s, file.sample_interval_ns / 10**9)

        # values in SI units
        voltages = np.linspace(3.60, 1.90, int(file.samplerate_sps * duration_s))
        currents = np.linspace(100e-6, 2000e-6, int(file.samplerate_sps * duration_s))

        for idx in trange(repetitions, desc="repetitions"):

            timestamps = idx * duration_s + timestamp_vector
            file.append_iv_data_si(timestamps, voltages, currents)

        file.save_metadata()

    with ShepherdReader(file_path) as db:
        print(f"Mode: {db.get_mode()}")
        print(f"Window: {db.get_window_samples()}")
        print(f"Config: {db.get_config()}")
