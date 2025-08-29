"""
Spectrum Analyzer Data Reader
----------------------------
This script loads .npz files saved by the spectrum analyzer scripts, displays metadata,
and plots the data.

Usage:
    Run the script and enter the filename (with or without .npz extension) when prompted.

Dependencies:
    - numpy
    - matplotlib
"""

import os
import numpy as np
import matplotlib.pyplot as plt


def main():
    """
    Main function that loads and displays spectrum analyzer data files.
    Prompts user for filename, loads .npz file, displays metadata, and plots data.
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
