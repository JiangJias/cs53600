#!/usr/bin/env python3
"""
Data collection and storage module
Collects TCP statistics and throughput measurements from multiple destinations
"""

import json
import csv
import logging
from typing import List, Dict
from pathlib import Path
import random
import time

from iperf_client import IperfClient, IperfResult, IPERF_CONTROL_PORT


class DataCollector:
    """Collect data from multiple iPerf servers"""

    def __init__(self, output_dir: str = "results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)
        self.logger = logging.getLogger("DataCollector")
        self.results: List[IperfResult] = []

    def collect_from_servers(self, servers: List[Dict[str, any]],
                            duration: int = 60,
                            sampling_interval: float = 0.2,
                            max_attempts: int = 3) -> List[IperfResult]:
        """
        Collect data from multiple iPerf servers

        Args:
            servers: List of server dicts with 'host' and optionally 'port'
            duration: Test duration in seconds
            sampling_interval: Sampling interval in seconds
            max_attempts: Max attempts per server before skipping

        Returns:
            List of successful IperfResult objects
        """
        results = []

        for server_info in servers:
            host = server_info.get('host')
            port = server_info.get('port', IPERF_CONTROL_PORT)

            self.logger.info(f"Testing server: {host}:{port}")

            success = False
            for attempt in range(max_attempts):
                try:
                    client = IperfClient(host, port, duration, sampling_interval)
                    result = client.run_test()

                    if result.success:
                        results.append(result)
                        self.logger.info(f"Successfully tested {host}:{port}")
                        success = True
                        break
                    else:
                        self.logger.warning(f"Attempt {attempt+1}/{max_attempts} failed for {host}:{port}: {result.error_msg}")

                except Exception as e:
                    self.logger.error(f"Attempt {attempt+1}/{max_attempts} exception for {host}:{port}: {e}")

                if attempt < max_attempts - 1:
                    time.sleep(2)  # Wait before retry

            if not success:
                self.logger.error(f"Skipping {host}:{port} after {max_attempts} failed attempts")

        self.results = results
        return results

    def save_results_json(self, filename: str = "iperf_results.json"):
        """Save all results to JSON file"""
        output_file = self.output_dir / filename

        results_data = []
        for result in self.results:
            result_dict = {
                'server_host': result.server_host,
                'server_port': result.server_port,
                'duration': result.duration,
                'total_bytes': result.total_bytes,
                'avg_throughput': result.avg_throughput,
                'throughput_samples': result.throughput_samples,
                'tcp_stats': result.tcp_stats,
                'success': result.success,
                'error_msg': result.error_msg
            }
            results_data.append(result_dict)

        with open(output_file, 'w') as f:
            json.dump(results_data, f, indent=2)

        self.logger.info(f"Results saved to {output_file}")

    def save_tcp_stats_csv(self, result: IperfResult, filename: str = None):
        """Save TCP statistics to CSV file for a single result"""
        if filename is None:
            filename = f"tcp_stats_{result.server_host.replace('.', '_')}.csv"

        output_file = self.output_dir / filename

        if not result.tcp_stats:
            self.logger.warning(f"No TCP stats to save for {result.server_host}")
            return

        # Get all possible fields
        all_fields = set()
        for stat in result.tcp_stats:
            all_fields.update(stat.keys())

        fieldnames = sorted(all_fields)

        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(result.tcp_stats)

        self.logger.info(f"TCP stats saved to {output_file}")

    def save_all_tcp_stats(self):
        """Save TCP statistics for all results"""
        for result in self.results:
            if result.success:
                self.save_tcp_stats_csv(result)

    def get_summary_statistics(self) -> List[Dict]:
        """Calculate summary statistics for each destination"""
        import numpy as np

        summary = []
        for result in self.results:
            if not result.success or not result.throughput_samples:
                continue

            throughputs = [sample[1] for sample in result.throughput_samples]
            throughputs_mbps = [t / 1e6 for t in throughputs]

            summary_dict = {
                'server': f"{result.server_host}:{result.server_port}",
                'min_mbps': np.min(throughputs_mbps),
                'median_mbps': np.median(throughputs_mbps),
                'avg_mbps': np.mean(throughputs_mbps),
                'p95_mbps': np.percentile(throughputs_mbps, 95),
                'max_mbps': np.max(throughputs_mbps),
                'samples': len(throughputs)
            }
            summary.append(summary_dict)

        return summary

    def save_summary_csv(self, filename: str = "summary_statistics.csv"):
        """Save summary statistics to CSV"""
        output_file = self.output_dir / filename

        summary = self.get_summary_statistics()
        if not summary:
            self.logger.warning("No summary statistics to save")
            return

        fieldnames = ['server', 'min_mbps', 'median_mbps', 'avg_mbps', 'p95_mbps', 'max_mbps', 'samples']

        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(summary)

        self.logger.info(f"Summary statistics saved to {output_file}")


def load_server_list(filename: str) -> List[Dict]:
    """Load server list from file (one per line or JSON)"""
    servers = []

    with open(filename, 'r') as f:
        content = f.read().strip()

        # Try JSON first
        try:
            data = json.loads(content)
            if isinstance(data, list):
                servers = data
            else:
                servers = [data]
        except json.JSONDecodeError:
            # Assume one server per line
            for line in content.split('\n'):
                line = line.strip()
                if line and not line.startswith('#'):
                    if ':' in line:
                        host, port = line.split(':')
                        servers.append({'host': host.strip(), 'port': int(port.strip())})
                    else:
                        servers.append({'host': line})

    return servers


def select_random_servers(all_servers: List[Dict], n: int) -> List[Dict]:
    """Select n random servers from the list"""
    if len(all_servers) <= n:
        return all_servers
    return random.sample(all_servers, n)


if __name__ == "__main__":
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    if len(sys.argv) < 2:
        print("Usage: python data_collector.py <server_list_file> [n_servers] [duration]")
        sys.exit(1)

    server_file = sys.argv[1]
    n_servers = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    duration = int(sys.argv[3]) if len(sys.argv) > 3 else 60

    # Load servers
    all_servers = load_server_list(server_file)
    print(f"Loaded {len(all_servers)} servers from {server_file}")

    # Select random servers
    selected_servers = select_random_servers(all_servers, n_servers)
    print(f"Selected {len(selected_servers)} servers for testing")

    # Collect data
    collector = DataCollector()
    results = collector.collect_from_servers(selected_servers, duration=duration)

    print(f"\nSuccessfully collected data from {len(results)} servers")

    # Save results
    collector.save_results_json()
    collector.save_all_tcp_stats()
    collector.save_summary_csv()

    # Print summary
    print("\nSummary Statistics:")
    summary = collector.get_summary_statistics()
    for s in summary:
        print(f"{s['server']}: avg={s['avg_mbps']:.2f} Mbps, "
              f"median={s['median_mbps']:.2f} Mbps, "
              f"p95={s['p95_mbps']:.2f} Mbps")
