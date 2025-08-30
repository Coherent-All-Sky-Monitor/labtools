# Lab Tools

Scripts and Software to control and record measurements from Lab instruments and conduct common experiments.

## Current Scripts

- **`sa.py`** - Single trace acquisition.
- **`sa_avg.py`** - Multiple trace averaging.
- **`sa_waterfall.py`** - Live waterfall display (frequency vs time).
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
