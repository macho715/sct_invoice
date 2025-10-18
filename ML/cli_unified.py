#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unified ML Pipeline CLI Interface
TDD Implementation: CLI for integrated ML systems

Usage:
    python cli_unified.py train --data DSV_SHPT_ALL.xlsx --weights-training-data training_data.json
    python cli_unified.py predict --data new_invoice.xlsx --use-ml-weights
    python cli_unified.py ab-test --data test_data.xlsx
"""

import argparse
import pandas as pd
import json
from pathlib import Path
from unified_ml_pipeline import UnifiedMLPipeline


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Unified ML Pipeline - Integrated CostGuard and Weight Optimizer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Train both systems
  python cli_unified.py train --data DSV_SHPT_ALL.xlsx --weights-training-data training_data.json

  # Predict with ML weights
  python cli_unified.py predict --data new_invoice.xlsx --use-ml-weights

  # A/B test performance
  python cli_unified.py ab-test --data test_data.xlsx

  # Retrain models
  python cli_unified.py retrain --data DSV_SHPT_ALL.xlsx --weights-training-data training_data.json
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
        default="logi_costguard_ml_v2/config/schema.json",
        help="Configuration file path",
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
        default="logi_costguard_ml_v2/config/schema.json",
        help="Configuration file path",
    )
    predict_parser.add_argument(
        "--models-dir", default="output/models", help="Models directory"
    )
    predict_parser.add_argument(
        "--output",
        default="output/prediction_results.xlsx",
        help="Output file for results",
    )
    predict_parser.add_argument(
        "--use-ml-weights", action="store_true", help="Use ML-optimized weights"
    )

    # A/B test command
    ab_test_parser = subparsers.add_parser(
        "ab-test", help="Run A/B test comparing default vs ML weights"
    )
    ab_test_parser.add_argument("--data", required=True, help="Test data file")
    ab_test_parser.add_argument(
        "--approved-lanes", required=True, help="Approved lanes file"
    )
    ab_test_parser.add_argument(
        "--config",
        default="logi_costguard_ml_v2/config/schema.json",
        help="Configuration file path",
    )
    ab_test_parser.add_argument(
        "--output",
        default="output/ab_test_results.json",
        help="Output file for A/B test results",
    )

    # Retrain command
    retrain_parser = subparsers.add_parser(
        "retrain", help="Retrain models with new data"
    )
    retrain_parser.add_argument("--data", required=True, help="New invoice data file")
    retrain_parser.add_argument(
        "--weights-training-data", required=True, help="New matching training data file"
    )
    retrain_parser.add_argument(
        "--config",
        default="logi_costguard_ml_v2/config/schema.json",
        help="Configuration file path",
    )
    retrain_parser.add_argument(
        "--output-dir", default="output", help="Output directory for models and metrics"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    try:
        if args.command == "train":
            run_train_command(args)
        elif args.command == "predict":
            run_predict_command(args)
        elif args.command == "ab-test":
            run_ab_test_command(args)
        elif args.command == "retrain":
            run_retrain_command(args)
        else:
            print(f"Unknown command: {args.command}")
            parser.print_help()

    except Exception as e:
        print(f"[ERROR] Error: {e}")
        return 1

    return 0


def run_train_command(args):
    """Run training command"""
    print("[START] Starting Unified ML Pipeline Training...")

    # Load data
    print(f"[DATA] Loading invoice data from {args.data}")
    invoice_data = load_data_file(args.data)

    print(f"[DATA] Loading matching training data from {args.weights_training_data}")
    matching_data = load_data_file(args.weights_training_data)

    # Initialize pipeline
    print(f"[INIT] Initializing pipeline with config: {args.config}")
    pipeline = UnifiedMLPipeline(args.config)

    # Train
    print("[TRAIN] Training CostGuard and Weight Optimizer models...")
    result = pipeline.train_all(invoice_data, matching_data, args.output_dir)

    # Print results
    print("\n[SUCCESS] Training completed!")
    print(f"[RESULT] CostGuard MAPE: {result.get('costguard_mape', 'N/A'):.3f}")
    print(
        f"[RESULT] Weight Optimizer Accuracy: {result.get('weight_optimizer_accuracy', 'N/A'):.3f}"
    )

    if result.get("fallback_to_default"):
        print(
            "[WARNING] Some models fell back to default weights due to insufficient data"
        )

    print(f"[SAVE] Models saved to: {args.output_dir}/models/")
    print(f"[SAVE] Metrics saved to: {args.output_dir}/out/metrics.json")


def run_predict_command(args):
    """Run prediction command"""
    print("[START] Starting Unified ML Pipeline Prediction...")

    # Load data
    print(f"[DATA] Loading invoice data from {args.data}")
    invoice_data = load_data_file(args.data)

    print(f"[DATA] Loading approved lanes from {args.approved_lanes}")
    approved_lanes = load_approved_lanes(args.approved_lanes)

    # Initialize pipeline
    print(f"[INIT] Initializing pipeline with config: {args.config}")
    pipeline = UnifiedMLPipeline(args.config)

    # Load ML weights if requested
    if args.use_ml_weights:
        weight_model_path = f"{args.models_dir}/optimized_weights.pkl"
        if Path(weight_model_path).exists():
            pipeline.weights_manager.load_weights(weight_model_path)
            print("[SUCCESS] ML-optimized weights loaded")
        else:
            print("[WARNING] ML weights not found, using default weights")

    # Predict
    print("[PREDICT] Running prediction pipeline...")
    results = pipeline.predict_all(invoice_data, approved_lanes, args.models_dir)

    # Save results
    print(f"[SAVE] Saving results to {args.output}")
    save_prediction_results(results, args.output)

    # Print summary
    print("\n[SUCCESS] Prediction completed!")
    total_items = len(results)
    matched_items = sum(1 for r in results if r.get("match_result") is not None)

    print(f"[STATS] Total items: {total_items}")
    print(
        f"[STATS] Matched items: {matched_items} ({matched_items/total_items*100:.1f}%)"
    )
    print(f"[STATS] No match items: {total_items - matched_items}")

    # Band distribution
    bands = {}
    for r in results:
        band = r.get("band", "NA")
        bands[band] = bands.get(band, 0) + 1

    print("\n[STATS] Band Distribution:")
    for band, count in bands.items():
        print(f"  {band}: {count} ({count/total_items*100:.1f}%)")


def run_ab_test_command(args):
    """Run A/B test command"""
    print("[START] Starting A/B Test...")

    # Load data
    print(f"[DATA] Loading test data from {args.data}")
    test_data = load_data_file(args.data)

    print(f"[DATA] Loading approved lanes from {args.approved_lanes}")
    approved_lanes = load_approved_lanes(args.approved_lanes)

    # Initialize pipeline
    print(f"[INIT] Initializing pipeline with config: {args.config}")
    pipeline = UnifiedMLPipeline(args.config)

    # Define weights
    default_weights = {"token_set": 0.4, "levenshtein": 0.3, "fuzzy_sort": 0.3}
    ml_weights = {"token_set": 0.45, "levenshtein": 0.25, "fuzzy_sort": 0.30}

    # Run A/B test
    print("[TEST] Running A/B test comparison...")
    ab_result = pipeline.run_ab_test(
        test_data, approved_lanes, default_weights, ml_weights, "output"
    )

    # Save results
    print(f"[SAVE] Saving A/B test results to {args.output}")
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(ab_result, f, ensure_ascii=False, indent=2)

    # Print results
    print("\n[SUCCESS] A/B Test completed!")
    print("\n[STATS] Performance Comparison:")
    print("Metric          Default      ML Optimized  Improvement")
    print("-------------------------------------------------------")

    for metric in ["accuracy", "precision", "recall", "f1"]:
        default_val = ab_result["default"][metric]
        optimized_val = ab_result["optimized"][metric]
        improvement = ab_result["improvement"][metric]

        print(
            f"{metric.capitalize():12} {default_val:8.3f}    {optimized_val:8.3f}    {improvement:+6.1%}"
        )


def run_retrain_command(args):
    """Run retrain command"""
    print("[START] Starting Model Retraining...")

    # Load data
    print(f"[DATA] Loading new invoice data from {args.data}")
    invoice_data = load_data_file(args.data)

    print(
        f"[DATA] Loading new matching training data from {args.weights_training_data}"
    )
    matching_data = load_data_file(args.weights_training_data)

    # Initialize pipeline
    print(f"[INIT] Initializing pipeline with config: {args.config}")
    pipeline = UnifiedMLPipeline(args.config)

    # Retrain
    print("[RETRAIN] Retraining models with new data...")
    result = pipeline.train_all(
        invoice_data, matching_data, args.output_dir, retrain=True
    )

    # Print results
    print("\n[SUCCESS] Retraining completed!")
    print(f"[RESULT] CostGuard MAPE: {result.get('costguard_mape', 'N/A'):.3f}")
    print(
        f"[RESULT] Weight Optimizer Accuracy: {result.get('weight_optimizer_accuracy', 'N/A'):.3f}"
    )

    print(f"[SAVE] Updated models saved to: {args.output_dir}/models/")
    print(f"[SAVE] Updated metrics saved to: {args.output_dir}/out/metrics.json")


def load_data_file(file_path: str) -> pd.DataFrame:
    """Load data from various file formats"""
    file_path = Path(file_path)

    if file_path.suffix.lower() == ".xlsx":
        return pd.read_excel(file_path)
    elif file_path.suffix.lower() == ".csv":
        return pd.read_csv(file_path)
    elif file_path.suffix.lower() == ".json":
        return pd.read_json(file_path)
    else:
        raise ValueError(f"Unsupported file format: {file_path.suffix}")


def load_approved_lanes(file_path: str) -> list:
    """Load approved lanes from file"""
    file_path = Path(file_path)

    if file_path.suffix.lower() == ".csv":
        df = pd.read_csv(file_path)
        return df.to_dict("records")
    elif file_path.suffix.lower() == ".json":
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        raise ValueError(
            f"Unsupported file format for approved lanes: {file_path.suffix}"
        )


def save_prediction_results(results: list, output_path: str):
    """Save prediction results to Excel file"""
    output_path = Path(output_path)

    # Convert results to DataFrame
    df_results = pd.DataFrame(results)

    # Extract nested data
    if "match_result" in df_results.columns:
        match_data = []
        for idx, row in df_results.iterrows():
            if row["match_result"]:
                match_data.append(
                    {
                        "item_index": row["item_index"],
                        "match_score": row["match_result"].get("match_score", 0),
                        "match_level": row["match_result"].get("match_level", ""),
                        "band": row.get("band", ""),
                        "anomaly_score": row.get("anomaly_score", 0),
                    }
                )
            else:
                match_data.append(
                    {
                        "item_index": row["item_index"],
                        "match_score": 0,
                        "match_level": "NO_MATCH",
                        "band": row.get("band", ""),
                        "anomaly_score": row.get("anomaly_score", 0),
                    }
                )

        df_final = pd.DataFrame(match_data)
    else:
        df_final = df_results

    # Save to Excel
    if output_path.suffix.lower() == ".xlsx":
        df_final.to_excel(output_path, index=False)
    elif output_path.suffix.lower() == ".csv":
        df_final.to_csv(output_path, index=False)
    else:
        raise ValueError(f"Unsupported output format: {output_path.suffix}")


if __name__ == "__main__":
    exit(main())
