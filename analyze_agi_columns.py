import pandas as pd

# 원본 파일 로드
df = pd.read_excel("Data/HVDC WAREHOUSE_HITACHI(HE).xlsx")

# 전체 컬럼 리스트
cols = list(df.columns)
print(f"전체 컬럼 수: {len(cols)}")

# AGI 컬럼 찾기
agi_idx = next((i for i, col in enumerate(cols) if "AGI" in str(col).upper()), None)

if agi_idx is not None:
    print(f"\n✅ AGI 컬럼 위치: {agi_idx+1}번째 ({cols[agi_idx]})")

    # AGI 이후 컬럼들
    after_agi = cols[agi_idx + 1 :]
    print(f"\n📊 AGI 이후 컬럼들 ({len(after_agi)}개):\n")

    for i, col in enumerate(after_agi, 1):
        non_null_count = df[col].notna().sum()
        total_count = len(df)
        percentage = (non_null_count / total_count * 100) if total_count > 0 else 0

        print(f"{i}. {col}")
        print(f"   - 데이터 타입: {df[col].dtype}")
        print(f"   - Non-null: {non_null_count}/{total_count} ({percentage:.1f}%)")

        # 샘플 값 출력
        non_null_values = df[col].dropna()
        if len(non_null_values) > 0:
            sample = non_null_values.iloc[0]
            print(f"   - 샘플 값: {sample}")

            # 고유값 개수 (범주형 데이터 확인)
            unique_count = df[col].nunique()
            if unique_count <= 20:
                print(f"   - 고유값 ({unique_count}개): {list(df[col].unique()[:10])}")
        else:
            print(f"   - 샘플 값: N/A (모두 null)")

        print()

    # 패턴 분석
    print("\n🔍 패턴 분석:")

    # 1. Status 관련 컬럼들
    status_cols = [col for col in after_agi if "Status" in col or "status" in col]
    if status_cols:
        print(f"\n✅ Status 관련 컬럼 ({len(status_cols)}개):")
        for col in status_cols:
            print(f"   - {col}")

    # 2. Handling 관련 컬럼들
    handling_cols = [col for col in after_agi if "handling" in col.lower()]
    if handling_cols:
        print(f"\n✅ Handling 관련 컬럼 ({len(handling_cols)}개):")
        for col in handling_cols:
            print(f"   - {col}")

    # 3. 기타 컬럼들
    other_cols = [
        col for col in after_agi if col not in status_cols and col not in handling_cols
    ]
    if other_cols:
        print(f"\n✅ 기타 컬럼 ({len(other_cols)}개):")
        for col in other_cols:
            print(f"   - {col}")
else:
    print("❌ AGI 컬럼을 찾을 수 없습니다.")

# 원본 파일 로드
df = pd.read_excel("Data/HVDC WAREHOUSE_HITACHI(HE).xlsx")

# 전체 컬럼 리스트
cols = list(df.columns)
print(f"전체 컬럼 수: {len(cols)}")

# AGI 컬럼 찾기
agi_idx = next((i for i, col in enumerate(cols) if "AGI" in str(col).upper()), None)

if agi_idx is not None:
    print(f"\n✅ AGI 컬럼 위치: {agi_idx+1}번째 ({cols[agi_idx]})")

    # AGI 이후 컬럼들
    after_agi = cols[agi_idx + 1 :]
    print(f"\n📊 AGI 이후 컬럼들 ({len(after_agi)}개):\n")

    for i, col in enumerate(after_agi, 1):
        non_null_count = df[col].notna().sum()
        total_count = len(df)
        percentage = (non_null_count / total_count * 100) if total_count > 0 else 0

        print(f"{i}. {col}")
        print(f"   - 데이터 타입: {df[col].dtype}")
        print(f"   - Non-null: {non_null_count}/{total_count} ({percentage:.1f}%)")

        # 샘플 값 출력
        non_null_values = df[col].dropna()
        if len(non_null_values) > 0:
            sample = non_null_values.iloc[0]
            print(f"   - 샘플 값: {sample}")

            # 고유값 개수 (범주형 데이터 확인)
            unique_count = df[col].nunique()
            if unique_count <= 20:
                print(f"   - 고유값 ({unique_count}개): {list(df[col].unique()[:10])}")
        else:
            print(f"   - 샘플 값: N/A (모두 null)")

        print()

    # 패턴 분석
    print("\n🔍 패턴 분석:")

    # 1. Status 관련 컬럼들
    status_cols = [col for col in after_agi if "Status" in col or "status" in col]
    if status_cols:
        print(f"\n✅ Status 관련 컬럼 ({len(status_cols)}개):")
        for col in status_cols:
            print(f"   - {col}")

    # 2. Handling 관련 컬럼들
    handling_cols = [col for col in after_agi if "handling" in col.lower()]
    if handling_cols:
        print(f"\n✅ Handling 관련 컬럼 ({len(handling_cols)}개):")
        for col in handling_cols:
            print(f"   - {col}")

    # 3. 기타 컬럼들
    other_cols = [
        col for col in after_agi if col not in status_cols and col not in handling_cols
    ]
    if other_cols:
        print(f"\n✅ 기타 컬럼 ({len(other_cols)}개):")
        for col in other_cols:
            print(f"   - {col}")
else:
    print("❌ AGI 컬럼을 찾을 수 없습니다.")
