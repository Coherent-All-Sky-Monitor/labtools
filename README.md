# Lab Tools

Scripts and Software to control and record measurements from Lab instruments.

## Current Scripts

- **`sa.py`** - Single trace acquisition.
- **`sa_avg.py`** - Multiple trace averaging.
- **`sa_waterfall.py`** - Live waterfall display (frequency vs time).
- **`sa_yfactor.py`** - Y-factor noise temperature measurement.
- **`sa_read.py`** - Load and display saved measurement files/

## Hardware Connection Setup

### Connecting to the Spectrum Analyzer

1. **Physical Connection**: Connect your laptop/PC to the spectrum analyzer using a standard RJ45 Ethernet cable.

2. **Find Network Settings on SA**:
   - Navigate using buttons on the SA: **System → Interface → LAN**
   - Note the IP address and subnet mask displayed

3. **Configure Your Computer's Network**:
   - Manually set your computer's network interface to match the SA's subnet
   - Use the same subnet mask as shown on the SA
   - Choose an IP address in the same range but different from the SA

   **Example:**
   - If SA shows IP: `192.168.1.100` and subnet: `255.255.255.0`
   - Set your computer to: `192.168.1.50` with subnet `255.255.255.0`

4. **Test Connection**: Ping the SA's IP address to verify connectivity

*Note: A DHCP method exists but manual IP configuration is more reliable for instrument control.*

## Dependencies

```bash
pip install pyvisa numpy matplotlib
```

## Usage

Run any script and follow the interactive prompts:

```bash
python sa.py
```

## Y-Factor Noise Temperature Measurements

The `sa_yfactor.py` script implements the standard Y-factor method for measuring system noise temperature.

### Theory

The Y-factor method uses two calibrated noise sources at different temperatures:

```text
Y = P_hot / P_cold  (linear power ratio)
T_sys = (T_hot - Y × T_cold) / (Y - 1)
```

Where:

- **T_hot**: Hot source temperature (~295K room temperature)
- **T_cold**: Cold source temperature (~77K liquid nitrogen or ambient)
- **P_hot, P_cold**: Power measurements from spectrum analyzer (converted from dB)
- **T_sys**: Calculated system noise temperature

### Y-Factor Usage

```bash
python sa_yfactor.py
```

The script will guide through:

1. Spectrum analyzer setup (frequency range, RBW, etc.)
2. Noise source temperature configuration
3. Hot source measurement (manual connection prompt)
4. Cold source measurement (manual connection prompt)
5. Automatic Y-factor and T_sys calculation
6. Results visualization and data saving