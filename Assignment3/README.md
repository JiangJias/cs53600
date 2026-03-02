# Assignment 3: TCP Congestion Control Implementation in NS-3

**Course**: CS 536: Data Communication and Computer Networks, Spring 2026
**Student**: [Your Name]
**Date**: February 2026

---

## Table of Contents

1. [Overview](#overview)
2. [Implementation Choice](#implementation-choice)
3. [File Structure](#file-structure)
4. [Algorithm Description](#algorithm-description)
5. [Network Topology](#network-topology)
6. [Design Choices](#design-choices)
7. [Installation](#installation)
8. [Running the Simulation](#running-the-simulation)
9. [Results](#results)
10. [Code References](#code-references)

---

## Overview

This project implements **Option 2** from Assignment 3: NS-3 implementation of a custom TCP congestion control algorithm. The algorithm is based on machine learning insights from Assignment 2 and implements AIMD (Additive Increase Multiplicative Decrease) with RTT-aware adjustments.

### Key Features

- ✅ Custom TCP congestion control algorithm (TcpMlCong)
- ✅ Leaf-spine datacenter topology (2 ToR, 2 Spine, 32 servers)
- ✅ All-to-all traffic pattern (992 flows, 64MB each)
- ✅ Comparison with TCP CUBIC and TCP NewReno
- ✅ Flow completion time (FCT) analysis
- ✅ Automated build and run scripts
- ✅ Comprehensive visualization and analysis

---

## Implementation Choice

**Selected Option**: Option 2 - NS-3 Implementation

**Rationale**:
- NS-3 provides a controlled simulation environment for reproducible results
- Easier to test and debug compared to kernel modules
- Safe to run without system-level privileges
- Allows precise control over network conditions
- Can run multiple experiments efficiently

---

## File Structure

```
Assignment3/
├── tcp-ml-cong.h                 # TCP congestion control header
├── tcp-ml-cong.cc                # TCP congestion control implementation
├── leaf-spine-simulation.cc      # NS-3 simulation script
├── analyze_results.py            # Result analysis and plotting
├── build_and_run.sh             # Automated build and run script
├── run_standalone.py            # Standalone simulation (no NS-3)
├── README.md                    # This file
├── REPORT.md                    # Detailed report
├── assignment-3.pdf             # Original assignment
│
├── results/                     # Generated during simulation
│   └── flow_completion_times.csv
│
└── plots/                       # Generated plots
    ├── fct_comparison.pdf
    ├── fct_cdf.pdf
    ├── fct_boxplot.pdf
    ├── fct_histogram.pdf
    └── fct_stats_table.tex
```

---

## Algorithm Description

### TcpMlCong: ML-Inspired TCP Congestion Control

Based on the learned patterns from Assignment 2, TcpMlCong implements the following strategy:

#### 1. **Slow Start Phase** (cwnd < ssthresh)
- Exponential increase: `cwnd += 1` per ACK
- Standard TCP behavior for fast ramp-up

#### 2. **Congestion Avoidance Phase** (cwnd >= ssthresh)

**Base Behavior**: AIMD (Additive Increase, Multiplicative Decrease)
- Increase: `cwnd += 1/cwnd` per ACK (1 MSS per RTT)
- Decrease on loss: `cwnd = cwnd / 2`

**RTT-Aware Adjustments**:
- Track minimum RTT (baseline)
- Monitor current RTT relative to baseline
- If RTT increases > 20% above baseline:
  - Reduce growth rate: `cwnd += 0.5/cwnd` (slow down by 50%)
  - Prevents queue buildup and bufferbloat
- If RTT increases > 10% but < 20%:
  - Conservative growth: `cwnd += 0.75/cwnd`
- If RTT stable:
  - Normal AIMD: `cwnd += 1.0/cwnd`

**Throughput Optimization**:
- After 5 consecutive cwnd increases with stable RTT:
  - Slightly aggressive: `cwnd += 1.5/cwnd`
  - Exploits available bandwidth

#### 3. **Loss Detection**
- Multiplicative decrease: `ssthresh = max(cwnd/2, 2 segments)`
- Reset cwnd to ssthresh
- Reset consecutive increment counter

### Key Principles Applied

1. **Bandwidth-Delay Product (BDP)**: cwnd should approach BDP for optimal throughput
2. **Queue Management**: RTT increase indicates queue buildup → slow down
3. **AIMD Fairness**: Standard AIMD ensures fairness among competing flows
4. **Proactive Congestion Avoidance**: React to RTT before loss occurs

---

## Network Topology

### Leaf-Spine Datacenter Topology

```
                    [Spine 0]     [Spine 1]
                       |  \\     /  |  \\     /
                       |   \\   /   |   \\   /
                       |    \\ /    |    \\ /
                       |     X      |     X
                       |    / \\    |    / \\
                       |   /   \\   |   /   \\
                    [ToR 0]      [ToR 1]
                       |            |
                   16 servers   16 servers
```

### Specifications

| Component | Count | Link Bandwidth | Propagation Delay |
|-----------|-------|----------------|-------------------|
| Servers | 32 (16 per ToR) | 100 Gbps | 500 ns |
| ToR Switches | 2 | - | - |
| Spine Switches | 2 | - | - |
| ToR-Spine Links | 4 (full mesh) | 400 Gbps | 500 ns |

### Traffic Pattern

- **All-to-all communication**: Each server sends to every other server
- **Flow size**: 64 MB per flow
- **Total flows**: 32 × 31 = 992 concurrent flows
- **Application**: BulkSend (TCP)

---

## Design Choices

### 1. Buffer Sizing at Switches

**Design Decision**: Moderate buffering strategy

- **Server-facing ports (100 Gbps)**: 10 MB buffer per port
- **Spine links (400 Gbps)**: 40 MB buffer per port

**Rationale**:
- Based on typical datacenter switch specifications [1][2]
- Rule of thumb: Buffer = RTT × Bandwidth / sqrt(#flows)
- For 100G ports: ~10-20 MB typical [3]
- For 400G ports: ~40-80 MB typical [4]
- Moderate buffering balances throughput and latency

**Tradeoffs**:
- ✅ Larger buffers: Higher throughput, absorb bursts
- ❌ Larger buffers: Increased latency (bufferbloat)
- ✅ Smaller buffers: Lower latency
- ❌ Smaller buffers: Higher loss rate

Our choice provides sufficient buffering to prevent excessive loss while limiting bufferbloat.

**References**:
- [1] Cisco Nexus 9000 Series Switches Data Sheet
- [2] Broadcom StrataXGS Tomahawk Series
- [3] "Buffer Sizing for Congested Internet Links" - Appenzeller et al.
- [4] SIGCOMM 2019: "Re-architecting Datacenter Networks and Stacks"

### 2. TCP Segment Size

**Choice**: 1448 bytes (typical Ethernet MTU - headers)

**Rationale**:
- Standard for datacenter networks
- Ethernet MTU = 1500 bytes
- TCP/IP headers = ~52 bytes
- Payload = 1448 bytes

### 3. Initial Congestion Window

**Choice**: 10 segments (IW10)

**Rationale**:
- Modern TCP standard (RFC 6928)
- Faster flow startup in high-bandwidth networks
- Standard practice in datacenters

---

## Installation

### Prerequisites

#### Option 1: Full NS-3 Simulation

1. **NS-3 Simulator** (version 3.36 or later)
   ```bash
   # Download NS-3
   wget https://www.nsnam.org/releases/ns-allinone-3.41.tar.bz2
   tar xjf ns-allinone-3.41.tar.bz2
   cd ns-allinone-3.41/ns-3.41

   # Build NS-3
   ./ns3 configure --enable-examples --enable-tests
   ./ns3 build
   ```

2. **Python 3** (for analysis)
   ```bash
   pip3 install numpy pandas matplotlib
   ```

#### Option 2: Standalone Simulation

Just Python 3 with dependencies:
```bash
pip3 install numpy pandas matplotlib
```

---

## Running the Simulation

### Method 1: Automated Build and Run (Recommended)

```bash
# From Assignment3 directory
./build_and_run.sh
```

This script will:
1. Copy files to NS-3 source tree
2. Build NS-3 with custom TCP
3. Run simulations for all three TCP variants
4. Generate plots and analysis

### Method 2: Manual NS-3 Build

```bash
# Copy files to NS-3
cp tcp-ml-cong.h /path/to/ns-3/src/internet/model/
cp tcp-ml-cong.cc /path/to/ns-3/src/internet/model/
cp leaf-spine-simulation.cc /path/to/ns-3/scratch/

# Build NS-3
cd /path/to/ns-3
./ns3 build

# Run simulation
./ns3 run "scratch/leaf-spine-simulation --runAll=true"

# Copy results back
cp flow_completion_times.csv /path/to/Assignment3/

# Analyze results
cd /path/to/Assignment3
python3 analyze_results.py
```

### Method 3: Standalone Simulation (No NS-3)

```bash
# Run simplified simulation
./run_standalone.py
```

**Note**: This is a simplified simulation for demonstration. For accurate results, use NS-3.

---

## Results

### Expected Output Files

After running the simulation, you will get:

1. **flow_completion_times.csv** - Raw data with FCT for each flow
2. **plots/fct_comparison.pdf** - Bar charts comparing average and P99 FCT
3. **plots/fct_cdf.pdf** - CDF of flow completion times
4. **plots/fct_boxplot.pdf** - Box plot showing distribution
5. **plots/fct_histogram.pdf** - Histograms for each TCP variant
6. **plots/fct_stats_table.tex** - LaTeX table for report

### Statistics Reported

For each TCP variant:
- Average FCT
- Median FCT
- 99th percentile FCT
- Minimum FCT
- Maximum FCT
- Standard deviation
- Total flows completed

### Performance Comparison

The analysis script automatically compares TcpMlCong with baseline algorithms and reports:
- Mean FCT improvement vs TcpNewReno
- Mean FCT improvement vs TcpCubic
- P99 FCT improvement vs baselines

---

## Code References

### Key Implementation Files

1. **TCP Congestion Control Algorithm**
   - Header: `tcp-ml-cong.h` (lines 1-100)
   - Implementation: `tcp-ml-cong.cc` (lines 1-250)
   - Key function: `IncreaseWindow()` (tcp-ml-cong.cc, lines 161-194)
   - RTT tracking: `PktsAcked()` (tcp-ml-cong.cc, lines 88-107)

2. **NS-3 Simulation**
   - Main simulation: `leaf-spine-simulation.cc`
   - Topology creation: lines 200-300
   - Flow generation: lines 350-380
   - Flow tracking: lines 100-150

3. **Analysis and Plotting**
   - Analysis script: `analyze_results.py`
   - Plot generation: lines 50-250
   - Statistics: lines 20-45

### Link to Repository

**GitHub Repository**: [Insert your repository URL here]

**Key Code Sections**:
- Custom TCP: [`tcp-ml-cong.cc#L161-L194`](link)
- Topology setup: [`leaf-spine-simulation.cc#L200-L300`](link)
- Flow creation: [`leaf-spine-simulation.cc#L350-L380`](link)
- Analysis: [`analyze_results.py#L50-L250`](link)

---

## Troubleshooting

### NS-3 Build Issues

**Problem**: Cannot find NS-3 directory
- **Solution**: Edit `build_and_run.sh` to point to your NS-3 installation

**Problem**: Build errors
- **Solution**: Make sure you're using NS-3 version 3.36 or later
- **Solution**: Check that all dependencies are installed

### Simulation Issues

**Problem**: Simulation runs but no flows complete
- **Cause**: Insufficient simulation time or network congestion
- **Solution**: Increase simulation time in `leaf-spine-simulation.cc` (line ~380)

**Problem**: Out of memory
- **Cause**: Too many flows with large buffers
- **Solution**: Reduce number of servers or buffer size

### Python Issues

**Problem**: Module not found
- **Solution**: `pip3 install numpy pandas matplotlib`

**Problem**: Cannot generate plots
- **Solution**: Make sure matplotlib backend is set correctly

---

## Performance Notes

- **Simulation time**: ~5-10 minutes for all three TCP variants (depends on hardware)
- **Memory usage**: ~2-4 GB RAM
- **Disk space**: ~100 MB for results and plots

---

## Report

For detailed analysis, design decisions, and experimental results, see **REPORT.md**.

---

## References

1. Assignment 2: iPerf client and ML-based congestion control
2. NS-3 Documentation: https://www.nsnam.org/documentation/
3. TCP CUBIC: "CUBIC: A New TCP-Friendly High-Speed TCP Variant" - Ha et al.
4. TCP NewReno: RFC 6582
5. Datacenter TCP: "Data Center TCP (DCTCP)" - Alizadeh et al., SIGCOMM 2010
6. Buffer sizing: "Sizing Router Buffers" - Appenzeller et al., SIGCOMM 2004

---

## Contact

For questions or issues, please contact:
- **Email**: [Your email]
- **Office Hours**: [Times]

---

## License

This code is submitted as part of CS 536 coursework and is for educational purposes only.
