#!/usr/bin/env python3
"""
Analyze NS-3 simulation results and generate plots
"""

import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import sys
from pathlib import Path

def load_results(filename='flow_completion_times.csv'):
    """Load FCT results from CSV file"""
    try:
        df = pd.read_csv(filename)
        return df
    except FileNotFoundError:
        print(f"Error: {filename} not found!")
        return None

def calculate_statistics(df):
    """Calculate statistics for each TCP variant"""
    stats = {}

    for variant in df['TcpVariant'].unique():
        variant_data = df[df['TcpVariant'] == variant]['FCT(seconds)'].values

        stats[variant] = {
            'mean': np.mean(variant_data),
            'median': np.median(variant_data),
            'p99': np.percentile(variant_data, 99),
            'min': np.min(variant_data),
            'max': np.max(variant_data),
            'std': np.std(variant_data),
            'count': len(variant_data)
        }

    return stats

def plot_fct_comparison(df, output_dir='plots'):
    """Generate FCT comparison plots"""
    Path(output_dir).mkdir(exist_ok=True)

    variants = df['TcpVariant'].unique()
    colors = {'TcpNewReno': '#1f77b4', 'TcpCubic': '#ff7f0e', 'TcpMlCong': '#2ca02c'}

    # Plot 1: Average and 99th percentile FCT
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    avg_fcts = []
    p99_fcts = []
    variant_names = []

    for variant in variants:
        variant_data = df[df['TcpVariant'] == variant]['FCT(seconds)'].values
        avg_fcts.append(np.mean(variant_data))
        p99_fcts.append(np.percentile(variant_data, 99))
        variant_names.append(variant)

    # Average FCT
    bars1 = ax1.bar(range(len(variant_names)), avg_fcts,
                    color=[colors.get(v, 'gray') for v in variant_names])
    ax1.set_xticks(range(len(variant_names)))
    ax1.set_xticklabels(variant_names, rotation=45, ha='right')
    ax1.set_ylabel('Average FCT (seconds)')
    ax1.set_title('Average Flow Completion Time')
    ax1.grid(True, alpha=0.3)

    # Add value labels on bars
    for i, (bar, val) in enumerate(zip(bars1, avg_fcts)):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{val:.4f}s',
                ha='center', va='bottom', fontsize=10)

    # 99th percentile FCT
    bars2 = ax2.bar(range(len(variant_names)), p99_fcts,
                    color=[colors.get(v, 'gray') for v in variant_names])
    ax2.set_xticks(range(len(variant_names)))
    ax2.set_xticklabels(variant_names, rotation=45, ha='right')
    ax2.set_ylabel('99th Percentile FCT (seconds)')
    ax2.set_title('99th Percentile Flow Completion Time')
    ax2.grid(True, alpha=0.3)

    # Add value labels on bars
    for i, (bar, val) in enumerate(zip(bars2, p99_fcts)):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{val:.4f}s',
                ha='center', va='bottom', fontsize=10)

    plt.tight_layout()
    plt.savefig(f'{output_dir}/fct_comparison.pdf', dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Saved: {output_dir}/fct_comparison.pdf")

    # Plot 2: CDF of FCT
    fig, ax = plt.subplots(figsize=(10, 6))

    for variant in variants:
        variant_data = df[df['TcpVariant'] == variant]['FCT(seconds)'].values
        sorted_data = np.sort(variant_data)
        cdf = np.arange(1, len(sorted_data) + 1) / len(sorted_data)

        ax.plot(sorted_data, cdf, label=variant, linewidth=2,
                color=colors.get(variant, 'gray'))

    ax.set_xlabel('Flow Completion Time (seconds)')
    ax.set_ylabel('CDF')
    ax.set_title('CDF of Flow Completion Times')
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(f'{output_dir}/fct_cdf.pdf', dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Saved: {output_dir}/fct_cdf.pdf")

    # Plot 3: Box plot
    fig, ax = plt.subplots(figsize=(10, 6))

    data_for_boxplot = [df[df['TcpVariant'] == variant]['FCT(seconds)'].values
                        for variant in variants]

    bp = ax.boxplot(data_for_boxplot, labels=variants, patch_artist=True)

    # Color the boxes
    for patch, variant in zip(bp['boxes'], variants):
        patch.set_facecolor(colors.get(variant, 'gray'))
        patch.set_alpha(0.7)

    ax.set_ylabel('Flow Completion Time (seconds)')
    ax.set_title('Flow Completion Time Distribution')
    ax.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    plt.savefig(f'{output_dir}/fct_boxplot.pdf', dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Saved: {output_dir}/fct_boxplot.pdf")

    # Plot 4: Histogram
    fig, axes = plt.subplots(len(variants), 1, figsize=(10, 4*len(variants)))

    if len(variants) == 1:
        axes = [axes]

    for ax, variant in zip(axes, variants):
        variant_data = df[df['TcpVariant'] == variant]['FCT(seconds)'].values

        ax.hist(variant_data, bins=50, alpha=0.7,
               color=colors.get(variant, 'gray'), edgecolor='black')
        ax.set_xlabel('Flow Completion Time (seconds)')
        ax.set_ylabel('Frequency')
        ax.set_title(f'FCT Distribution - {variant}')
        ax.grid(True, alpha=0.3)

        # Add statistics text
        stats_text = f'Mean: {np.mean(variant_data):.4f}s\n'
        stats_text += f'Median: {np.median(variant_data):.4f}s\n'
        stats_text += f'P99: {np.percentile(variant_data, 99):.4f}s'
        ax.text(0.95, 0.95, stats_text,
               transform=ax.transAxes,
               verticalalignment='top',
               horizontalalignment='right',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5),
               fontsize=10)

    plt.tight_layout()
    plt.savefig(f'{output_dir}/fct_histogram.pdf', dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Saved: {output_dir}/fct_histogram.pdf")

def print_statistics_table(stats):
    """Print statistics in a formatted table"""
    print("\n" + "="*80)
    print("FLOW COMPLETION TIME STATISTICS")
    print("="*80)

    print(f"\n{'TCP Variant':<15} {'Mean':<12} {'Median':<12} {'P99':<12} {'Min':<12} {'Max':<12} {'Count':<8}")
    print("-"*80)

    for variant, stat in stats.items():
        print(f"{variant:<15} {stat['mean']:<12.6f} {stat['median']:<12.6f} "
              f"{stat['p99']:<12.6f} {stat['min']:<12.6f} {stat['max']:<12.6f} "
              f"{stat['count']:<8}")

    print("="*80)

def generate_latex_table(stats, output_file='plots/fct_stats_table.tex'):
    """Generate LaTeX table for report"""
    with open(output_file, 'w') as f:
        f.write("\\begin{table}[h]\n")
        f.write("\\centering\n")
        f.write("\\begin{tabular}{|l|c|c|c|c|c|}\n")
        f.write("\\hline\n")
        f.write("TCP Variant & Mean FCT (s) & Median FCT (s) & P99 FCT (s) & Min FCT (s) & Max FCT (s) \\\\\n")
        f.write("\\hline\n")

        for variant, stat in stats.items():
            f.write(f"{variant} & {stat['mean']:.6f} & {stat['median']:.6f} & "
                   f"{stat['p99']:.6f} & {stat['min']:.6f} & {stat['max']:.6f} \\\\\n")

        f.write("\\hline\n")
        f.write("\\end{tabular}\n")
        f.write("\\caption{Flow Completion Time Statistics for Different TCP Variants}\n")
        f.write("\\label{tab:fct_stats}\n")
        f.write("\\end{table}\n")

    print(f"Saved: {output_file}")

def compare_improvements(stats):
    """Compare TcpMlCong with baseline algorithms"""
    if 'TcpMlCong' not in stats:
        print("\nWarning: TcpMlCong results not found!")
        return

    print("\n" + "="*80)
    print("PERFORMANCE COMPARISON (TcpMlCong vs Baselines)")
    print("="*80)

    ml_mean = stats['TcpMlCong']['mean']
    ml_p99 = stats['TcpMlCong']['p99']

    for variant in ['TcpNewReno', 'TcpCubic']:
        if variant in stats:
            baseline_mean = stats[variant]['mean']
            baseline_p99 = stats[variant]['p99']

            mean_improvement = ((baseline_mean - ml_mean) / baseline_mean) * 100
            p99_improvement = ((baseline_p99 - ml_p99) / baseline_p99) * 100

            print(f"\nTcpMlCong vs {variant}:")
            print(f"  Mean FCT improvement: {mean_improvement:+.2f}%")
            print(f"  P99 FCT improvement: {p99_improvement:+.2f}%")

    print("="*80)

def main():
    # Load results
    print("Loading results from flow_completion_times.csv...")
    df = load_results()

    if df is None:
        print("Error: Could not load results!")
        return 1

    print(f"Loaded {len(df)} flow records")
    print(f"TCP variants: {df['TcpVariant'].unique()}")

    # Calculate statistics
    stats = calculate_statistics(df)

    # Print statistics
    print_statistics_table(stats)

    # Compare improvements
    compare_improvements(stats)

    # Generate plots
    print("\nGenerating plots...")
    plot_fct_comparison(df)

    # Generate LaTeX table
    print("\nGenerating LaTeX table...")
    generate_latex_table(stats)

    print("\n✓ Analysis complete!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
