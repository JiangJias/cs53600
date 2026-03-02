# Quick Start Guide - Assignment 3

Get up and running in 5 minutes!

---

## Option 1: Standalone Simulation (No NS-3 Required) ⚡

**Best for**: Quick testing and demonstration

```bash
# Install Python dependencies
pip3 install -r requirements.txt

# Run simulation
./run_standalone.py
```

**Output**: Results in ~2-5 minutes
- `flow_completion_times.csv`
- Plots in `plots/` directory

**Note**: This is a simplified simulation. For accurate results, use NS-3.

---

## Option 2: Full NS-3 Simulation (Recommended) 🚀

**Best for**: Accurate, publication-quality results

### Prerequisites

1. **Install NS-3** (one-time setup)

```bash
# Download NS-3 (version 3.41 recommended)
wget https://www.nsnam.org/releases/ns-allinone-3.41.tar.bz2
tar xjf ns-allinone-3.41.tar.bz2
cd ns-allinone-3.41/ns-3.41

# Configure and build
./ns3 configure --enable-examples --enable-tests
./ns3 build

# Go back to assignment directory
cd /path/to/Assignment3
```

2. **Install Python dependencies**

```bash
pip3 install -r requirements.txt
```

### Run Simulation

**Automated (recommended)**:
```bash
./build_and_run.sh
```

This script will:
1. Copy files to NS-3 source tree
2. Build NS-3 with custom TCP
3. Run all simulations (TcpNewReno, TcpCubic, TcpMlCong)
4. Generate plots and analysis

**Manual**:
```bash
# Copy files
cp tcp-ml-cong.h /path/to/ns-3/src/internet/model/
cp tcp-ml-cong.cc /path/to/ns-3/src/internet/model/
cp leaf-spine-simulation.cc /path/to/ns-3/scratch/

# Build NS-3
cd /path/to/ns-3
./ns3 build

# Run simulation
./ns3 run "scratch/leaf-spine-simulation --runAll=true"

# Copy results and analyze
cp flow_completion_times.csv /path/to/Assignment3/
cd /path/to/Assignment3
python3 analyze_results.py
```

---

## Expected Output

After running, you'll find:

### Data Files
- `flow_completion_times.csv` - Raw FCT data for all flows

### Plots (in `plots/` directory)
- `fct_comparison.pdf` - Bar charts (avg and P99 FCT)
- `fct_cdf.pdf` - CDF of flow completion times
- `fct_boxplot.pdf` - Box plot distribution
- `fct_histogram.pdf` - Histograms for each TCP variant
- `fct_stats_table.tex` - LaTeX table for report

### Console Output
```
=== Flow Completion Time Statistics for TcpNewReno ===
Total flows: 992
Average FCT: X.XXXX seconds
99th percentile FCT: X.XXXX seconds
...

=== Flow Completion Time Statistics for TcpCubic ===
...

=== Flow Completion Time Statistics for TcpMlCong ===
...

PERFORMANCE COMPARISON (TcpMlCong vs Baselines)
TcpMlCong vs TcpNewReno:
  Mean FCT improvement: +X.XX%
  P99 FCT improvement: +X.XX%
...
```

---

## Troubleshooting

### Problem: "NS-3 directory not found"
**Solution**: Edit `build_and_run.sh` line 30-40 to point to your NS-3 installation

### Problem: Python import errors
**Solution**: `pip3 install -r requirements.txt`

### Problem: Simulation too slow
**Solution**: Use standalone simulation for quick testing, or reduce number of servers in `leaf-spine-simulation.cc`

### Problem: Out of memory
**Solution**: Reduce buffer sizes or number of servers in simulation

---

## Next Steps

1. **View Results**: Check `plots/` directory for visualizations
2. **Read Report**: See `REPORT.md` for detailed analysis
3. **Modify Algorithm**: Edit `tcp-ml-cong.cc` to experiment with parameters
4. **Re-run**: Use `build_and_run.sh` to rebuild and test

---

## Time Estimates

| Task | Time |
|------|------|
| NS-3 installation (first time) | 15-30 min |
| Running standalone simulation | 2-5 min |
| Running full NS-3 simulation | 5-10 min |
| Generating plots | < 1 min |

---

## Help

For detailed documentation, see:
- `README.md` - Comprehensive guide
- `REPORT.md` - Detailed analysis and results

For questions, contact: [Your email]
