# Assignment 2: iPerf, TCP Statistics, and Congestion Control

CS 536: Data Communication and Computer Networks, Spring 2026

## Overview

This project implements a complete iPerf3-compatible TCP client, collects TCP statistics during data transfer, and uses machine learning to analyze congestion window behavior.

## Features

### 1. iPerf3-Compatible TCP Client (`iperf_client.py`)
- Implements iPerf3 protocol from scratch
- Establishes control and data connections
- JSON-based parameter exchange
- Continuous data transmission with configurable duration
- Compatible with standard iPerf3 servers (https://iperf3serverlist.net/)
- Robust error handling for non-responsive servers

### 2. TCP Statistics Collection (`data_collector.py`)
- Collects throughput measurements at regular intervals (200ms default)
- Extracts TCP socket statistics using `TCP_INFO`:
  - Congestion window (snd_cwnd)
  - Round-trip time (RTT)
  - Retransmissions (loss proxy)
  - RTT variance, pacing rate, bytes acked/sent
- Saves data in JSON and CSV formats
- Generates summary statistics (min/median/avg/p95)

### 3. Visualization (`visualization.py`)
- Time series plots:
  - Throughput evolution for all destinations
  - Congestion window, RTT, loss, throughput per destination
- Scatter plots showing relationships:
  - snd_cwnd vs goodput
  - RTT vs goodput
  - Loss signal vs goodput
- Publication-quality PDF outputs

### 4. ML Model for Congestion Control (`ml_model.py`)
- Builds dataset from TCP statistics
- Features: throughput, RTT, loss, cwnd, ssthresh, etc.
- Target: Δ snd_cwnd (congestion window change)
- Custom objective function: η(t) = goodput(t) - α·RTT(t) - β·loss(t)
- Trains Random Forest / Gradient Boosting models
- Evaluates predictions on test set
- Generates cwnd prediction plots for multiple destinations
- Extracts hand-written congestion control algorithm based on learned patterns

### 5. Complete Automation (`run_experiment.py`)
- Single script to run entire pipeline
- Configurable parameters via command line
- Automated data collection, visualization, and ML training
- Comprehensive logging

## Requirements

### System Requirements
- **Linux system** (Ubuntu 22.04+ recommended) or **Windows with WSL2**
- Docker installed (optional but recommended)
- Python 3.10+

### Python Dependencies
See `requirements.txt`:
- numpy
- pandas
- matplotlib
- scikit-learn
- scipy

## Installation

### Option 1: Using Docker (Recommended)

1. Build the Docker image:
```bash
cd cs53600/Assignment2
docker build -t iperf-assignment .
```

2. Run the experiment:
```bash
docker run --rm -v $(pwd)/results:/app/results \
                -v $(pwd)/plots:/app/plots \
                -v $(pwd)/models:/app/models \
                iperf-assignment \
                python3 run_experiment.py servers.txt --n-servers 10 --duration 60
```

### Option 2: Local Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the experiment:
```bash
python3 run_experiment.py servers.txt --n-servers 10 --duration 60
```

## Usage

### Basic Usage

Run the complete experiment with default settings (10 servers, 60-second tests):
```bash
python3 run_experiment.py servers.txt
```

### Advanced Options

```bash
python3 run_experiment.py servers.txt \
    --n-servers 5 \           # Number of random servers to test
    --duration 30 \            # Test duration in seconds
    --sampling-interval 0.2 \  # Sampling interval in seconds
    --alpha 1.0 \              # RTT weight in ML objective
    --beta 1.0 \               # Loss weight in ML objective
    --output-dir results \     # Output directory for data
    --plots-dir plots \        # Output directory for plots
    --models-dir models        # Output directory for models
```

### Skip Certain Steps

```bash
# Skip data collection (use existing results)
python3 run_experiment.py servers.txt --skip-collection

# Skip visualization
python3 run_experiment.py servers.txt --skip-visualization

# Skip ML training
python3 run_experiment.py servers.txt --skip-ml
```

### Testing Individual Components

Test iPerf client with a single server:
```bash
python3 iperf_client.py iperf3.velnet.co.uk
```

Generate visualizations from existing data:
```bash
python3 visualization.py
```

Train ML model from existing data:
```bash
python3 ml_model.py 1.0 1.0  # alpha=1.0, beta=1.0
```

## Project Structure

```
cs53600/Assignment2/
├── iperf_client.py           # iPerf3-compatible TCP client
├── data_collector.py         # Data collection from multiple servers
├── visualization.py          # Visualization generation
├── ml_model.py              # ML model for congestion window prediction
├── run_experiment.py        # Main automation script
├── servers.txt              # List of iPerf3 servers
├── requirements.txt         # Python dependencies
├── Dockerfile              # Docker containerization
├── README.md              # This file
├── results/               # Output data (JSON, CSV)
├── plots/                 # Generated plots (PDF)
├── models/               # Trained ML models
└── logs/                 # Experiment logs
```

## Output Files

After running the experiment, the following files are generated:

### Results Directory (`results/`)
- `iperf_results.json`: Complete results from all tests
- `summary_statistics.csv`: Summary statistics per destination
- `tcp_stats_<server>.csv`: TCP statistics for each server

### Plots Directory (`plots/`)
- `throughput_all.pdf`: Throughput time series for all destinations
- `representative_cwnd.pdf`: Congestion window time series
- `representative_rtt.pdf`: RTT time series
- `representative_retrans.pdf`: Retransmissions time series
- `representative_throughput.pdf`: Throughput time series
- `representative_cwnd_vs_throughput.pdf`: Scatter plot
- `representative_rtt_vs_throughput.pdf`: Scatter plot
- `representative_loss_vs_throughput.pdf`: Scatter plot
- `cwnd_prediction_*.pdf`: ML model predictions for each destination
- `congestion_algorithm.txt`: Extracted congestion control algorithm
- `summary_table.tex`: LaTeX table with summary statistics

### Models Directory (`models/`)
- `cwnd_model.pkl`: Trained ML model and scaler

## Implementation Details

### iPerf3 Protocol Implementation

The client implements the iPerf3 protocol:
1. **Control Connection**: TCP connection for parameter exchange
2. **Parameter Negotiation**: JSON-based handshake with server
3. **Data Connection**: Separate TCP connection for data transfer
4. **Cookie Authentication**: Server-provided cookie for test identification
5. **Graceful Termination**: Proper cleanup and result collection

### TCP Statistics Extraction

Uses `TCP_INFO` socket option to extract:
- Congestion window (snd_cwnd)
- Slow start threshold (snd_ssthresh)
- RTT and RTT variance
- Retransmissions, lost packets, sacked packets
- Unacknowledged packets

### ML Model

**Features**: throughput, RTT, RTT variance, cwnd, ssthresh, retrans, lost, unacked, sacked, incremental loss

**Target**: Δ snd_cwnd (change in congestion window)

**Objective Function**: η(t) = goodput(t) - α·RTT(t) - β·loss(t)
- Maximizes throughput while penalizing high RTT (latency) and packet loss
- α and β are configurable weights

**Model**: Random Forest Regressor (default) or Gradient Boosting
- Handles non-linear relationships
- Provides feature importance analysis
- Robust to outliers

### Congestion Control Algorithm

Based on ML predictions and network principles:
1. **Congestion Avoidance**: Additive increase (AIMD)
2. **Loss Detection**: Multiplicative decrease
3. **RTT-based**: Proactive adjustment based on queue buildup
4. **Throughput Optimization**: Balance throughput vs latency
5. **Bandwidth-Delay Product**: Respect BDP constraints

## Observations and Analysis

### TCP Metrics and Their Influence on Goodput

1. **Congestion Window (snd_cwnd)**:
   - Direct relationship with throughput
   - Larger cwnd → more in-flight data → higher throughput (up to BDP limit)
   - Too large → bufferbloat and increased RTT

2. **Round-Trip Time (RTT)**:
   - Inverse relationship with throughput
   - Higher RTT → slower ACK arrival → slower window growth
   - Increasing RTT indicates queue buildup

3. **Retransmissions (Loss)**:
   - Strong negative impact on throughput
   - Triggers cwnd reduction (multiplicative decrease)
   - Indicates network congestion

### Anomalous Behaviors Observed

1. **RTT Spikes**: Sudden RTT increases without loss indicate bufferbloat
2. **Throughput Plateaus**: cwnd increasing but throughput flat → bottleneck reached
3. **Sawtooth Pattern**: Classic TCP congestion avoidance behavior
4. **Loss Without Congestion**: May indicate wireless interference or other non-congestion loss

## Troubleshooting

### Server Connection Issues

- Some servers from iperf3serverlist.net may be offline or rate-limiting
- The script automatically skips non-responsive servers
- Increase `--n-servers` to ensure enough successful tests

### Docker Issues

- Ensure Docker has access to host network
- Use `--network host` flag if needed:
  ```bash
  docker run --rm --network host -v $(pwd)/results:/app/results ...
  ```

### TCP_INFO Not Available

- TCP_INFO is Linux-specific
- Some fields may not be available on all kernel versions
- The code handles missing fields gracefully

### Low Throughput

- Check network connectivity
- Try different servers (some may be geographically distant)
- Increase test duration for more stable measurements

## References

- iPerf3 Documentation: https://iperf.fr/
- iPerf3 Source Code: https://github.com/esnet/iperf
- iPerf3 Server List: https://iperf3serverlist.net/
- TCP_INFO: Linux kernel documentation
- RFC 5681: TCP Congestion Control

## Authors

Student implementation for CS 536: Data Communication and Computer Networks

## License

Academic use only - CS 536 Assignment 2
