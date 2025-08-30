"""Spectrum Analyzer VISA Control Tool (Combined).

This unified module provides a complete interface for spectrum analyzer operations including
single trace acquisition, trace averaging, and live waterfall display. Users can select
the desired measurement mode through an interactive menu system.

Dependencies
------------
pyvisa : library
    For VISA instrument communication
numpy : library
    For numerical operations and data averaging
matplotlib : library
    For plotting, data visualization, and real-time animation
spectrum_utils : module
    Local utilities for spectrum analyzer operations

Notes
-----
This script combines functionality from sa.py, sa_avg.py, and sa_waterfall.py into a
single unified interface with mode selection:
- Single trace: Basic spectrum measurement
- Averaged trace: Multiple trace averaging for noise reduction
- Live waterfall: Real-time spectral evolution display
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from spectrum_utils import SpectrumAnalyzer, pick_resource, prompt_sa_settings


def prompt_measurement_mode():
    """Prompt user to select measurement mode.

    Interactive menu for selecting between single trace, averaging, or waterfall modes.
    Handles invalid selections with retry prompts.

    Returns
    -------
    str
        Selected mode: 'single', 'average', or 'waterfall'

    Examples
    --------
    >>> mode = prompt_measurement_mode()
    Select measurement mode:
      [1] Single trace
      [2] Averaged trace
      [3] Live waterfall
    Enter choice (1-3): 2
    """
    print("\nSelect measurement mode:")
    print("  [1] Single trace")
    print("  [2] Averaged trace")
    print("  [3] Live waterfall")

    while True:
        try:
            choice = int(input("Enter choice (1-3): "))
            if choice == 1:
                return 'single'
            elif choice == 2:
                return 'average'
            elif choice == 3:
                return 'waterfall'
            else:
                print("Invalid choice. Please enter 1, 2, or 3.")
        except ValueError:
            print("Invalid input. Please enter a number 1-3.")


def run_single_trace(sa, settings):
    """Execute single trace measurement workflow.

    Acquires a single spectrum trace and displays it with interactive save functionality.

    Parameters
    ----------
    sa : SpectrumAnalyzer
        Connected spectrum analyzer instance
    settings : dict
        Measurement configuration settings

    Returns
    -------
    None
    """
    print("\n=== Single Trace Measurement ===")
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


def run_averaged_trace(sa, settings):
    """Execute averaged trace measurement workflow.

    Acquires multiple traces, computes their average, and displays the result with
    comprehensive metadata including averaging information.

    Parameters
    ----------
    sa : SpectrumAnalyzer
        Connected spectrum analyzer instance
    settings : dict
        Measurement configuration settings including n_avg parameter

    Returns
    -------
    None
    """
    print("\n=== Averaged Trace Measurement ===")
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


def run_live_waterfall(sa, settings):
    """Execute live waterfall display workflow.

    Sets up and runs a real-time animated waterfall display showing spectral evolution
    over time with continuous trace acquisition and rolling buffer updates.

    Parameters
    ----------
    sa : SpectrumAnalyzer
        Connected spectrum analyzer instance
    settings : dict
        Measurement configuration settings

    Returns
    -------
    None
    """
    print("\n=== Live Waterfall Display ===")
    print("Starting live waterfall... Close plot window to stop.")

    # Set up waterfall parameters
    n_traces = 100  # Number of lines in the waterfall

    # Get initial trace to determine data dimensions
    freq, data = sa.acquire_trace()
    n_points = len(data)

    # Initialize waterfall array
    waterfall = np.zeros((n_traces, n_points))

    # Get instrument identification
    instrument_id = sa.inst.query('*IDN?').strip()

    def update(_):
        """Animation update function for waterfall display.

        Called by matplotlib FuncAnimation to update the waterfall plot with new data.
        Acquires new trace, shifts existing data, and updates the plot visualization.

        Parameters
        ----------
        _ : int
            Frame number (unused but required by FuncAnimation interface)

        Returns
        -------
        list
            Empty list (required by FuncAnimation for blitting support)

        Notes
        -----
        This function modifies the nonlocal waterfall array by rolling data and
        adding new measurements. The plot is updated through the plot_waterfall method.
        """
        nonlocal waterfall

        try:
            # Acquire new trace
            _, data = sa.acquire_trace()

            # Roll waterfall array and add new data
            waterfall = np.roll(waterfall, -1, axis=0)
            waterfall[-1, :] = data

            # Update plot
            sa.plot_waterfall(
                freq, waterfall,
                preamp=settings["preamp"],
                att=settings["att"],
                instrument_id=instrument_id,
                fstart=settings["fstart"],
                fstop=settings["fstop"],
                rbw=settings["rbw"],
                n_traces=n_traces
            )
        except RuntimeError as e:
            print(f"Runtime error in waterfall update: {e}")
        except ValueError as e:
            print(f"Value error in waterfall update: {e}")

        return []

    # Start animation
    _ = animation.FuncAnimation(plt.gcf(), update, interval=200, blit=False)
    plt.show()


def main():
    """Execute the unified spectrum analyzer measurement workflow.

    This function orchestrates the complete process of:
    1. Interactive measurement mode selection
    2. Instrument selection and connection
    3. Parameter configuration
    4. Execution of selected measurement type

    The user first selects from single trace, averaged trace, or live waterfall modes,
    then follows the standard workflow for instrument setup and measurement execution.

    Parameters
    ----------
    None

    Returns
    -------
    None

    Examples
    --------
    >>> main()
    Select measurement mode:
      [1] Single trace
      [2] Averaged trace
      [3] Live waterfall
    Enter choice (1-3): 1
    Available VISA resources:
      [0] TCPIP::192.168.1.100::INSTR
    ...
    """
    print("Spectrum Analyzer Control Tool")
    print("=" * 40)

    # Select measurement mode
    mode = prompt_measurement_mode()

    # Connect to instrument
    print("\n=== Instrument Connection ===")
    resource = pick_resource()
    sa = SpectrumAnalyzer(resource)

    # Get measurement settings
    print("\n=== Measurement Configuration ===")
    include_avg = mode == 'average'
    settings = prompt_sa_settings(include_avg=include_avg)

    # Configure instrument
    sa.setup(
        fstart=settings["fstart"],
        fstop=settings["fstop"],
        rbw=settings["rbw"],
        preamp=settings["preamp"],
        att=settings["att"]
    )

    # Execute selected measurement
    try:
        if mode == 'single':
            run_single_trace(sa, settings)
        elif mode == 'average':
            run_averaged_trace(sa, settings)
        elif mode == 'waterfall':
            run_live_waterfall(sa, settings)
    finally:
        # Clean up connection
        sa.close()
        print("\nMeasurement complete. Connection closed.")


if __name__ == "__main__":
    main()
