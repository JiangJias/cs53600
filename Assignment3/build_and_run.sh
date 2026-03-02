#!/bin/bash
#
# Build and run NS-3 simulation for Assignment 3
# This script automates the entire process from building to generating plots
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}Assignment 3: NS-3 Simulation Runner${NC}"
echo -e "${GREEN}======================================${NC}"
echo

# Check if NS-3 is installed
if ! command -v ns3 &> /dev/null && ! [ -d "ns-3-dev" ] && ! [ -d "../ns-3-dev" ]; then
    echo -e "${YELLOW}Warning: NS-3 not found in current or parent directory${NC}"
    echo -e "${YELLOW}This script assumes NS-3 is installed${NC}"
    echo
    echo "Please follow these steps:"
    echo "1. Download NS-3: https://www.nsnam.org/releases/"
    echo "2. Extract to this directory or parent directory"
    echo "3. Build NS-3 first"
    echo
    echo "Alternative: This script can work if you have NS-3 in your PATH"
    echo
fi

# Function to find NS-3 directory
find_ns3_dir() {
    if [ -d "ns-3-dev" ]; then
        echo "ns-3-dev"
    elif [ -d "../ns-3-dev" ]; then
        echo "../ns-3-dev"
    elif [ -d "ns-3.41" ]; then
        echo "ns-3.41"
    elif [ -d "../ns-3.41" ]; then
        echo "../ns-3.41"
    else
        echo ""
    fi
}

NS3_DIR=$(find_ns3_dir)

# Step 1: Copy files to NS-3 source tree (if NS-3 found)
if [ ! -z "$NS3_DIR" ]; then
    echo -e "${GREEN}Step 1: Copying files to NS-3 source tree${NC}"

    # Copy congestion control files
    cp tcp-ml-cong.h "$NS3_DIR/src/internet/model/"
    cp tcp-ml-cong.cc "$NS3_DIR/src/internet/model/"

    # Copy simulation script
    cp leaf-spine-simulation.cc "$NS3_DIR/scratch/"

    echo -e "${GREEN}✓ Files copied successfully${NC}"
    echo

    # Step 2: Build NS-3
    echo -e "${GREEN}Step 2: Building NS-3 with custom TCP${NC}"
    cd "$NS3_DIR"

    if command -v ./ns3 &> /dev/null; then
        ./ns3 configure --enable-examples --enable-tests
        ./ns3 build
    elif command -v ./waf &> /dev/null; then
        ./waf configure --enable-examples --enable-tests
        ./waf build
    else
        echo -e "${RED}Error: Cannot find NS-3 build system (ns3 or waf)${NC}"
        exit 1
    fi

    echo -e "${GREEN}✓ NS-3 built successfully${NC}"
    echo

    # Go back to assignment directory
    cd - > /dev/null
else
    echo -e "${YELLOW}NS-3 directory not found, skipping build step${NC}"
    echo -e "${YELLOW}Assuming you will build manually${NC}"
    echo
fi

# Step 3: Run simulations
echo -e "${GREEN}Step 3: Running simulations${NC}"
echo

# Create output directory
mkdir -p results
mkdir -p plots

# Function to run simulation
run_simulation() {
    TCP_VARIANT=$1
    echo -e "${YELLOW}Running simulation with $TCP_VARIANT...${NC}"

    if [ ! -z "$NS3_DIR" ]; then
        cd "$NS3_DIR"
        if command -v ./ns3 &> /dev/null; then
            ./ns3 run "scratch/leaf-spine-simulation --tcp=$TCP_VARIANT"
        elif command -v ./waf &> /dev/null; then
            ./waf --run "scratch/leaf-spine-simulation --tcp=$TCP_VARIANT"
        fi
        cd - > /dev/null
    else
        echo -e "${RED}Cannot run simulation: NS-3 directory not found${NC}"
        exit 1
    fi
}

# Run all three TCP variants
if [ ! -z "$NS3_DIR" ]; then
    # Run all variants in one go
    cd "$NS3_DIR"
    echo -e "${YELLOW}Running all TCP variants...${NC}"
    if command -v ./ns3 &> /dev/null; then
        ./ns3 run "scratch/leaf-spine-simulation --runAll=true"
    elif command -v ./waf &> /dev/null; then
        ./waf --run "scratch/leaf-spine-simulation --runAll=true"
    fi

    # Copy results back
    if [ -f "flow_completion_times.csv" ]; then
        cp flow_completion_times.csv "../Assignment3/" 2>/dev/null || cp flow_completion_times.csv "Assignment3/" 2>/dev/null || true
    fi

    cd - > /dev/null
fi

echo -e "${GREEN}✓ Simulations completed${NC}"
echo

# Step 4: Analyze results and generate plots
echo -e "${GREEN}Step 4: Analyzing results and generating plots${NC}"

if [ -f "flow_completion_times.csv" ]; then
    python3 analyze_results.py
    echo -e "${GREEN}✓ Analysis completed${NC}"
else
    echo -e "${RED}Error: flow_completion_times.csv not found${NC}"
    echo -e "${YELLOW}Please check if simulations ran successfully${NC}"
fi

echo
echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}All steps completed!${NC}"
echo -e "${GREEN}======================================${NC}"
echo
echo "Output files:"
echo "  - flow_completion_times.csv (raw data)"
echo "  - plots/fct_comparison.pdf"
echo "  - plots/fct_cdf.pdf"
echo "  - plots/fct_boxplot.pdf"
echo "  - plots/fct_histogram.pdf"
echo "  - plots/fct_stats_table.tex"
echo
