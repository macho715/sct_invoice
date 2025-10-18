#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""성능 최적화 테스트"""

import sys
from pathlib import Path
import time
import logging

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from hitachi import DataSynchronizer, HeaderMatcher, CaseMatcher

# 로깅 설정 (파일로만 출력)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("performance_test.log"), logging.StreamHandler()],
)


def test_performance():
    """성능 테스트"""
    print("=" * 80)
    print("HVDC 동기화 성능 테스트 (최적화 버전)")
    print("=" * 80)

    # 최적화된 동기화기 생성
    synchronizer = DataSynchronizer(
        column_limit="AG",  # Master 파일의 실제 마지막 컬럼
        backup_enabled=False,  # 백업 비활성화로 속도 향상
        validation_enabled=True,
        prioritize_dates=True,
        max_workers=None,  # 자동 최적화
    )

    print(f"워커 수: {synchronizer.parallel_processor.max_workers}")
    print(f"컬럼 제한: A-{synchronizer.column_limit}")

    # 성능 측정
    start_time = time.time()

    try:
        result = synchronizer.synchronize_data(
            "CASE LIST.xlsx", "HVDC WAREHOUSE_HITACHI(HE).xlsx", dry_run=True
        )

        end_time = time.time()
        execution_time = end_time - start_time

        print(f"\n실행 시간: {execution_time:.2f}초")

        if result["success"]:
            summary = result["matching_results"]["summary"]
            us = result["update_summary"]

            print(f"\n=== 매칭 결과 ===")
            print(f"정확한 매치:    {summary['exact_matches']:,}개")
            print(f"유사 매치:      {summary['fuzzy_matches']:,}개")
            print(f"신규 케이스:    {summary['new_cases']:,}개")
            print(f"모호한 매치:    {summary['ambiguous_matches']:,}개")
            print(f"매치율:         {summary['match_rate']:.1f}%")

            print(f"\n=== 업데이트 결과 ===")
            print(f"업데이트 레코드: {us['updated_records']:,}개")
            print(f"신규 레코드:     {us['new_records']:,}개")
            print(f"총 변경사항:     {us['total_changes']:,}개")

            # 성능 평가
            if execution_time < 30:
                print(f"\n✅ 성능 목표 달성: {execution_time:.2f}초 < 30초")
            elif execution_time < 60:
                print(f"\n⚠️  성능 개선 필요: {execution_time:.2f}초 (30-60초)")
            else:
                print(f"\n❌ 성능 목표 미달: {execution_time:.2f}초 > 60초")

        else:
            print(f"\n❌ 동기화 실패: {result.get('issues', [])}")

    except Exception as e:
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"\n❌ 오류 발생: {str(e)}")
        print(f"실행 시간: {execution_time:.2f}초")


def test_header_matching():
    """헤더 매칭 테스트"""
    print("\n" + "=" * 80)
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


def main():
    test_header_matching()
    test_performance()

    print("\n" + "=" * 80)
    print("성능 최적화 완료")
    print("=" * 80)


if __name__ == "__main__":
    main()
