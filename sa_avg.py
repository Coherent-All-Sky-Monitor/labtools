# --- Copied from sa.py, with averaging logic and full metadata/save support ---
"""
Spectrum Analyzer VISA Control Tool (Averaged Traces)
----------------------------------------------------
This module provides an interface for connecting to, configuring, and acquiring
averaged data from a spectrum analyzer using the `pyvisa` library.
It includes interactive resource selection, user-specified frequency/RBW, preamp,
attenuation, and averaging of multiple traces. Metadata is saved with the data.

Dependencies:
    - pyvisa
    - numpy
    - matplotlib
"""

import datetime
import pyvisa
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Button, TextBox


class SpectrumAnalyzer:
    """
    Object-oriented interface for controlling and acquiring data from a spectrum analyzer via VISA.
    """

    def __init__(self, resource):
        """
        Initialize the SpectrumAnalyzer with a VISA resource string.
        Args:
            resource (str): VISA resource string for the instrument.
        """
        self.rm = pyvisa.ResourceManager()
        self.inst = self.rm.open_resource(resource)
        self.inst.timeout = 5000  # ms
        print(f"Connected to: {self.inst.query('*IDN?').strip()}")

    def setup(self,
              fstart='375MHz',
              fstop='500MHz',
              rbw='10kHz',
              preamp=None,
              att=None):
        """
        Configure the frequency range, resolution bandwidth, preamp, and attenuation.
        Args:
            fstart (str): Start frequency (e.g., '375MHz').
            fstop (str): Stop frequency (e.g., '500MHz').
            rbw (str): Resolution bandwidth (e.g., '10kHz').
            preamp (bool or None): Enable (True), disable (False), or leave unchanged (None).
            att (float or None): Set input attenuation in dB, or leave unchanged (None).
        """
        self.inst.write(f'FREQ:START {fstart}')
        self.inst.write(f'FREQ:STOP {fstop}')
        self.inst.write(f'BAND {rbw}')
        if preamp is not None:
            self.inst.write(f'PREAMP:STATE {"ON" if preamp else "OFF"}')
        if att is not None:
            self.inst.write(f'INP:ATT {att}')

    def acquire_trace(self):
        """
        Acquire trace data without frequency queries - optimized for averaging.
        Returns:
            list: Amplitude data array.
        """
        self.inst.write('INIT;*WAI')
        trace_data = self.inst.query_ascii_values('TRAC? TRACE1')
        return trace_data

    def acquire_trace_with_freq(self):
        """
        Acquire trace data with frequency axis - use for first trace to get freq axis.
        Returns:
            tuple: (frequency array, amplitude data array).
        """
        self.inst.write('INIT;*WAI')
        start_freq = float(self.inst.query('FREQ:STAR?'))
        stop_freq = float(self.inst.query('FREQ:STOP?'))
        trace_data = self.inst.query_ascii_values('TRAC? TRACE1')
        freq_axis = np.linspace(start_freq, stop_freq, len(trace_data))
        return freq_axis, trace_data

    def close(self):
        """
        Close the VISA connection to the instrument.
        """
        self.inst.close()

    def plot_trace(self,
                   freq,
                   data,
                   preamp=None,
                   att=None,
                   instrument_id=None,
                   freq_start=None,
                   freq_stop=None,
                   rbw=None,
                   n_avg=None):
        """
        Plot the acquired spectrum trace using matplotlib with save functionality.
        Args:
            freq (array-like): Frequency values (Hz).
            data (array-like): Amplitude values (dBm).
            preamp (bool or None): Preamp state for display.
            att (float or None): Attenuation value for display.
            instrument_id (str or None): Instrument identification string.
            freq_start (str or None): Start frequency for metadata.
            freq_stop (str or None): Stop frequency for metadata.
            rbw (str or None): Resolution bandwidth for metadata.
            n_avg (int or None): Number of averages for display and metadata.
        """

        fig, ax = plt.subplots()
        plt.subplots_adjust(top=0.82, bottom=0.13)  # Make space for widgets
        ax.plot(freq, data)
        ax.set_xlabel('Frequency (Hz)')
        ax.set_ylabel('Amplitude (dBm)')
        preamp_str = (f"Preamp: {'ON' if preamp else 'OFF'}"
                      if preamp is not None else "Preamp: N/A")
        att_str = f"Att: {att} dB" if att is not None else "Att: N/A"
        avg_str = f"Averages: {n_avg}" if n_avg is not None else ""
        ax.set_title(f"Averaged Spectrum Trace ({preamp_str}, {att_str}, {avg_str})")

        # TextBox for filename (top right)
        axbox = plt.axes([0.65, 0.88, 0.2, 0.06])
        text_box = TextBox(axbox, 'File name:', initial="")

        # Save button (top right, next to textbox)
        ax_save = plt.axes([0.87, 0.88, 0.1, 0.06])
        btn_save = Button(ax_save, 'Save')

        def save_handler(_):
            """
            Handle save button click - saves current plot and data with metadata.
            Args:
                _: Unused event parameter required by button callback.
            """
            user_name = text_box.text.strip()
            if not user_name:
                print("No name entered. Not saving.")
                return
            iso_date = (datetime.datetime.now()
                        .isoformat(timespec='seconds')
                        .replace(':', '-'))
            base = f"{iso_date}_{user_name}"
            png_name = base + ".png"
            npy_name = base + ".npz"
            fig.savefig(png_name)
            meta = {
                'instrument': instrument_id or '',
                'freq_start': freq_start or '',
                'freq_stop': freq_stop or '',
                'rbw': rbw or '',
                'preamp': preamp,
                'attenuation': att,
                'measurement_type': 'averaged_trace',
                'n_avg': n_avg,
                'timestamp': iso_date
            }
            np.savez(npy_name, freq=freq, data=data, metadata=meta)
            print(f"Saved plot as {png_name} and data as {npy_name}")

        btn_save.on_clicked(save_handler)
        plt.show()

def pick_resource():
    """
    List available VISA resources and prompt the user to select one interactively.
    Returns:
        str: The selected VISA resource string.
    """
    rm = pyvisa.ResourceManager()
    instruments = rm.list_resources()
    if not instruments:
        print("No VISA instruments found.")
        exit(1)
    print("Available VISA resources:")
    for idx, res in enumerate(instruments):
        print(f"  [{idx}] {res}")
    while True:
        try:
            choice = int(input("Select resource number: "))
            if 0 <= choice < len(instruments):
                return instruments[choice]
        except ValueError:
            pass
        print("Invalid selection. Try again.")


def main():
    """
    Main function that orchestrates instrument connection, configuration, and averaging.
    """
    resource = pick_resource()
    sa = SpectrumAnalyzer(resource)

    fstart = (input("Enter start frequency (e.g., 375MHz) [default: 375MHz]: ").strip()
              or "375MHz")
    fstop = (input("Enter stop frequency (e.g., 500MHz) [default: 500MHz]: ").strip()
             or "500MHz")
    rbw = (input("Enter resolution bandwidth (e.g., 10kHz) [default: 10kHz]: ").strip()
           or "10kHz")

    preamp = None
    preamp_input = input("Enable preamp? (y/n, blank to skip): ").strip().lower()
    if preamp_input == 'y':
        preamp = True
    elif preamp_input == 'n':
        preamp = False

    att = None
    att_input = input("Set attenuation in dB (blank to skip): ").strip()
    if att_input:
        try:
            att = float(att_input)
        except ValueError:
            print("Invalid attenuation value. Skipping.")

    n_avg_str = (input("Enter number of traces to average [default: 4]: ").strip()
                 or "4")
    try:
        n_avg = int(n_avg_str)
        if n_avg < 1:
            raise ValueError
    except ValueError:
        print("Invalid number, using default of 4.")
        n_avg = 4

    sa.setup(fstart=fstart, fstop=fstop, rbw=rbw, preamp=preamp, att=att)

    print(f"Acquiring {n_avg} traces for averaging...")
    # Get frequency axis from first trace
    freq, first_data = sa.acquire_trace_with_freq()
    avg_data = np.array(first_data, dtype=np.float64)

    # Acquire remaining traces faster (no freq queries)
    for i in range(1, n_avg):
        print(f"Trace {i+1}/{n_avg}")
        data = sa.acquire_trace()
        avg_data += np.array(data, dtype=np.float64)

    avg_data /= n_avg
    print("Averaging complete!")
    instrument_id = sa.inst.query('*IDN?').strip()
    sa.plot_trace(
        freq, avg_data,
        preamp=preamp,
        att=att,
        instrument_id=instrument_id,
        freq_start=fstart,
        freq_stop=fstop,
        rbw=rbw,
        n_avg=n_avg
    )
    sa.close()


if __name__ == "__main__":
    main()
