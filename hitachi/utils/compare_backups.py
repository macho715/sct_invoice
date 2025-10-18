#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
백업 파일과 현재 파일 비교
"""

import pandas as pd
import os
from pathlib import Path

# 현재 파일
current_file = "HVDC WAREHOUSE_HITACHI(HE).xlsx"

# 백업 파일들
backup_dir = Path("backups")
backup_files = sorted(backup_dir.glob("HVDC WAREHOUSE_HITACHI(HE)_backup_*.xlsx"))

print("=" * 60)
print("백업 파일 목록")
print("=" * 60)
for i, bf in enumerate(backup_files, 1):
    stat = bf.stat()
    print(f"{i}. {bf.name}")
    print(f"   크기: {stat.st_size:,} bytes")
    print(f"   수정 시간: {pd.Timestamp.fromtimestamp(stat.st_mtime)}")
    print()

if len(backup_files) >= 2:
    print("=" * 60)
    print("최신 2개 백업 파일과 현재 파일 비교")
    print("=" * 60)

    # 최신 백업
    latest_backup = backup_files[-1]
    previous_backup = backup_files[-2] if len(backup_files) >= 2 else None

    # 파일 로드
    current_df = pd.read_excel(current_file, sheet_name="Case List")
    latest_backup_df = pd.read_excel(latest_backup, sheet_name="Case List")

    print(f"\n현재 파일: {len(current_df)} rows")
    print(f"최신 백업: {len(latest_backup_df)} rows")

    if previous_backup:
        previous_backup_df = pd.read_excel(previous_backup, sheet_name="Case List")
        print(f"이전 백업: {len(previous_backup_df)} rows")

        # 날짜 컬럼 샘플 비교
        date_col = "MIR"
        if date_col in current_df.columns:
            test_case = "280753"

            print(f"\n케이스 {test_case}의 {date_col} 값 변화:")
            print(
                f"  이전 백업: {previous_backup_df[previous_backup_df['Case No.'] == test_case][date_col].values[0] if len(previous_backup_df[previous_backup_df['Case No.'] == test_case]) > 0 else 'Not found'}"
            )
            print(
                f"  최신 백업: {latest_backup_df[latest_backup_df['Case No.'] == test_case][date_col].values[0] if len(latest_backup_df[latest_backup_df['Case No.'] == test_case]) > 0 else 'Not found'}"
            )
            print(
                f"  현재 파일: {current_df[current_df['Case No.'] == test_case][date_col].values[0] if len(current_df[current_df['Case No.'] == test_case]) > 0 else 'Not found'}"
            )

    # 실제 차이 계산
    print("\n=" * 60)
    print("현재 파일 vs 최신 백업 비교")
    print("=" * 60)

    # 동일성 체크
    if current_df.equals(latest_backup_df):
        print("⚠️  현재 파일과 최신 백업이 완전히 동일합니다!")
        print("     → 마지막 실행 후 파일이 저장되지 않았거나")
        print("     → 변경사항이 없었을 가능성이 있습니다.")
    else:
        print("✅ 현재 파일과 최신 백업 간 차이가 있습니다.")

        # 몇 개 셀이 다른지 확인
        diff_count = 0
        for col in current_df.columns:
            if col in latest_backup_df.columns:
                try:
                    diff_mask = current_df[col] != latest_backup_df[col]
                    diff_count += diff_mask.sum()
                except:
                    pass

        print(f"   변경된 셀 수: 약 {diff_count}개")
