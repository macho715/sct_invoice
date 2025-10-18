#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
업데이트 검증 스크립트
"""

import pandas as pd
import numpy as np

# 파일 로드
print("Loading files...")
master = pd.read_excel("CASE LIST.xlsx")
warehouse = pd.read_excel("HVDC WAREHOUSE_HITACHI(HE).xlsx", sheet_name="Case List")

print("\n" + "=" * 60)
print("파일 기본 정보")
print("=" * 60)
print(f"Master 행 수: {len(master)}")
print(f"Warehouse 행 수: {len(warehouse)}")

print("\n" + "=" * 60)
print("CASE NO 컬럼 분석")
print("=" * 60)
print(f"\nMaster 'Case No.' 샘플 (처음 10개):")
print(master["Case No."].head(10).tolist())
print(f"타입: {master['Case No.'].dtype}")

print(f"\nWarehouse 'Case No.' 샘플 (처음 10개):")
print(warehouse["Case No."].head(10).tolist())
print(f"타입: {warehouse['Case No.'].dtype}")

# 특정 케이스 확인
test_case = 280753
print(f"\n" + "=" * 60)
print(f"테스트 케이스: {test_case}")
print("=" * 60)

# Master에서 찾기
master_match = master[master["Case No."] == test_case]
print(f"\nMaster에서 '{test_case}' 찾기:")
if len(master_match) > 0:
    print("발견됨!")
    if "MIR" in master.columns:
        print(f"MIR 값: {master_match['MIR'].values[0]}")
else:
    print("발견되지 않음")
    # 문자열로 시도
    master_match_str = master[master["Case No."].astype(str) == str(test_case)]
    if len(master_match_str) > 0:
        print(f"문자열로 발견됨!")

# Warehouse에서 찾기
warehouse_match = warehouse[warehouse["Case No."] == test_case]
print(f"\nWarehouse에서 '{test_case}' 찾기:")
if len(warehouse_match) > 0:
    print("발견됨!")
    if "MIR" in warehouse.columns:
        print(f"MIR 값: {warehouse_match['MIR'].values[0]}")
else:
    print("발견되지 않음")
    # 문자열로 시도
    warehouse_match_str = warehouse[warehouse["Case No."].astype(str) == str(test_case)]
    if len(warehouse_match_str) > 0:
        print(f"문자열로 발견됨!")
        if "MIR" in warehouse.columns:
            print(f"MIR 값: {warehouse_match_str['MIR'].values[0]}")

print("\n" + "=" * 60)
print("날짜 컬럼 확인")
print("=" * 60)

# 날짜 관련 컬럼 찾기
date_keywords = [
    "MIR",
    "DSV",
    "DHL",
    "MOSB",
    "SHU",
    "DAS",
    "AGI",
    "ETD",
    "ETA",
    "Outdoor",
    "Indoor",
    "Markaz",
]
master_date_cols = [
    col
    for col in master.columns
    if any(kw.lower() in col.lower() for kw in date_keywords)
]
warehouse_date_cols = [
    col
    for col in warehouse.columns
    if any(kw.lower() in col.lower() for kw in date_keywords)
]

print(f"\nMaster 날짜 관련 컬럼 ({len(master_date_cols)}개):")
print(master_date_cols[:10])

print(f"\nWarehouse 날짜 관련 컬럼 ({len(warehouse_date_cols)}개):")
print(warehouse_date_cols[:10])

# 샘플 케이스의 날짜 값 비교
if len(master) > 0 and len(warehouse) > 0:
    print("\n" + "=" * 60)
    print("첫 번째 케이스의 날짜 필드 비교")
    print("=" * 60)

    first_master_case = master["Case No."].iloc[0]
    print(f"\n첫 번째 Master Case: {first_master_case}")

    # Master의 첫 번째 케이스 날짜 값
    if len(master_date_cols) > 0:
        print("\nMaster 날짜 값:")
        for col in master_date_cols[:5]:
            val = master[col].iloc[0]
            print(f"  {col}: {val} (type: {type(val).__name__})")

    # Warehouse에서 같은 케이스 찾기
    warehouse_same = warehouse[warehouse["Case No."] == first_master_case]
    if len(warehouse_same) == 0:
        warehouse_same = warehouse[
            warehouse["Case No."].astype(str) == str(first_master_case)
        ]

    if len(warehouse_same) > 0:
        print("\nWarehouse 같은 케이스 날짜 값:")
        for col in warehouse_date_cols[:5]:
            if col in warehouse.columns:
                val = warehouse_same[col].iloc[0]
                print(f"  {col}: {val} (type: {type(val).__name__})")
    else:
        print(f"\nWarehouse에서 케이스 '{first_master_case}'를 찾을 수 없음")

print("\n" + "=" * 60)
print("분석 완료")
print("=" * 60)
