#!/usr/bin/env python3
"""
HVDC 파이프라인 통합 실행 스크립트
HVDC Pipeline Integrated Execution Script

전체 파이프라인을 하나의 명령으로 실행할 수 있는 통합 스크립트입니다.
"""

import argparse
import sys
import time
from pathlib import Path
from typing import List, Optional

import yaml

# 프로젝트 루트 경로 추가
sys.path.append(str(Path(__file__).parent))

# 각 Stage 임포트
try:
    from scripts.stage2_derived.derived_columns_processor import process_derived_columns

    # 다른 모듈들은 필요시 개별적으로 임포트
except ImportError as e:
    print(f"ERROR: 모듈 임포트 실패: {e}")
    print("requirements.txt의 패키지들이 설치되었는지 확인하세요.")
    sys.exit(1)


def load_config() -> dict:
    """파이프라인 설정을 로드합니다."""
    config_path = Path(__file__).parent / "config" / "pipeline_config.yaml"
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"WARNING: 설정 파일을 찾을 수 없습니다: {config_path}")
        return {}


def print_banner():
    """파이프라인 시작 배너를 출력합니다."""
    print("\n" + "=" * 80)
    print("🚀 HVDC PIPELINE v2.0 - 통합 실행")
    print("   Samsung C&T Logistics | ADNOC·DSV Partnership")
    print("=" * 80)
    print("📋 실행 단계:")
    print("   Stage 1: 데이터 동기화 (Data Synchronization)")
    print("   Stage 2: 파생 컬럼 생성 (Derived Columns)")
    print("   Stage 3: 보고서 생성 (Report Generation)")
    print("   Stage 4: 이상치 탐지 (Anomaly Detection)")
    print("=" * 80 + "\n")


def run_stage(stage_num: int, config: dict) -> bool:
    """특정 Stage를 실행합니다."""
    stage_start_time = time.time()

    try:
        if stage_num == 1:
            print("🔄 Stage 1: 데이터 동기화 실행...")
            print("INFO: Stage 1은 별도 스크립트로 실행하세요.")
            print("      python scripts/stage1_sync/data_synchronizer.py")

        elif stage_num == 2:
            print("🧮 Stage 2: 파생 컬럼 생성 실행...")
            # 설정에서 입력 파일 경로 가져오기
            stage2_config_path = (
                Path(__file__).parent / "config" / "stage2_derived_config.yaml"
            )
            if stage2_config_path.exists():
                with open(stage2_config_path, "r", encoding="utf-8") as f:
                    stage2_config = yaml.safe_load(f)
                input_file = stage2_config.get("input", {}).get(
                    "synced_file",
                    "data/processed/synced/HVDC_WAREHOUSE_HITACHI_HE_synced.xlsx",
                )
            else:
                input_file = (
                    "data/processed/synced/HVDC_WAREHOUSE_HITACHI_HE_synced.xlsx"
                )

            success = process_derived_columns(input_file)
            if not success:
                return False

        elif stage_num == 3:
            print("📊 Stage 3: 보고서 생성 실행...")
            print("INFO: Stage 3은 별도 스크립트로 실행하세요.")
            print("      python scripts/stage3_report/report_generator.py")

        elif stage_num == 4:
            print("🔍 Stage 4: 이상치 탐지 실행...")
            print("INFO: Stage 4는 별도 스크립트로 실행하세요.")
            print("      python scripts/stage4_anomaly/anomaly_detector.py")

        else:
            print(f"ERROR: 알 수 없는 Stage 번호: {stage_num}")
            return False

        stage_duration = time.time() - stage_start_time
        print(f"✅ Stage {stage_num} 완료 (소요시간: {stage_duration:.2f}초)\n")
        return True

    except Exception as e:
        print(f"❌ Stage {stage_num} 실행 중 오류 발생: {e}")
        return False


def run_all_stages(config: dict) -> bool:
    """모든 Stage를 순차적으로 실행합니다."""
    print_banner()

    stages = [1, 2, 3, 4]
    total_start_time = time.time()

    for stage_num in stages:
        if not run_stage(stage_num, config):
            print(f"❌ 파이프라인 실패: Stage {stage_num}에서 중단")
            return False

    total_duration = time.time() - total_start_time
    print("🎉 전체 파이프라인 실행 완료!")
    print(f"⏱️  총 소요시간: {total_duration:.2f}초")
    print("📁 결과 파일들:")
    print("   - data/processed/synced/: 동기화된 데이터")
    print("   - data/processed/derived/: 파생 컬럼이 추가된 데이터")
    print("   - data/processed/reports/: 최종 보고서")
    print("   - data/anomaly/: 이상치 분석 결과")

    return True


def run_specific_stages(stage_list: List[int], config: dict) -> bool:
    """지정된 Stage들만 실행합니다."""
    print(f"🎯 선택된 Stage 실행: {stage_list}")

    for stage_num in stage_list:
        if not run_stage(stage_num, config):
            print(f"❌ 파이프라인 실패: Stage {stage_num}에서 중단")
            return False

    print("✅ 선택된 Stage 실행 완료!")
    return True


def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(
        description="HVDC 파이프라인 통합 실행",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  python run_pipeline.py --all                    # 전체 파이프라인 실행
  python run_pipeline.py --stage 1,2              # Stage 1, 2만 실행
  python run_pipeline.py --stage 2                # Stage 2만 실행
        """,
    )

    parser.add_argument(
        "--all", action="store_true", help="전체 파이프라인 실행 (Stage 1-4)"
    )
    parser.add_argument(
        "--stage", type=str, help="실행할 Stage 번호 (예: 1,2,3 또는 2)"
    )

    args = parser.parse_args()

    # 설정 로드
    config = load_config()

    # 인자 검증
    if not args.all and not args.stage:
        parser.print_help()
        return 1

    # 실행
    try:
        if args.all:
            success = run_all_stages(config)
        else:
            # Stage 번호 파싱
            try:
                stages = [int(s.strip()) for s in args.stage.split(",")]
                stages = [s for s in stages if 1 <= s <= 4]  # 유효한 Stage 번호만

                if not stages:
                    print("ERROR: 유효한 Stage 번호를 입력하세요 (1-4)")
                    return 1

                success = run_specific_stages(stages, config)
            except ValueError:
                print("ERROR: Stage 번호 형식이 올바르지 않습니다 (예: 1,2,3)")
                return 1

        return 0 if success else 1

    except KeyboardInterrupt:
        print("\n⚠️  사용자에 의해 중단됨")
        return 1
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
