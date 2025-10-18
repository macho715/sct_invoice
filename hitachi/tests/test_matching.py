#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""매칭 결과 상세 분석 스크립트"""

import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from hitachi import DataSynchronizer


def main():
    print("=" * 80)
    print("매칭 결과 상세 분석")
    print("=" * 80)

    s = DataSynchronizer()
    result = s.synchronize_data(
        "CASE LIST.xlsx", "HVDC WAREHOUSE_HITACHI(HE).xlsx", dry_run=True
    )

    print("\n=== MATCHING SUMMARY ===")
    mr = result.get("matching_results", {})
    summary = mr.get("summary", {})

    print(f"총 소스 케이스:  {summary.get('total_source_cases', 0):,}개")
    print(f"정확한 매치:     {summary.get('exact_matches', 0):,}개")
    print(f"유사 매치:       {summary.get('fuzzy_matches', 0):,}개")
    print(f"신규 케이스:     {summary.get('new_cases', 0):,}개")
    print(f"모호한 매치:     {summary.get('ambiguous_matches', 0):,}개")
    print(f"매칭률:          {summary.get('match_rate', 0):.1f}%")

    print("\n=== UPDATE SUMMARY ===")
    us = result.get("update_summary", {})

    print(f"업데이트된 레코드: {us.get('updated_records', 0):,}개")
    print(f"신규 레코드:       {us.get('new_records', 0):,}개")
    print(f"건너뛴 레코드:     {us.get('skipped_records', 0):,}개")
    print(f"총 변경사항:       {us.get('total_changes', 0):,}개")

    # 문제 분석
    print("\n=== 문제 분석 ===")

    total_matched = summary.get("exact_matches", 0) + summary.get("fuzzy_matches", 0)
    ambiguous = summary.get("ambiguous_matches", 0)
    new_cases = summary.get("new_cases", 0)
    total_source = summary.get("total_source_cases", 0)

    unaccounted = total_source - total_matched - new_cases

    print(f"총 소스:          {total_source:,}개")
    print(f"매칭됨 (exact+fuzzy): {total_matched:,}개")
    print(f"신규:             {new_cases:,}개")
    print(f"모호한 매치:      {ambiguous:,}개")
    print(f"계산 차이:        {unaccounted:,}개")

    if ambiguous > 0 and new_cases == 0:
        print(f"\n⚠️  경고: {ambiguous}개의 모호한 매치가 발견되었습니다!")
        print("이들 중 일부는 실제로 신규 케이스일 가능성이 있습니다.")
        print("case_matcher.py의 매칭 로직 개선이 필요합니다.")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()

