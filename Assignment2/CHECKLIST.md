# Assignment 2 Submission Checklist

Use this checklist to ensure you have completed all requirements before submission.

---

## Pre-Submission Checklist

### 1. Code Implementation ✅

#### Q1: iPerf Throughput Application (20 points)
- [ ] Socket program written from scratch in Python
- [ ] TCP connection established with iPerf3 server
- [ ] Control connection working
- [ ] JSON parameter exchange implemented
- [ ] Data connection established
- [ ] Continuous data transmission for configurable duration
- [ ] Proper test termination
- [ ] Compatible with public iPerf3 servers (tested with at least 3)
- [ ] Handles non-responsive servers gracefully
- [ ] Random server selection from list (n configurable)
- [ ] Goodput measurement at regular intervals
- [ ] Throughput time series plot generated
- [ ] Summary statistics table created (min/median/avg/p95)

#### Q2: TCP Stats Tracing (40 points)
- [ ] TCP statistics extracted periodically during transfer
- [ ] Sampling interval: 200ms or configurable
- [ ] Required fields collected: timestamp, snd_cwnd, RTT, loss signal, goodput
- [ ] Recommended fields collected: rttvar, pacing rate, bytes acked/sent
- [ ] Data stored in readable format (CSV/JSON)
- [ ] Time series plots generated:
  - [ ] snd_cwnd vs time
  - [ ] RTT vs time
  - [ ] Loss signal vs time
  - [ ] Throughput vs time
- [ ] Scatter plots generated:
  - [ ] snd_cwnd vs goodput
  - [ ] RTT vs goodput
  - [ ] Loss signal vs goodput
- [ ] Observations written (what each metric means)
- [ ] Analysis of how metrics influence goodput
- [ ] Anomalous behaviors identified and explained

#### Q3: ML Model + Algorithm (40 points)
- [ ] Dataset constructed from traces
- [ ] Features defined and preprocessed
- [ ] Target variable: Δ snd_cwnd
- [ ] Train/test split implemented
- [ ] Model trained with objective: η(t) = goodput(t) - α·RTT(t) - β·loss(t)
- [ ] α and β parameters configurable
- [ ] cwnd timeseries plot with train/test split
- [ ] Predicted cwnd overlaid on actual cwnd
- [ ] Plots generated for 5 destinations
- [ ] Hand-written congestion algorithm extracted
- [ ] Algorithm grounded in network principles:
  - [ ] Bandwidth-Delay Product
  - [ ] Queueing theory
  - [ ] AIMD (Additive Increase, Multiplicative Decrease)
  - [ ] Relation between cwnd and goodput

### 2. Automation ✅

- [ ] Single script runs entire pipeline
- [ ] Input: file with list of IP addresses
- [ ] Command-line arguments for configuration
- [ ] Script generates all plots automatically
- [ ] Script generates PDF outputs
- [ ] Script invokes ML training
- [ ] Script generates all visualizations
- [ ] One-shot execution possible
- [ ] All inputs and scripts included
- [ ] Reproducible results

### 3. Docker Containerization ✅

- [ ] Dockerfile created
- [ ] Base image: ubuntu:24.04
- [ ] All dependencies included
- [ ] Container runs on any machine with Docker
- [ ] Full experiment pipeline executes when run
- [ ] Container tested and working
- [ ] .dockerignore file created

### 4. Documentation ✅

- [ ] README.md with:
  - [ ] Overview of the project
  - [ ] Installation instructions
  - [ ] Usage examples
  - [ ] Output description
  - [ ] Code structure explanation
- [ ] Code comments explaining key functions
- [ ] Docstrings for classes and methods
- [ ] GitHub/GitLab repository created
- [ ] Repository link in report

---

## Testing Checklist

### Basic Functionality Tests

- [ ] `python3 test_setup.py` passes all tests
- [ ] iPerf client can connect to public server:
  ```bash
  python3 iperf_client.py iperf3.velnet.co.uk
  ```
- [ ] Full pipeline runs without errors:
  ```bash
  python3 run_experiment.py servers.txt --n-servers 3 --duration 10
  ```
- [ ] Output files created:
  - [ ] `results/iperf_results.json`
  - [ ] `results/summary_statistics.csv`
  - [ ] `results/tcp_stats_*.csv`
  - [ ] `plots/throughput_all.pdf`
  - [ ] `plots/representative_*.pdf`
  - [ ] `plots/cwnd_prediction_*.pdf`
  - [ ] `plots/congestion_algorithm.txt`
  - [ ] `models/cwnd_model.pkl`

### Docker Tests

- [ ] Docker image builds successfully:
  ```bash
  docker build -t iperf-assignment .
  ```
- [ ] Docker container runs successfully:
  ```bash
  docker run --rm --network host \
    -v $(pwd)/results:/app/results \
    -v $(pwd)/plots:/app/plots \
    -v $(pwd)/models:/app/models \
    iperf-assignment \
    python3 run_experiment.py servers.txt --n-servers 3 --duration 10
  ```
- [ ] Output files appear in host directories

---

## Report Checklist

Use `REPORT_TEMPLATE.md` as a guide.

### Q1: iPerf Throughput Application

- [ ] Implementation overview written
- [ ] Code references included
- [ ] Server list documented
- [ ] Throughput plot included (`throughput_all.pdf`)
- [ ] Summary statistics table included

### Q2: TCP Stats Tracing

- [ ] TCP statistics extraction methodology described
- [ ] Code references included
- [ ] Representative destination identified
- [ ] All time series plots included:
  - [ ] Congestion window
  - [ ] RTT
  - [ ] Retransmissions
  - [ ] Throughput
- [ ] All scatter plots included:
  - [ ] cwnd vs goodput
  - [ ] RTT vs goodput
  - [ ] Loss vs goodput
- [ ] Observations section complete:
  - [ ] What each metric means
  - [ ] Expected influence on goodput
  - [ ] Actual observations from data
  - [ ] Anomalous behaviors identified

### Q3: ML Model + Algorithm

- [ ] Dataset construction described
- [ ] Features and preprocessing documented
- [ ] Target variable explained
- [ ] Train/test split methodology described
- [ ] Model selection rationale provided
- [ ] Objective function (η) explained
- [ ] Training results documented (RMSE, R², etc.)
- [ ] Prediction plots included (5 destinations)
- [ ] Analysis of model performance written
- [ ] Hand-written algorithm documented
- [ ] Algorithm grounded in network principles:
  - [ ] BDP explanation
  - [ ] Queueing theory application
  - [ ] AIMD discussion
  - [ ] cwnd-goodput relationship

### Report Quality

- [ ] All plots have captions
- [ ] All figures referenced in text
- [ ] Code sections linked to repository
- [ ] GitHub/GitLab repository link included
- [ ] Repository is public or accessible
- [ ] Proper formatting and organization
- [ ] No spelling/grammar errors
- [ ] Professional presentation

---

## File Structure Verification

Check that your submission includes:

```
cs53600/Assignment2/
├── Source Code
│   ├── iperf_client.py          ✅
│   ├── data_collector.py        ✅
│   ├── visualization.py         ✅
│   ├── ml_model.py             ✅
│   ├── run_experiment.py       ✅
│   └── test_setup.py           ✅
├── Configuration
│   ├── servers.txt             ✅
│   ├── requirements.txt        ✅
│   ├── Dockerfile             ✅
│   └── .dockerignore          ✅
├── Documentation
│   ├── README.md              ✅
│   ├── QUICKSTART.md          ✅
│   ├── INSTALLATION.md        ✅
│   ├── REPORT_TEMPLATE.md     ✅
│   └── PROJECT_SUMMARY.md     ✅
├── Original Assignment
│   └── assignment-2.pdf       ✅
└── Output (not submitted, but generated)
    ├── results/
    ├── plots/
    └── models/
```

---

## Pre-Submission Tests

Run these commands to verify everything works:

### 1. Setup Test
```bash
python3 test_setup.py
```
**Expected**: All tests pass ✓

### 2. Quick Functionality Test
```bash
python3 run_experiment.py servers.txt --n-servers 3 --duration 10
```
**Expected**: Completes without errors, generates outputs

### 3. Docker Build Test
```bash
docker build -t iperf-assignment .
```
**Expected**: Builds successfully

### 4. Docker Run Test
```bash
docker run --rm --network host \
  -v $(pwd)/results:/app/results \
  -v $(pwd)/plots:/app/plots \
  -v $(pwd)/models:/app/models \
  iperf-assignment \
  python3 run_experiment.py servers.txt --n-servers 3 --duration 10
```
**Expected**: Completes successfully, outputs appear in host directories

### 5. Output Verification
```bash
ls results/
ls plots/
ls models/
```
**Expected**: All expected files present

---

## Common Issues to Check

- [ ] Code works on Linux (Ubuntu 22.04+) or WSL2
- [ ] TCP_INFO availability verified on target platform
- [ ] Network connectivity to iPerf servers verified
- [ ] At least 3-5 servers successfully tested
- [ ] Plots are readable and properly labeled
- [ ] ML model training completes without errors
- [ ] All paths are relative (not absolute)
- [ ] No hardcoded usernames or system-specific paths
- [ ] Requirements.txt includes all dependencies
- [ ] Docker container uses host network for iPerf
- [ ] Output directories are created automatically
- [ ] Scripts have execute permissions

---

## Submission Checklist

- [ ] All code committed to repository
- [ ] Repository is clean (no unnecessary files)
- [ ] .gitignore properly configured
- [ ] README.md is up to date
- [ ] All documentation is complete
- [ ] Report is written and polished
- [ ] All plots are included in report
- [ ] Code sections are referenced in report
- [ ] Repository link is in report
- [ ] Docker instructions are clear
- [ ] Submission tested on clean machine
- [ ] Final test run successful

---

## Optional Enhancements (Extra Credit)

If you have time, consider:

- [ ] Additional ML models (compare performance)
- [ ] More sophisticated feature engineering
- [ ] Interactive visualization dashboard
- [ ] Comprehensive error analysis
- [ ] Performance optimizations
- [ ] Additional network metrics
- [ ] Extended analysis and insights

---

## Final Verification

Before submitting:

1. **Clone your repository to a new location**
   ```bash
   git clone <your-repo-url> test-submission
   cd test-submission/cs53600/Assignment2
   ```

2. **Test from scratch**
   ```bash
   python3 test_setup.py
   python3 run_experiment.py servers.txt --n-servers 3 --duration 10
   ```

3. **Verify outputs**
   ```bash
   ls results/
   ls plots/
   ls models/
   ```

4. **Check Docker**
   ```bash
   docker build -t iperf-test .
   docker run --rm --network host \
     -v $(pwd)/results:/app/results \
     iperf-test \
     python3 --version
   ```

5. **Review report**
   - Read through completely
   - Check all links
   - Verify all plots are included
   - Check for typos

---

## Submission Ready!

If all items are checked ✓, you're ready to submit!

**Submission includes:**
1. GitHub/GitLab repository link
2. Written report (PDF)
3. All code and documentation in repository

**Good luck!** 🎉

---

**Due Date**: March 10, 2026 @ 11:45 PM Eastern Time

Don't forget to submit before the deadline!
