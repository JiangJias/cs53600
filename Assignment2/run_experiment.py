#!/usr/bin/env python3
"""
Main automation script for Assignment 2
Runs the complete experiment pipeline:
1. Collect data from iPerf servers
2. Generate visualizations
3. Train ML model
4. Generate reports
"""

import argparse
import logging
import sys
from pathlib import Path

from data_collector import DataCollector, load_server_list, select_random_servers
from visualization import Visualizer, generate_summary_table_latex
from ml_model import run_ml_pipeline


def setup_logging(log_file: str = "experiment.log"):
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )


def main():
    parser = argparse.ArgumentParser(
        description='Run iPerf experiment and ML analysis',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with default settings (10 servers, 60 second tests)
  python run_experiment.py servers.txt

  # Run with custom settings
  python run_experiment.py servers.txt --n-servers 5 --duration 30

  # Skip data collection and only run analysis
  python run_experiment.py servers.txt --skip-collection

  # Use custom parameters for ML objective
  python run_experiment.py servers.txt --alpha 2.0 --beta 1.5
        """
    )

    parser.add_argument('server_file', type=str,
                       help='File containing list of iPerf servers')
    parser.add_argument('--n-servers', type=int, default=10,
                       help='Number of random servers to test (default: 10)')
    parser.add_argument('--duration', type=int, default=60,
                       help='Test duration in seconds (default: 60)')
    parser.add_argument('--sampling-interval', type=float, default=0.2,
                       help='Sampling interval in seconds (default: 0.2)')
    parser.add_argument('--output-dir', type=str, default='results',
                       help='Output directory for results (default: results)')
    parser.add_argument('--plots-dir', type=str, default='plots',
                       help='Output directory for plots (default: plots)')
    parser.add_argument('--models-dir', type=str, default='models',
                       help='Output directory for models (default: models)')
    parser.add_argument('--skip-collection', action='store_true',
                       help='Skip data collection, use existing results')
    parser.add_argument('--skip-visualization', action='store_true',
                       help='Skip visualization generation')
    parser.add_argument('--skip-ml', action='store_true',
                       help='Skip ML model training')
    parser.add_argument('--alpha', type=float, default=1.0,
                       help='Alpha parameter for ML objective (RTT weight, default: 1.0)')
    parser.add_argument('--beta', type=float, default=1.0,
                       help='Beta parameter for ML objective (loss weight, default: 1.0)')
    parser.add_argument('--log-file', type=str, default='experiment.log',
                       help='Log file path (default: experiment.log)')

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.log_file)
    logger = logging.getLogger("MainExperiment")

    logger.info("=" * 80)
    logger.info("Starting Assignment 2 Experiment Pipeline")
    logger.info("=" * 80)

    # Create output directories
    Path(args.output_dir).mkdir(exist_ok=True, parents=True)
    Path(args.plots_dir).mkdir(exist_ok=True, parents=True)
    Path(args.models_dir).mkdir(exist_ok=True, parents=True)

    # Step 1: Data Collection
    if not args.skip_collection:
        logger.info("\n" + "=" * 80)
        logger.info("STEP 1: Data Collection")
        logger.info("=" * 80)

        # Load server list
        logger.info(f"Loading servers from {args.server_file}")
        all_servers = load_server_list(args.server_file)
        logger.info(f"Loaded {len(all_servers)} servers")

        # Select random servers
        selected_servers = select_random_servers(all_servers, args.n_servers)
        logger.info(f"Selected {len(selected_servers)} servers for testing")

        # Collect data
        collector = DataCollector(output_dir=args.output_dir)
        results = collector.collect_from_servers(
            selected_servers,
            duration=args.duration,
            sampling_interval=args.sampling_interval
        )

        logger.info(f"Successfully collected data from {len(results)} servers")

        # Save results
        collector.save_results_json()
        collector.save_all_tcp_stats()
        collector.save_summary_csv()

        # Print summary
        summary = collector.get_summary_statistics()
        logger.info("\nThroughput Summary:")
        for s in summary:
            logger.info(f"  {s['server']}: avg={s['avg_mbps']:.2f} Mbps, "
                       f"median={s['median_mbps']:.2f} Mbps, "
                       f"p95={s['p95_mbps']:.2f} Mbps")
    else:
        logger.info("Skipping data collection (using existing results)")

    # Step 2: Visualization
    if not args.skip_visualization:
        logger.info("\n" + "=" * 80)
        logger.info("STEP 2: Visualization")
        logger.info("=" * 80)

        visualizer = Visualizer(
            results_dir=args.output_dir,
            plots_dir=args.plots_dir
        )
        visualizer.plot_all_visualizations()
        generate_summary_table_latex(
            results_dir=args.output_dir,
            output_dir=args.plots_dir
        )

        logger.info("All visualizations generated successfully")
    else:
        logger.info("Skipping visualization")

    # Step 3: ML Model Training
    if not args.skip_ml:
        logger.info("\n" + "=" * 80)
        logger.info("STEP 3: ML Model Training and Analysis")
        logger.info("=" * 80)

        logger.info(f"Training with alpha={args.alpha}, beta={args.beta}")

        predictor, metrics = run_ml_pipeline(
            results_dir=args.output_dir,
            models_dir=args.models_dir,
            plots_dir=args.plots_dir,
            alpha=args.alpha,
            beta=args.beta
        )

        logger.info("\nModel Evaluation Metrics:")
        logger.info(f"  RMSE: {metrics['rmse']:.4f}")
        logger.info(f"  MAE: {metrics['mae']:.4f}")
        logger.info(f"  R²: {metrics['r2']:.4f}")
        logger.info(f"  Test samples: {metrics['samples']}")
    else:
        logger.info("Skipping ML model training")

    # Final summary
    logger.info("\n" + "=" * 80)
    logger.info("EXPERIMENT COMPLETED SUCCESSFULLY")
    logger.info("=" * 80)
    logger.info(f"Results saved to: {args.output_dir}")
    logger.info(f"Plots saved to: {args.plots_dir}")
    logger.info(f"Models saved to: {args.models_dir}")
    logger.info(f"Log saved to: {args.log_file}")

    print("\n" + "=" * 80)
    print("EXPERIMENT COMPLETED SUCCESSFULLY")
    print("=" * 80)
    print(f"\nOutput locations:")
    print(f"  Results: {args.output_dir}/")
    print(f"  Plots: {args.plots_dir}/")
    print(f"  Models: {args.models_dir}/")
    print(f"  Log: {args.log_file}")
    print("\nKey files:")
    print(f"  - {args.output_dir}/iperf_results.json")
    print(f"  - {args.output_dir}/summary_statistics.csv")
    print(f"  - {args.plots_dir}/throughput_all.pdf")
    print(f"  - {args.plots_dir}/representative_*.pdf")
    print(f"  - {args.plots_dir}/congestion_algorithm.txt")
    print(f"  - {args.models_dir}/cwnd_model.pkl")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nExperiment interrupted by user")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Fatal error: {e}", exc_info=True)
        print(f"\nError: {e}")
        sys.exit(1)
