"""Spectrum Analyzer VISA Control Tool.

This module provides an interface for connecting to, configuring, and acquiring data from
a spectrum analyzer using the pyvisa library. It includes interactive resource selection
and plotting of acquired traces with save functionality.

Dependencies
------------
pyvisa : library
    For VISA instrument communication
numpy : library
    For numerical operations
matplotlib : library
    For plotting and data visualization
spectrum_utils : module
    Local utilities for spectrum analyzer operations

Notes
-----
This script provides basic single-trace spectrum analyzer measurements with interactive
parameter selection and plot display.
"""

from spectrum_utils import SpectrumAnalyzer, pick_resource, prompt_sa_settings


def main():
    """Execute single trace spectrum analyzer measurement workflow.

    This function orchestrates the complete process of:
    1. Interactive instrument selection and connection
    2. User configuration of measurement parameters
    3. Single trace data acquisition
    4. Plot display with save functionality

    The measurement settings are collected interactively and the resulting trace
    is displayed with metadata for easy identification and archival.

    Parameters
    ----------
    None

    Returns
    -------
    None

    Examples
    --------
    >>> main()
    Available VISA resources:
      [0] TCPIP::192.168.1.100::INSTR
    Select resource number: 0
    Connected to: Keysight Technologies,E5071C,MY12345678,A.09.90
    Enter start frequency (e.g., 375MHz) [default: 375MHz]:
    ...
    """
    resource = pick_resource()
    sa = SpectrumAnalyzer(resource)
    settings = prompt_sa_settings()
    sa.setup(fstart=settings["fstart"], fstop=settings["fstop"], rbw=settings["rbw"],
             preamp=settings["preamp"], att=settings["att"])
    freq, data = sa.acquire_trace()
    instrument_id = sa.inst.query('*IDN?').strip()
    sa.plot_trace(
        freq, data,
        preamp=settings["preamp"],
        att=settings["att"],
        instrument_id=instrument_id,
        freq_start=settings["fstart"],
        freq_stop=settings["fstop"],
        rbw=settings["rbw"]
    )
    sa.close()


if __name__ == "__main__":
    main()
