#!/usr/bin/env python3
"""
Standalone simulation runner for Assignment 3

This script provides a simplified Python-based simulation that demonstrates
the congestion control algorithm without requiring full NS-3 installation.
For actual NS-3 simulation, use build_and_run.sh
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
import sys

# Simulation parameters
NUM_SERVERS = 32
NUM_TORS = 2
NUM_SPINES = 2
FLOW_SIZE = 64 * 1024 * 1024  # 64 MB
SERVER_BANDWIDTH = 100e9  # 100 Gbps
SPINE_BANDWIDTH = 400e9   # 400 Gbps
PROPAGATION_DELAY = 500e-9  # 500 ns
SEGMENT_SIZE = 1448  # bytes

class SimplifiedTcpSimulator:
    """Simplified TCP congestion control simulator"""

    def __init__(self, tcp_variant='TcpNewReno'):
        self.tcp_variant = tcp_variant
        self.flows = []

    def simulate_flow(self, src, dst):
        """Simulate a single TCP flow"""
        # Initial conditions
        cwnd = 10  # Initial congestion window (segments)
        ssthresh = 65535  # Initial slow start threshold
        rtt = 4 * PROPAGATION_DELAY  # Base RTT (4 hops)
        bytes_sent = 0
        time = 0
        min_rtt = rtt

        # Simplified network conditions
        # Model queue delay and loss probability
        queue_delay = 0
        loss_prob = 0.001  # 0.1% base loss rate

        while bytes_sent < FLOW_SIZE:
            # Calculate throughput based on cwnd and RTT
            effective_rtt = rtt + queue_delay
            throughput = (cwnd * SEGMENT_SIZE) / effective_rtt

            # Limit by link bandwidth
            throughput = min(throughput, SERVER_BANDWIDTH)

            # Send data for one RTT
            bytes_in_rtt = int(throughput * effective_rtt)
            bytes_in_rtt = min(bytes_in_rtt, FLOW_SIZE - bytes_sent)
            bytes_sent += bytes_in_rtt

            # Simulate loss
            if np.random.random() < loss_prob:
                # Loss detected: multiplicative decrease
                ssthresh = max(cwnd // 2, 2)
                cwnd = ssthresh
            else:
                # No loss: increase cwnd
                if self.tcp_variant == 'TcpNewReno':
                    cwnd = self._tcp_newreno_increase(cwnd, ssthresh)
                elif self.tcp_variant == 'TcpCubic':
                    cwnd = self._tcp_cubic_increase(cwnd, ssthresh, time)
                elif self.tcp_variant == 'TcpMlCong':
                    cwnd = self._tcp_mlcong_increase(cwnd, ssthresh, rtt, min_rtt)

            # Update queue delay based on congestion
            # More cwnd -> more queue buildup
            queue_delay = (cwnd / 100) * PROPAGATION_DELAY

            # Update RTT
            rtt = 4 * PROPAGATION_DELAY + queue_delay
            min_rtt = min(min_rtt, rtt)

            # Update loss probability based on queue size
            queue_occupancy = queue_delay / (10 * PROPAGATION_DELAY)  # Normalized
            loss_prob = 0.001 + 0.01 * queue_occupancy  # Increases with queue

            # Advance time
            time += effective_rtt

        return time

    def _tcp_newreno_increase(self, cwnd, ssthresh):
        """TCP NewReno congestion window increase"""
        if cwnd < ssthresh:
            # Slow start: exponential increase
            return cwnd + 1
        else:
            # Congestion avoidance: additive increase
            return cwnd + 1.0 / cwnd

    def _tcp_cubic_increase(self, cwnd, ssthresh, time):
        """TCP CUBIC congestion window increase (simplified)"""
        if cwnd < ssthresh:
            # Slow start
            return cwnd + 1
        else:
            # CUBIC function (simplified)
            C = 0.4
            beta = 0.7
            W_max = cwnd / beta
            K = np.cbrt(W_max * (1 - beta) / C)
            t = time - K
            cubic_cwnd = C * (t ** 3) + W_max
            return max(cwnd + 1.0 / cwnd, cubic_cwnd)

    def _tcp_mlcong_increase(self, cwnd, ssthresh, rtt, min_rtt):
        """ML-based TCP congestion window increase"""
        if cwnd < ssthresh:
            # Slow start
            return cwnd + 1
        else:
            # RTT-aware congestion avoidance
            rtt_ratio = rtt / min_rtt

            if rtt_ratio > 1.2:
                # RTT increased significantly: slow down
                increase = 0.5 / cwnd
            elif rtt_ratio > 1.1:
                # RTT slightly increased: be conservative
                increase = 0.75 / cwnd
            else:
                # RTT stable: normal AIMD
                increase = 1.0 / cwnd

            return cwnd + increase

    def run_simulation(self):
        """Run simulation for all flows"""
        print(f"Running simulation with {self.tcp_variant}...")

        flow_times = []
        flow_id = 0

        # Each server sends to every other server
        for src in range(NUM_SERVERS):
            for dst in range(NUM_SERVERS):
                if src != dst:
                    fct = self.simulate_flow(src, dst)
                    flow_times.append({
                        'TcpVariant': self.tcp_variant,
                        'FlowId': flow_id,
                        'FCT(seconds)': fct
                    })
                    flow_id += 1

            # Progress indicator
            if (src + 1) % 8 == 0:
                print(f"  Completed {src + 1}/{NUM_SERVERS} servers")

        return pd.DataFrame(flow_times)

def main():
    print("="*60)
    print("Assignment 3: Standalone TCP Simulation")
    print("="*60)
    print()
    print("Note: This is a simplified simulation for demonstration.")
    print("For full NS-3 simulation, use build_and_run.sh")
    print()

    # Create output directories
    Path('plots').mkdir(exist_ok=True)

    # Run simulations for all variants
    all_results = []

    variants = ['TcpNewReno', 'TcpCubic', 'TcpMlCong']

    for variant in variants:
        print(f"\nRunning {variant}...")
        sim = SimplifiedTcpSimulator(tcp_variant=variant)
        results = sim.run_simulation()
        all_results.append(results)

    # Combine results
    df = pd.concat(all_results, ignore_index=True)

    # Save to CSV
    df.to_csv('flow_completion_times.csv', index=False)
    print(f"\n✓ Results saved to flow_completion_times.csv")

    # Run analysis
    print("\nRunning analysis...")
    import analyze_results
    analyze_results.main()

    print("\n" + "="*60)
    print("Simulation complete!")
    print("="*60)
    print("\nGenerated files:")
    print("  - flow_completion_times.csv")
    print("  - plots/fct_comparison.pdf")
    print("  - plots/fct_cdf.pdf")
    print("  - plots/fct_boxplot.pdf")
    print("  - plots/fct_histogram.pdf")
    print("  - plots/fct_stats_table.tex")

if __name__ == "__main__":
    sys.exit(main())
