# Assignment 2 - File Index

Quick reference guide to all files in this project.

---

## 📁 Core Implementation Files (1,809 lines of Python)

### `iperf_client.py` (426 lines)
**Purpose**: iPerf3-compatible TCP client implementation
**Key Classes**: `IperfClient`, `IperfResult`
**Key Functions**:
- `_establish_control_connection()` - TCP control connection
- `_exchange_parameters()` - JSON parameter handshake
- `_open_data_connection()` - Data transfer connection
- `_send_data()` - Continuous data transmission with TCP stats collection
- `_get_tcp_info()` - TCP_INFO socket statistics extraction
- `run_test()` - Complete test execution

**Usage**: `python3 iperf_client.py <server_host>`

### `data_collector.py` (252 lines)
**Purpose**: Collect data from multiple iPerf servers
**Key Classes**: `DataCollector`
**Key Functions**:
- `collect_from_servers()` - Test multiple servers
- `save_results_json()` - Save complete results
- `save_tcp_stats_csv()` - Save TCP statistics per server
- `get_summary_statistics()` - Calculate min/median/avg/p95
- `load_server_list()` - Load servers from file
- `select_random_servers()` - Random server selection

**Usage**: `python3 data_collector.py <server_file> [n_servers] [duration]`

### `visualization.py` (274 lines)
**Purpose**: Generate all plots and visualizations
**Key Classes**: `Visualizer`
**Key Functions**:
- `plot_throughput_timeseries_all()` - Throughput for all destinations
- `plot_tcp_stats_timeseries()` - cwnd, RTT, loss, throughput time series
- `plot_scatter_relationships()` - Correlation scatter plots
- `generate_summary_table_latex()` - LaTeX summary table

**Usage**: `python3 visualization.py`

### `ml_model.py` (483 lines)
**Purpose**: Machine learning model for congestion window prediction
**Key Classes**: `CongestionWindowPredictor`
**Key Functions**:
- `prepare_dataset()` - Feature/label extraction
- `split_data()` - Train/test split by destination
- `train_model()` - Random Forest training
- `predict()` - cwnd delta prediction
- `plot_cwnd_comparison()` - Actual vs predicted plots
- `extract_algorithm()` - Hand-written algorithm extraction

**Usage**: `python3 ml_model.py [alpha] [beta]`

### `run_experiment.py` (214 lines)
**Purpose**: Main automation script - runs complete pipeline
**Key Functions**:
- Complete pipeline orchestration
- Command-line argument parsing
- Logging and progress reporting

**Usage**: `python3 run_experiment.py <server_file> [options]`

### `test_setup.py` (160 lines)
**Purpose**: Verify installation and setup
**Key Functions**:
- `test_imports()` - Check Python packages
- `test_tcp_info()` - Verify TCP_INFO availability
- `test_network()` - Check network connectivity
- `test_file_structure()` - Verify all files present

**Usage**: `python3 test_setup.py`

---

## 📄 Documentation Files (2,075 lines)

### `README.md` (310 lines) 📘
**Purpose**: Comprehensive project documentation
**Contents**:
- Overview of all features
- Installation instructions
- Usage examples
- Implementation details
- Output file descriptions
- Troubleshooting guide

**Start here** for understanding the project.

### `QUICKSTART.md` (138 lines) ⚡
**Purpose**: Get started quickly
**Contents**:
- Quick test (5 servers, 30 seconds)
- Full experiment (10 servers, 60 seconds)
- Docker and local Python commands
- Result verification

**Use this** to run your first experiment.

### `INSTALLATION.md` (392 lines) 🔧
**Purpose**: Detailed installation guide
**Contents**:
- Prerequisites and requirements
- Docker installation method
- Local Python installation method
- Platform-specific notes (Ubuntu, WSL2, macOS)
- Troubleshooting common issues

**Use this** if you encounter installation problems.

### `REPORT_TEMPLATE.md` (378 lines) 📝
**Purpose**: Template for writing your report
**Contents**:
- Structured sections for Q1, Q2, Q3
- Placeholders for plots and analysis
- Observation and analysis templates
- Algorithm extraction template

**Use this** when writing your assignment report.

### `PROJECT_SUMMARY.md` (472 lines) 📊
**Purpose**: Technical project overview
**Contents**:
- Complete feature list
- Implementation details
- File structure
- Output files description
- Compliance with requirements

**Use this** to understand technical details.

### `CHECKLIST.md` (385 lines) ✅
**Purpose**: Pre-submission verification
**Contents**:
- Code implementation checklist
- Testing checklist
- Report checklist
- Submission verification steps

**Use this** before submitting your assignment.

### `INDEX.md` (this file) 📇
**Purpose**: Quick reference to all files

---

## ⚙️ Configuration Files

### `requirements.txt` (5 lines)
Python dependencies:
- numpy >= 1.24.0
- pandas >= 2.0.0
- matplotlib >= 3.7.0
- scikit-learn >= 1.3.0
- scipy >= 1.11.0

### `servers.txt` (14 lines)
List of public iPerf3 servers to test.
Format: `host:port` or just `host`

Edit this file to add/remove servers.

### `Dockerfile` (29 lines)
Docker containerization:
- Base: ubuntu:24.04
- Installs Python and dependencies
- Sets up working environment

### `.dockerignore` (23 lines)
Files to exclude from Docker image:
- Output directories (results, plots, models)
- Python cache
- IDE files

### `.gitignore` (51 lines)
Files to exclude from Git:
- Python cache and build files
- Output directories
- Large data files
- IDE and OS files

---

## 🔨 Utility Scripts

### `run_docker.sh` (26 lines)
Convenience script to build and run Docker container.

**Usage**: `./run_docker.sh`

---

## 📖 Original Assignment

### `assignment-2.pdf` (3 pages)
Original assignment document from course.

### `assignment-2.txt` (122 lines)
Text version of assignment (for reference).

---

## 🎯 Quick Navigation

### I want to...

**...understand what this project does**
→ Read `README.md`

**...run my first test quickly**
→ Read `QUICKSTART.md`

**...install and setup the environment**
→ Read `INSTALLATION.md`

**...understand the implementation**
→ Read `PROJECT_SUMMARY.md`

**...write my report**
→ Use `REPORT_TEMPLATE.md`

**...verify before submission**
→ Use `CHECKLIST.md`

**...understand a specific code file**
→ See "Core Implementation Files" section above

**...troubleshoot an issue**
→ Check `INSTALLATION.md` troubleshooting section

**...modify the code**
→ Start with the relevant file in "Core Implementation Files"

**...add more servers**
→ Edit `servers.txt`

**...change ML parameters**
→ Use `--alpha` and `--beta` flags in `run_experiment.py`

---

## 📊 Project Statistics

- **Python Code**: 1,809 lines (6 files)
- **Documentation**: 2,075 lines (7 files)
- **Total Files**: 22 files
- **Core Features**: 3 (iPerf client, TCP stats, ML model)
- **Automation**: Full pipeline automation
- **Containerization**: Docker support

---

## 🚀 Common Commands

```bash
# Verify setup
python3 test_setup.py

# Quick test (5 minutes)
python3 run_experiment.py servers.txt --n-servers 3 --duration 10

# Full test (30 minutes)
python3 run_experiment.py servers.txt --n-servers 10 --duration 60

# Docker build
docker build -t iperf-assignment .

# Docker run
docker run --rm --network host \
  -v $(pwd)/results:/app/results \
  -v $(pwd)/plots:/app/plots \
  -v $(pwd)/models:/app/models \
  iperf-assignment \
  python3 run_experiment.py servers.txt --n-servers 10 --duration 60

# Test single component
python3 iperf_client.py iperf3.velnet.co.uk
python3 visualization.py
python3 ml_model.py 1.0 1.0

# View results
cat results/summary_statistics.csv
ls plots/*.pdf
cat plots/congestion_algorithm.txt
```

---

## 📂 Output Directory Structure

After running the experiment:

```
cs53600/Assignment2/
├── results/
│   ├── iperf_results.json           # Complete test results
│   ├── summary_statistics.csv       # Summary per server
│   └── tcp_stats_<server>.csv       # TCP stats per server
├── plots/
│   ├── throughput_all.pdf           # All destinations
│   ├── representative_*.pdf         # Time series & scatter
│   ├── cwnd_prediction_*.pdf        # ML predictions
│   ├── congestion_algorithm.txt     # Extracted algorithm
│   └── summary_table.tex            # LaTeX table
├── models/
│   └── cwnd_model.pkl              # Trained ML model
└── experiment.log                   # Execution log
```

---

## 🎓 Assignment Requirements Mapping

| Requirement | Implementation File | Documentation |
|-------------|-------------------|---------------|
| Q1: iPerf Client | `iperf_client.py` | README.md Q1 |
| Q1: Data Collection | `data_collector.py` | README.md Q1 |
| Q1: Throughput Plot | `visualization.py` | README.md Q2 |
| Q2: TCP Stats | `iperf_client.py` | README.md Q2 |
| Q2: Visualizations | `visualization.py` | README.md Q2 |
| Q2: Observations | REPORT_TEMPLATE.md Q2 | README.md Q2 |
| Q3: ML Dataset | `ml_model.py` | README.md Q3 |
| Q3: Model Training | `ml_model.py` | README.md Q3 |
| Q3: Predictions | `ml_model.py` | README.md Q3 |
| Q3: Algorithm | `ml_model.py` | README.md Q3 |
| Automation | `run_experiment.py` | QUICKSTART.md |
| Docker | `Dockerfile` | INSTALLATION.md |

---

## 📞 Getting Help

1. **Installation issues** → `INSTALLATION.md`
2. **Usage questions** → `README.md` or `QUICKSTART.md`
3. **Code questions** → This file (INDEX.md) + code comments
4. **Report writing** → `REPORT_TEMPLATE.md`
5. **Verification** → `CHECKLIST.md`

---

**Last Updated**: February 22, 2026
**Assignment Due**: March 10, 2026 @ 11:45 PM ET

---

## 🎉 Ready to Start?

1. **First time**: Read `README.md`
2. **Quick start**: Follow `QUICKSTART.md`
3. **Issues**: Check `INSTALLATION.md`
4. **Development**: Refer to code files above
5. **Report**: Use `REPORT_TEMPLATE.md`
6. **Submission**: Use `CHECKLIST.md`

**Good luck!** 🚀
