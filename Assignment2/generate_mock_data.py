#!/usr/bin/env python3
"""
Generate mock data for demonstration purposes
This script creates realistic-looking TCP statistics and throughput data
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MockDataGenerator")


def generate_tcp_trace(server_name, duration=60, sampling_interval=1.0, base_rtt=50):
    """Generate realistic TCP statistics trace"""
    samples = []
    time_points = np.arange(0, duration, sampling_interval)

    # Initialize TCP parameters
    cwnd = 10  # Initial cwnd
    ssthresh = 65535  # Initial ssthresh
    retrans = 0
    base_throughput = np.random.uniform(10, 100) * 1e6  # 10-100 Mbps

    for t in time_points:
        # Simulate slow start and congestion avoidance
        if cwnd < ssthresh:
            # Slow start: exponential growth
            cwnd = min(cwnd * 1.05, ssthresh)
        else:
            # Congestion avoidance: linear growth
            cwnd += np.random.uniform(0, 2)

        # Randomly introduce congestion events
        if np.random.random() < 0.05:  # 5% chance of congestion
            ssthresh = max(cwnd / 2, 2)
            cwnd = ssthresh
            retrans += 1

        # RTT increases with queue buildup (related to cwnd)
        queue_delay = max(0, (cwnd - 100) * 0.5)
        rtt = base_rtt + queue_delay + np.random.uniform(-2, 2)

        # Throughput is limited by cwnd/RTT and network capacity
        theoretical_throughput = (cwnd * 1460 * 8) / (rtt / 1000)  # bits/s
        throughput = min(theoretical_throughput, base_throughput) * np.random.uniform(0.9, 1.1)

        # Add some random noise
        cwnd = max(2, cwnd + np.random.uniform(-1, 1))

        sample = {
            'timestamp': t,
            'destination': server_name,
            'cwnd': int(cwnd),
            'ssthresh': int(ssthresh),
            'rtt_ms': round(rtt, 2),
            'rttvar_ms': round(np.random.uniform(1, 10), 2),
            'retrans': retrans,
            'bytes_acked': int(throughput * sampling_interval / 8),
            'bytes_sent': int(throughput * sampling_interval / 8 * 1.05),
            'throughput_bps': round(throughput, 2),
            'throughput_mbps': round(throughput / 1e6, 2),
            'pacing_rate': round(throughput * 1.2, 2),
            'delivered': int(t * throughput / 8),
            'lost': retrans * 1460
        }
        samples.append(sample)

    return samples


def generate_mock_results():
    """Generate complete mock experimental results"""
    logger.info("Generating mock experiment data...")

    # Create output directories
    Path("results").mkdir(exist_ok=True)
    Path("plots").mkdir(exist_ok=True)
    Path("models").mkdir(exist_ok=True)

    # Define mock servers with different characteristics
    servers = [
        ("bouygues.iperf.fr:5201", 30, 80),  # Low RTT, high throughput
        ("ping.online.net:5201", 25, 90),
        ("iperf.he.net:5201", 100, 50),  # High RTT, medium throughput
        ("nyc.speedtest.clouvider.net:5201", 150, 30),  # Very high RTT, low throughput
        ("sgp.proof.ovh.net:5201", 200, 20),  # Intercontinental, high RTT
    ]

    all_results = []
    all_tcp_stats = []

    for server_name, base_rtt, _ in servers:
        logger.info(f"Generating data for {server_name}...")

        # Generate TCP trace
        duration = 60
        samples = generate_tcp_trace(server_name, duration=duration,
                                     sampling_interval=1.0, base_rtt=base_rtt)

        # Calculate summary statistics
        throughputs = [s['throughput_mbps'] for s in samples]
        total_bytes = sum(s['bytes_acked'] for s in samples)

        # Create throughput samples in expected format: (timestamp, throughput_bps)
        throughput_samples = [(s['timestamp'], s['throughput_bps']) for s in samples]

        result = {
            'server': server_name,
            'server_host': server_name.split(':')[0],
            'server_port': int(server_name.split(':')[1]),
            'host': server_name.split(':')[0],
            'port': int(server_name.split(':')[1]),
            'duration': duration,
            'total_bytes': total_bytes,
            'avg_throughput': np.mean([s['throughput_bps'] for s in samples]),
            'avg_throughput_bps': np.mean([s['throughput_bps'] for s in samples]),
            'avg_throughput_mbps': np.mean(throughputs),
            'min_throughput_mbps': np.min(throughputs),
            'max_throughput_mbps': np.max(throughputs),
            'median_throughput_mbps': np.median(throughputs),
            'p95_throughput_mbps': np.percentile(throughputs, 95),
            'throughput_samples': throughput_samples,
            'tcp_stats': samples,
            'success': True,
            'error': None,
            'error_msg': None
        }

        all_results.append(result)
        all_tcp_stats.extend(samples)

    # Save iperf_results.json
    results_file = "results/iperf_results.json"
    with open(results_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    logger.info(f"Saved results to {results_file}")

    # Save TCP stats for each destination
    for server_name, _, _ in servers:
        server_stats = [s for s in all_tcp_stats if s['destination'] == server_name]
        server_file = f"results/{server_name.replace(':', '_')}_tcp_stats.csv"
        df = pd.DataFrame(server_stats)
        df.to_csv(server_file, index=False)
        logger.info(f"Saved TCP stats to {server_file}")

    # Save combined TCP stats
    combined_file = "results/all_tcp_stats.csv"
    df_all = pd.DataFrame(all_tcp_stats)
    df_all.to_csv(combined_file, index=False)
    logger.info(f"Saved combined TCP stats to {combined_file}")

    # Save summary statistics
    summary_file = "results/summary_statistics.csv"
    df_summary = pd.DataFrame(all_results)
    df_summary = df_summary[['server', 'avg_throughput_mbps', 'min_throughput_mbps',
                             'median_throughput_mbps', 'p95_throughput_mbps', 'max_throughput_mbps']]
    df_summary.columns = ['Server', 'Avg (Mbps)', 'Min (Mbps)', 'Median (Mbps)', 'P95 (Mbps)', 'Max (Mbps)']
    df_summary.to_csv(summary_file, index=False)
    logger.info(f"Saved summary to {summary_file}")

    logger.info("Mock data generation complete!")
    return all_results, all_tcp_stats


if __name__ == "__main__":
    generate_mock_results()
