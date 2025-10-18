#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced ML Pipeline CLI Interface
CLI for Enhanced Unified ML Pipeline with improved performance and error handling

Usage:
    python cli_enhanced.py train --data DSV_SHPT_ALL.xlsx --weights-training-data training_data.json
    python cli_enhanced.py predict --data new_invoice.xlsx --use-ml-weights
    python cli_enhanced.py ab-test --data test_data.xlsx
"""

import argparse
import pandas as pd
import json
from pathlib import Path
from enhanced_unified_ml_pipeline import EnhancedUnifiedMLPipeline
from config_manager import reset_config


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Enhanced ML Pipeline - Improved CostGuard and Weight Optimizer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Train both systems
  python cli_enhanced.py train --data DSV_SHPT_ALL.xlsx --weights-training-data training_data.json

  # Predict with ML weights
  python cli_enhanced.py predict --data new_invoice.xlsx --approved-lanes lanes.json --use-ml-weights

  # A/B test performance
  python cli_enhanced.py ab-test --data test_data.xlsx --approved-lanes lanes.json

  # Retrain models
  python cli_enhanced.py retrain --data DSV_SHPT_ALL.xlsx --weights-training-data training_data.json
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Train command
    train_parser = subparsers.add_parser(
        "train", help="Train both CostGuard and Weight Optimizer models"
    )
    train_parser.add_argument(
        "--data", required=True, help="Invoice data file (Excel/CSV)"
    )
    train_parser.add_argument(
        "--weights-training-data",
        required=True,
        help="Matching training data file (JSON/CSV)",
    )
    train_parser.add_argument(
        "--config",
        default=None,
        help="Configuration file path (optional)",
    )
    train_parser.add_argument(
        "--output-dir", default="output", help="Output directory for models and metrics"
    )

    # Predict command
    predict_parser = subparsers.add_parser("predict", help="Run prediction pipeline")
    predict_parser.add_argument(
        "--data", required=True, help="Invoice data file to predict"
    )
    predict_parser.add_argument(
        "--approved-lanes", required=True, help="Approved lanes file (CSV/JSON)"
    )
    predict_parser.add_argument(
        "--config",
        default=None,
        help="Configuration file path (optional)",
    )
    predict_parser.add_argument(
        "--models-dir", default="output/models", help="Models directory"
    )
    predict_parser.add_argument(
        "--use-ml-weights", action="store_true", help="Use ML-optimized weights"
    )
    predict_parser.add_argument(
        "--output-dir", default="output", help="Output directory for results"
    )

    # A/B Test command
    abtest_parser = subparsers.add_parser(
        "ab-test", help="Run A/B test comparing default vs ML weights"
    )
    abtest_parser.add_argument("--data", required=True, help="Test data file")
    abtest_parser.add_argument(
        "--approved-lanes", required=True, help="Approved lanes file (CSV/JSON)"
    )
    abtest_parser.add_argument(
        "--config",
        default=None,
        help="Configuration file path (optional)",
    )
    abtest_parser.add_argument(
        "--models-dir", default="output/models", help="Models directory"
    )
    abtest_parser.add_argument(
        "--output-dir", default="output", help="Output directory for results"
    )

    # Retrain command
    retrain_parser = subparsers.add_parser(
        "retrain", help="Retrain models with new data"
    )
    retrain_parser.add_argument(
        "--data", required=True, help="Invoice data file (Excel/CSV)"
    )
    retrain_parser.add_argument(
        "--weights-training-data",
        required=True,
        help="Matching training data file (JSON/CSV)",
    )
    retrain_parser.add_argument(
        "--config",
        default=None,
        help="Configuration file path (optional)",
    )
    retrain_parser.add_argument(
        "--output-dir", default="output", help="Output directory for models and metrics"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    try:
        # Initialize Enhanced Pipeline
        print("=" * 60)
        print("Enhanced ML Pipeline CLI")
        print("=" * 60)

        pipeline = EnhancedUnifiedMLPipeline(config_path=args.config)
        print("OK Enhanced ML Pipeline initialized successfully")

        # Set output directory
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        if args.command == "train":
            return train_command(pipeline, args, output_dir)
        elif args.command == "predict":
            return predict_command(pipeline, args, output_dir)
        elif args.command == "ab-test":
            return abtest_command(pipeline, args, output_dir)
        elif args.command == "retrain":
            return retrain_command(pipeline, args, output_dir)
        else:
            print(f"Unknown command: {args.command}")
            return 1

    except Exception as e:
        print(f"FAIL Error: {e}")
        import traceback

        traceback.print_exc()
        return 1
    finally:
        # Reset configuration for clean state
        reset_config()


def train_command(pipeline, args, output_dir):
    """Train both CostGuard and Weight Optimizer models"""
    print("\nStarting Enhanced ML Training...")

    # Load training data
    print(f"Loading training data: {args.data}")
    if args.data.endswith((".xlsx", ".xlsm")):
        # Try to read MasterData sheet first
        try:
            invoice_data = pd.read_excel(args.data, sheet_name="MasterData")
        except:
            # Fallback to first sheet
            invoice_data = pd.read_excel(args.data, sheet_name=0)
    else:
        invoice_data = pd.read_csv(args.data, encoding="utf-8")

    print(f"OK Invoice data loaded: {len(invoice_data)} rows")

    # Load weights training data
    print(f"Loading weights training data: {args.weights_training_data}")
    if args.weights_training_data.endswith(".json"):
        with open(args.weights_training_data, "r", encoding="utf-8") as f:
            weights_data = pd.DataFrame(json.load(f))
    else:
        weights_data = pd.read_csv(args.weights_training_data)

    print(f"OK Weights training data loaded: {len(weights_data)} samples")

    # Train models
    print("\nTraining models...")
    results = pipeline.train_all(invoice_data, weights_data, retrain=False)

    # Save results
    models_dir = output_dir / "models"
    models_dir.mkdir(parents=True, exist_ok=True)

    print(f"\nSaving models to: {models_dir}")

    # Save training results
    results_file = output_dir / "training_results.json"
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"OK Training completed successfully!")
    print(f"Results saved to: {results_file}")

    return 0


def predict_command(pipeline, args, output_dir):
    """Run prediction pipeline"""
    print("\nStarting Enhanced ML Prediction...")

    # Load test data
    print(f"Loading test data: {args.data}")
    if args.data.endswith((".xlsx", ".xlsm")):
        try:
            test_data = pd.read_excel(args.data, sheet_name="MasterData")
        except:
            test_data = pd.read_excel(args.data, sheet_name=0)
    else:
        test_data = pd.read_csv(args.data, encoding="utf-8")

    print(f"OK Test data loaded: {len(test_data)} rows")

    # Load approved lanes
    print(f"Loading approved lanes: {args.approved_lanes}")
    if args.approved_lanes.endswith(".json"):
        with open(args.approved_lanes, "r", encoding="utf-8") as f:
            approved_lanes = json.load(f)
    else:
        approved_lanes = pd.read_csv(args.approved_lanes).to_dict("records")

    print(f"OK Approved lanes loaded: {len(approved_lanes)} lanes")

    # Run prediction
    print(f"\nRunning prediction (ML weights: {args.use_ml_weights})...")
    results = pipeline.predict_all(
        test_data, approved_lanes, use_ml_weights=args.use_ml_weights
    )

    # Save results
    predictions_dir = output_dir / "predictions"
    predictions_dir.mkdir(parents=True, exist_ok=True)

    # Convert results to DataFrame
    results_df = pd.DataFrame(results)

    # Save as CSV
    results_file = (
        predictions_dir
        / f"predictions_{'ml' if args.use_ml_weights else 'default'}.csv"
    )
    results_df.to_csv(results_file, index=False, encoding="utf-8")

    # Save as JSON
    results_json = (
        predictions_dir
        / f"predictions_{'ml' if args.use_ml_weights else 'default'}.json"
    )
    with open(results_json, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"OK Prediction completed successfully!")
    print(f"Results saved to: {results_file}")
    print(f"Processed {len(results)} items")

    return 0


def abtest_command(pipeline, args, output_dir):
    """Run A/B test comparing default vs ML weights"""
    print("\nStarting Enhanced ML A/B Test...")

    # Load test data
    print(f"Loading test data: {args.data}")
    if args.data.endswith((".xlsx", ".xlsm")):
        try:
            test_data = pd.read_excel(args.data, sheet_name="MasterData")
        except:
            test_data = pd.read_excel(args.data, sheet_name=0)
    else:
        test_data = pd.read_csv(args.data, encoding="utf-8")

    print(f"OK Test data loaded: {len(test_data)} rows")

    # Load approved lanes
    print(f"Loading approved lanes: {args.approved_lanes}")
    if args.approved_lanes.endswith(".json"):
        with open(args.approved_lanes, "r", encoding="utf-8") as f:
            approved_lanes = json.load(f)
    else:
        approved_lanes = pd.read_csv(args.approved_lanes).to_dict("records")

    print(f"OK Approved lanes loaded: {len(approved_lanes)} lanes")

    # Run A/B test
    print(f"\nRunning A/B test...")
    ab_results = pipeline.run_ab_test(test_data, approved_lanes)

    # Save results
    abtest_dir = output_dir / "ab_test"
    abtest_dir.mkdir(parents=True, exist_ok=True)

    # Save A/B test results
    abtest_file = abtest_dir / "ab_test_results.json"
    with open(abtest_file, "w", encoding="utf-8") as f:
        json.dump(ab_results, f, indent=2, ensure_ascii=False)

    # Generate report
    report_file = abtest_dir / "ab_test_report.txt"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write("Enhanced ML Pipeline A/B Test Report\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Test Data: {args.data}\n")
        f.write(f"Test Items: {len(test_data)}\n")
        f.write(f"Approved Lanes: {len(approved_lanes)}\n\n")

        f.write("Performance Comparison:\n")
        f.write("-" * 30 + "\n")
        for metric, values in ab_results.get("metrics", {}).items():
            f.write(f"{metric}:\n")
            f.write(f"  Default: {values.get('default', 'N/A'):.3f}\n")
            f.write(f"  ML Optimized: {values.get('ml_optimized', 'N/A'):.3f}\n")
            f.write(f"  Improvement: {values.get('improvement', 'N/A'):.1f}%\n\n")

        f.write("Recommendation:\n")
        f.write("-" * 15 + "\n")
        f.write(f"{ab_results.get('recommendation', 'No recommendation available')}\n")

    print(f"OK A/B test completed successfully!")
    print(f"Results saved to: {abtest_file}")
    print(f"Report saved to: {report_file}")

    # Print summary
    print(f"\nA/B Test Summary:")
    for metric, values in ab_results.get("metrics", {}).items():
        print(
            f"  {metric}: Default {values.get('default', 0):.3f} → ML {values.get('ml_optimized', 0):.3f} ({values.get('improvement', 0):.1f}% improvement)"
        )

    return 0


def retrain_command(pipeline, args, output_dir):
    """Retrain models with new data"""
    print("\nStarting Enhanced ML Retraining...")

    # Load training data
    print(f"Loading training data: {args.data}")
    if args.data.endswith((".xlsx", ".xlsm")):
        try:
            invoice_data = pd.read_excel(args.data, sheet_name="MasterData")
        except:
            invoice_data = pd.read_excel(args.data, sheet_name=0)
    else:
        invoice_data = pd.read_csv(args.data, encoding="utf-8")

    print(f"OK Invoice data loaded: {len(invoice_data)} rows")

    # Load weights training data
    print(f"Loading weights training data: {args.weights_training_data}")
    if args.weights_training_data.endswith(".json"):
        with open(args.weights_training_data, "r", encoding="utf-8") as f:
            weights_data = pd.DataFrame(json.load(f))
    else:
        weights_data = pd.read_csv(args.weights_training_data)

    print(f"OK Weights training data loaded: {len(weights_data)} samples")

    # Retrain models
    print("\nRetraining models...")
    results = pipeline.train_all(invoice_data, weights_data, retrain=True)

    # Save results
    models_dir = output_dir / "models"
    models_dir.mkdir(parents=True, exist_ok=True)

    print(f"\nSaving retrained models to: {models_dir}")

    # Save training results
    results_file = output_dir / "retraining_results.json"
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"OK Retraining completed successfully!")
    print(f"Results saved to: {results_file}")

    return 0


if __name__ == "__main__":
    exit(main())
