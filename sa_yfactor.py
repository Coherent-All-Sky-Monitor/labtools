#!/usr/bin/env python3
"""
Y-Factor Noise Figure Measurement Script
========================================

This script performs hot and cold RF measurements using the Y-factor method
to determine noise figure (NF) and system temperature (Tsys). The Y-factor
method is a standard technique for noise figure measurement.

Theory:
- Y = P_hot / P_cold (power ratio)
- NF = ENR / (Y - 1)  [in linear units]
- NF_dB = 10 * log10(NF)
- Tsys = (T_hot - Y * T_cold) / (Y - 1)

Where:
- ENR = Excess Noise Ratio of noise source (dB)
- T_hot, T_cold = Physical temperatures of hot/cold loads (K)
- P_hot, P_cold = Measured power levels (linear)

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

# Import from the refactored labtools package
from labtools import SpectrumAnalyzer, pick_resource
from labtools.core.data_handler import DataHandler
from labtools.utils.input_helpers import get_frequency_settings


def get_yfactor_parameters():
    """
    Get Y-factor measurement parameters from user input.
    
    Returns:
        dict: Dictionary containing measurement parameters.
    """
    print("\n=== Y-Factor Measurement Parameters ===")
    
    # Get ENR (Excess Noise Ratio) of noise source
    enr_input = input("Enter noise source ENR in dB [default: 15.0]: ").strip()
    try:
        enr_db = float(enr_input) if enr_input else 15.0
    except ValueError:
        print("Invalid ENR value, using default 15.0 dB")
        enr_db = 15.0
    
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
    
    # Get number of averages for each measurement
    n_avg_input = input("Enter number of averages per measurement [default: 10]: ").strip()
    try:
        n_avg = int(n_avg_input) if n_avg_input else 10
        if n_avg < 1:
            raise ValueError
    except ValueError:
        print("Invalid number of averages, using default 10")
        n_avg = 10
    
    return {
        'enr_db': enr_db,
        'enr_linear': 10**(enr_db / 10.0),
        't_hot': t_hot,
        't_cold': t_cold,
        'n_avg': n_avg
    }


def acquire_averaged_power_spectrum(sa, n_avg, measurement_name):
    """
    Acquire averaged power spectrum measurements.
    
    Args:
        sa (SpectrumAnalyzer): Spectrum analyzer instance.
        n_avg (int): Number of traces to average.
        measurement_name (str): Name of measurement for display.
        
    Returns:
        tuple: (frequency array, averaged power data in linear units)
    """
    print(f"\nAcquiring {measurement_name} measurement ({n_avg} averages)...")
    
    # Get frequency axis from first trace
    freq, first_data = sa.acquire_trace_with_freq()
    
    # Convert dBm to linear power (mW)
    avg_power = 10**(np.array(first_data) / 10.0)
    
    # Acquire remaining traces
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
    Calculate Y-factor, noise figure, and system temperature.
    
    Args:
        freq (array): Frequency array.
        p_hot (array): Hot load power measurements (linear).
        p_cold (array): Cold load power measurements (linear).
        params (dict): Y-factor measurement parameters.
        
    Returns:
        dict: Dictionary containing calculated results.
    """
    # Calculate Y-factor (linear power ratio)
    y_factor = p_hot / p_cold
    
    # Calculate noise figure in linear units
    nf_linear = params['enr_linear'] / (y_factor - 1.0)
    
    # Convert to dB
    nf_db = 10.0 * np.log10(nf_linear)
    y_factor_db = 10.0 * np.log10(y_factor)
    
    # Calculate system temperature
    t_sys = (params['t_hot'] - y_factor * params['t_cold']) / (y_factor - 1.0)
    
    # Calculate average values for summary
    avg_y_factor_db = np.mean(y_factor_db)
    avg_nf_db = np.mean(nf_db)
    avg_tsys = np.mean(t_sys)
    
    return {
        'freq': freq,
        'y_factor_linear': y_factor,
        'y_factor_db': y_factor_db,
        'nf_linear': nf_linear,
        'nf_db': nf_db,
        't_sys': t_sys,
        'avg_y_factor_db': avg_y_factor_db,
        'avg_nf_db': avg_nf_db,
        'avg_tsys': avg_tsys
    }


def create_yfactor_plots(results, params, hot_dbm, cold_dbm, 
                        preamp=None, att=None, instrument_id=None,
                        freq_start=None, freq_stop=None, rbw=None):
    """
    Create comprehensive plots for Y-factor measurement results.
    
    Args:
        results (dict): Calculated Y-factor results.
        params (dict): Measurement parameters.
        hot_dbm (array): Hot load data in dBm.
        cold_dbm (array): Cold load data in dBm.
        preamp (bool): Preamp state.
        att (float): Attenuation setting.
        instrument_id (str): Instrument identification.
        freq_start (str): Start frequency setting.
        freq_stop (str): Stop frequency setting.
        rbw (str): Resolution bandwidth setting.
    """
    # Create figure with subplots
    fig = plt.figure(figsize=(12, 10))
    
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
    
    # Plot 3: Noise Figure
    ax3 = plt.subplot(2, 2, 3)
    ax3.plot(results['freq'], results['nf_db'], 'm-', linewidth=1.5)
    ax3.set_xlabel('Frequency (Hz)')
    ax3.set_ylabel('Noise Figure (dB)')
    ax3.set_title(f'Noise Figure (Avg: {results["avg_nf_db"]:.2f} dB)')
    ax3.grid(True, alpha=0.3)
    
    # Plot 4: System Temperature
    ax4 = plt.subplot(2, 2, 4)
    ax4.plot(results['freq'], results['t_sys'], 'c-', linewidth=1.5)
    ax4.set_xlabel('Frequency (Hz)')
    ax4.set_ylabel('System Temperature (K)')
    ax4.set_title(f'System Temperature (Avg: {results["avg_tsys"]:.1f} K)')
    ax4.grid(True, alpha=0.3)
    
    # Add overall title with measurement details
    preamp_str = f"Preamp: {'ON' if preamp else 'OFF'}" if preamp is not None else "Preamp: N/A"
    att_str = f"Att: {att} dB" if att is not None else "Att: N/A"
    fig.suptitle(f'Y-Factor Noise Figure Measurement '
                f'(ENR: {params["enr_db"]:.1f} dB, {preamp_str}, {att_str})', 
                fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    plt.subplots_adjust(top=0.93, bottom=0.08)
    
    # Add save widgets
    add_yfactor_save_widget(fig, results, params, hot_dbm, cold_dbm,
                           preamp, att, instrument_id, freq_start, freq_stop, rbw)
    
    plt.show()


def add_yfactor_save_widget(fig, results, params, hot_dbm, cold_dbm,
                           preamp, att, instrument_id, freq_start, freq_stop, rbw):
    """
    Add save functionality widget to the Y-factor plot.
    
    Args:
        fig: Matplotlib figure object.
        results (dict): Calculated results.
        params (dict): Measurement parameters.
        hot_dbm (array): Hot load data in dBm.
        cold_dbm (array): Cold load data in dBm.
        preamp (bool): Preamp state.
        att (float): Attenuation setting.
        instrument_id (str): Instrument identification.
        freq_start (str): Start frequency setting.
        freq_stop (str): Stop frequency setting.
        rbw (str): Resolution bandwidth setting.
    """
    # TextBox for filename
    axbox = plt.axes([0.65, 0.02, 0.2, 0.04])
    text_box = TextBox(axbox, 'File name:', initial="")
    
    # Save button
    ax_save = plt.axes([0.87, 0.02, 0.1, 0.04])
    btn_save = Button(ax_save, 'Save')
    
    def save_handler(_):
        """Handle save button click."""
        user_name = text_box.text.strip()
        if not user_name:
            print("No name entered. Not saving.")
            return
        
        # Generate timestamp
        iso_date = (datetime.datetime.now()
                   .isoformat(timespec='seconds')
                   .replace(':', '-'))
        base = f"{iso_date}_{user_name}"
        
        # Save plot
        png_name = base + "_yfactor.png"
        fig.savefig(png_name, dpi=300, bbox_inches='tight')
        
        # Create comprehensive metadata
        metadata = DataHandler.create_metadata(
            instrument_id=instrument_id or '',
            freq_start=freq_start or '',
            freq_stop=freq_stop or '',
            rbw=rbw or '',
            preamp=preamp,
            attenuation=att,
            measurement_type='yfactor_noise_figure',
            n_avg=params['n_avg']
        )
        
        # Add Y-factor specific metadata
        metadata.update({
            'enr_db': params['enr_db'],
            't_hot_k': params['t_hot'],
            't_cold_k': params['t_cold'],
            'avg_y_factor_db': results['avg_y_factor_db'],
            'avg_noise_figure_db': results['avg_nf_db'],
            'avg_system_temp_k': results['avg_tsys']
        })
        
        # Save comprehensive data
        npy_name = base + "_yfactor.npz"
        np.savez(npy_name, 
                freq=results['freq'],
                hot_data_dbm=hot_dbm,
                cold_data_dbm=cold_dbm,
                y_factor_db=results['y_factor_db'],
                noise_figure_db=results['nf_db'],
                system_temp_k=results['t_sys'],
                metadata=metadata)
        
        print("\nSaved Y-factor measurement:")
        print(f"  Plot: {png_name}")
        print(f"  Data: {npy_name}")
        print(f"  Average Y-factor: {results['avg_y_factor_db']:.2f} dB")
        print(f"  Average Noise Figure: {results['avg_nf_db']:.2f} dB")
        print(f"  Average System Temperature: {results['avg_tsys']:.1f} K")
    
    btn_save.on_clicked(save_handler)


def main():
    """
    Main function for Y-factor noise figure measurement.
    """
    print("=" * 60)
    print("Y-FACTOR NOISE FIGURE MEASUREMENT")
    print("=" * 60)
    print("This script performs hot and cold RF measurements to determine")
    print("noise figure and system temperature using the Y-factor method.")
    print()
    
    # Connect to instrument
    resource = pick_resource()
    
    with SpectrumAnalyzer(resource) as sa:
        # Get measurement settings
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
        
        # Get Y-factor specific parameters
        yfactor_params = get_yfactor_parameters()
        
        # Setup spectrum analyzer
        sa.setup(fstart=fstart, 
                fstop=fstop, 
                rbw=rbw,
                preamp=preamp, 
                att=att)
        
        print("\n" + "=" * 40)
        print("MEASUREMENT SEQUENCE")
        print("=" * 40)
        
        # Measure hot load
        input("\nConnect HOT load and press Enter to start hot measurement...")
        freq, p_hot = acquire_averaged_power_spectrum(
            sa, yfactor_params['n_avg'], "HOT LOAD")
        
        # Measure cold load
        input("\nConnect COLD load and press Enter to start cold measurement...")
        _, p_cold = acquire_averaged_power_spectrum(
            sa, yfactor_params['n_avg'], "COLD LOAD")
        
        # Convert back to dBm for display
        hot_dbm = 10.0 * np.log10(p_hot)
        cold_dbm = 10.0 * np.log10(p_cold)
        
        # Calculate Y-factor results
        print("\nCalculating Y-factor, noise figure, and system temperature...")
        results = calculate_yfactor_results(freq, p_hot, p_cold, yfactor_params)
        
        # Display summary
        print("\n" + "=" * 40)
        print("MEASUREMENT RESULTS")
        print("=" * 40)
        print(f"Average Y-factor: {results['avg_y_factor_db']:.2f} dB")
        print(f"Average Noise Figure: {results['avg_nf_db']:.2f} dB")
        print(f"Average System Temperature: {results['avg_tsys']:.1f} K")
        print(f"ENR used: {yfactor_params['enr_db']:.1f} dB")
        print(f"Hot load temperature: {yfactor_params['t_hot']:.1f} K")
        print(f"Cold load temperature: {yfactor_params['t_cold']:.1f} K")
        
        # Create plots
        create_yfactor_plots(results, yfactor_params, hot_dbm, cold_dbm,
                           preamp=preamp, att=att, 
                           instrument_id=sa.instrument_id,
                           freq_start=fstart,
                           freq_stop=fstop,
                           rbw=rbw)


if __name__ == "__main__":
    main()
