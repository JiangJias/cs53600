#!/usr/bin/env python3
"""
Visualization module for iPerf results and TCP statistics
Generates plots for throughput, congestion window, RTT, and loss metrics
"""

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
import json
from pathlib import Path
from typing import List, Dict, Tuple
import logging


class Visualizer:
    """Create visualizations for iPerf results"""

    def __init__(self, results_dir: str = "results", plots_dir: str = "plots"):
        self.results_dir = Path(results_dir)
        self.plots_dir = Path(plots_dir)
        self.plots_dir.mkdir(exist_ok=True, parents=True)
        self.logger = logging.getLogger("Visualizer")

        # Set publication-quality defaults
        plt.rcParams['figure.figsize'] = (10, 6)
        plt.rcParams['font.size'] = 10
        plt.rcParams['axes.labelsize'] = 11
        plt.rcParams['axes.titlesize'] = 12
        plt.rcParams['legend.fontsize'] = 9

    def load_results(self, filename: str = "iperf_results.json") -> List[Dict]:
        """Load results from JSON file"""
        results_file = self.results_dir / filename
        with open(results_file, 'r') as f:
            return json.load(f)

    def plot_throughput_timeseries_all(self, results: List[Dict], filename: str = "throughput_all.pdf"):
        """Plot throughput time series for all destinations on same plot"""
        plt.figure(figsize=(12, 6))

        for result in results:
            if not result['success']:
                continue

            samples = result['throughput_samples']
            if not samples:
                continue

            timestamps = [s[0] for s in samples]
            throughputs_mbps = [s[1] / 1e6 for s in samples]

            label = f"{result['server_host']}"
            plt.plot(timestamps, throughputs_mbps, label=label, alpha=0.7, linewidth=1)

        plt.xlabel('Time (seconds)')
        plt.ylabel('Throughput (Mbps)')
        plt.title('Throughput Time Series - All Destinations')
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()

        output_file = self.plots_dir / filename
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()

        self.logger.info(f"Saved throughput plot: {output_file}")

    def plot_tcp_stats_timeseries(self, result: Dict, filename_prefix: str = None):
        """Plot TCP statistics time series for a single destination"""
        if not result['success'] or not result['tcp_stats']:
            self.logger.warning(f"No TCP stats for {result['server_host']}")
            return

        if filename_prefix is None:
            filename_prefix = f"tcp_stats_{result['server_host'].replace('.', '_')}"

        stats = result['tcp_stats']

        # Extract data
        timestamps = [s['timestamp'] for s in stats if 'timestamp' in s]
        cwnd = [s.get('snd_cwnd', 0) for s in stats]
        rtt = [s.get('rtt', 0) / 1000 for s in stats]  # Convert to ms
        retrans = [s.get('retrans', 0) for s in stats]
        throughput_mbps = [s.get('throughput_bps', 0) / 1e6 for s in stats]

        # Plot 1: Congestion Window
        plt.figure(figsize=(10, 5))
        plt.plot(timestamps, cwnd, linewidth=1.5, color='blue')
        plt.xlabel('Time (seconds)')
        plt.ylabel('Congestion Window (packets)')
        plt.title(f'Congestion Window - {result["server_host"]}')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(self.plots_dir / f"{filename_prefix}_cwnd.pdf", dpi=300, bbox_inches='tight')
        plt.close()

        # Plot 2: RTT
        plt.figure(figsize=(10, 5))
        plt.plot(timestamps, rtt, linewidth=1.5, color='green')
        plt.xlabel('Time (seconds)')
        plt.ylabel('RTT (ms)')
        plt.title(f'Round Trip Time - {result["server_host"]}')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(self.plots_dir / f"{filename_prefix}_rtt.pdf", dpi=300, bbox_inches='tight')
        plt.close()

        # Plot 3: Retransmissions (loss proxy)
        plt.figure(figsize=(10, 5))
        plt.plot(timestamps, retrans, linewidth=1.5, color='red')
        plt.xlabel('Time (seconds)')
        plt.ylabel('Cumulative Retransmissions')
        plt.title(f'Retransmissions - {result["server_host"]}')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(self.plots_dir / f"{filename_prefix}_retrans.pdf", dpi=300, bbox_inches='tight')
        plt.close()

        # Plot 4: Throughput
        plt.figure(figsize=(10, 5))
        plt.plot(timestamps, throughput_mbps, linewidth=1.5, color='purple')
        plt.xlabel('Time (seconds)')
        plt.ylabel('Throughput (Mbps)')
        plt.title(f'Throughput - {result["server_host"]}')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(self.plots_dir / f"{filename_prefix}_throughput.pdf", dpi=300, bbox_inches='tight')
        plt.close()

        self.logger.info(f"Saved TCP stats plots for {result['server_host']}")

    def plot_scatter_relationships(self, result: Dict, filename_prefix: str = None):
        """Plot scatter plots showing relationships between metrics"""
        if not result['success'] or not result['tcp_stats']:
            self.logger.warning(f"No TCP stats for {result['server_host']}")
            return

        if filename_prefix is None:
            filename_prefix = f"scatter_{result['server_host'].replace('.', '_')}"

        stats = result['tcp_stats']

        # Extract data
        cwnd = [s.get('snd_cwnd', 0) for s in stats]
        rtt = [s.get('rtt', 0) / 1000 for s in stats]  # Convert to ms
        retrans = [s.get('retrans', 0) for s in stats]
        throughput_mbps = [s.get('throughput_bps', 0) / 1e6 for s in stats]

        # Calculate incremental retransmissions for loss signal
        retrans_incremental = [0] + [retrans[i] - retrans[i-1] for i in range(1, len(retrans))]

        # Scatter 1: Congestion Window vs Throughput
        plt.figure(figsize=(8, 6))
        plt.scatter(cwnd, throughput_mbps, alpha=0.5, s=20)
        plt.xlabel('Congestion Window (packets)')
        plt.ylabel('Throughput (Mbps)')
        plt.title(f'Congestion Window vs Throughput - {result["server_host"]}')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(self.plots_dir / f"{filename_prefix}_cwnd_vs_throughput.pdf", dpi=300, bbox_inches='tight')
        plt.close()

        # Scatter 2: RTT vs Throughput
        plt.figure(figsize=(8, 6))
        plt.scatter(rtt, throughput_mbps, alpha=0.5, s=20, color='green')
        plt.xlabel('RTT (ms)')
        plt.ylabel('Throughput (Mbps)')
        plt.title(f'RTT vs Throughput - {result["server_host"]}')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(self.plots_dir / f"{filename_prefix}_rtt_vs_throughput.pdf", dpi=300, bbox_inches='tight')
        plt.close()

        # Scatter 3: Loss signal vs Throughput
        plt.figure(figsize=(8, 6))
        plt.scatter(retrans_incremental, throughput_mbps, alpha=0.5, s=20, color='red')
        plt.xlabel('Incremental Retransmissions')
        plt.ylabel('Throughput (Mbps)')
        plt.title(f'Loss Signal vs Throughput - {result["server_host"]}')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(self.plots_dir / f"{filename_prefix}_loss_vs_throughput.pdf", dpi=300, bbox_inches='tight')
        plt.close()

        self.logger.info(f"Saved scatter plots for {result['server_host']}")

    def plot_all_visualizations(self):
        """Generate all visualizations"""
        # Load results
        results = self.load_results()

        # Plot throughput for all destinations
        self.plot_throughput_timeseries_all(results)

        # Find a representative destination (one with most samples)
        best_result = None
        max_samples = 0

        for result in results:
            if result['success'] and result['tcp_stats']:
                n_samples = len(result['tcp_stats'])
                if n_samples > max_samples:
                    max_samples = n_samples
                    best_result = result

        if best_result:
            self.logger.info(f"Selected {best_result['server_host']} as representative destination")
            # Plot detailed TCP stats for representative destination
            self.plot_tcp_stats_timeseries(best_result, filename_prefix="representative")
            self.plot_scatter_relationships(best_result, filename_prefix="representative")
        else:
            self.logger.warning("No suitable representative destination found")

        self.logger.info("All visualizations generated")


def generate_summary_table_latex(results_dir: str = "results", output_dir: str = "plots"):
    """Generate LaTeX table with summary statistics"""
    import csv

    results_path = Path(results_dir)
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True, parents=True)

    summary_file = results_path / "summary_statistics.csv"
    if not summary_file.exists():
        logging.warning(f"Summary file not found: {summary_file}")
        return

    # Read summary data
    with open(summary_file, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Generate LaTeX table
    latex_file = output_path / "summary_table.tex"
    with open(latex_file, 'w') as f:
        f.write("\\begin{table}[h]\n")
        f.write("\\centering\n")
        f.write("\\begin{tabular}{|l|r|r|r|r|}\n")
        f.write("\\hline\n")
        f.write("Server & Min (Mbps) & Median (Mbps) & Avg (Mbps) & P95 (Mbps) \\\\\n")
        f.write("\\hline\n")

        for row in rows:
            server = row['server'].replace('_', '\\_')
            f.write(f"{server} & "
                   f"{float(row['min_mbps']):.2f} & "
                   f"{float(row['median_mbps']):.2f} & "
                   f"{float(row['avg_mbps']):.2f} & "
                   f"{float(row['p95_mbps']):.2f} \\\\\n")

        f.write("\\hline\n")
        f.write("\\end{tabular}\n")
        f.write("\\caption{Summary statistics for throughput measurements}\n")
        f.write("\\label{tab:summary}\n")
        f.write("\\end{table}\n")

    logging.info(f"Generated LaTeX table: {latex_file}")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    visualizer = Visualizer()
    visualizer.plot_all_visualizations()
    generate_summary_table_latex()

    print("All visualizations generated successfully")
