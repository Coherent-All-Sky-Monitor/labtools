"""
Spectrum Analyzer VISA Control Tool (Live Waterfall)
--------------------------------------------------
This script connects to a spectrum analyzer using pyvisa, acquires repeated traces,
and displays a live waterfall plot (frequency vs. time, color = amplitude).

Dependencies:
    - pyvisa
    - numpy
    - matplotlib
"""
import datetime
import pyvisa
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
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

    def setup(self, fstart='375MHz', fstop='500MHz', rbw='10kHz', preamp=None, att=None):
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
        Acquire a single trace from the spectrum analyzer.
        Returns:
            tuple: (frequency array, amplitude data array).
        """
        self.inst.write('INIT;*WAI')
        fstart = float(self.inst.query('FREQ:STAR?'))
        fstop = float(self.inst.query('FREQ:STOP?'))
        data = self.inst.query_ascii_values('TRAC? TRACE1')
        freq = np.linspace(fstart, fstop, len(data))
        return freq, data

    def close(self):
        """
        Close the VISA connection to the instrument.
        """
        self.inst.close()

def pick_resource():
    """
    Interactively prompt user to select a VISA resource from available instruments.
    Returns:
        str: Selected VISA resource string.
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
    Main function that orchestrates instrument connection, configuration, and live waterfall.
    """
    resource = pick_resource()
    sa = SpectrumAnalyzer(resource)
    fstart = (input("Enter start frequency (e.g., 375MHz) [default: 375MHz]: ").strip()
              or "375MHz")
    fstop = (input("Enter stop frequency (e.g., 500MHz) [default: 500MHz]: ").strip()
             or "500MHz")
    rbw = (input("Enter resolution bandwidth (e.g., 10kHz) [default: 10kHz]: ").strip()
           or "10kHz")
    # Prompt for preamp and attenuation
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

    sa.setup(fstart=fstart, fstop=fstop, rbw=rbw, preamp=preamp, att=att)

    n_traces = 100  # Number of lines in the waterfall
    freq, data = sa.acquire_trace()
    n_points = len(data)
    waterfall = np.zeros((n_traces, n_points))

    fig, ax = plt.subplots()
    plt.subplots_adjust(top=0.82, bottom=0.13)
    im = ax.imshow(waterfall, aspect='auto', origin='lower',
                   extent=[freq[0], freq[-1], 0, n_traces], cmap='viridis')
    ax.set_xlabel('Frequency (Hz)')
    ax.set_ylabel('Time (trace index)')
    preamp_str = (f"Preamp: {'ON' if preamp else 'OFF'}"
                  if preamp is not None else "Preamp: N/A")
    att_str = f"Att: {att} dB" if att is not None else "Att: N/A"
    ax.set_title(f"Live Spectrum Waterfall ({preamp_str}, {att_str})")
    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label('Amplitude (dBm)')

    axbox = plt.axes([0.65, 0.88, 0.2, 0.06])
    text_box = TextBox(axbox, 'File name:', initial="")
    ax_save = plt.axes([0.87, 0.88, 0.1, 0.06])
    btn_save = Button(ax_save, 'Save')

    instrument_id = sa.inst.query('*IDN?').strip()

    def save_handler(_):
        """
        Handle save button click - saves current waterfall plot and data.
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
            'freq_start': fstart or '',
            'freq_stop': fstop or '',
            'rbw': rbw or '',
            'preamp': preamp,
            'attenuation': att,
            'measurement_type': 'waterfall',
            'n_avg': 1,
            'n_traces': n_traces,
            'timestamp': iso_date
        }
        np.savez(npy_name, freq=freq, waterfall=waterfall, metadata=meta)
        print(f"Saved plot as {png_name} and data as {npy_name}")

    btn_save.on_clicked(save_handler)

    def update(_):
        """
        Update function for animation - acquires new trace and updates waterfall display.
        Args:
            _: Frame parameter unused but required by FuncAnimation.
        Returns:
            list: List containing updated image artist for blitting.
        """
        nonlocal waterfall
        _, data = sa.acquire_trace()
        waterfall = np.roll(waterfall, -1, axis=0)
        waterfall[-1, :] = data
        im.set_data(waterfall)
        return [im]

    # Start animation
    _ = animation.FuncAnimation(fig, update, interval=200, blit=True)
    plt.show()
    sa.close()

if __name__ == "__main__":
    main()
