"""Spectrum Analyzer VISA Control Tool (Live Waterfall).

This script connects to a spectrum analyzer using pyvisa, acquires repeated traces,
and displays a live waterfall plot (frequency vs. time, color = amplitude).
The waterfall display updates in real-time showing spectral evolution over time.

Dependencies
------------
pyvisa : library
    For VISA instrument communication
numpy : library
    For numerical operations and array manipulation
matplotlib : library
    For plotting and real-time animation
spectrum_utils : module
    Local utilities for spectrum analyzer operations

Notes
-----
This script provides a live waterfall display where:
- X-axis represents frequency
- Y-axis represents time (older traces at bottom, newer at top)
- Color intensity represents signal amplitude
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from spectrum_utils import SpectrumAnalyzer, pick_resource, prompt_sa_settings


def main():
    """Execute the main spectrum analyzer waterfall workflow.

    This function orchestrates the entire process of:
    1. Connecting to a spectrum analyzer instrument
    2. Configuring measurement parameters through user input
    3. Setting up a live waterfall display
    4. Continuously acquiring traces and updating the waterfall plot

    The function creates a real-time animated waterfall display where new traces
    are added to the top and older traces scroll downward. The animation
    continues until the user closes the plot window.

    Parameters
    ----------
    None

    Returns
    -------
    None

    Notes
    -----
    The waterfall display shows:
    - Frequency on the x-axis
    - Time progression on the y-axis (newest traces at top)
    - Signal amplitude represented by color intensity

    The animation updates every 200ms and maintains a rolling buffer
    of the most recent traces.
    """
    # Select and connect to instrument
    resource = pick_resource()
    sa = SpectrumAnalyzer(resource)

    # Get measurement settings from user
    settings = prompt_sa_settings()

    # Configure instrument
    sa.setup(
        fstart=settings["fstart"],
        fstop=settings["fstop"],
        rbw=settings["rbw"],
        preamp=settings["preamp"],
        att=settings["att"]
    )

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
        return []

    # Start animation
    _ = animation.FuncAnimation(plt.gcf(), update, interval=200, blit=False)
    plt.show()

    # Clean up connection
    sa.close()


if __name__ == "__main__":
    main()
