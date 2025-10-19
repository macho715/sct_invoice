diff --git a/pipe1/post_agi_column_processor.py b/pipe1/post_agi_column_processor.py
index cbcdc0474de8c43dfa4a02ad112e2c36d87a1de5..911ded37fc22d9d4ed8ee9421dc897a83acd3e5d 100644
--- a/pipe1/post_agi_column_processor.py
+++ b/pipe1/post_agi_column_processor.py
@@ -1,176 +1,258 @@
 """
 Post-AGI 컬럼 처리기 (Post-AGI Column Processor)

 AGI 컬럼 이후 13개 컬럼을 자동으로 계산하는 최적화된 스크립트입니다.
 Excel 공식을 Python pandas 벡터화 연산으로 변환하여 고성능 처리를 제공합니다.

 주요 기능:
 - AGI 이후 13개 컬럼 자동 계산
 - 벡터화 연산으로 고성능 처리 (10배 속도 향상)
 - 원본 컬럼명 보존 (site  handling - 공백 2개)
 - 색상 보존 전략 지원

 작성자: AI Development Team
 버전: v1.0
 작성일: 2025-10-18
 """

-import pandas as pd
-from pathlib import Path
-
-from .agi_columns import (
-    DERIVED_COLUMNS,
-    FINAL_HANDLING_COLUMN,
-    MINUS_COLUMN,
-    SITE_COLUMNS,
-    SITE_HANDLING_COLUMN,
-    SQM_COLUMN,
-    STACK_STATUS_COLUMN,
-    STATUS_CURRENT_COLUMN,
-    STATUS_LOCATION_COLUMN,
-    STATUS_LOCATION_DATE_COLUMN,
-    STATUS_SITE_COLUMN,
-    STATUS_STORAGE_COLUMN,
-    STATUS_WAREHOUSE_COLUMN,
-    TOTAL_HANDLING_COLUMN,
-    WH_HANDLING_COLUMN,
-    WAREHOUSE_COLUMNS,
-)
-
-
-def process_post_agi_columns(
-    input_file: str = "HVDC WAREHOUSE_HITACHI(HE).synced.xlsx",
-) -> bool:
-    """
-    AGI 이후 13개 컬럼을 처리하는 메인 함수
-
-    Args:
-        input_file (str): 입력 Excel 파일 경로
-
-    Returns:
-        bool: 처리 성공 여부
-
-    Raises:
-        FileNotFoundError: 입력 파일이 존재하지 않는 경우
-        KeyError: 필수 컬럼이 없는 경우
-    """
-    print("=== Post-AGI 컬럼 처리 시작 ===")
-    print(f"입력 파일: {input_file}")
-
-    # 파일 존재 확인
-    if not Path(input_file).exists():
-        raise FileNotFoundError(f"입력 파일을 찾을 수 없습니다: {input_file}")
+from __future__ import annotations

-    # 데이터 로드
-    df = pd.read_excel(input_file)
-    print(f"원본 데이터 로드 완료: {len(df)}행, {len(df.columns)}컬럼")
-
-    # 컬럼 정의
-    # 실제 존재하는 컬럼만 필터링
-    wh_cols = [c for c in WAREHOUSE_COLUMNS if c in df.columns]
-    st_cols = [c for c in SITE_COLUMNS if c in df.columns]
-
-    print(f"Warehouse 컬럼: {len(wh_cols)}개 - {wh_cols}")
-    print(f"Site 컬럼: {len(st_cols)}개 - {st_cols}")
-
-    # 1. Status_WAREHOUSE: 창고 데이터 존재 여부
-    # Excel: =IF(COUNT($AF2:$AN2)>0, 1, "")
-    df[STATUS_WAREHOUSE_COLUMN] = (
-        (df[wh_cols].notna().sum(axis=1) > 0).astype(int).replace(0, "")
-    )
+from pathlib import Path
+from typing import Iterable, Tuple
+
+import pandas as pd  # type: ignore[import-untyped]
+
+from .agi_columns import (DERIVED_COLUMNS, FINAL_HANDLING_COLUMN, MINUS_COLUMN,
+                          SITE_COLUMNS, SITE_HANDLING_COLUMN, SQM_COLUMN,
+                          STACK_STATUS_COLUMN, STATUS_CURRENT_COLUMN,
+                          STATUS_LOCATION_COLUMN, STATUS_LOCATION_DATE_COLUMN,
+                          STATUS_SITE_COLUMN, STATUS_STORAGE_COLUMN,
+                          STATUS_WAREHOUSE_COLUMN, TOTAL_HANDLING_COLUMN,
+                          WAREHOUSE_COLUMNS, WH_HANDLING_COLUMN)
+
+SITE_COLUMN_LOOKUP = {col.lower() for col in SITE_COLUMNS}
+WAREHOUSE_COLUMN_LOOKUP = {col.lower() for col in WAREHOUSE_COLUMNS}
+
+
+def _latest_location_and_date(
+    row: pd.Series,
+) -> Tuple[str | None, pd.Timestamp | pd.NaT]:
+    """최근 위치와 날짜를 계산합니다. / Compute the latest location and date."""
+    non_null = row.dropna()
+    if non_null.empty:
+        return None, pd.NaT
+    latest_date = non_null.max()
+    latest_columns = non_null[non_null == latest_date].index
+    return latest_columns[0], latest_date
+
+
+def _classify_storage(location: str | None) -> str:
+    """위치 기반 보관 유형을 분류합니다. / Classify storage based on location."""
+    if location is None or location == "":
+        return ""
+    if location == "Pre Arrival":
+        return "Pre Arrival"
+    lowered = location.lower()
+    if lowered in SITE_COLUMN_LOOKUP:
+        return "site"
+    if lowered in WAREHOUSE_COLUMN_LOOKUP:
+        return "warehouse"
+    return ""
+
+
+def _to_datetime_columns(df: pd.DataFrame, columns: Iterable[str]) -> None:
+    """지정된 컬럼을 datetime으로 변환합니다. / Cast selected columns to datetime."""
+    for column in columns:
+        df[column] = pd.to_datetime(df[column], errors="coerce")
+
+
+def apply_post_agi_calculations(df: pd.DataFrame) -> pd.DataFrame:
+    """Post-AGI 컬럼을 계산합니다. / Compute Post-AGI derived columns."""
+    working_df = df.copy()
+
+    wh_cols = [c for c in WAREHOUSE_COLUMNS if c in working_df.columns]
+    st_cols = [c for c in SITE_COLUMNS if c in working_df.columns]
+
+    _to_datetime_columns(working_df, wh_cols + st_cols)
+
+    if wh_cols:
+        warehouse_presence = working_df[wh_cols].notna().sum(axis=1) > 0
+        warehouse_presence = warehouse_presence.astype(int)
+        working_df[STATUS_WAREHOUSE_COLUMN] = warehouse_presence.replace(0, "")
+    else:
+        working_df[STATUS_WAREHOUSE_COLUMN] = ""

-    # 2. Status_SITE: 현장 데이터 존재 여부
-    # Excel: =IF(COUNT($AO2:$AR2)>0, 1, "")
-    df[STATUS_SITE_COLUMN] = (
-        (df[st_cols].notna().sum(axis=1) > 0).astype(int).replace(0, "")
-    )
+    if st_cols:
+        site_presence = working_df[st_cols].notna().sum(axis=1) > 0
+        site_presence = site_presence.astype(int)
+        working_df[STATUS_SITE_COLUMN] = site_presence.replace(0, "")
+    else:
+        working_df[STATUS_SITE_COLUMN] = ""

-    # 3. Status_Current: 현재 상태 판별
-    # Excel: =IF($AT2=1, "site", IF($AS2=1, "warehouse", "Pre Arrival"))
-    df[STATUS_CURRENT_COLUMN] = df.apply(
+    working_df[STATUS_CURRENT_COLUMN] = working_df.apply(
         lambda row: (
             "site"
             if row[STATUS_SITE_COLUMN] == 1
             else (
                 "warehouse"
                 if row[STATUS_WAREHOUSE_COLUMN] == 1
                 else "Pre Arrival"
             )
         ),
         axis=1,
     )

-    # 4. Status_Location: 최신 위치 (단순화 - 실제로는 복잡한 INDEX/MATCH 로직)
-    df[STATUS_LOCATION_COLUMN] = "Pre Arrival"
+    if st_cols:
+        site_latest = working_df[st_cols].apply(
+            _latest_location_and_date,
+            axis=1,
+            result_type="expand",
+        )
+    else:
+        site_latest = pd.DataFrame(index=working_df.index, columns=[0, 1])
+
+    if wh_cols:
+        warehouse_latest = working_df[wh_cols].apply(
+            _latest_location_and_date,
+            axis=1,
+            result_type="expand",
+        )
+    else:
+        warehouse_latest = pd.DataFrame(index=working_df.index, columns=[0, 1])
+
+    if not site_latest.empty:
+        site_latest.columns = ["location", "date"]
+    if not warehouse_latest.empty:
+        warehouse_latest.columns = ["location", "date"]
+
+    location_series = pd.Series("Pre Arrival", index=working_df.index)
+    location_date_series = pd.Series(
+        pd.NaT,
+        index=working_df.index,
+        dtype="datetime64[ns]",
+    )

-    # 5. Status_Location_Date: 최신 날짜 (단순화)
-    df[STATUS_LOCATION_DATE_COLUMN] = ""
+    site_mask = working_df[STATUS_CURRENT_COLUMN] == "site"
+    warehouse_mask = working_df[STATUS_CURRENT_COLUMN] == "warehouse"
+
+    if not site_latest.empty:
+        site_locations = site_latest.loc[site_mask, "location"]
+        site_locations = site_locations.fillna("Pre Arrival")
+        location_series.loc[site_mask] = site_locations
+        site_dates = site_latest.loc[site_mask, "date"]
+        location_date_series.loc[site_mask] = site_dates
+
+    if not warehouse_latest.empty:
+        warehouse_locations = warehouse_latest.loc[
+            warehouse_mask,
+            "location",
+        ]
+        warehouse_locations = warehouse_locations.fillna("Pre Arrival")
+        location_series.loc[warehouse_mask] = warehouse_locations
+        location_date_series.loc[warehouse_mask] = warehouse_latest.loc[
+            warehouse_mask,
+            "date",
+        ]
+
+    location_filled = location_series.replace({None: "Pre Arrival"})
+    working_df[STATUS_LOCATION_COLUMN] = location_filled
+    working_df[STATUS_LOCATION_DATE_COLUMN] = location_date_series
+
+    storage_series = location_series.apply(_classify_storage)
+    unresolved_storage_mask = storage_series == ""
+    storage_series.loc[unresolved_storage_mask] = working_df.loc[
+        unresolved_storage_mask,
+        STATUS_CURRENT_COLUMN,
+    ]
+    working_df[STATUS_STORAGE_COLUMN] = storage_series
+
+    if wh_cols:
+        warehouse_handling = working_df[wh_cols].notna().sum(axis=1)
+        working_df[WH_HANDLING_COLUMN] = warehouse_handling
+    else:
+        working_df[WH_HANDLING_COLUMN] = 0

-    # 6. Status_Storage: 창고/현장 분류
-    df[STATUS_STORAGE_COLUMN] = df[STATUS_CURRENT_COLUMN]
+    if st_cols:
+        site_handling = working_df[st_cols].notna().sum(axis=1)
+        working_df[SITE_HANDLING_COLUMN] = site_handling
+    else:
+        working_df[SITE_HANDLING_COLUMN] = 0
+    working_df[TOTAL_HANDLING_COLUMN] = (
+        working_df[WH_HANDLING_COLUMN] + working_df[SITE_HANDLING_COLUMN]
+    )
+    working_df[MINUS_COLUMN] = (
+        working_df[SITE_HANDLING_COLUMN] - working_df[WH_HANDLING_COLUMN]
+    )
+    working_df[FINAL_HANDLING_COLUMN] = (
+        working_df[TOTAL_HANDLING_COLUMN] + working_df[MINUS_COLUMN]
+    )

-    # 7. wh handling: 창고 핸들링 횟수
-    # Excel: =SUMPRODUCT(--ISNUMBER(AF2:AN2))
-    df[WH_HANDLING_COLUMN] = df[wh_cols].notna().sum(axis=1)
+    if "규격" in working_df.columns and "수량" in working_df.columns:
+        working_df[SQM_COLUMN] = (working_df["규격"] * working_df["수량"]) / 10000
+    else:
+        working_df[SQM_COLUMN] = ""
+        print("⚠️ '규격' 또는 '수량' 컬럼이 없어 SQM 계산을 건너뜁니다.")
+
+    working_df[STACK_STATUS_COLUMN] = ""
+
+    return working_df

-    # 8. site  handling: 현장 핸들링 횟수 (공백 2개 - 원본 컬럼명 보존)
-    # Excel: =SUMPRODUCT(--ISNUMBER(AO2:AR2))
-    df[SITE_HANDLING_COLUMN] = df[st_cols].notna().sum(axis=1)

-    # 9. total handling: 총 핸들링
-    # Excel: =AY2+AZ2
-    df[TOTAL_HANDLING_COLUMN] = df[WH_HANDLING_COLUMN] + df[SITE_HANDLING_COLUMN]
+def process_post_agi_columns(
+    input_file: str = "HVDC WAREHOUSE_HITACHI(HE).synced.xlsx",
+) -> bool:
+    """AGI 이후 컬럼을 계산합니다. / Process post-AGI columns."""
+    print("=== Post-AGI 컬럼 처리 시작 ===")
+    print(f"입력 파일: {input_file}")
+
+    # 파일 존재 확인
+    if not Path(input_file).exists():
+        raise FileNotFoundError(f"입력 파일을 찾을 수 없습니다: {input_file}")

-    # 10. minus: 현장-창고 차이
-    # Excel: =AZ2-AY2
-    df[MINUS_COLUMN] = df[SITE_HANDLING_COLUMN] - df[WH_HANDLING_COLUMN]
+    # 데이터 로드
+    df = pd.read_excel(input_file)
+    print(f"원본 데이터 로드 완료: {len(df)}행, {len(df.columns)}컬럼")

-    # 11. final handling: 최종 핸들링
-    # Excel: =BA2+BB2
-    df[FINAL_HANDLING_COLUMN] = df[TOTAL_HANDLING_COLUMN] + df[MINUS_COLUMN]
+    df = apply_post_agi_calculations(df)

-    # 12. SQM: 면적 계산
-    # Excel: =O2*P2/10000
-    if "규격" in df.columns and "수량" in df.columns:
-        df[SQM_COLUMN] = (df["규격"] * df["수량"]) / 10000
-    else:
-        df[SQM_COLUMN] = ""
-        print("⚠️ '규격' 또는 '수량' 컬럼이 없어 SQM 계산을 건너뜁니다.")
+    wh_cols = [c for c in WAREHOUSE_COLUMNS if c in df.columns]
+    st_cols = [c for c in SITE_COLUMNS if c in df.columns]

-    # 13. Stack_Status: 적재 상태 (현재 빈 값)
-    df[STACK_STATUS_COLUMN] = ""
+    print(f"Warehouse 컬럼: {len(wh_cols)}개 - {wh_cols}")
+    print(f"Site 컬럼: {len(st_cols)}개 - {st_cols}")

     print(
-        f"✅ Post-AGI 컬럼 {len(DERIVED_COLUMNS)}개 계산 완료 (행: {len(df)}, 컬럼: {len(df.columns)})"
+        "✅ Post-AGI 컬럼 %s개 계산 완료 (행: %s, 컬럼: %s)"
+        % (len(DERIVED_COLUMNS), len(df), len(df.columns))
     )

     # 결과 저장
     output_file = "HVDC WAREHOUSE_HITACHI(HE).xlsx"
     df.to_excel(output_file, index=False)
     print(f"✅ 파일 저장 완료: {output_file}")

     return True


-def main():
-    """메인 실행 함수"""
+def main() -> int:
+    """메인 실행을 수행합니다. / Execute script entry point."""
     try:
         success = process_post_agi_columns()
         if success:
             print("\n" + "=" * 60)
             print("✅ Post-AGI 컬럼 처리 완료!")
             print("📁 결과 파일: HVDC WAREHOUSE_HITACHI(HE).xlsx")
             print("💡 색상은 Step 1에서 이미 적용되었습니다.")
             print("=" * 60)
         else:
             print("❌ 처리 실패")
             return 1
     except Exception as e:
         print(f"❌ 오류 발생: {e}")
         return 1

     return 0


 if __name__ == "__main__":
     exit(main())
diff --git a/tests/test_post_agi_column_processor.py b/tests/test_post_agi_column_processor.py
new file mode 100644
index 0000000000000000000000000000000000000000..d094d4bab7d32d4f1a34f7c4d99dfc8a876d861f
--- /dev/null
+++ b/tests/test_post_agi_column_processor.py
@@ -0,0 +1,73 @@
+# isort: skip_file
+
+import sys
+from pathlib import Path
+
+sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
+
+import pandas as pd  # type: ignore[import-untyped]  # noqa: E402
+
+from pipe1.agi_columns import SITE_COLUMNS  # noqa: E402
+from pipe1.agi_columns import (STATUS_CURRENT_COLUMN,  # noqa: E402
+                               STATUS_LOCATION_COLUMN,
+                               STATUS_LOCATION_DATE_COLUMN, STATUS_SITE_COLUMN,
+                               STATUS_STORAGE_COLUMN, STATUS_WAREHOUSE_COLUMN)
+from pipe1.post_agi_column_processor import \
+    apply_post_agi_calculations  # noqa: E402
+
+
+def test_apply_post_agi_calculations_latest_location_and_storage() -> None:
+    """최신 위치와 보관 분류를 확인합니다. / Validate latest location and storage."""
+    data = {
+        "DHL Warehouse": ["2024-01-01", None, None],
+        "DSV Indoor": [None, "2024-01-05", None],
+        "MIR": [None, None, None],
+        "SHU": ["2024-02-01", None, None],
+        "AGI": [None, None, None],
+        "DAS": [None, None, None],
+        "규격": [1, 1, 1],
+        "수량": [1, 1, 1],
+    }
+    df = pd.DataFrame(data)
+
+    result = apply_post_agi_calculations(df)
+
+    assert list(result[STATUS_SITE_COLUMN]) == [1, "", ""]
+    assert list(result[STATUS_WAREHOUSE_COLUMN]) == [1, 1, ""]
+
+    assert result.loc[0, STATUS_CURRENT_COLUMN] == "site"
+    assert result.loc[0, STATUS_LOCATION_COLUMN] == SITE_COLUMNS[1]
+    assert result.loc[0, STATUS_LOCATION_DATE_COLUMN] == pd.Timestamp(
+        "2024-02-01"
+    )
+    assert result.loc[0, STATUS_STORAGE_COLUMN] == "site"
+
+    assert result.loc[1, STATUS_CURRENT_COLUMN] == "warehouse"
+    assert result.loc[1, STATUS_LOCATION_COLUMN] == "DSV Indoor"
+    assert result.loc[1, STATUS_LOCATION_DATE_COLUMN] == pd.Timestamp(
+        "2024-01-05"
+    )
+    assert result.loc[1, STATUS_STORAGE_COLUMN] == "warehouse"
+
+    assert result.loc[2, STATUS_CURRENT_COLUMN] == "Pre Arrival"
+    assert result.loc[2, STATUS_LOCATION_COLUMN] == "Pre Arrival"
+    assert pd.isna(result.loc[2, STATUS_LOCATION_DATE_COLUMN])
+    assert result.loc[2, STATUS_STORAGE_COLUMN] == "Pre Arrival"
+
+    latest_date_series = result[STATUS_LOCATION_DATE_COLUMN]
+    assert pd.api.types.is_datetime64_any_dtype(latest_date_series)
+
+
+def test_apply_post_agi_calculations_without_movement_columns() -> None:
+    """현장·창고 부재 기본값을 확인합니다. / Validate defaults without movement columns."""
+    data = {"규격": [2], "수량": [5]}
+    df = pd.DataFrame(data)
+
+    result = apply_post_agi_calculations(df)
+
+    assert result.loc[0, STATUS_WAREHOUSE_COLUMN] == ""
+    assert result.loc[0, STATUS_SITE_COLUMN] == ""
+    assert result.loc[0, STATUS_CURRENT_COLUMN] == "Pre Arrival"
+    assert result.loc[0, STATUS_LOCATION_COLUMN] == "Pre Arrival"
+    assert pd.isna(result.loc[0, STATUS_LOCATION_DATE_COLUMN])
+    assert result.loc[0, STATUS_STORAGE_COLUMN] == "Pre Arrival"
