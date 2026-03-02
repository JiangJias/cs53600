# Assignment 2 Report Template

Student Name: [Your Name]
Student ID: [Your ID]
Course: CS 536 - Data Communication and Computer Networks
Date: [Date]

---

## Question 1: iPerf Throughput Application (20 points)

### Implementation Overview

Describe your iPerf3 client implementation:
- How you implemented the control connection
- JSON-based parameter exchange
- Data connection management
- Error handling for non-responsive servers

**Code Reference**: [Link to relevant code sections in your repository]

### Server Selection

List the servers you tested:
1. Server 1: [host:port]
2. Server 2: [host:port]
...

### Throughput Measurements

Include the plot: `plots/throughput_all.pdf`

**Figure 1**: Throughput time series for all destinations

### Summary Statistics

Include the summary table from `results/summary_statistics.csv`:

| Server | Min (Mbps) | Median (Mbps) | Avg (Mbps) | P95 (Mbps) |
|--------|-----------|---------------|------------|------------|
| ...    | ...       | ...           | ...        | ...        |

---

## Question 2: TCP Stats Tracing During Transfer (40 points)

### TCP Statistics Extraction

Describe how you extracted TCP statistics:
- Which TCP_INFO fields you collected
- Sampling methodology (200ms intervals)
- Data storage format (CSV/JSON)

**Code Reference**: [Link to TCP stats extraction code]

### Visualizations

#### Representative Destination: [Server Name]

##### Time Series Plots

Include the following plots:

**Figure 2**: Congestion Window over time (`plots/representative_cwnd.pdf`)

![Congestion Window](plots/representative_cwnd.pdf)

**Figure 3**: RTT over time (`plots/representative_rtt.pdf`)

![RTT](plots/representative_rtt.pdf)

**Figure 4**: Retransmissions (loss proxy) over time (`plots/representative_retrans.pdf`)

![Retransmissions](plots/representative_retrans.pdf)

**Figure 5**: Throughput over time (`plots/representative_throughput.pdf`)

![Throughput](plots/representative_throughput.pdf)

##### Scatter Plots

**Figure 6**: Congestion Window vs Goodput (`plots/representative_cwnd_vs_throughput.pdf`)

![cwnd vs throughput](plots/representative_cwnd_vs_throughput.pdf)

**Figure 7**: RTT vs Goodput (`plots/representative_rtt_vs_throughput.pdf`)

![RTT vs throughput](plots/representative_rtt_vs_throughput.pdf)

**Figure 8**: Loss Signal vs Goodput (`plots/representative_loss_vs_throughput.pdf`)

![Loss vs throughput](plots/representative_loss_vs_throughput.pdf)

### Observations and Analysis

#### Congestion Window (snd_cwnd)

**What it means**: The congestion window represents the maximum amount of unacknowledged data that can be in flight at any time. It controls how much data the sender can transmit before receiving an acknowledgment.

**Expected influence on goodput**:
- Larger cwnd allows more data in flight, potentially increasing throughput
- However, cwnd is limited by the Bandwidth-Delay Product (BDP = bandwidth × RTT)
- cwnd above BDP leads to queueing and increased latency without throughput gain

**Observations from your data**:
[Describe what you observed in your traces]
- Typical cwnd range: [X-Y packets]
- Correlation with throughput: [positive/negative/nonlinear]
- Pattern: [sawtooth/stable/erratic]

**Anomalous behaviors**:
[Describe any unexpected patterns]

#### Round-Trip Time (RTT)

**What it means**: RTT measures the time for a packet to travel to the destination and back. It includes propagation delay, transmission delay, queueing delay, and processing delay.

**Expected influence on goodput**:
- Higher RTT reduces throughput in congestion avoidance (slower window growth)
- Increasing RTT during transfer indicates queue buildup (bufferbloat)
- TCP throughput ≈ cwnd / RTT in steady state

**Observations from your data**:
[Describe what you observed]
- Baseline RTT: [X ms]
- RTT variation: [stable/increasing/oscillating]
- Correlation with throughput: [description]

**Anomalous behaviors**:
[Describe any unexpected patterns]

#### Loss Signal (Retransmissions)

**What it means**: Retransmissions indicate packet loss, which TCP interprets as a congestion signal. Each loss event triggers cwnd reduction.

**Expected influence on goodput**:
- Loss directly reduces throughput (retransmitted packets don't contribute to goodput)
- Loss triggers multiplicative decrease in cwnd (AIMD)
- Recovery phase has reduced throughput until cwnd rebuilds

**Observations from your data**:
[Describe what you observed]
- Loss frequency: [rare/occasional/frequent]
- Impact on throughput: [description]
- Recovery pattern: [fast/slow]

**Anomalous behaviors**:
[Describe any unexpected patterns, e.g., loss without congestion]

---

## Question 3: ML Model + Hand-Written Congestion Avoidance Algorithm (40 points)

### Dataset Construction

#### Features

Describe your feature set:
- Features used: throughput, RTT, loss, cwnd, ssthresh, etc.
- Preprocessing: normalization, windowing, lag features
- Feature engineering decisions

**Code Reference**: [Link to dataset preparation code]

#### Target Variable

- Target: Δ snd_cwnd (change in congestion window)
- Rationale: [explain why this target makes sense]

#### Dataset Statistics

- Total samples: [X]
- Training samples: [X]
- Test samples: [X]
- Number of destinations: [X]
- Train destinations: [X]
- Test destinations: [X]

### Model Training

#### Model Selection

- Model type: [Random Forest / Gradient Boosting / Other]
- Rationale: [why this model?]
- Hyperparameters: [list key parameters]

**Code Reference**: [Link to model training code]

#### Objective Function

η(t) = goodput(t) - α·RTT(t) - β·loss(t)

- α (RTT weight): [value]
- β (loss weight): [value]
- Interpretation: [explain what this objective optimizes for]

#### Training Results

- Training RMSE: [X]
- Training R²: [X]
- Test RMSE: [X]
- Test R²: [X]
- Feature importances: [list top features]

### Model Predictions

Include cwnd prediction plots for 5 destinations:

**Figure 9-13**: Congestion window predictions for different destinations

![Prediction 1](plots/cwnd_prediction_dest1.pdf)
![Prediction 2](plots/cwnd_prediction_dest2.pdf)
...

**Analysis**:
[Discuss how well the model predicts cwnd evolution]
- Where does it work well?
- Where does it struggle?
- What patterns did it learn?

### Hand-Written Congestion Control Algorithm

Based on the ML model predictions and network principles, extract a congestion window update algorithm.

**Code Reference**: [Link to algorithm extraction code]

#### Algorithm Description

```
Algorithm: Learned Congestion Window Update

Input: current_state = {throughput, RTT, cwnd, ssthresh, loss, ...}
Output: delta_cwnd (change in congestion window)

1. Congestion Avoidance Phase (no loss):
   [Describe rules for increasing cwnd]

   - If [condition]:
     * delta_cwnd = [formula]
     * Rationale: [explain based on BDP, RTT, etc.]

   - If [condition]:
     * delta_cwnd = [formula]
     * Rationale: [explain]

2. Loss Detection:
   [Describe rules for decreasing cwnd on loss]

   - If [condition]:
     * delta_cwnd = [formula]
     * Rationale: [explain based on AIMD]

3. RTT-based Adjustments:
   [Describe proactive adjustments based on RTT]

   - If [condition]:
     * delta_cwnd = [formula]
     * Rationale: [explain based on queueing theory]

4. Throughput Optimization:
   [Describe rules for optimizing objective function]

   - If [condition]:
     * delta_cwnd = [formula]
     * Rationale: [explain]

5. Bounds:
   - cwnd_min = [value]
   - cwnd_max = [value]
```

#### Grounding in Network Principles

**Bandwidth-Delay Product (BDP)**:
[Explain how your algorithm respects BDP]

**Queueing Theory**:
[Explain how queue buildup (increasing RTT) influences decisions]

**AIMD Principle**:
[Explain additive increase, multiplicative decrease]

**Relation between cwnd and goodput**:
[Explain the relationship and how algorithm exploits it]

**Trade-offs**:
[Discuss throughput vs latency trade-off]

---

## Automation and Reproducibility

### Docker Setup

Describe your Docker setup:
- Base image: ubuntu:24.04
- Dependencies installed
- How to build and run

**Commands**:
```bash
# Build
docker build -t iperf-assignment .

# Run
docker run --rm --network host \
  -v $(pwd)/results:/app/results \
  -v $(pwd)/plots:/app/plots \
  -v $(pwd)/models:/app/models \
  iperf-assignment \
  python3 run_experiment.py servers.txt --n-servers 10 --duration 60
```

### Automation Script

- Script name: `run_experiment.py`
- Input: server list file
- Output: all plots, data, and models
- Usage: [describe command-line arguments]

**Code Reference**: [Link to automation script]

---

## Challenges and Solutions

### Challenge 1: [Describe challenge]
**Solution**: [How you solved it]

### Challenge 2: [Describe challenge]
**Solution**: [How you solved it]

---

## Conclusions

Summarize key findings:
1. [Finding 1]
2. [Finding 2]
3. [Finding 3]

---

## References

1. iPerf3 documentation and source code
2. Linux TCP_INFO documentation
3. RFC 5681: TCP Congestion Control
4. Course lecture notes
5. [Any other references]

---

## Appendix

### Repository Structure

```
cs53600/Assignment2/
├── iperf_client.py
├── data_collector.py
├── visualization.py
├── ml_model.py
├── run_experiment.py
├── servers.txt
├── requirements.txt
├── Dockerfile
├── README.md
└── [other files]
```

### GitHub/GitLab Link

Repository: [Your repository URL]

### Code Snippets

Include key code snippets here if needed, with links to full code in repository.
