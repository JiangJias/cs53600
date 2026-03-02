# Installation Guide

## Prerequisites

### System Requirements

One of the following:
- **Linux**: Ubuntu 22.04+ (recommended)
- **Windows**: WSL2 with Ubuntu 22.04+
- **macOS**: Not recommended (TCP_INFO may not work)

### Software Requirements

- Python 3.10 or higher
- pip (Python package manager)
- Docker (optional, but recommended)

---

## Installation Methods

### Method 1: Docker (Recommended)

This is the easiest method and ensures a consistent environment.

#### Step 1: Install Docker

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install docker.io
sudo systemctl start docker
sudo systemctl enable docker
```

**Windows:**
1. Install Docker Desktop for Windows
2. Enable WSL2 integration
3. Restart your computer

**Verification:**
```bash
docker --version
```

#### Step 2: Build Docker Image

```bash
cd cs53600/Assignment2
docker build -t iperf-assignment .
```

This will:
- Create Ubuntu 24.04 container
- Install Python and dependencies
- Set up the environment

#### Step 3: Verify Installation

```bash
docker run --rm iperf-assignment python3 --version
```

You should see Python 3.x.x

#### Step 4: Run the Experiment

```bash
docker run --rm --network host \
  -v $(pwd)/results:/app/results \
  -v $(pwd)/plots:/app/plots \
  -v $(pwd)/models:/app/models \
  iperf-assignment \
  python3 run_experiment.py servers.txt --n-servers 5 --duration 30
```

**Done!** Skip to the "Verifying Installation" section.

---

### Method 2: Local Python Installation

This method requires manual dependency installation.

#### Step 1: Check Python Version

```bash
python3 --version
```

Required: Python 3.10 or higher

If you don't have Python 3.10+:

**Ubuntu:**
```bash
sudo apt-get update
sudo apt-get install python3.10 python3.10-pip
```

#### Step 2: Install Python Dependencies

```bash
cd cs53600/Assignment2
pip3 install -r requirements.txt
```

This installs:
- numpy >= 1.24.0
- pandas >= 2.0.0
- matplotlib >= 3.7.0
- scikit-learn >= 1.3.0
- scipy >= 1.11.0

**Note**: On some systems you may need to use `--user` flag:
```bash
pip3 install --user -r requirements.txt
```

#### Step 3: Verify Installation

```bash
python3 test_setup.py
```

This will check:
- ✓ Python package imports
- ✓ TCP_INFO availability
- ✓ Network connectivity
- ✓ File structure

**Expected output:**
```
================================================================================
Assignment 2 Setup Test
================================================================================
Testing package imports...
  ✓ numpy
  ✓ pandas
  ✓ matplotlib
  ✓ sklearn
  ✓ scipy
  ✓ json
  ✓ csv
All packages imported successfully!

Testing TCP_INFO availability...
  ✓ TCP_INFO is available

Testing network connectivity...
  ✓ Connected to 8.8.8.8:53
Network connectivity OK!

Testing file structure...
  ✓ iperf_client.py
  ✓ data_collector.py
  ...
All required files present!

================================================================================
Test Summary
================================================================================
✓ PASS: Package imports
✓ PASS: TCP_INFO availability
✓ PASS: Network connectivity
✓ PASS: File structure
================================================================================

✓ All tests passed! Setup is complete.
```

#### Step 4: Run the Experiment

```bash
python3 run_experiment.py servers.txt --n-servers 5 --duration 30
```

---

## Verifying Installation

### Quick Test

Run a minimal test to verify everything works:

```bash
# Using Docker
docker run --rm --network host \
  -v $(pwd)/results:/app/results \
  iperf-assignment \
  python3 iperf_client.py iperf3.velnet.co.uk

# Using local Python
python3 iperf_client.py iperf3.velnet.co.uk
```

**Expected output:**
```
INFO - Connecting to iperf3.velnet.co.uk:5201
INFO - Control connection established
INFO - Parameters sent to server
INFO - Data connection established
INFO - Starting data transfer for 10 seconds
INFO - Data transfer completed
Test successful!
Duration: 10s
Avg throughput: XX.XX Mbps
```

---

## Troubleshooting

### Issue: "No module named 'numpy'"

**Solution**: Install dependencies
```bash
pip3 install -r requirements.txt
```

### Issue: "TCP_INFO not available"

**Cause**: Not on Linux or kernel too old

**Solutions**:
1. Use WSL2 on Windows
2. Use a Linux VM
3. The code will still work but with limited TCP statistics

### Issue: "Connection refused" when testing iPerf

**Cause**: Server may be offline or blocking connections

**Solutions**:
1. Try a different server:
   ```bash
   python3 iperf_client.py bouygues.iperf.fr
   ```
2. Check https://iperf3serverlist.net/ for working servers
3. The main script automatically skips non-working servers

### Issue: Docker "permission denied"

**Solution**: Add your user to docker group
```bash
sudo usermod -aG docker $USER
newgrp docker
```

### Issue: "ModuleNotFoundError: No module named 'sklearn'"

**Solution**: The package is scikit-learn but imports as sklearn
```bash
pip3 install scikit-learn
```

### Issue: WSL2 network not working

**Solution**: Restart WSL networking
```bash
# In PowerShell (as Administrator)
wsl --shutdown
# Start WSL again
```

### Issue: Matplotlib display errors

**Cause**: The code uses non-interactive backend (Agg)

**Solution**: This is expected. Plots are saved to files, not displayed on screen.

---

## Platform-Specific Notes

### Ubuntu/Debian

Everything should work out of the box. If you get permission errors with Docker:
```bash
sudo usermod -aG docker $USER
newgrp docker
```

### Windows with WSL2

1. Install WSL2 from Microsoft Store
2. Install Ubuntu 22.04 from Microsoft Store
3. Open Ubuntu terminal
4. Follow the local Python installation steps

**Network access**: Use `--network host` with Docker or ensure WSL2 has internet access.

### macOS

**Not recommended** because:
- TCP_INFO may not be available or have different fields
- Some socket options may not work

If you must use macOS:
1. Use Docker Desktop
2. Expect limited TCP statistics
3. The code will handle missing fields gracefully

---

## Uninstallation

### Docker

```bash
docker rmi iperf-assignment
```

### Local Python

```bash
pip3 uninstall numpy pandas matplotlib scikit-learn scipy
```

---

## Next Steps

After successful installation:

1. **Read the documentation**
   ```bash
   cat README.md
   cat QUICKSTART.md
   ```

2. **Run a quick test** (5 minutes)
   ```bash
   python3 run_experiment.py servers.txt --n-servers 3 --duration 10
   ```

3. **Run the full experiment** (30 minutes)
   ```bash
   python3 run_experiment.py servers.txt --n-servers 10 --duration 60
   ```

4. **Check the results**
   ```bash
   ls results/
   ls plots/
   cat results/summary_statistics.csv
   ```

5. **Fill out the report**
   - Use `REPORT_TEMPLATE.md` as a guide
   - Include plots from `plots/` directory
   - Reference code from your repository

---

## Getting Help

1. **Verify setup**: `python3 test_setup.py`
2. **Check logs**: `cat experiment.log`
3. **Test components individually**:
   - iPerf client: `python3 iperf_client.py <server>`
   - Visualization: `python3 visualization.py`
   - ML model: `python3 ml_model.py`

4. **Read documentation**:
   - `README.md` - Comprehensive guide
   - `QUICKSTART.md` - Quick start
   - `PROJECT_SUMMARY.md` - Technical details

---

## Minimum System Requirements

- **CPU**: 1 core (2+ recommended)
- **RAM**: 2 GB (4 GB recommended)
- **Disk**: 1 GB free space
- **Network**: Internet connection with reasonable bandwidth
- **OS**: Linux kernel 4.x or higher (for full TCP_INFO support)

---

## Support

For issues related to:
- **Setup/Installation**: Check this file
- **Usage**: Check `README.md` and `QUICKSTART.md`
- **Implementation details**: Check `PROJECT_SUMMARY.md`
- **Report writing**: Check `REPORT_TEMPLATE.md`

---

**Installation Complete!** You're ready to run the experiment.
