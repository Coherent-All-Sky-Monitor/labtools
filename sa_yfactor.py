#!/usr/bin/env python3
"""
Y-Factor System Temperature Measurement Script
=============================================

This script performs hot and cold RF measurements using the Y-factor method
to determine system temperature (Tsys). All results are based solely on 
spectrum analyzer measurements and user-supplied load temperatures.

Dependencies:
    - pyvisa
    - numpy
    - matplotlib
    - labtools package
"""

import datetime
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Button, TextBox

from labtools import SpectrumAnalyzer, pick_resource
from labtools.core.data_handler import DataHandler
from labtools.utils.input_helpers import get_frequency_settings


def get_measurement_parameters():
    """Prompt user for physical temperatures and number of averages."""
    print("\n=== Measurement Parameters ===")
    # Get physical temperatures
    t_hot_input = input("Enter hot load temperature in Kelvin [default: 293.15]: ").strip()
    try:
        t_hot = float(t_hot_input) if t_hot_input else 293.15
    except ValueError:
        print("Invalid hot temperature, using default 293.15 K")
        t_hot = 293.15

    t_cold_input = input("Enter cold load temperature in Kelvin [default: 77.15]: ").strip()
    try:
        t_cold = float(t_cold_input) if t_cold_input else 77.15
    except ValueError:
        print("Invalid cold temperature, using default 77.15 K")
        t_cold = 77.15

    n_avg_input = input("Enter number of averages per measurement [default: 10]: ").strip()
    try:
        n_avg = int(n_avg_input) if n_avg_input else 10
        if n_avg < 1:
            raise ValueError
    except ValueError:
        print("Invalid number of averages, using default 10")
        n_avg = 10

    return {
        't_hot': t_hot,
        't_cold': t_cold,
        'n_avg': n_avg
    }

def acquire_averaged_power_spectrum(sa, n_avg, measurement_name):
    """
    Acquire averaged power spectrum measurements.
    """
    print(f"\nAcquiring {measurement_name} measurement ({n_avg} averages)...")

    # Get frequency axis from first trace
    freq, first_data = sa.acquire_trace_with_freq()
    avg_power = 10**(np.array(first_data) / 10.0)  # dBm to mW

    for i in range(1, n_avg):
        print(f"  Trace {i+1}/{n_avg}")
        data = sa.acquire_trace_fast()
        power_linear = 10**(np.array(data) / 10.0)
        avg_power += power_linear

    avg_power /= n_avg
    print(f"  {measurement_name} measurement complete!")
    return freq, avg_power

def calculate_yfactor_results(freq, p_hot, p_cold, params):
    """
    Calculate Y-factor and system temperature from spectrum analyzer data.
    """
    y_factor = p_hot / p_cold
    y_factor_db = 10.0 * np.log10(y_factor)
    t_sys = (params['t_hot'] - y_factor * params['t_cold']) / (y_factor - 1.0)

    avg_y_factor_db = np.mean(y_factor_db)
    avg_tsys = np.mean(t_sys)
    return {
        'freq': freq,
        'y_factor_linear': y_factor,
        'y_factor_db': y_factor_db,
        't_sys': t_sys,
        'avg_y_factor_db': avg_y_factor_db,
        'avg_tsys': avg_tsys
    }

def create_yfactor_plots(results, params, hot_dbm, cold_dbm, 
                        preamp=None, att=None, instrument_id=None,
                        freq_start=None, freq_stop=None, rbw=None):
    """Plot Hot/Cold, Y-factor, and system temperature."""
    fig = plt.figure(figsize=(12, 8))

    # Plot 1: Raw Hot/Cold Measurements
    ax1 = plt.subplot(2, 2, 1)
    ax1.plot(results['freq'], hot_dbm, 'r-', label='Hot Load', linewidth=1.5)
    ax1.plot(results['freq'], cold_dbm, 'b-', label='Cold Load', linewidth=1.5)
    ax1.set_xlabel('Frequency (Hz)')
    ax1.set_ylabel('Power (dBm)')
    ax1.set_title('Hot and Cold Load Measurements')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Plot 2: Y-Factor
    ax2 = plt.subplot(2, 2, 2)
    ax2.plot(results['freq'], results['y_factor_db'], 'g-', linewidth=1.5)
    ax2.set_xlabel('Frequency (Hz)')
    ax2.set_ylabel('Y-Factor (dB)')
    ax2.set_title(f'Y-Factor (Avg: {results["avg_y_factor_db"]:.2f} dB)')
    ax2.grid(True, alpha=0.3)

    # Plot 3: System Temperature
    ax3 = plt.subplot(2, 1, 2)
    ax3.plot(results['freq'], results['t_sys'], 'c-', linewidth=1.5)
    ax3.set_xlabel('Frequency (Hz)')
    ax3.set_ylabel('System Temperature (K)')
    ax3.set_title(f'System Temperature (Avg: {results["avg_tsys"]:.1f} K)')
    ax3.grid(True, alpha=0.3)

    # Title String
    preamp_str = f"Preamp: {'ON' if preamp else 'OFF'}" if preamp is not None else "Preamp: N/A"
    att_str = f"Att: {att} dB" if att is not None else "Att: N/A"
    fig.suptitle(f'Y-Factor System Temp Measurement ({preamp_str}, {att_str})', 
                 fontsize=14, fontweight='bold')

    plt.tight_layout()
    plt.subplots_adjust(top=0.93, bottom=0.08)

    add_yfactor_save_widget(fig, results, params, hot_dbm, cold_dbm,
                           preamp, att, instrument_id, freq_start, freq_stop, rbw)
    plt.show()

def add_yfactor_save_widget(fig, results, params, hot_dbm, cold_dbm,
                           preamp, att, instrument_id, freq_start, freq_stop, rbw):
    """Add save widget for Y-factor results."""
    axbox = plt.axes([0.65, 0.02, 0.2, 0.04])
    text_box = TextBox(axbox, 'File name:', initial="")
    ax_save = plt.axes([0.87, 0.02, 0.1, 0.04])
    btn_save = Button(ax_save, 'Save')

    def save_handler(_):
        user_name = text_box.text.strip()
        if not user_name:
            print("No name entered. Not saving.")
            return
        iso_date = datetime.datetime.now().isoformat(timespec='seconds').replace(':', '-')
        base = f"{iso_date}_{user_name}"

        # Save plot
        png_name = base + "_yfactor.png"
        fig.savefig(png_name, dpi=300, bbox_inches='tight')

        # Metadata
        metadata = DataHandler.create_metadata(
            instrument_id=instrument_id or '',
            freq_start=freq_start or '',
            freq_stop=freq_stop or '',
            rbw=rbw or '',
            preamp=preamp,
            attenuation=att,
            measurement_type='yfactor_system_temperature',
            n_avg=params['n_avg']
        )
        metadata.update({
            't_hot_k': params['t_hot'],
            't_cold_k': params['t_cold'],
            'avg_y_factor_db': results['avg_y_factor_db'],
            'avg_system_temp_k': results['avg_tsys']
        })

        # Save results
        npy_name = base + "_yfactor.npz"
        np.savez(npy_name,
                 freq=results['freq'],
                 hot_data_dbm=hot_dbm,
                 cold_data_dbm=cold_dbm,
                 y_factor_db=results['y_factor_db'],
                 system_temp_k=results['t_sys'],
                 metadata=metadata)

        print("\nSaved Y-factor measurement:")
        print(f"  Plot: {png_name}")
        print(f"  Data: {npy_name}")
        print(f"  Average Y-factor: {results['avg_y_factor_db']:.2f} dB")
        print(f"  Average System Temperature: {results['avg_tsys']:.1f} K")

    btn_save.on_clicked(save_handler)

def main():
    """Main function for Y-factor measurement using only analyzer and physical loads."""
    print("=" * 60)
    print("Y-FACTOR SYSTEM TEMPERATURE MEASUREMENT")
    print("=" * 60)
    print("This script measures hot and cold RF spectra to determine system temperature.")
    print()

    # Connect to instrument
    resource = pick_resource()
    with SpectrumAnalyzer(resource) as sa:
        fstart, fstop, rbw = get_frequency_settings()

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

        params = get_measurement_parameters()

        sa.setup(fstart=fstart, fstop=fstop, rbw=rbw, preamp=preamp, att=att)

        print("\n" + "=" * 40)
        print("MEASUREMENT SEQUENCE")
        print("=" * 40)

        # Measure hot load
        input("\nConnect HOT load and press Enter to start hot measurement...")
        freq, p_hot = acquire_averaged_power_spectrum(sa, params['n_avg'], "HOT LOAD")
        # Measure cold load
        input("\nConnect COLD load and press Enter to start cold measurement...")
        _, p_cold = acquire_averaged_power_spectrum(sa, params['n_avg'], "COLD LOAD")

        # Convert back to dBm for display
        hot_dbm = 10.0 * np.log10(p_hot)
        cold_dbm = 10.0 * np.log10(p_cold)

        results = calculate_yfactor_results(freq, p_hot, p_cold, params)

        # Display results
        print("\n" + "=" * 40)
        print("MEASUREMENT RESULTS")
        print("=" * 40)
        print(f"Average Y-factor: {results['avg_y_factor_db']:.2f} dB")
        print(f"Average System Temperature: {results['avg_tsys']:.1f} K")
        print(f"Hot load temperature: {params['t_hot']:.1f} K")
        print(f"Cold load temperature: {params['t_cold']:.1f} K")

        # Plot and save
        create_yfactor_plots(results, params, hot_dbm, cold_dbm,
                             preamp=preamp, att=att, 
                             instrument_id=sa.instrument_id,
                             freq_start=fstart,
                             freq_stop=fstop,
                             rbw=rbw)

if __name__ == "__main__":
    main()
