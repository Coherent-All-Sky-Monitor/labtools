"""Y-Factor Noise Temperature Measurement Tool.

This script implements the Y-factor method for measuring system noise temperature (Tsys)
using a spectrum analyzer. The Y-factor method compares measurements from a hot and cold
noise source to determine receiver noise characteristics.

Theory
------
The Y-factor method uses two noise sources at different temperatures to measure
system noise temperature:

    Y = P_hot / P_cold  (in linear scale)
    T_sys = (T_hot - Y * T_cold) / (Y - 1)

Where:
- P_hot, P_cold: Power measurements from hot and cold sources (converted from dB)
- T_hot, T_cold: Physical temperatures of the noise sources (K)
- T_sys: System noise temperature (K)

Standard reference temperatures:
- Hot load: ~295 K (room temperature)
- Cold load: ~77 K (liquid nitrogen) or ambient if no cooling available

Dependencies
------------
numpy : library
    For numerical operations and Y-factor calculations
matplotlib : library
    For plotting noise temperature results
spectrum_utils : module
    Local utilities for spectrum analyzer operations

Usage
-----
Run the script and follow prompts to:
1. Configure spectrum analyzer settings
2. Measure hot noise source
3. Measure cold noise source
4. View computed noise temperature results
5. Save measurement data
"""

import numpy as np
import matplotlib.pyplot as plt
import datetime
from spectrum_utils import SpectrumAnalyzer, pick_resource, prompt_sa_settings


def prompt_noise_source_temps():
    """Prompt user for noise source temperatures.
    
    Interactive function to collect hot and cold source temperatures with
    sensible defaults for common Y-factor setups.
    
    Returns
    -------
    tuple[float, float]
        Hot and cold source temperatures in Kelvin
        
    Examples
    --------
    >>> t_hot, t_cold = prompt_noise_source_temps()
    """
    print("\nNoise Source Temperature Setup")
    print("Enter temperatures in Kelvin (K)")
    
    # Hot source (typically room temperature)
    t_hot_str = input("Hot source temperature [default: 295K]: ").strip()
    if t_hot_str:
        try:
            t_hot = float(t_hot_str)
        except ValueError:
            print("Invalid temperature, using default 295K")
            t_hot = 295.0
    else:
        t_hot = 295.0
    
    # Cold source (typically liquid nitrogen or ambient)
    t_cold_str = input("Cold source temperature [default: 77K]: ").strip()
    if t_cold_str:
        try:
            t_cold = float(t_cold_str)
        except ValueError:
            print("Invalid temperature, using default 77K")
            t_cold = 77.0
    else:
        t_cold = 77.0
    
    print(f"Using T_hot = {t_hot}K, T_cold = {t_cold}K")
    return t_hot, t_cold


def calculate_yfactor_tsys(hot_db, cold_db, t_hot, t_cold):
    """Calculate Y-factor and system noise temperature.
    
    Converts dB measurements to linear scale, computes Y-factor, and calculates
    system noise temperature using the standard Y-factor formula.
    
    Parameters
    ----------
    hot_db : array-like
        Hot source power measurements in dB
    cold_db : array-like
        Cold source power measurements in dB
    t_hot : float
        Hot source temperature in Kelvin
    t_cold : float
        Cold source temperature in Kelvin
        
    Returns
    -------
    tuple[np.ndarray, np.ndarray]
        Y-factor (linear) and system noise temperature (K) arrays
        
    Notes
    -----
    The Y-factor method assumes:
    - Measurements are properly calibrated
    - System is linear
    - Noise sources are well-characterized
    
    Examples
    --------
    >>> y_factor, t_sys = calculate_yfactor_tsys(hot_data, cold_data, 295, 77)
    """
    # Convert dB to linear scale (power ratios)
    hot_linear = 10**(hot_db / 10)
    cold_linear = 10**(cold_db / 10)
    
    # Calculate Y-factor (ratio of hot to cold power)
    y_factor = hot_linear / cold_linear
    
    # Calculate system noise temperature
    # T_sys = (T_hot - Y * T_cold) / (Y - 1)
    t_sys = (t_hot - y_factor * t_cold) / (y_factor - 1)
    
    return y_factor, t_sys


def plot_yfactor_results(freq, hot_data, cold_data, y_factor, t_sys, t_hot, t_cold,
                        settings, instrument_id=None):
    """Plot Y-factor measurement results with save functionality.
    
    Creates comprehensive visualization showing hot/cold measurements, Y-factor,
    and computed noise temperature with interactive save interface.
    
    Parameters
    ----------
    freq : array-like
        Frequency values in Hz
    hot_data : array-like
        Hot source measurements in dB
    cold_data : array-like
        Cold source measurements in dB
    y_factor : array-like
        Computed Y-factor values (linear)
    t_sys : array-like
        Computed system noise temperature in K
    t_hot : float
        Hot source temperature in K
    t_cold : float
        Cold source temperature in K
    settings : dict
        Measurement settings dictionary
    instrument_id : str or None, optional
        Instrument identification for metadata
    """
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 8))
    plt.subplots_adjust(top=0.85, bottom=0.10, hspace=0.3, wspace=0.3)
    
    # Plot 1: Hot and Cold measurements
    ax1.plot(freq, hot_data, 'r-', label=f'Hot ({t_hot}K)', linewidth=1.5)
    ax1.plot(freq, cold_data, 'b-', label=f'Cold ({t_cold}K)', linewidth=1.5)
    ax1.set_xlabel('Frequency (Hz)')
    ax1.set_ylabel('Power (dBm)')
    ax1.set_title('Hot vs Cold Measurements')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Y-factor
    ax2.plot(freq, y_factor, 'g-', linewidth=1.5)
    ax2.set_xlabel('Frequency (Hz)')
    ax2.set_ylabel('Y-factor (linear)')
    ax2.set_title('Y-Factor vs Frequency')
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: System noise temperature
    ax3.plot(freq, t_sys, 'm-', linewidth=2)
    ax3.set_xlabel('Frequency (Hz)')
    ax3.set_ylabel('T_sys (K)')
    ax3.set_title('System Noise Temperature')
    ax3.grid(True, alpha=0.3)
    
    # Plot 4: Statistics summary
    ax4.axis('off')
    stats_text = f"""Y-Factor Statistics:
    Mean Y-factor: {np.mean(y_factor):.2f}
    Std Y-factor: {np.std(y_factor):.3f}
    
    T_sys Statistics:
    Mean T_sys: {np.mean(t_sys):.1f} K
    Std T_sys: {np.std(t_sys):.1f} K
    Min T_sys: {np.min(t_sys):.1f} K
    Max T_sys: {np.max(t_sys):.1f} K
    
    Measurement Settings:
    Hot source: {t_hot} K
    Cold source: {t_cold} K
    Freq range: {settings.get('fstart', 'N/A')} - {settings.get('fstop', 'N/A')}
    RBW: {settings.get('rbw', 'N/A')}"""
    
    ax4.text(0.05, 0.95, stats_text, transform=ax4.transAxes, fontsize=10,
             verticalalignment='top', fontfamily='monospace')
    
    # Overall title
    preamp_str = f"Preamp: {'ON' if settings.get('preamp') else 'OFF'}" if settings.get('preamp') is not None else "Preamp: N/A"
    att_str = f"Att: {settings.get('att')} dB" if settings.get('att') is not None else "Att: N/A"
    fig.suptitle(f'Y-Factor Noise Temperature Measurement ({preamp_str}, {att_str})', fontsize=14)
    
    # Add save functionality
    from matplotlib.widgets import Button, TextBox
    
    # TextBox for filename
    axbox = plt.axes([0.65, 0.92, 0.2, 0.04])
    text_box = TextBox(axbox, 'File name:', initial="")
    
    # Save button
    ax_save = plt.axes([0.87, 0.92, 0.1, 0.04])
    btn_save = Button(ax_save, 'Save')
    
    def save_handler(_):
        """Handle save button click for Y-factor data."""
        user_name = text_box.text.strip()
        if not user_name:
            print("No name entered. Not saving.")
            return
            
        iso_date = datetime.datetime.now().isoformat(timespec='seconds').replace(':', '-')
        base = f"{iso_date}_yfactor_{user_name}"
        png_name = base + ".png"
        npz_name = base + ".npz"
        
        # Save plot
        fig.savefig(png_name, dpi=300, bbox_inches='tight')
        
        # Save data with comprehensive metadata
        metadata = {
            'instrument': instrument_id or '',
            'measurement_type': 'yfactor_noise_temperature',
            'freq_start': settings.get('fstart', ''),
            'freq_stop': settings.get('fstop', ''),
            'rbw': settings.get('rbw', ''),
            'preamp': settings.get('preamp'),
            'attenuation': settings.get('att'),
            't_hot_kelvin': t_hot,
            't_cold_kelvin': t_cold,
            'mean_yfactor': float(np.mean(y_factor)),
            'std_yfactor': float(np.std(y_factor)),
            'mean_tsys_kelvin': float(np.mean(t_sys)),
            'std_tsys_kelvin': float(np.std(t_sys)),
            'min_tsys_kelvin': float(np.min(t_sys)),
            'max_tsys_kelvin': float(np.max(t_sys)),
            'timestamp': iso_date
        }
        
        np.savez(npz_name, 
                freq=freq, 
                hot_data=hot_data, 
                cold_data=cold_data,
                y_factor=y_factor,
                t_sys=t_sys,
                metadata=metadata)
        
        print(f"Saved plot as {png_name} and data as {npz_name}")
    
    btn_save.on_clicked(save_handler)
    plt.show()


def main():
    """Main Y-factor measurement routine.
    
    Orchestrates the complete Y-factor measurement process including instrument
    setup, data acquisition, calculation, and visualization.
    """
    print("Y-Factor Noise Temperature Measurement")
    print("=" * 40)
    
    # Select and connect to spectrum analyzer
    print("\nStep 1: Connect to Spectrum Analyzer")
    resource = pick_resource()
    sa = SpectrumAnalyzer(resource)
    instrument_id = sa.inst.query('*IDN?').strip()
    
    # Get measurement settings
    print("\nStep 2: Configure Measurement Settings")
    settings = prompt_sa_settings()
    sa.setup(
        fstart=settings['fstart'],
        fstop=settings['fstop'],
        rbw=settings['rbw'],
        preamp=settings['preamp'],
        att=settings['att']
    )
    
    # Get noise source temperatures
    print("\nStep 3: Configure Noise Sources")
    t_hot, t_cold = prompt_noise_source_temps()
    
    # Measure hot source
    print(f"\nStep 4: Hot Source Measurement ({t_hot}K)")
    input("Connect HOT noise source and press Enter to measure...")
    freq, hot_data = sa.acquire_trace()
    print(f"Hot measurement complete: {len(hot_data)} points acquired")
    
    # Measure cold source
    print(f"\nStep 5: Cold Source Measurement ({t_cold}K)")
    input("Connect COLD noise source and press Enter to measure...")
    _, cold_data = sa.acquire_trace()
    print(f"Cold measurement complete: {len(cold_data)} points acquired")
    
    # Calculate Y-factor and noise temperature
    print("\nStep 6: Calculate Y-Factor and Noise Temperature")
    y_factor, t_sys = calculate_yfactor_tsys(hot_data, cold_data, t_hot, t_cold)
    
    # Display results summary
    print("\nResults Summary:")
    print(f"Mean Y-factor: {np.mean(y_factor):.3f}")
    print(f"Mean T_sys: {np.mean(t_sys):.1f} K")
    print(f"T_sys range: {np.min(t_sys):.1f} - {np.max(t_sys):.1f} K")
    
    # Plot results
    print("\nStep 7: Display Results")
    plot_yfactor_results(freq, hot_data, cold_data, y_factor, t_sys, 
                        t_hot, t_cold, settings, instrument_id)
    
    # Cleanup
    sa.close()
    print("\nMeasurement complete!")


if __name__ == "__main__":
    main()
