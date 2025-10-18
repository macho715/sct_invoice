#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hitachi CASE LIST → HVDC WAREHOUSE 동기화 스크립트

사용법:
    python sync_hitachi.py              # 시뮬레이션 모드
    python sync_hitachi.py --execute    # 실제 실행
"""

import sys
import os
from pathlib import Path

# 패키지 import (상대 import로 통일)
try:
    from .core.data_synchronizer import DataSynchronizer
except ImportError:
    # 직접 실행 시 fallback
    from core.data_synchronizer import DataSynchronizer

# 파일 경로
MASTER_FILE = "CASE LIST.xlsx"
WAREHOUSE_FILE = "HVDC WAREHOUSE_HITACHI(HE).xlsx"


def check_files_exist(script_dir: Path) -> tuple[bool, str]:
    """
    필요한 파일들이 존재하는지 확인

    Args:
        script_dir: 스크립트 디렉토리

    Returns:
        (모든 파일 존재 여부, 누락된 파일 목록)
    """
    required_files = [MASTER_FILE, WAREHOUSE_FILE]
    missing_files = []

    for file_name in required_files:
        file_path = script_dir / file_name
        if not file_path.exists():
            missing_files.append(file_name)

    return len(missing_files) == 0, missing_files


def print_banner(mode: str) -> None:
    """배너 출력"""
    print("=" * 80)
    print("Hitachi CASE LIST -> HVDC WAREHOUSE 동기화")
    print("=" * 80)
    print(f"모드: {mode}")
    print(f"Master 파일: {MASTER_FILE}")
    print(f"Warehouse 파일: {WAREHOUSE_FILE}")
    print("=" * 80)
    print()


def print_result_summary(result: dict) -> None:
    """결과 요약 출력"""
    if not result.get("success"):
        print("[ERROR] 동기화 실패")
        if result.get("issues"):
            print("\n발생한 이슈:")
            for issue in result["issues"]:
                print(f"  - {issue}")
        return

    print("[SUCCESS] 동기화 성공")

    # 기본 통계
    update_summary = result.get("update_summary", {})
    print(f"\n[STATS] 업데이트 통계:")
    print(f"  - 업데이트된 레코드: {update_summary.get('updated_records', 0):,}개")
    print(f"  - 신규 레코드: {update_summary.get('new_records', 0):,}개")
    print(f"  - 건너뛴 레코드: {update_summary.get('skipped_records', 0):,}개")
    print(f"  - 총 변경사항: {update_summary.get('total_changes', 0):,}개")

    # 날짜 업데이트 상세
    date_updates = update_summary.get("date_updates", {})
    if any(date_updates.values()):
        print(f"\n[DATE] 날짜 업데이트 상세:")
        print(
            f"  - 최우선 (창고/현장): {date_updates.get('high_priority_dates', 0):,}개"
        )
        print(
            f"  - 중간 (일반 날짜): {date_updates.get('medium_priority_dates', 0):,}개"
        )
        print(f"  - 낮음 (기타 시간): {date_updates.get('low_priority_dates', 0):,}개")
        print(f"  - 날짜 외 필드: {date_updates.get('non_date_fields', 0):,}개")

    # 매칭 결과
    matching_results = result.get("matching_results", {})
    if matching_results:
        summary = matching_results.get("summary", {})
        print(f"\n[MATCH] 매칭 결과:")
        print(f"  - 전체 소스 케이스: {summary.get('total_source_cases', 0):,}개")
        print(f"  - 정확한 매치: {summary.get('exact_matches', 0):,}개")
        print(f"  - 유사 매치: {summary.get('fuzzy_matches', 0):,}개")
        print(f"  - 신규 케이스: {summary.get('new_cases', 0):,}개")
        print(f"  - 모호한 매치: {summary.get('ambiguous_matches', 0):,}개")
        print(f"  - 매치율: {summary.get('match_rate', 0):.1f}%")

    # 백업 정보
    if result.get("backup_path"):
        print(f"\n[BACKUP] 백업 파일: {result['backup_path']}")

    # 리포트 파일들
    if result.get("heatmap_path"):
        print(f"[HEATMAP] 히트맵: {result['heatmap_path']}")
    if result.get("detailed_report_path"):
        print(f"[REPORT] 상세 리포트: {result['detailed_report_path']}")


def main(dry_run: bool = True) -> dict:
    """
    동기화 실행

    Args:
        dry_run: 시뮬레이션 모드 여부

    Returns:
        동기화 결과
    """
    # 스크립트 디렉토리 확인
    script_dir = Path(__file__).parent
    master_path = script_dir / MASTER_FILE
    warehouse_path = script_dir / WAREHOUSE_FILE

    # 파일 존재 확인
    files_exist, missing_files = check_files_exist(script_dir)
    if not files_exist:
        print("[ERROR] 필요한 파일이 없습니다:")
        for file_name in missing_files:
            print(f"  - {file_name}")
        print(f"\n현재 디렉토리: {script_dir}")
        print("파일을 올바른 위치에 배치한 후 다시 실행하세요.")
        return {
            "success": False,
            "issues": [f"누락된 파일: {', '.join(missing_files)}"],
        }

    # 배너 출력
    mode = "[시뮬레이션]" if dry_run else "[실제 실행]"
    print_banner(mode)

    try:
        # DataSynchronizer 초기화 (날짜 우선순위 활성화)
        print("[INIT] 동기화 엔진 초기화 중...")
        synchronizer = DataSynchronizer(
            column_limit="AQ",
            backup_enabled=True,
            validation_enabled=True,
            prioritize_dates=True,
        )

        # 출력 경로 정보 표시
        print(f"[CONFIG] 백업 경로: {script_dir / 'backups'}")
        print(f"[CONFIG] 결과물 경로: {script_dir / 'out'}")

        # 동기화 실행
        print("[SYNC] 동기화 실행 중...")
        result = synchronizer.synchronize_data(
            str(master_path), str(warehouse_path), dry_run=dry_run
        )

        # 결과 출력
        print_result_summary(result)

        # 상세 리포트 출력 (성공한 경우)
        if result.get("success") and not dry_run:
            print(f"\n[REPORT] 상세 리포트:")
            print(synchronizer.generate_sync_report(result))

        return result

    except Exception as e:
        error_msg = f"동기화 중 오류 발생: {str(e)}"
        print(f"[ERROR] {error_msg}")
        return {"success": False, "issues": [error_msg]}


# 직접 실행을 위해서는 run_sync.py를 사용하세요
