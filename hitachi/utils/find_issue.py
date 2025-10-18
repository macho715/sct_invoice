#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
업데이트 문제 원인 찾기
"""

import pandas as pd
import numpy as np

# 파일 로드
master = pd.read_excel("CASE LIST.xlsx")
warehouse = pd.read_excel("HVDC WAREHOUSE_HITACHI(HE).xlsx", sheet_name="Case List")

print("=" * 60)
print("CASE NO 매칭 분석")
print("=" * 60)

# CASE NO 정규화
master_cases = set(str(x).strip() for x in master["Case No."].dropna())
warehouse_cases = set(str(x).strip() for x in warehouse["Case No."].dropna())

print(f"\nMaster CASE 수: {len(master_cases)}")
print(f"Warehouse CASE 수: {len(warehouse_cases)}")

# 차이 분석
only_in_master = master_cases - warehouse_cases
only_in_warehouse = warehouse_cases - master_cases
common = master_cases & warehouse_cases

print(f"\n공통 CASE 수: {len(common)}")
print(f"Master에만 있는 CASE 수: {len(only_in_master)}")
print(f"Warehouse에만 있는 CASE 수: {len(only_in_warehouse)}")

# Master에만 있는 케이스 샘플
if len(only_in_master) > 0:
    print(f"\nMaster에만 있는 CASE 샘플 (처음 20개):")
    samples = sorted(list(only_in_master))[:20]
    for case in samples:
        print(f"  - {case}")

    # 이 케이스들이 실제로 업데이트되어야 하는지 확인
    print(f"\n이 케이스들은 '신규 레코드'로 추가되어야 합니다!")
    print(
        f"그러나 스크립트는 {len(only_in_master)}개 중 0개를 추가했다고 보고했습니다."
    )
    print("=" * 60)
    print("문제 발견: 신규 레코드 추가 로직이 작동하지 않았습니다!")
    print("=" * 60)

# 특정 케이스 280753 확인
test_case = "280753"
print(f"\n테스트 케이스 {test_case}:")
print(f"  Master에 있음: {test_case in master_cases}")
print(f"  Warehouse에 있음: {test_case in warehouse_cases}")

if test_case in master_cases and test_case not in warehouse_cases:
    print(f"  → 이 케이스는 신규로 추가되어야 했으나 추가되지 않았습니다!")

# 실제로 업데이트된 케이스 확인
print("\n=" * 60)
print("실제 변경사항 확인")
print("=" * 60)

# 공통 케이스 중 하나를 선택하여 값 비교
if len(common) > 0:
    test_common_case = list(common)[0]

    master_row = master[
        master["Case No."].astype(str).str.strip() == test_common_case
    ].iloc[0]
    warehouse_row = warehouse[
        warehouse["Case No."].astype(str).str.strip() == test_common_case
    ].iloc[0]

    print(f"\n공통 케이스 샘플: {test_common_case}")

    # 날짜 컬럼들 비교
    date_cols = ["MIR", "DSV Indoor", "DSV Outdoor", "ETD/ATD", "ETA/ATA"]

    changes_found = False
    for col in date_cols:
        if col in master.columns and col in warehouse.columns:
            master_val = master_row[col]
            warehouse_val = warehouse_row[col]

            # NaT 처리
            master_is_nat = pd.isna(master_val)
            warehouse_is_nat = pd.isna(warehouse_val)

            if not (master_is_nat and warehouse_is_nat):
                if master_is_nat != warehouse_is_nat or (
                    not master_is_nat and str(master_val) != str(warehouse_val)
                ):
                    print(f"  {col}:")
                    print(f"    Master:    {master_val}")
                    print(f"    Warehouse: {warehouse_val}")
                    changes_found = True

    if not changes_found:
        print("  이 케이스에서는 변경사항이 발견되지 않았습니다.")
        print("  → Master와 Warehouse의 데이터가 이미 동일한 상태일 수 있습니다.")

print("\n=" * 60)
print("결론")
print("=" * 60)
print("1. 신규 레코드 추가 기능이 작동하지 않음")
print(f"2. {len(only_in_master)}개의 케이스가 추가되어야 했으나 추가되지 않음")
print("3. 기존 레코드 업데이트는 정상 작동할 수 있음")
