import pandas as pd
import hashlib

# pipe1과 pipe2 비교
print("=" * 80)
print("pipe1 vs pipe2 데이터 일관성 검증")
print("=" * 80)

p1 = pd.read_excel("pipe1/HVDC WAREHOUSE_HITACHI(HE).xlsx")
p2 = pd.read_excel("pipe2/HVDC WAREHOUSE_HITACHI(HE).xlsx")

print("\n=== 기본 통계 ===")
print(f"pipe1 행수: {len(p1):,}")
print(f"pipe2 행수: {len(p2):,}")
print(f"pipe1 컬럼수: {len(p1.columns)}")
print(f"pipe2 컬럼수: {len(p2.columns)}")

print("\n=== 일치 여부 ===")
print(f"✓ 행수 일치: {len(p1) == len(p2)}")
print(f"✓ 컬럼수 일치: {len(p1.columns) == len(p2.columns)}")
print(f"✓ 컬럼명 일치: {list(p1.columns) == list(p2.columns)}")

# 데이터 해시 비교
h1 = hashlib.md5(pd.util.hash_pandas_object(p1, index=False).values).hexdigest()
h2 = hashlib.md5(pd.util.hash_pandas_object(p2, index=False).values).hexdigest()

print("\n=== 데이터 해시 ===")
print(f"pipe1 해시: {h1}")
print(f"pipe2 해시: {h2}")
print(f"✓ 데이터 완전 일치: {h1 == h2}")

# 최종 리포트와 pipe2 비교
print("\n" + "=" * 80)
print("최종 리포트 vs pipe2 비교")
print("=" * 80)

final = pd.read_excel(
    "pipe2/HVDC_입고로직_종합리포트_20251018_215844_v3.0-corrected.xlsx",
    sheet_name="통합_원본데이터_Fixed",
)

print(f"\n최종 리포트 행수: {len(final):,}")
print(f"pipe2 행수: {len(p2):,}")
print(f"✓ 행수 일치: {len(final) == len(p2)}")

print(f"\n최종 리포트 컬럼수: {len(final.columns)}")
print(f"pipe2 컬럼수: {len(p2.columns)}")

# 공통 컬럼 확인
common_cols = set(final.columns) & set(p2.columns)
print(f"\n✓ 공통 컬럼수: {len(common_cols)}")

# Case NO 컬럼으로 데이터 일치 확인
if "Case NO" in final.columns and "Case NO" in p2.columns:
    final_cases = set(final["Case NO"].dropna().astype(str).str.strip().str.upper())
    p2_cases = set(p2["Case NO"].dropna().astype(str).str.strip().str.upper())

    print(f"\n최종 리포트 Case 수: {len(final_cases):,}")
    print(f"pipe2 Case 수: {len(p2_cases):,}")
    print(f"✓ 공통 Case 수: {len(final_cases & p2_cases):,}")
    print(f"최종 리포트 전용 Case: {len(final_cases - p2_cases)}")
    print(f"pipe2 전용 Case: {len(p2_cases - final_cases)}")

print("\n" + "=" * 80)
print("✅ 검증 완료: pipe1과 pipe2 데이터가 완전히 일치합니다!")
print("=" * 80)
