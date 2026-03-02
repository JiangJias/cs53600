#!/bin/bash
# Convenience script to build and run the Docker container

set -e

echo "Building Docker image..."
docker build -t iperf-assignment .

echo ""
echo "Docker image built successfully!"
echo ""
echo "To run the experiment, use:"
echo "  docker run --rm --network host \\"
echo "    -v \$(pwd)/results:/app/results \\"
echo "    -v \$(pwd)/plots:/app/plots \\"
echo "    -v \$(pwd)/models:/app/models \\"
echo "    iperf-assignment \\"
echo "    python3 run_experiment.py servers.txt --n-servers 10 --duration 60"
echo ""

# Optionally run the experiment
read -p "Do you want to run the experiment now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Running experiment..."
    docker run --rm --network host \
        -v $(pwd)/results:/app/results \
        -v $(pwd)/plots:/app/plots \
        -v $(pwd)/models:/app/models \
        iperf-assignment \
        python3 run_experiment.py servers.txt --n-servers 5 --duration 30
fi
