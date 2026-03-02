# Quick Start Guide

## Prerequisites

- Linux system (Ubuntu 22.04+) or Windows with WSL2
- Python 3.10+ OR Docker

## Option 1: Quick Test (5 servers, 30 seconds each)

### Using Docker (Recommended)

```bash
# Build Docker image
docker build -t iperf-assignment .

# Run experiment
docker run --rm --network host \
  -v $(pwd)/results:/app/results \
  -v $(pwd)/plots:/app/plots \
  -v $(pwd)/models:/app/models \
  iperf-assignment \
  python3 run_experiment.py servers.txt --n-servers 5 --duration 30
```

### Using Python directly

```bash
# Install dependencies
pip install -r requirements.txt

# Test setup
python3 test_setup.py

# Run experiment
python3 run_experiment.py servers.txt --n-servers 5 --duration 30
```

## Option 2: Full Experiment (10 servers, 60 seconds each)

This will take approximately 10-15 minutes.

### Using Docker

```bash
docker run --rm --network host \
  -v $(pwd)/results:/app/results \
  -v $(pwd)/plots:/app/plots \
  -v $(pwd)/models:/app/models \
  iperf-assignment \
  python3 run_experiment.py servers.txt --n-servers 10 --duration 60
```

### Using Python directly

```bash
python3 run_experiment.py servers.txt --n-servers 10 --duration 60
```

## Check Results

After the experiment completes:

```bash
# View summary statistics
cat results/summary_statistics.csv

# View generated plots
ls plots/*.pdf

# View ML algorithm
cat plots/congestion_algorithm.txt

# View experiment log
cat experiment.log
```

## Test Individual Components

### Test iPerf client only

```bash
python3 iperf_client.py iperf3.velnet.co.uk
```

### Generate visualizations only (from existing data)

```bash
python3 visualization.py
```

### Train ML model only (from existing data)

```bash
python3 ml_model.py 1.0 1.0
```

## Troubleshooting

### "No module named 'numpy'" or similar

Install dependencies:
```bash
pip install -r requirements.txt
```

### "Connection refused" or servers not responding

Some servers may be offline. The script will automatically skip them and try others. Consider:
- Using more servers: `--n-servers 15`
- Updating the server list in `servers.txt`

### Docker: "Cannot connect to the Docker daemon"

Start Docker:
```bash
sudo systemctl start docker
```

### WSL2: Network issues

Ensure WSL2 has network access:
```bash
ping 8.8.8.8
```

## Next Steps

1. Review the generated plots in `plots/` directory
2. Examine the data files in `results/` directory
3. Read the extracted algorithm in `plots/congestion_algorithm.txt`
4. Fill out the report template in `REPORT_TEMPLATE.md`

## Getting Help

- Check `README.md` for detailed documentation
- Run `python3 test_setup.py` to verify setup
- Review logs in `experiment.log`
- Check server availability at https://iperf3serverlist.net/
