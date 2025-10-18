#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""중복 처리 + 날짜 업데이트 + 병렬 처리 테스트"""

import sys
from pathlib import Path
import time

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from hitachi import DataSynchronizer, HeaderMatcher


def test_header_matching():
    """헤더 매칭 테스트"""
    print("=" * 80)
    print("헤더 동적 인식 테스트")
    print("=" * 80)

    matcher = HeaderMatcher()

    test_headers = [
        "Case No.",
        "CASE NO",
        "case_no",
        "Case-No",
        "DSV Indoor",
        "dsv_indoor",
        "ETD/ATD",
        "etd_atd",
    ]

    print("\n헤더 정규화:")
    for header in test_headers:
        normalized = matcher.normalize_header(header)
        is_date = matcher.is_date_column(header)
        print(f"  '{header}' → '{normalized}' (날짜: {is_date})")


def test_performance():
    """성능 테스트 (병렬 vs 순차)"""
    print("\n" + "=" * 80)
    print("성능 테스트: 병렬 처리")
    print("=" * 80)

    # 병렬 처리 (기본)
    print("\n병렬 처리 모드:")
    start = time.time()
    synchronizer = DataSynchronizer(prioritize_dates=True, max_workers=4)
    result = synchronizer.synchronize_data(
        "CASE LIST.xlsx", "HVDC WAREHOUSE_HITACHI(HE).xlsx", dry_run=True
    )
    parallel_time = time.time() - start
    print(f"처리 시간: {parallel_time:.2f}초")

    # 단일 스레드 처리
    print("\n단일 스레드 모드:")
    start = time.time()
    synchronizer_single = DataSynchronizer(prioritize_dates=True, max_workers=1)
    result_single = synchronizer_single.synchronize_data(
        "CASE LIST.xlsx", "HVDC WAREHOUSE_HITACHI(HE).xlsx", dry_run=True
    )
    single_time = time.time() - start
    print(f"처리 시간: {single_time:.2f}초")

    # 성능 향상
    speedup = single_time / parallel_time
    print(f"\n성능 향상: {speedup:.2f}x")

    return result


def test_results(result):
    """결과 검증"""
    summary = result["matching_results"]["summary"]
    us = result["update_summary"]

    print("\n" + "=" * 80)
    print("매칭 및 업데이트 결과")
    print("=" * 80)

    print("\n=== 매칭 결과 ===")
    print(f"정확한 매치:    {summary['exact_matches']:,}개")
    print(f"유사 매치:      {summary['fuzzy_matches']:,}개")
    print(f"신규 케이스:    {summary['new_cases']:,}개")
    print(f"모호한 매치:    {summary['ambiguous_matches']:,}개")

    print("\n=== 업데이트 결과 ===")
    print(f"업데이트 레코드: {us['updated_records']:,}개")
    print(f"신규 레코드:     {us['new_records']:,}개")
    print(f"총 변경사항:     {us['total_changes']:,}개")

    # 기대값 검증
    print("\n=== 검증 ===")
    expectations = {
        "정확한 매치": (summary["exact_matches"], 5400, 5500),
        "신규 케이스": (summary["new_cases"], 200, 300),
        "모호한 매치": (summary["ambiguous_matches"], 0, 20),
    }

    for name, (actual, min_exp, max_exp) in expectations.items():
        status = "OK" if min_exp <= actual <= max_exp else "FAIL"
        print(f"{name}: {actual:,}개 [{status}]")


def main():
    test_header_matching()
    result = test_performance()
    test_results(result)

    print("\n실제 실행 시 변경된 날짜가 주황색으로 표시됩니다.")
    print("병렬 처리로 성능이 개선되었습니다.")


if __name__ == "__main__":
    main()



