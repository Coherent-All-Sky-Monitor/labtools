"""Spectrum Analyzer Data Reader.

This module loads and displays data files saved by spectrum analyzer scripts. It provides
functionality to read .npz files, display comprehensive metadata, and plot both single
traces and waterfall data with appropriate visualizations.

Dependencies
------------
numpy : library
    For data loading and array operations
matplotlib : library
    For plotting and data visualization
os : module
    For file system operations

Notes
-----
Supports both single trace data and waterfall data formats with automatic detection
based on data structure. Displays formatted metadata and creates appropriate plots
for each data type.
"""

import os
import numpy as np
import matplotlib.pyplot as plt


def main():
    """Load and display spectrum analyzer data files.

    Interactive function that prompts for filename, loads .npz data file, displays
    comprehensive metadata in formatted output, and creates appropriate plots based
    on data type (single trace or waterfall).

    The function automatically detects data format and creates optimized visualizations
    with titles derived from metadata. Handles missing files gracefully with error
    messages.

    Parameters
    ----------
    None

    Returns
    -------
    None

    Examples
    --------
    >>> main()
    Enter filename to load (with or without .npz): measurement_data

    --- Metadata ---
    Instrument: Keysight Technologies,E5071C,MY12345678,A.09.90
    Measurement Type: Averaged Trace
    ...
    """
    fname = input("Enter filename to load (with or without .npz): ").strip()
    if not fname.endswith('.npz'):
        fname += '.npz'
    if not os.path.exists(fname):
        print(f"File not found: {fname}")
        return
    data = np.load(fname, allow_pickle=True)
    print("\n--- Metadata ---")
    meta = data.get('metadata', None)
    if meta is not None:
        # If saved as dict, convert to dict
        if hasattr(meta, 'item'):
            meta = meta.item()

        # Display structured metadata
        print(f"Instrument: {meta.get('instrument', 'N/A')}")
        print(f"Measurement Type: {meta.get('measurement_type', 'N/A')}")
        print(f"Frequency Range: {meta.get('freq_start', 'N/A')} to "
              f"{meta.get('freq_stop', 'N/A')}")
        print(f"Resolution Bandwidth: {meta.get('rbw', 'N/A')}")
        print(f"Preamp: {'ON' if meta.get('preamp') else 'OFF'}")
        print(f"Attenuation: {meta.get('attenuation', 'N/A')} dB")
        print(f"Number of Averages: {meta.get('n_avg', 'N/A')}")
        if 'n_traces' in meta:
            print(f"Waterfall Traces: {meta.get('n_traces', 'N/A')}")
        print(f"Timestamp: {meta.get('timestamp', 'N/A')}")

        print("\nAll metadata fields:")
        for k, v in meta.items():
            print(f"  {k}: {v}")
    else:
        print("No metadata found.")

    # Plot based on measurement type
    if 'data' in data:
        plt.plot(data['freq'], data['data'])
        plt.xlabel('Frequency (Hz)')
        plt.ylabel('Amplitude (dBm)')

        # Build title from metadata
        if meta is not None:
            measurement_type = meta.get('measurement_type', 'spectrum')
            title = f"Loaded {measurement_type.replace('_', ' ').title()}"

            # Add measurement details to title
            details = []
            if meta.get('preamp') is not None:
                details.append(f"Preamp: {'ON' if meta.get('preamp') else 'OFF'}")
            if meta.get('attenuation') is not None:
                details.append(f"Att: {meta.get('attenuation')} dB")
            if meta.get('n_avg') and meta.get('n_avg') > 1:
                details.append(f"Avg: {meta.get('n_avg')}")

            if details:
                title += f" ({', '.join(details)})"
        else:
            title = 'Loaded Spectrum Trace'

        plt.title(title)
        plt.show()
    elif 'waterfall' in data:
        plt.imshow(data['waterfall'], aspect='auto', origin='lower',
                   extent=[data['freq'][0], data['freq'][-1], 0,
                           data['waterfall'].shape[0]],
                   cmap='viridis')
        plt.xlabel('Frequency (Hz)')
        plt.ylabel('Time (trace index)')

        # Build title from metadata
        if meta is not None:
            title = 'Loaded Waterfall'
            details = []
            if meta.get('preamp') is not None:
                details.append(f"Preamp: {'ON' if meta.get('preamp') else 'OFF'}")
            if meta.get('attenuation') is not None:
                details.append(f"Att: {meta.get('attenuation')} dB")
            if meta.get('n_traces'):
                details.append(f"Traces: {meta.get('n_traces')}")

            if details:
                title += f" ({', '.join(details)})"
        else:
            title = 'Loaded Waterfall'
        plt.title(title)
        plt.colorbar(label='Amplitude (dBm)')
        plt.show()
    else:
        print("No plottable data found in file.")

if __name__ == "__main__":
    main()
