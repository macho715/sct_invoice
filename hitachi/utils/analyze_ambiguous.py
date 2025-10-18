#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""모호한 매치 653개 상세 분석 스크립트"""

import sys
from pathlib import Path
import pandas as pd

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from hitachi import DataSynchronizer, CaseMatcher

def analyze_ambiguous_matches():
    """모호한 매치 653개 상세 분석"""
    print("=" * 80)
    print("모호한 매치 653개 상세 분석")
    print("=" * 80)

    # 1. DataSynchronizer로 매칭 결과 가져오기
    synchronizer = DataSynchronizer(prioritize_dates=True)
    result = synchronizer.synchronize_data(
        'CASE LIST.xlsx',
        'HVDC WAREHOUSE_HITACHI(HE).xlsx',
        dry_run=True
    )

    matching_results = result.get('matching_results', {})
    ambiguous_matches = matching_results.get('ambiguous_matches', {})

    print(f"\n총 모호한 매치: {len(ambiguous_matches)}개")

    if len(ambiguous_matches) == 0:
        print("모호한 매치가 없습니다.")
        return

    # 2. Master 파일 로드 (CASE NO 확인용)
    master_df = pd.read_excel('CASE LIST.xlsx')
    print(f"Master 파일 총 케이스: {len(master_df)}개")

    # 3. Warehouse 파일 로드 (CASE NO 확인용)
    warehouse_df = pd.read_excel('HVDC WAREHOUSE_HITACHI(HE).xlsx')
    print(f"Warehouse 파일 총 케이스: {len(warehouse_df)}개")

    # 4. 모호한 매치 상세 분석
    print(f"\n=== 모호한 매치 상세 분석 (처음 20개) ===")

    case_matcher = CaseMatcher()

    # 유사도별 분류
    high_similarity = []  # >= 0.95
    medium_similarity = []  # 0.90-0.94
    low_similarity = []  # < 0.90

    for i, (master_idx, ambig_info) in enumerate(list(ambiguous_matches.items())[:20]):
        source_case = ambig_info['source_case']
        candidates = ambig_info['candidates']
        best_candidate = ambig_info['best_candidate']

        best_similarity = best_candidate['similarity']

        print(f"\n--- 모호한 매치 #{i+1} ---")
        print(f"소스 CASE NO: {source_case}")
        print(f"Master 인덱스: {master_idx}")
        print(f"후보 수: {len(candidates)}개")
        print(f"최고 유사도: {best_similarity:.3f}")

        # 후보들 상세 정보
        print("후보들:")
        for j, candidate in enumerate(candidates[:5]):  # 최대 5개만 표시
            target_idx = candidate['target_index']
            target_case = candidate['target_case']
            similarity = candidate['similarity']
            print(f"  {j+1}. {target_case} (유사도: {similarity:.3f}, 타겟 인덱스: {target_idx})")

        if len(candidates) > 5:
            print(f"  ... 및 {len(candidates) - 5}개 더")

        # 유사도별 분류
        if best_similarity >= 0.95:
            high_similarity.append((master_idx, source_case, best_similarity))
        elif best_similarity >= 0.90:
            medium_similarity.append((master_idx, source_case, best_similarity))
        else:
            low_similarity.append((master_idx, source_case, best_similarity))

        # 실제 매치 가능성 분석
        if best_similarity >= 0.95:
            print("  → 명확한 매치 가능 (유사도 ≥95%)")
        elif best_similarity < 0.90:
            print("  → 신규 케이스 가능성 높음 (유사도 <90%)")
        else:
            print("  → 진짜 모호한 케이스 (유사도 90-94%)")

    # 5. 전체 통계
    print(f"\n=== 전체 모호한 매치 통계 ===")
    print(f"고유사도 (≥95%): {len(high_similarity)}개")
    print(f"중간유사도 (90-94%): {len(medium_similarity)}개")
    print(f"저유사도 (<90%): {len(low_similarity)}개")

    # 6. 개선 방안 제시
    print(f"\n=== 개선 방안 제시 ===")

    if len(high_similarity) > 0:
        print(f"1. {len(high_similarity)}개는 명확한 매치로 처리 가능 (유사도 ≥95%)")

    if len(low_similarity) > 0:
        print(f"2. {len(low_similarity)}개는 신규 케이스로 처리 가능 (유사도 <90%)")

    remaining_ambiguous = len(medium_similarity)
    print(f"3. {remaining_ambiguous}개만 진짜 모호한 케이스로 유지")

    # 7. 샘플 케이스 확인
    if len(high_similarity) > 0:
        print(f"\n=== 고유사도 샘플 (처음 3개) ===")
        for i, (master_idx, case_no, similarity) in enumerate(high_similarity[:3]):
            print(f"{i+1}. {case_no} (유사도: {similarity:.3f})")

    if len(low_similarity) > 0:
        print(f"\n=== 저유사도 샘플 (처음 3개) ===")
        for i, (master_idx, case_no, similarity) in enumerate(low_similarity[:3]):
            print(f"{i+1}. {case_no} (유사도: {similarity:.3f})")

    print(f"\n=== 분석 완료 ===")
    print(f"총 모호한 매치: {len(ambiguous_matches)}개")
    print(f"명확한 매치로 전환 가능: {len(high_similarity)}개")
    print(f"신규 케이스로 전환 가능: {len(low_similarity)}개")
    print(f"진짜 모호한 케이스: {remaining_ambiguous}개")

def main():
    try:
        analyze_ambiguous_matches()
    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

