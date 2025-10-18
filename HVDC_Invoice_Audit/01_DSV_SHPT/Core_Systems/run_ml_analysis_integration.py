#!/usr/bin/env python3
"""
ML Analysis Integration Script - Enhanced with New File Naming
의존성 충돌 없이 ML 결과와 Invoice Audit 결과를 통합
새로운 파일명 규칙 및 ResultsManager 통합

Version: 2.0.0
Created: 2025-10-17
Author: MACHO-GPT Enhanced File Naming System
"""

import sys
import time
import subprocess
from pathlib import Path
from datetime import datetime
import pandas as pd
import json

# ResultsManager import
sys.path.insert(0, str(Path(__file__).parent.parent / "Results"))
from results_manager import ResultsManager


def run_ml_prediction():
    """Run ML prediction independently with new file naming"""
    print("\n" + "=" * 80)
    print("PHASE 1: ML Prediction (Enhanced System with New File Naming)")
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

    # ResultsManager 초기화
    results_manager = ResultsManager()
    ml_output_dir = results_manager.current_dir / "ML_Analysis" / "Results"
    ml_output_dir.mkdir(parents=True, exist_ok=True)

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
        str(ml_output_dir),
    ]

    print(f"Executing: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd, cwd=str(ml_dir), capture_output=True, text=True, timeout=300
        )

        if result.returncode == 0:
            print("OK ML prediction completed successfully")
            print(f"Output directory: {ml_output_dir}")
            return ml_output_dir
        else:
            print("FAIL ML prediction failed")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return None

    except subprocess.TimeoutExpired:
        print("FAIL ML prediction timed out after 5 minutes")
        return None
    except Exception as e:
        print(f"FAIL ML prediction error: {e}")
        return None


def run_invoice_audit():
    """Run Invoice Audit independently with new file naming"""
    print("\n" + "=" * 80)
    print("PHASE 2: Invoice Audit Validation (Enhanced System)")
    print("=" * 80)

    audit_dir = Path(__file__).parent

    # Run Invoice Audit using subprocess
    cmd = [sys.executable, str(audit_dir / "run_invoice_audit.py")]

    print(f"Executing: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd, cwd=str(audit_dir), capture_output=True, text=True, timeout=600
        )

        if result.returncode == 0:
            print("OK Invoice Audit completed successfully")
            print(f"Output directory: {audit_dir.parent / 'Results' / 'Current'}")
            return audit_dir.parent / "Results" / "Current"
        else:
            print("FAIL Invoice Audit failed")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return None

    except subprocess.TimeoutExpired:
        print("FAIL Invoice Audit timed out after 10 minutes")
        return None
    except Exception as e:
        print(f"FAIL Invoice Audit error: {e}")
        return None


def integrate_results(ml_output_dir, audit_output_dir):
    """Integrate ML and Invoice Audit results with new file naming"""
    print("\n" + "=" * 80)
    print("PHASE 3: Results Integration (Enhanced File Naming)")
    print("=" * 80)

    results_manager = ResultsManager()

    integrated_results = {
        "timestamp": datetime.now().isoformat(),
        "integration_type": "independent_execution_with_new_naming",
        "ml_results": {},
        "audit_results": {},
        "combined_summary": {},
    }

    # Load ML prediction results
    if ml_output_dir and ml_output_dir.exists():
        try:
            # ML 예측 결과 파일 찾기
            ml_predictions_file = ml_output_dir / "predictions_ml.json"
            if not ml_predictions_file.exists():
                ml_predictions_file = ml_output_dir / "predictions_ml.csv"

            if ml_predictions_file.exists():
                if ml_predictions_file.suffix == ".json":
                    with open(ml_predictions_file, "r", encoding="utf-8") as f:
                        ml_data = json.load(f)
                else:
                    ml_df = pd.read_csv(ml_predictions_file, encoding="utf-8")
                    ml_data = ml_df.to_dict("records")

                integrated_results["ml_results"] = {
                    "status": "success",
                    "file": str(ml_predictions_file),
                    "total_predictions": len(ml_data),
                }
                print(f"OK ML results loaded: {len(ml_data)} predictions")

                # ResultsManager를 사용하여 ML 결과 저장
                ml_results = results_manager.save_file(
                    "ml_analysis", "predictions", ml_data
                )
                print(
                    f"OK ML results saved with new naming: {Path(ml_results['timestamp_file']).name}"
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

    # Load Invoice Audit results
    if audit_output_dir and audit_output_dir.exists():
        try:
            # Invoice Audit 결과 파일 찾기
            audit_results_dir = audit_output_dir / "Invoice_Audit"
            if audit_results_dir.exists():
                # JSON 결과 파일 찾기
                json_dir = audit_results_dir / "JSON"
                if json_dir.exists():
                    result_files = list(json_dir.glob("invoice_audit_*.json"))
                    if result_files:
                        latest_result = max(
                            result_files, key=lambda p: p.stat().st_mtime
                        )
                        with open(latest_result, "r", encoding="utf-8") as f:
                            audit_data = json.load(f)

                        integrated_results["audit_results"] = {
                            "status": "success",
                            "file": str(latest_result),
                            "summary": audit_data.get("summary", {}),
                        }
                        print(
                            f"OK Invoice Audit results loaded from: {latest_result.name}"
                        )
                    else:
                        integrated_results["audit_results"] = {
                            "status": "no_json_files"
                        }
                        print("WARN No JSON result files found in Invoice Audit")
                else:
                    integrated_results["audit_results"] = {"status": "no_json_dir"}
                    print("WARN No JSON directory found in Invoice Audit")
            else:
                integrated_results["audit_results"] = {"status": "no_audit_dir"}
                print("WARN No Invoice_Audit directory found")
        except Exception as e:
            integrated_results["audit_results"] = {"status": "error", "error": str(e)}
            print(f"FAIL Failed to load Invoice Audit results: {e}")
    else:
        integrated_results["audit_results"] = {"status": "skipped"}
        print("WARN Invoice Audit results directory not found")

    # Create combined summary
    integrated_results["combined_summary"] = {
        "ml_available": integrated_results["ml_results"].get("status") == "success",
        "audit_available": integrated_results["audit_results"].get("status")
        == "success",
        "integration_method": "independent_subprocess_execution_with_new_naming",
        "note": "Results generated independently to avoid module conflicts, using new file naming system",
    }

    # Save integrated results using ResultsManager
    try:
        # 통합 결과를 ML_Analysis로 저장
        integration_results = results_manager.save_file(
            "ml_analysis", "predictions", integrated_results
        )
        print(
            f"OK Integrated results saved with new naming: {Path(integration_results['timestamp_file']).name}"
        )

        # 요약 보고서 생성
        summary_content = f"""ML Analysis Integration Summary
Generated: {integrated_results['timestamp']}
Integration Type: {integrated_results['integration_type']}

ML Prediction Results:
{'-' * 30}
Status: {integrated_results['ml_results'].get('status', 'unknown')}
Total Predictions: {integrated_results['ml_results'].get('total_predictions', 'N/A')}
File: {Path(integrated_results['ml_results'].get('file', 'N/A')).name}

Invoice Audit Results:
{'-' * 30}
Status: {integrated_results['audit_results'].get('status', 'unknown')}
File: {Path(integrated_results['audit_results'].get('file', 'N/A')).name}
Summary: {integrated_results['audit_results'].get('summary', {})}

Integration Status:
{'-' * 30}
ML Available: {integrated_results['combined_summary']['ml_available']}
Audit Available: {integrated_results['combined_summary']['audit_available']}
Method: {integrated_results['combined_summary']['integration_method']}
Note: {integrated_results['combined_summary']['note']}
"""

        summary_results = results_manager.save_file(
            "ml_analysis", "summary", summary_content
        )
        print(
            f"OK Integration summary saved: {Path(summary_results['timestamp_file']).name}"
        )

        print(f"\n[SUCCESS] Integration completed with new file naming system!")
        print(f"Output directory: {results_manager.current_dir}")

        return results_manager.current_dir

    except Exception as e:
        print(f"FAIL Failed to save integrated results: {e}")
        return None


def main():
    """Main integration workflow with enhanced file naming"""
    print("\n" + "=" * 80)
    print("ML Analysis Integration Script")
    print("Enhanced File Naming System")
    print("=" * 80)

    start_time = time.time()

    # Run ML prediction
    ml_output_dir = run_ml_prediction()

    # Run Invoice Audit
    audit_output_dir = run_invoice_audit()

    # Integrate results
    if ml_output_dir or audit_output_dir:
        integration_dir = integrate_results(ml_output_dir, audit_output_dir)

        elapsed_time = time.time() - start_time
        print(f"\n[RESULTS]")
        print(f"  Total processing time: {elapsed_time:.2f} seconds")
        print(f"  ML prediction: {'OK' if ml_output_dir else 'SKIPPED'}")
        print(f"  Invoice Audit: {'OK' if audit_output_dir else 'SKIPPED'}")
        print(f"  Integration: {'OK' if integration_dir else 'FAILED'}")
        print(f"  Output directory: {integration_dir}")

        return 0
    else:
        print("\n[ERROR] Both ML prediction and Invoice Audit failed")
        return 1


if __name__ == "__main__":
    exit(main())




