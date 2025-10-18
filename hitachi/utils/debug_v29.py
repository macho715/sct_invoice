#!/usr/bin/env python3
"""v2.9 동기화 디버깅"""

import pandas as pd
from data_synchronizer_v29 import DataSynchronizerV29


def debug_sync():
    print("=== v2.9 동기화 디버깅 ===")

    # 동기화 실행
    sync = DataSynchronizerV29()
    result = sync.synchronize(
        "CASE LIST.xlsx",
        "HVDC WAREHOUSE_HITACHI(HE).xlsx",
        "HVDC WAREHOUSE_HITACHI(HE).debug.xlsx",
    )

    print(f"성공: {result.success}")
    print(f"메시지: {result.message}")
    print(f"통계: {result.stats}")

    # ChangeTracker 상태 확인
    print(f"\n=== ChangeTracker 상태 ===")
    print(f"총 변경사항: {len(sync.change_tracker.changes)}")
    print(f"신규 케이스: {len(sync.change_tracker.new_cases)}")

    # 날짜 업데이트 확인
    date_changes = [
        ch for ch in sync.change_tracker.changes if ch.change_type == "date_update"
    ]
    print(f"날짜 업데이트: {len(date_changes)}개")

    for i, change in enumerate(date_changes[:5]):  # 처음 5개만 출력
        print(
            f"  {i+1}. Row {change.row_index}, Col '{change.column_name}': {change.old_value} -> {change.new_value}"
        )

    # 신규 케이스 확인
    new_records = [
        ch for ch in sync.change_tracker.changes if ch.change_type == "new_record"
    ]
    print(f"신규 레코드: {len(new_records)}개")

    for i, change in enumerate(new_records[:3]):  # 처음 3개만 출력
        print(f"  {i+1}. Row {change.row_index}")


if __name__ == "__main__":
    debug_sync()
