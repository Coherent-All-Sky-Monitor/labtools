"""Spectrum Analyzer VISA Control Tool (Averaged Traces).

This module provides an interface for connecting to, configuring, and acquiring
averaged data from a spectrum analyzer using the `pyvisa` library.
It includes interactive resource selection, user-specified frequency/RBW, preamp,
attenuation, and averaging of multiple traces. Metadata is saved with the data.

Dependencies
------------
pyvisa : library
    For VISA instrument communication
numpy : library
    For numerical operations and data averaging
matplotlib : library
    For plotting and data visualization
spectrum_utils : module
    Local utilities for spectrum analyzer operations

Notes
-----
This script is based on sa.py but adds averaging logic and full metadata/save support.
"""

import numpy as np
from spectrum_utils import SpectrumAnalyzer, pick_resource, prompt_sa_settings


def main():
    """Execute the main spectrum analyzer averaging workflow.

    This function orchestrates the entire process of:
    1. Connecting to a spectrum analyzer instrument
    2. Configuring measurement parameters through user input
    3. Acquiring multiple traces and computing their average
    4. Displaying the averaged result with metadata

    The function prompts the user to select an instrument and measurement parameters,
    then acquires the specified number of traces for averaging. The averaged trace is
    displayed with a plot that includes save functionality and comprehensive metadata.

    Parameters
    ----------
    None

    Returns
    -------
    None

    Notes
    -----
    The function handles all user interaction, instrument communication, and data
    processing internally. Error handling for instrument communication is managed
    by the spectrum_utils module.

    Examples
    --------
    >>> main()
    Available VISA resources:
      [0] TCPIP::192.168.1.100::INSTR
    Select resource number: 0
    Connected to: Keysight Technologies,E5071C,MY12345678,A.09.90
    Enter start frequency (e.g., 375MHz) [default: 375MHz]:
    Enter number of traces to average [default: 4]: 10
    Acquiring 10 traces for averaging...
    Trace 1/10
    ...
    """
    # Select and connect to instrument
    resource = pick_resource()
    sa = SpectrumAnalyzer(resource)

    # Get measurement settings from user
    settings = prompt_sa_settings(include_avg=True)

    # Configure instrument
    sa.setup(
        fstart=settings["fstart"],
        fstop=settings["fstop"],
        rbw=settings["rbw"],
        preamp=settings["preamp"],
        att=settings["att"]
    )    # Perform averaging
    n_avg = settings["n_avg"]
    print(f"Acquiring {n_avg} traces for averaging...")

    # Get first trace with frequency data
    freq, first_data = sa.acquire_trace_with_freq()
    avg_data = np.array(first_data, dtype=np.float64)

    # Acquire and accumulate remaining traces
    for i in range(1, n_avg):
        print(f"Trace {i+1}/{n_avg}")
        _, data = sa.acquire_trace()
        avg_data += np.array(data, dtype=np.float64)

    # Compute average
    avg_data /= n_avg
    print("Averaging complete!")

    # Get instrument identification
    instrument_id = sa.inst.query('*IDN?').strip()

    # Plot results with metadata
    sa.plot_trace(
        freq, avg_data,
        preamp=settings["preamp"],
        att=settings["att"],
        instrument_id=instrument_id,
        freq_start=settings["fstart"],
        freq_stop=settings["fstop"],
        rbw=settings["rbw"],
        n_avg=n_avg
    )

    # Clean up connection
    sa.close()


if __name__ == "__main__":
    main()
