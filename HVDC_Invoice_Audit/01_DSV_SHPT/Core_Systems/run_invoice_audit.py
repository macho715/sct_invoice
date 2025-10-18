#!/usr/bin/env python3
"""
Invoice Audit System - Enhanced CLI with New File Naming
통합 Configuration + Contract 로직으로 전체 인보이스 검증
새로운 파일명 규칙 및 ResultsManager 통합

Version: 3.0.0
Created: 2025-10-17
Author: MACHO-GPT Enhanced File Naming System
"""

import sys
import time
import pandas as pd
from pathlib import Path
from datetime import datetime

# 모듈 import
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "00_Shared"))
from shipment_audit_engine import ShipmentAuditEngine

# ResultsManager import
sys.path.insert(0, str(Path(__file__).parent.parent / "Results"))
from results_manager import ResultsManager


class InvoiceAuditEngine:
    """향상된 인보이스 감사 엔진 - 새로운 파일명 규칙 적용"""

    def __init__(self):
        """InvoiceAuditEngine 초기화"""
        self.results_manager = ResultsManager()
        self.audit_system = ShipmentAuditEngine()

    def get_output_filename(self, file_type: str) -> str:
        """파일 타입에 따른 출력 파일명 반환"""
        return self.results_manager.get_output_filename(
            "invoice_audit", file_type, True
        )

    def save_as_latest(self, source_file: Path, file_type: str):
        """결과를 latest 파일로도 저장"""
        latest_filename = self.results_manager.get_output_filename(
            "invoice_audit", file_type, False
        )
        latest_path = (
            self.results_manager.current_dir
            / "Invoice_Audit"
            / file_type.upper()
            / latest_filename
        )
        latest_path.parent.mkdir(parents=True, exist_ok=True)

        if source_file.exists():
            import shutil

            shutil.copy2(source_file, latest_path)
            print(f"OK Latest file saved: {latest_path.name}")


def run_full_validation():
    """통합 시스템으로 전체 검증 실행 - 새로운 파일명 규칙 적용"""

    print("\n" + "=" * 80)
    print("Enhanced Invoice Validation - New File Naming System")
    print("=" * 80)

    # 시작 시간 측정
    start_time = time.time()

    # Enhanced Audit System 초기화
    print("\n[STEP 1] Initializing Enhanced Invoice Audit Engine...")
    try:
        audit_engine = InvoiceAuditEngine()
        audit_system = audit_engine.audit_system
        print("OK Enhanced Invoice Audit Engine initialized successfully")
    except Exception as e:
        print(f"FAIL Invoice Audit Engine initialization failed: {e}")
        return None

    # 설정 확인
    try:
        config_summary = audit_system.config_manager.get_config_summary()
        print(f"\n[CONFIG] Configuration Manager:")
        print(f"  Lanes loaded: {config_summary['lanes_loaded']}")
        print(f"  Cost Guard bands: {config_summary['cost_guard_bands']}")
        print(f"  Contract rates: {config_summary['contract_rates']}")
        print(f"  Portal fees: {config_summary['portal_fees']}")
    except Exception as e:
        print(f"WARN Configuration summary failed: {e}")

    # Excel 파일 확인
    print(f"\n[STEP 2] Checking Excel file...")
    print(f"  File: {audit_system.excel_file.name}")
    print(f"  Exists: {audit_system.excel_file.exists()}")
    if audit_system.excel_file.exists():
        file_size = audit_system.excel_file.stat().st_size / 1024 / 1024
        print(f"  Size: {file_size:.2f} MB")

    # 전체 검증 실행
    print(f"\n[STEP 3] Running full validation...")
    try:
        results = audit_system.run_full_enhanced_audit()

        # 처리 시간
        elapsed_time = time.time() - start_time

        # 결과 요약
        print(f"\n[RESULTS]")
        print(f"  Total items processed: {results['summary']['total_items']}")
        print(f"  Total sheets: {results['summary']['total_sheets']}")
        print(f"  Processing time: {elapsed_time:.2f} seconds")

        # Contract 검증 분석
        contract_items = [
            item
            for item in results["detailed_results"]
            if item.get("charge_group") == "Contract"
        ]
        contract_with_ref = len(
            [item for item in contract_items if item.get("ref_rate_usd") is not None]
        )
        contract_coverage = (
            (contract_with_ref / len(contract_items) * 100)
            if len(contract_items) > 0
            else 0
        )

        print(f"\n[CONTRACT VALIDATION]")
        print(f"  Total Contract items: {len(contract_items)}")
        print(f"  Items with ref_rate: {contract_with_ref}")
        print(f"  Coverage: {contract_coverage:.1f}%")

        # 상태 분포
        status_counts = {}
        for item in results["detailed_results"]:
            status = item.get("status", "UNKNOWN")
            status_counts[status] = status_counts.get(status, 0) + 1

        print(f"\n[STATUS DISTRIBUTION]")
        for status, count in sorted(status_counts.items()):
            percentage = (
                (count / results["summary"]["total_items"] * 100)
                if results["summary"]["total_items"] > 0
                else 0
            )
            print(f"  {status}: {count} ({percentage:.1f}%)")

        # Charge Group 분포
        charge_groups = {}
        for item in results["detailed_results"]:
            group = item.get("charge_group", "UNKNOWN")
            charge_groups[group] = charge_groups.get(group, 0) + 1

        print(f"\n[CHARGE GROUP DISTRIBUTION]")
        for group, count in sorted(charge_groups.items()):
            percentage = (
                (count / results["summary"]["total_items"] * 100)
                if results["summary"]["total_items"] > 0
                else 0
            )
            print(f"  {group}: {count} ({percentage:.1f}%)")

        # 성능 메트릭
        items_per_second = (
            results["summary"]["total_items"] / elapsed_time if elapsed_time > 0 else 0
        )
        print(f"\n[PERFORMANCE]")
        print(f"  Items/second: {items_per_second:.1f}")
        print(
            f"  Avg time/item: {elapsed_time / results['summary']['total_items'] * 1000:.2f} ms"
        )

        # 새로운 파일명 규칙으로 결과 저장
        print(f"\n[STEP 4] Saving results with new file naming...")
        try:
            # ResultsManager를 사용하여 파일 저장
            results_manager = audit_engine.results_manager

            # CSV 파일 저장
            if "dataframe" in results and results["dataframe"] is not None:
                csv_results = results_manager.save_file(
                    "invoice_audit", "csv", results["dataframe"]
                )
                print(f"  OK CSV saved: {Path(csv_results['timestamp_file']).name}")
                if "latest_file" in csv_results:
                    print(f"  OK Latest CSV: {Path(csv_results['latest_file']).name}")

            # JSON 파일 저장
            json_results = results_manager.save_file("invoice_audit", "json", results)
            print(f"  OK JSON saved: {Path(json_results['timestamp_file']).name}")
            if "latest_file" in json_results:
                print(f"  OK Latest JSON: {Path(json_results['latest_file']).name}")

            # 요약 파일 저장
            summary_content = f"""Invoice Audit Summary
Generated: {datetime.now().isoformat()}
Total Items: {results['summary']['total_items']}
Total Sheets: {results['summary']['total_sheets']}
Processing Time: {elapsed_time:.2f} seconds
Contract Coverage: {contract_coverage:.1f}%

Status Distribution:
{chr(10).join([f"  {status}: {count} ({count/results['summary']['total_items']*100:.1f}%)" for status, count in sorted(status_counts.items())])}

Charge Group Distribution:
{chr(10).join([f"  {group}: {count} ({count/results['summary']['total_items']*100:.1f}%)" for group, count in sorted(charge_groups.items())])}
"""

            summary_results = results_manager.save_file(
                "invoice_audit", "summary", summary_content
            )
            print(f"  OK Summary saved: {Path(summary_results['timestamp_file']).name}")
            if "latest_file" in summary_results:
                print(
                    f"  OK Latest Summary: {Path(summary_results['latest_file']).name}"
                )

        except Exception as e:
            print(f"  FAIL Failed to save results: {e}")

        # Enhanced Excel Report 생성 (새로운 파일명 규칙 적용)
        print(f"\n[STEP 5] Creating Enhanced Excel Report...")
        try:
            from create_enhanced_excel_report import create_enhanced_excel_report

            # 검증 결과 DataFrame 준비
            validation_df = results.get("dataframe", None)
            if validation_df is not None:
                # 새로운 파일명 규칙으로 Excel 파일명 생성
                excel_filename = audit_engine.get_output_filename("excel")
                excel_output_path = (
                    audit_engine.results_manager.current_dir
                    / "Invoice_Audit"
                    / "Excel"
                    / excel_filename
                )
                excel_output_path.parent.mkdir(parents=True, exist_ok=True)

                create_enhanced_excel_report(
                    validation_df, str(excel_output_path), preserve_formatting=True
                )

                print(f"  OK Enhanced Excel report created: {excel_output_path.name}")
                print(f"  INFO Report includes new columns:")
                print(f"    - Anomaly Score (0-100)")
                print(f"    - Risk Score (0-1.0)")
                print(f"    - Risk Level (LOW/MEDIUM/HIGH/CRITICAL)")
                print(f"    - Anomaly Details")
                print(f"    - Risk Components")

                # latest 파일로도 저장
                audit_engine.save_as_latest(excel_output_path, "excel")

            else:
                print(f"  WARNING No validation data available for Excel report")

        except ImportError as e:
            print(f"  WARNING Enhanced Excel report module not available: {e}")
        except Exception as e:
            print(f"  ERROR Failed to create Enhanced Excel report: {e}")

        # 결과 파일 위치 정보
        print(f"\n[OUTPUT FILES]")
        print(f"  Current directory: {audit_engine.results_manager.current_dir}")
        print(f"  Archive directory: {audit_engine.results_manager.archive_dir}")

        # 사용 가능한 파일 목록 표시
        available_files = audit_engine.results_manager.list_available_files(
            "invoice_audit"
        )
        print(f"\n[AVAILABLE FILES]")
        for file_type, files in available_files.items():
            if files:
                print(f"  {file_type}: {len(files)} files")
                for file in files:
                    print(f"    - {file}")

        print("\n" + "=" * 80)
        print("[SUCCESS] Enhanced invoice validation completed!")
        print("New file naming system applied successfully!")
        print("=" * 80)

        return results

    except Exception as e:
        print(f"\n[ERROR] Validation failed: {e}")
        import traceback

        traceback.print_exc()
        return None


def main():
    """Main entry point with enhanced error handling"""
    try:
        results = run_full_validation()
        if results:
            print(f"\n[FINAL] Validation completed successfully")
            return 0
        else:
            print(f"\n[FINAL] Validation failed")
            return 1
    except Exception as e:
        print(f"\n[FINAL] Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())




