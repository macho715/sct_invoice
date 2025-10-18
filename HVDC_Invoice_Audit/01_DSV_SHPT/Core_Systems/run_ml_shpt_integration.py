#!/usr/bin/env python3
"""
ML-SHPT Integration Script (독립 실행 방식)
의존성 충돌 없이 ML 결과와 SHPT 결과를 통합

Version: 1.0.0
Created: 2025-10-16
Author: MACHO-GPT Enhanced ML Integration
"""

import sys
import time
import subprocess
from pathlib import Path
from datetime import datetime
import pandas as pd
import json


def run_ml_prediction():
    """Run ML prediction independently"""
    print("\n" + "=" * 80)
    print("PHASE 1: ML Prediction (Enhanced System)")
    print("=" * 80)

    ml_dir = Path(__file__).parent.parent.parent.parent / "ML"
    data_file = (
        Path(__file__).parent.parent
        / "Data"
        / "DSV 202509"
        / "SCNT SHIPMENT DRAFT INVOICE (SEPT 2025)_FINAL.xlsm"
    )
    lanes_file = (
        ml_dir
        / "logi_costguard_ml_v2"
        / "ref"
        / "inland_trucking_reference_rates_clean (2).json"
    )

    if not data_file.exists():
        print(f"FAIL Data file not found: {data_file}")
        return None

    if not lanes_file.exists():
        print(f"FAIL Approved lanes file not found: {lanes_file}")
        return None

    # Run ML prediction using subprocess to avoid import conflicts
    cmd = [
        sys.executable,
        str(ml_dir / "cli_enhanced.py"),
        "predict",
        "--data",
        str(data_file),
        "--approved-lanes",
        str(lanes_file),
        "--use-ml-weights",
        "--output-dir",
        str(ml_dir / "output" / "sept_2025_integration"),
    ]

    print(f"Executing: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd, cwd=str(ml_dir), capture_output=True, text=True, timeout=300
        )

        if result.returncode == 0:
            print("OK ML prediction completed successfully")
            print(result.stdout)
            return ml_dir / "output" / "sept_2025_integration"
        else:
            print(f"FAIL ML prediction failed with code {result.returncode}")
            print(result.stderr)
            return None

    except subprocess.TimeoutExpired:
        print("FAIL ML prediction timed out after 5 minutes")
        return None
    except Exception as e:
        print(f"FAIL ML prediction error: {e}")
        return None


def run_shpt_audit():
    """Run SHPT audit independently"""
    print("\n" + "=" * 80)
    print("PHASE 2: SHPT Audit Validation")
    print("=" * 80)

    shpt_dir = Path(__file__).parent

    # Run SHPT audit using subprocess
    cmd = [sys.executable, str(shpt_dir / "run_audit.py")]

    print(f"Executing: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd, cwd=str(shpt_dir), capture_output=True, text=True, timeout=600
        )

        if result.returncode == 0:
            print("OK SHPT audit completed successfully")
            print(result.stdout)
            return Path(__file__).parent.parent / "Results" / "Sept_2025"
        else:
            print(f"FAIL SHPT audit failed with code {result.returncode}")
            print(result.stderr)
            return None

    except subprocess.TimeoutExpired:
        print("FAIL SHPT audit timed out after 10 minutes")
        return None
    except Exception as e:
        print(f"FAIL SHPT audit error: {e}")
        return None


def integrate_results(ml_output_dir, shpt_output_dir):
    """Integrate ML and SHPT results"""
    print("\n" + "=" * 80)
    print("PHASE 3: Results Integration")
    print("=" * 80)

    output_dir = Path(__file__).parent.parent / "Results" / "Sept_2025_ML_Enhanced"
    output_dir.mkdir(parents=True, exist_ok=True)

    integrated_results = {
        "timestamp": datetime.now().isoformat(),
        "integration_type": "independent_execution",
        "ml_results": {},
        "shpt_results": {},
        "combined_summary": {},
    }

    # Load ML prediction results
    if ml_output_dir and ml_output_dir.exists():
        try:
            # Try different possible paths
            ml_predictions_file = ml_output_dir / "predictions" / "predictions_ml.csv"
            if not ml_predictions_file.exists():
                ml_predictions_file = ml_output_dir / "predictions_ml.csv"

            if ml_predictions_file.exists():
                ml_df = pd.read_csv(ml_predictions_file, encoding="utf-8")
                integrated_results["ml_results"] = {
                    "status": "success",
                    "file": str(ml_predictions_file),
                    "total_predictions": len(ml_df),
                    "columns": list(ml_df.columns),
                }
                print(f"OK ML results loaded: {len(ml_df)} predictions")

                # Copy ML results to integration directory
                ml_df.to_csv(
                    output_dir
                    / f"ml_predictions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    index=False,
                    encoding="utf-8",
                )
            else:
                integrated_results["ml_results"] = {
                    "status": "not_found",
                    "file": str(ml_predictions_file),
                }
                print(f"WARN ML predictions file not found: {ml_predictions_file}")
        except Exception as e:
            integrated_results["ml_results"] = {"status": "error", "error": str(e)}
            print(f"FAIL Failed to load ML results: {e}")
    else:
        integrated_results["ml_results"] = {"status": "skipped"}
        print("WARN ML results directory not found")

    # Load SHPT audit results
    if shpt_output_dir and shpt_output_dir.exists():
        try:
            # Find latest result file
            result_files = list(shpt_output_dir.glob("*_results_*.json"))
            if result_files:
                latest_result = max(result_files, key=lambda p: p.stat().st_mtime)
                with open(latest_result, "r", encoding="utf-8") as f:
                    shpt_data = json.load(f)

                integrated_results["shpt_results"] = {
                    "status": "success",
                    "file": str(latest_result),
                    "summary": shpt_data.get("summary", {}),
                }
                print(f"OK SHPT results loaded from: {latest_result.name}")
            else:
                integrated_results["shpt_results"] = {"status": "not_found"}
                print("WARN SHPT result files not found")
        except Exception as e:
            integrated_results["shpt_results"] = {"status": "error", "error": str(e)}
            print(f"FAIL Failed to load SHPT results: {e}")
    else:
        integrated_results["shpt_results"] = {"status": "skipped"}
        print("WARN SHPT results directory not found")

    # Create combined summary
    integrated_results["combined_summary"] = {
        "ml_available": integrated_results["ml_results"].get("status") == "success",
        "shpt_available": integrated_results["shpt_results"].get("status") == "success",
        "integration_method": "independent_subprocess_execution",
        "note": "Results generated independently to avoid module conflicts",
    }

    # Save integrated results
    results_file = (
        output_dir
        / f"integrated_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(integrated_results, f, indent=2, ensure_ascii=False)

    print(f"OK Integrated results saved: {results_file}")

    # Generate summary report
    summary_file = (
        output_dir
        / f"integration_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    )
    with open(summary_file, "w", encoding="utf-8") as f:
        f.write("ML-SHPT Integration Summary\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Timestamp: {integrated_results['timestamp']}\n")
        f.write(f"Integration Type: {integrated_results['integration_type']}\n\n")

        f.write("ML Prediction Results:\n")
        f.write("-" * 30 + "\n")
        ml_status = integrated_results["ml_results"].get("status", "unknown")
        f.write(f"Status: {ml_status}\n")
        if ml_status == "success":
            f.write(
                f"Total Predictions: {integrated_results['ml_results']['total_predictions']}\n"
            )
            f.write(f"File: {integrated_results['ml_results']['file']}\n")
        f.write("\n")

        f.write("SHPT Audit Results:\n")
        f.write("-" * 30 + "\n")
        shpt_status = integrated_results["shpt_results"].get("status", "unknown")
        f.write(f"Status: {shpt_status}\n")
        if shpt_status == "success":
            summary = integrated_results["shpt_results"].get("summary", {})
            if summary:
                f.write(f"Total Items: {summary.get('total_items', 'N/A')}\n")
                f.write(f"Sheets Processed: {summary.get('total_sheets', 'N/A')}\n")
        f.write("\n")

        f.write("Integration Status:\n")
        f.write("-" * 30 + "\n")
        f.write(
            f"ML Available: {integrated_results['combined_summary']['ml_available']}\n"
        )
        f.write(
            f"SHPT Available: {integrated_results['combined_summary']['shpt_available']}\n"
        )
        f.write(
            f"Method: {integrated_results['combined_summary']['integration_method']}\n"
        )

    print(f"OK Summary report saved: {summary_file}")
    print(f"\n[SUCCESS] Integration completed. Output directory: {output_dir}")

    return output_dir


def main():
    """Main integration workflow"""
    print("\n" + "=" * 80)
    print("ML-SHPT Integration Script")
    print("Independent Execution to Avoid Module Conflicts")
    print("=" * 80)

    start_time = time.time()

    # Run ML prediction
    ml_output_dir = run_ml_prediction()

    # Run SHPT audit
    shpt_output_dir = run_shpt_audit()

    # Integrate results
    if ml_output_dir or shpt_output_dir:
        integration_dir = integrate_results(ml_output_dir, shpt_output_dir)

        elapsed_time = time.time() - start_time
        print(f"\n[RESULTS]")
        print(f"  Total processing time: {elapsed_time:.2f} seconds")
        print(f"  ML prediction: {'OK' if ml_output_dir else 'FAIL'}")
        print(f"  SHPT audit: {'OK' if shpt_output_dir else 'FAIL'}")
        print(f"  Integration: OK")
        print(f"  Output directory: {integration_dir}")

        return 0
    else:
        print("\n[FAIL] Both ML and SHPT executions failed")
        return 1


if __name__ == "__main__":
    exit(main())
