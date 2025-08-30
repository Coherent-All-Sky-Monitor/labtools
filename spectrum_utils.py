"""Shared utilities for spectrum analyzer scripts.

This module provides common functionality for spectrum analyzer control and data handling,
including instrument communication, user input prompts, and plotting utilities.

Classes
-------
SpectrumAnalyzer
    Object-oriented interface for spectrum analyzer control via VISA

Functions
---------
prompt_sa_settings : function
    Interactive user input for spectrum analyzer measurement parameters
pick_resource : function
    Interactive VISA resource selection from available instruments
"""

import datetime
import pyvisa
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Button, TextBox


def prompt_sa_settings(include_avg=False):
    """Prompt user for standard spectrum analyzer settings.

    Interactive function to collect measurement parameters from user input with sensible
    defaults. Handles frequency range, resolution bandwidth, preamp/attenuation settings,
    and optionally averaging parameters.

    Parameters
    ----------
    include_avg : bool, optional
        Whether to prompt for number of traces to average, by default False

    Returns
    -------
    dict
        Dictionary containing measurement settings with keys:
        - fstart : str, start frequency (e.g., '375MHz')
        - fstop : str, stop frequency (e.g., '500MHz')
        - rbw : str, resolution bandwidth (e.g., '10kHz')
        - preamp : bool or None, preamp enable state
        - att : float or None, attenuation value in dB
        - n_avg : int or None, number of averages (only if include_avg=True)

    Examples
    --------
    >>> settings = prompt_sa_settings()
    >>> settings = prompt_sa_settings(include_avg=True)
    """
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
    n_avg = None
    if include_avg:
        n_avg_str = (input("Enter number of traces to average [default: 4]: ").strip()
                     or "4")
        try:
            n_avg = int(n_avg_str)
            if n_avg < 1:
                raise ValueError
        except ValueError:
            print("Invalid number, using default of 4.")
            n_avg = 4
    return {
        "fstart": fstart,
        "fstop": fstop,
        "rbw": rbw,
        "preamp": preamp,
        "att": att,
        "n_avg": n_avg
    }


class SpectrumAnalyzer:
    """Object-oriented interface for controlling spectrum analyzers via VISA.

    Provides methods for instrument connection, configuration, data acquisition, and plotting.
    Supports common spectrum analyzer operations including frequency setup, trace acquisition,
    and data visualization with save functionality.

    Parameters
    ----------
    resource : str
        VISA resource string identifying the instrument (e.g., 'TCPIP::192.168.1.100::INSTR')

    Attributes
    ----------
    rm : pyvisa.ResourceManager
        PyVISA resource manager instance
    inst : pyvisa.Resource
        Connected instrument resource

    Examples
    --------
    >>> sa = SpectrumAnalyzer('TCPIP::192.168.1.100::INSTR')
    >>> sa.setup(fstart='1GHz', fstop='2GHz', rbw='1MHz')
    >>> freq, data = sa.acquire_trace()
    >>> sa.close()
    """

    def __init__(self, resource):
        """Initialize connection to spectrum analyzer.

        Parameters
        ----------
        resource : str
            VISA resource string for the instrument
        """
        self.rm = pyvisa.ResourceManager()
        self.inst = self.rm.open_resource(resource)
        self.inst.timeout = 5000  # ms
        print(f"Connected to: {self.inst.query('*IDN?').strip()}")

    def setup(self, fstart='375MHz', fstop='500MHz', rbw='10kHz', preamp=None, att=None):
        """Configure spectrum analyzer measurement parameters.

        Sets frequency range, resolution bandwidth, and optional preamp/attenuation settings.
        All frequency and bandwidth parameters should be strings with units.

        Parameters
        ----------
        fstart : str, optional
            Start frequency with units (e.g., '375MHz'), by default '375MHz'
        fstop : str, optional
            Stop frequency with units (e.g., '500MHz'), by default '500MHz'
        rbw : str, optional
            Resolution bandwidth with units (e.g., '10kHz'), by default '10kHz'
        preamp : bool or None, optional
            Preamp enable state (True/False) or None to skip, by default None
        att : float or None, optional
            Attenuation value in dB or None to skip, by default None
        """
        self.inst.write(f'FREQ:START {fstart}')
        self.inst.write(f'FREQ:STOP {fstop}')
        self.inst.write(f'BAND {rbw}')
        if preamp is not None:
            self.inst.write(f'PREAMP:STATE {"ON" if preamp else "OFF"}')
        if att is not None:
            self.inst.write(f'INP:ATT {att}')

    def acquire_trace(self):
        """Acquire a single trace with frequency axis.

        Triggers measurement, queries frequency settings, and retrieves trace data.
        Constructs frequency axis from start/stop frequencies and data length.

        Returns
        -------
        tuple[np.ndarray, np.ndarray]
            Frequency array (Hz) and amplitude data array (dBm)

        Examples
        --------
        >>> freq, data = sa.acquire_trace()
        >>> print(f"Acquired {len(data)} points from {freq[0]:.0f} to {freq[-1]:.0f} Hz")
        """
        self.inst.write('INIT;*WAI')
        fstart = float(self.inst.query('FREQ:STAR?'))
        fstop = float(self.inst.query('FREQ:STOP?'))
        data = self.inst.query_ascii_values('TRAC? TRACE1')
        freq = np.linspace(fstart, fstop, len(data))
        return freq, data

    def acquire_trace_with_freq(self):
        """Acquire trace data with frequency axis for first measurement.

        Identical to acquire_trace() but with explicit naming for clarity when used
        as the initial trace in averaging scenarios.

        Returns
        -------
        tuple[np.ndarray, np.ndarray]
            Frequency array (Hz) and amplitude data array (dBm)
        """
        self.inst.write('INIT;*WAI')
        start_freq = float(self.inst.query('FREQ:STAR?'))
        stop_freq = float(self.inst.query('FREQ:STOP?'))
        trace_data = self.inst.query_ascii_values('TRAC? TRACE1')
        freq_axis = np.linspace(start_freq, stop_freq, len(trace_data))
        return freq_axis, trace_data

    def acquire_trace_data_only(self):
        """Acquire only amplitude data without frequency queries.

        Optimized for fast repeated measurements (e.g., averaging) where frequency
        axis is already known. Skips frequency queries to improve acquisition speed.

        Returns
        -------
        np.ndarray
            Amplitude data array (dBm)
        """
        self.inst.write('INIT;*WAI')
        return self.inst.query_ascii_values('TRAC? TRACE1')

    def close(self):
        """Close the instrument connection.

        Releases the VISA resource connection to the instrument.
        """
        self.inst.close()

    def plot_trace(self, freq, data, preamp=None, att=None, instrument_id=None,
                   freq_start=None, freq_stop=None, rbw=None, n_avg=None):
        """Plot spectrum trace with interactive save functionality.

        Creates matplotlib plot with user-friendly interface including save button and
        filename input. Automatically generates timestamped filenames and saves both
        plot (PNG) and data (NPZ) with comprehensive metadata.

        Parameters
        ----------
        freq : array-like
            Frequency values in Hz
        data : array-like
            Amplitude values in dBm
        preamp : bool or None, optional
            Preamp state for display and metadata, by default None
        att : float or None, optional
            Attenuation value in dB for display and metadata, by default None
        instrument_id : str or None, optional
            Instrument identification string for metadata, by default None
        freq_start : str or None, optional
            Start frequency string for metadata, by default None
        freq_stop : str or None, optional
            Stop frequency string for metadata, by default None
        rbw : str or None, optional
            Resolution bandwidth string for metadata, by default None
        n_avg : int or None, optional
            Number of averages for display and metadata, by default None
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
        title = (f"Spectrum Trace ({preamp_str}, {att_str}"
                 + (f", {avg_str}" if avg_str else "") + ")")
        ax.set_title(title)

        # TextBox for filename (top right)
        axbox = plt.axes([0.65, 0.88, 0.2, 0.06])
        text_box = TextBox(axbox, 'File name:', initial="")

        # Save button (top right, next to textbox)
        ax_save = plt.axes([0.87, 0.88, 0.1, 0.06])
        btn_save = Button(ax_save, 'Save')

        def save_handler(_):
            """Handle save button click for trace data.

            Saves both plot image and data with metadata when save button is clicked.
            Generates timestamped filename and comprehensive metadata.

            Parameters
            ----------
            _ : object
                Button event (unused)
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
                'measurement_type': ('averaged_trace' if n_avg and n_avg > 1
                                     else 'single_trace'),
                'n_avg': n_avg or 1,
                'timestamp': iso_date
            }
            np.savez(npy_name, freq=freq, data=data, metadata=meta)
            print(f"Saved plot as {png_name} and data as {npy_name}")

        btn_save.on_clicked(save_handler)
        plt.show()

    def plot_waterfall(self, freq, waterfall, preamp=None, att=None, instrument_id=None,
                       fstart=None, fstop=None, rbw=None, n_traces=None):
        """Plot 2D waterfall spectrum with interactive save functionality.

        Creates colormap visualization of multiple traces over time with save interface.
        Frequency on x-axis, time on y-axis, amplitude represented by color intensity.

        Parameters
        ----------
        freq : array-like
            Frequency values in Hz
        waterfall : array-like
            2D array of amplitude data (time x frequency)
        preamp : bool or None, optional
            Preamp state for display and metadata, by default None
        att : float or None, optional
            Attenuation value in dB for display and metadata, by default None
        instrument_id : str or None, optional
            Instrument identification string for metadata, by default None
        fstart : str or None, optional
            Start frequency string for metadata, by default None
        fstop : str or None, optional
            Stop frequency string for metadata, by default None
        rbw : str or None, optional
            Resolution bandwidth string for metadata, by default None
        n_traces : int or None, optional
            Number of traces in waterfall for display and metadata, by default None
        """
        fig, ax = plt.subplots()
        plt.subplots_adjust(top=0.82, bottom=0.13)
        im = ax.imshow(waterfall, aspect='auto', origin='lower',
                       extent=[freq[0], freq[-1], 0, waterfall.shape[0]], cmap='viridis')
        ax.set_xlabel('Frequency (Hz)')
        ax.set_ylabel('Time (trace index)')
        preamp_str = (f"Preamp: {'ON' if preamp else 'OFF'}"
                      if preamp is not None else "Preamp: N/A")
        att_str = f"Att: {att} dB" if att is not None else "Att: N/A"
        ntraces_str = f"Traces: {n_traces}" if n_traces is not None else ""
        title = (f"Live Spectrum Waterfall ({preamp_str}, {att_str}"
                 + (f", {ntraces_str}" if ntraces_str else "") + ")")
        ax.set_title(title)
        cbar = fig.colorbar(im, ax=ax)
        cbar.set_label('Amplitude (dBm)')

        axbox = plt.axes([0.65, 0.88, 0.2, 0.06])
        text_box = TextBox(axbox, 'File name:', initial="")
        ax_save = plt.axes([0.87, 0.88, 0.1, 0.06])
        btn_save = Button(ax_save, 'Save')

        def save_handler(_):
            """Handle save button click for waterfall data.

            Saves both plot image and waterfall data with metadata when save button is clicked.
            Generates timestamped filename and comprehensive metadata for waterfall format.

            Parameters
            ----------
            _ : object
                Button event (unused)
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
        plt.show()


def pick_resource():
    """Interactive VISA resource selection from available instruments.

    Scans for available VISA instruments and presents numbered list for user selection.
    Handles invalid selections gracefully with retry prompts.

    Returns
    -------
    str
        Selected VISA resource string

    Raises
    ------
    SystemExit
        If no VISA instruments are found

    Examples
    --------
    >>> resource = pick_resource()
    Available VISA resources:
      [0] TCPIP::192.168.1.100::INSTR
      [1] USB0::0x1234::0x5678::SN123456::INSTR
    Select resource number: 0
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
