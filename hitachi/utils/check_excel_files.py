#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""엑셀 파일 CASE NO 확인 스크립트"""

import pandas as pd


def check_excel_files():
    """엑셀 파일의 CASE NO 패턴 확인"""

    # 1. Master 파일 로드
    print("=" * 80)
    print("MASTER 파일 분석 (CASE LIST.xlsx)")
    print("=" * 80)

    master = pd.read_excel("CASE LIST.xlsx")
    print(f"\n총 레코드: {len(master):,}개")
    print(f"컬럼명: {list(master.columns[:10])}")

    # CASE NO 컬럼명 찾기
    case_col = None
    for col in master.columns:
        if "case" in col.lower() and "no" in col.lower():
            case_col = col
            break

    if case_col is None:
        print("오류: CASE NO 컬럼을 찾을 수 없습니다!")
        return

    print(f"\nCASE NO 컬럼명: '{case_col}'")
    print(f"고유 CASE NO: {master[case_col].nunique():,}개")

    print("\nCASE NO 샘플 (처음 20개):")
    for i, case_no in enumerate(master[case_col].head(20), 1):
        print(f"  {i:2d}. {case_no}")

    # 2. Warehouse 파일 로드
    print("\n" + "=" * 80)
    print("WAREHOUSE 파일 분석 (HVDC WAREHOUSE_HITACHI(HE).xlsx)")
    print("=" * 80)

    warehouse = pd.read_excel("HVDC WAREHOUSE_HITACHI(HE).xlsx")
    print(f"\n총 레코드: {len(warehouse):,}개")
    print(f"컬럼명: {list(warehouse.columns[:10])}")

    # CASE NO 컬럼명 찾기
    wh_case_col = None
    for col in warehouse.columns:
        if "case" in col.lower() and "no" in col.lower():
            wh_case_col = col
            break

    if wh_case_col is None:
        print("오류: Warehouse CASE NO 컬럼을 찾을 수 없습니다!")
        return

    print(f"\nCASE NO 컬럼명: '{wh_case_col}'")
    print(f"고유 CASE NO: {warehouse[wh_case_col].nunique():,}개")
    print(f"중복 CASE NO: {len(warehouse) - warehouse[wh_case_col].nunique():,}개")

    print("\nCASE NO 샘플 (처음 20개):")
    for i, case_no in enumerate(warehouse[wh_case_col].head(20), 1):
        print(f"  {i:2d}. {case_no}")

    # 3. 중복 CASE NO 확인
    if len(warehouse) - warehouse[wh_case_col].nunique() > 0:
        print("\n" + "=" * 80)
        print("중복된 CASE NO 분석")
        print("=" * 80)

        duplicates = warehouse[warehouse.duplicated(subset=[wh_case_col], keep=False)]
        dup_case_nos = duplicates[wh_case_col].unique()

        print(f"\n중복된 CASE NO 개수: {len(dup_case_nos):,}개")
        print("\n중복 CASE NO 샘플 (처음 10개):")
        for i, case_no in enumerate(dup_case_nos[:10], 1):
            count = len(duplicates[duplicates[wh_case_col] == case_no])
            print(f"  {i:2d}. {case_no} ({count}번 중복)")

    # 4. Master에만 있는 CASE NO 확인
    print("\n" + "=" * 80)
    print("Master에만 있는 CASE NO (Warehouse에 없음)")
    print("=" * 80)

    master_only = set(master[case_col]) - set(warehouse[wh_case_col])
    print(f"\n개수: {len(master_only):,}개")

    if len(master_only) > 0:
        print("\n샘플 (처음 20개):")
        for i, case_no in enumerate(sorted(list(master_only))[:20], 1):
            print(f"  {i:2d}. {case_no}")

    # 5. Warehouse에만 있는 CASE NO 확인
    print("\n" + "=" * 80)
    print("Warehouse에만 있는 CASE NO (Master에 없음)")
    print("=" * 80)

    warehouse_only = set(warehouse[wh_case_col]) - set(master[case_col])
    print(f"\n개수: {len(warehouse_only):,}개")

    if len(warehouse_only) > 0:
        print("\n샘플 (처음 20개):")
        for i, case_no in enumerate(sorted(list(warehouse_only))[:20], 1):
            print(f"  {i:2d}. {case_no}")

    # 6. 공통 CASE NO 확인
    print("\n" + "=" * 80)
    print("공통 CASE NO (양쪽 모두 존재)")
    print("=" * 80)

    common = set(master[case_col]) & set(warehouse[wh_case_col])
    print(f"\n개수: {len(common):,}개")

    # 7. 요약 통계
    print("\n" + "=" * 80)
    print("요약 통계")
    print("=" * 80)

    print(f"\nMaster 총 케이스:          {len(master):,}개")
    print(f"Warehouse 총 케이스:       {len(warehouse):,}개")
    print(f"공통 케이스:               {len(common):,}개")
    print(
        f"Master에만 있음:           {len(master_only):,}개  <- 이것이 신규 케이스 후보"
    )
    print(f"Warehouse에만 있음:        {len(warehouse_only):,}개")
    print(
        f"Warehouse 중복:            {len(warehouse) - warehouse[wh_case_col].nunique():,}개"
    )

    # 8. 모호한 매치 653개 분석
    print("\n" + "=" * 80)
    print("653개 모호한 매치 분석")
    print("=" * 80)

    print(
        f"\n예상: Master에만 있는 {len(master_only):,}개가 '모호한 매치'로 잘못 분류됨"
    )
    print(f"실제 모호한 매치 예상: 653개")

    if len(master_only) == 653:
        print(
            "\n결론: 653개 모호한 매치는 실제로는 Warehouse에 없는 신규 케이스입니다!"
        )
        print("      이들을 신규 케이스로 처리해야 합니다.")
    elif len(warehouse) - warehouse["CASE NO"].nunique() == 653:
        print(
            "\n결론: Warehouse에 653개의 중복 CASE NO가 있어 모호한 매치가 발생합니다!"
        )
        print("      중복된 레코드를 정리하거나, 매칭 로직을 개선해야 합니다.")
    else:
        print(f"\n불일치: Master에만 있음({len(master_only)}개) vs 모호한 매치(653개)")
        print("       추가 분석이 필요합니다.")


if __name__ == "__main__":
    try:
        check_excel_files()
    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback

        traceback.print_exc()
