# 📋 HVDC Excel Reporter 시스템 상세 분석 보고서 - Part 2

> **핵심 로직 및 알고리즘 상세 분석**
> **문서 버전:** v3.0-corrected Analysis Part 2
> **작성일:** 2025-10-18

---

## 📑 목차 (Part 2)

1. [데이터 로드 및 전처리](#1-데이터-로드-및-전처리)
2. [Flow Code 계산](#2-flow-code-계산)
3. [창고 입고 계산](#3-창고-입고-계산)
4. [창고간 이동 감지](#4-창고간-이동-감지)
5. [창고 출고 계산](#5-창고-출고-계산)
6. [재고 계산 및 검증](#6-재고-계산-및-검증)
7. [SQM 기반 면적 관리](#7-sqm-기반-면적-관리)
8. [Flow Traceability](#8-flow-traceability)

---

## 🔄 1. 데이터 로드 및 전처리

### 1.1 함수: `load_real_hvdc_data()`

**목적:** HITACHI와 SIMENSE 2개 벤더 데이터를 통합하고 누락된 창고 컬럼을 자동 보완

#### 입력 파라미터

```python
hitachi_path: str = "HVDC WAREHOUSE_HITACHI(HE).xlsx"
siemens_path: str = "HVDC WAREHOUSE_SIMENSE(SIM).xlsx"
```

#### 알고리즘 상세

##### Step 1: HITACHI 데이터 로드

```python
# 1-1. 파일 읽기
hitachi_data = pd.read_excel(hitachi_path, sheet_name=0)

# 1-2. 컬럼명 정규화 (공백 표준화)
hitachi_data.columns = hitachi_data.columns.str.replace(
    r"\s+", " ", regex=True
).str.strip()

# 1-3. 창고 컬럼 검증 및 보완
warehouse_columns = [
    "AAA Storage", "DSV Al Markaz", "DSV Indoor", "DSV MZP",
    "DSV Outdoor", "Hauler Indoor", "MOSB", "DHL Warehouse"
]

for warehouse in warehouse_columns:
    if warehouse not in hitachi_data.columns:
        print(f"⚠️  Warning: {warehouse} 컬럼이 HITACHI 데이터에 없습니다. NaT로 생성.")
        hitachi_data[warehouse] = pd.NaT
```

##### Step 2: SIMENSE 데이터 로드 (동일 프로세스)

```python
siemens_data = pd.read_excel(siemens_path, sheet_name=0)
siemens_data.columns = siemens_data.columns.str.replace(
    r"\s+", " ", regex=True
).str.strip()

for warehouse in warehouse_columns:
    if warehouse not in siemens_data.columns:
        siemens_data[warehouse] = pd.NaT
```

##### Step 3: 데이터 통합

```python
# 3-1. 수직 병합 (행 추가)
combined = pd.concat(
    [hitachi_data, siemens_data],
    ignore_index=True,  # 인덱스 재설정
    sort=False          # 컬럼 순서 유지
)

# 3-2. 통합 후 재검증
for warehouse in warehouse_columns:
    if warehouse not in combined.columns:
        print(f"❌ Critical: {warehouse} 컬럼이 통합 데이터에 없습니다.")
        combined[warehouse] = pd.NaT
```

##### Step 4: 검증 및 로깅

```python
print("\n📊 창고 컬럼별 데이터 존재 여부:")
for warehouse in warehouse_columns:
    non_null_count = combined[warehouse].notna().sum()
    print(f"  {warehouse}: {non_null_count}건")

print(f"\n✅ 총 {len(combined)}건의 레코드가 로드되었습니다.")
```

#### 출력

```python
return combined  # pd.DataFrame
```

#### 핵심 포인트

1. **정규화 패턴:** `r"\s+"` → 모든 공백(스페이스, 탭, 줄바꿈)을 단일 스페이스로 통일
2. **Fail-safe:** 누락 컬럼은 자동으로 `pd.NaT` 생성하여 크래시 방지
3. **원본 보존:** `handling` 등 추가 컬럼은 그대로 유지

---

## 🔢 2. Flow Code 계산

### 2.1 함수: `_override_flow_code(df: pd.DataFrame)`

**목적:** 물류 경로를 0~4 단계로 분류 (Off-by-One 버그 수정 버전)

#### Flow Code 정의 (재확인)

```yaml
0: Pre Arrival
   - Status_Location에 "Pre Arrival" 포함
   - 아직 항구 도착 전

1: Port → Site (직송)
   - 창고 경유 없음
   - Offshore(MOSB) 경유 없음

2: Port → WH → Site
   - 창고 1회 경유
   - MOSB 미경유

3: Port → WH → MOSB → Site
   - 창고 1회 + Offshore 경유

4: Port → WH → WH → MOSB → Site
   - 창고 2회 이상 + Offshore 경유
```

#### 알고리즘 상세

##### Step 1: 데이터 정제

```python
# 1-1. 0값과 빈 문자열을 NaN으로 변환
for col in warehouse_columns + ["MOSB"]:
    if col in df.columns:
        df[col] = df[col].replace([0, "", " "], pd.NaT)
```

**이유:** `notna()` 함수가 0과 빈 문자열을 True로 인식하는 것을 방지

##### Step 2: Pre Arrival 명시적 판별

```python
# 2-1. Status_Location 컬럼에서 "Pre Arrival" 문자열 검색
is_pre_arrival = df["Status_Location"].str.contains(
    "Pre Arrival",
    case=False,  # 대소문자 무시
    na=False     # NaN은 False로 처리
)

print(f"📍 Pre Arrival 케이스: {is_pre_arrival.sum()}건")
```

##### Step 3: 창고 Hop 수 계산

```python
# 3-1. 8개 창고 컬럼에서 non-null 값 개수 세기
WH_COLS = [
    "AAA Storage", "DSV Al Markaz", "DSV Indoor", "DSV MZP",
    "DSV Outdoor", "Hauler Indoor", "DHL Warehouse"
]

wh_cnt = df[WH_COLS].notna().sum(axis=1)  # 행별 합계

# 3-2. 분포 확인
print(f"창고 Hop 분포: {wh_cnt.value_counts().to_dict()}")
# 예시: {0: 150, 1: 1200, 2: 400, 3: 50}
```

##### Step 4: Offshore(MOSB) 통과 여부

```python
# 4-1. MOSB 컬럼이 존재하고 non-null이면 1, 아니면 0
MOSB_COLS = ["MOSB"]

offshore = df[MOSB_COLS].notna().any(axis=1).astype(int)

print(f"MOSB 통과 케이스: {offshore.sum()}건")
```

##### Step 5: Flow Code 계산 (Off-by-One 수정)

```python
# 5-1. 기본 스텝 계산
base_step = 1  # Port → Site는 기본 1스텝

# 5-2. 총 스텝 = 창고 Hop + Offshore + 기본 스텝
flow_raw = wh_cnt + offshore + base_step

# 5-3. Pre Arrival은 0, 나머지는 1~4로 클리핑
FLOW_CODE = np.where(
    is_pre_arrival,
    0,  # Pre Arrival 명시
    np.clip(flow_raw, 1, 4)  # 1~4 범위로 제한
)

# 5-4. 데이터프레임에 추가
df["FLOW_CODE"] = FLOW_CODE
```

#### 검증 로직

```python
# Flow Code 분포 출력
flow_distribution = df["FLOW_CODE"].value_counts().sort_index()
print("\n📊 Flow Code 분포:")
for code, count in flow_distribution.items():
    description = {
        0: "Pre Arrival",
        1: "Port→Site (직송)",
        2: "Port→WH→Site",
        3: "Port→WH→MOSB→Site",
        4: "Port→WH→WH→MOSB→Site"
    }
    print(f"  Code {code}: {count}건 - {description.get(code, 'Unknown')}")
```

#### 출력 예시

```
📍 Pre Arrival 케이스: 45건
창고 Hop 분포: {0: 150, 1: 1200, 2: 400, 3: 50}
MOSB 통과 케이스: 320건

📊 Flow Code 분포:
  Code 0: 45건 - Pre Arrival
  Code 1: 150건 - Port→Site (직송)
  Code 2: 880건 - Port→WH→Site
  Code 3: 320건 - Port→WH→MOSB→Site
  Code 4: 405건 - Port→WH→WH→MOSB→Site
```

#### 핵심 수정 사항 (v3.0-corrected)

**이전 버전 (Off-by-One 버그):**
```python
# ❌ 버그: base_step=0이면 직송(0 Hop)이 Code 0이 됨
flow_raw = wh_cnt + offshore  # 0~N
```

**수정 버전 (v3.0-corrected):**
```python
# ✅ 수정: base_step=1로 직송이 Code 1이 되도록 보장
base_step = 1
flow_raw = wh_cnt + offshore + base_step  # 1~N+1
```

---

## 📥 3. 창고 입고 계산

### 3.1 함수: `calculate_warehouse_inbound_corrected()`

**목적:** 순수 외부 입고만 계산 (창고간 이동 제외)

#### 핵심 원칙

```yaml
Rule 1: 창고 컬럼만 입고로 계산
  - 8개 창고: AAA Storage, DSV Al Markaz, DSV Indoor, ...
  - 현장(AGI, DAS, MIR, SHU)은 제외

Rule 2: 창고간 이동의 목적지는 입고 제외
  - 예: DSV Indoor → DSV Al Markaz 이동이 있으면
  - DSV Al Markaz는 입고로 계산 안 함 (이중 계산 방지)

Rule 3: PKG 수량 정확히 반영
  - Pkg 컬럼이 없거나 0이면 기본값 1
```

#### 알고리즘 상세

##### Step 1: 창고간 이동 먼저 감지

```python
inbound_items = []
total_inbound = 0
by_warehouse = {wh: 0 for wh in warehouse_columns}
by_month = {}

for idx, row in df.iterrows():
    # 1-1. 창고간 이동 리스트 가져오기
    transfers = self._detect_warehouse_transfers(row)

    # 1-2. 이동 목적지 창고 추출
    transfer_destinations = [t["to_warehouse"] for t in transfers]
```

##### Step 2: 창고 입고 계산 (현장 제외)

```python
    # 2-1. 8개 창고만 순회
    for warehouse in warehouse_columns:
        if pd.notna(row[warehouse]):
            # 2-2. 날짜 파싱
            arrival_date = pd.to_datetime(row[warehouse])

            # 2-3. PKG 수량 추출
            pkg_quantity = self._get_pkg_quantity(row)

            # 2-4. 창고간 이동의 목적지인지 확인
            is_transfer_destination = warehouse in transfer_destinations

            # 2-5. 순수 입고만 계산
            if not is_transfer_destination:
                month_key = arrival_date.strftime("%Y-%m")

                # 집계
                total_inbound += pkg_quantity
                by_warehouse[warehouse] += pkg_quantity

                if month_key not in by_month:
                    by_month[month_key] = 0
                by_month[month_key] += pkg_quantity

                # 상세 기록
                inbound_items.append({
                    "Item_ID": idx,
                    "Warehouse": warehouse,
                    "Inbound_Date": arrival_date,
                    "Year_Month": month_key,
                    "Pkg_Quantity": pkg_quantity,
                    "Inbound_Type": "external_arrival"
                })
```

#### 헬퍼 함수: `_get_pkg_quantity(row)`

```python
def _get_pkg_quantity(self, row) -> int:
    """PKG 수량 추출 (안전한 변환)"""
    pkg_value = row.get("Pkg", 1)

    # Null/빈값/0 처리
    if pd.isna(pkg_value) or pkg_value == "" or pkg_value == 0:
        return 1

    # 정수 변환 시도
    try:
        return int(pkg_value)
    except (ValueError, TypeError):
        print(f"⚠️  Warning: PKG 값 '{pkg_value}'를 정수로 변환 불가. 기본값 1 사용.")
        return 1
```

#### 반환값 구조

```python
return {
    "total_inbound": total_inbound,          # int: 총 입고 PKG
    "by_warehouse": by_warehouse,            # dict: {warehouse: pkg_count}
    "by_month": by_month,                    # dict: {year-month: pkg_count}
    "inbound_items": inbound_items,          # list: 상세 입고 기록
    "warehouse_transfers": transfers_with_ym # list: 창고간 이동 기록
}
```

#### 출력 예시

```python
{
    "total_inbound": 1850,
    "by_warehouse": {
        "AAA Storage": 120,
        "DSV Al Markaz": 650,
        "DSV Indoor": 480,
        ...
    },
    "by_month": {
        "2024-08": 320,
        "2024-09": 540,
        "2024-10": 990
    },
    "inbound_items": [
        {
            "Item_ID": 42,
            "Warehouse": "DSV Al Markaz",
            "Inbound_Date": Timestamp('2024-09-15'),
            "Year_Month": "2024-09",
            "Pkg_Quantity": 12,
            "Inbound_Type": "external_arrival"
        },
        ...
    ]
}
```

---

## 🔄 4. 창고간 이동 감지

### 4.1 함수: `_detect_warehouse_transfers(row)`

**목적:** 동일 날짜 창고간 이동을 감지하고 논리적으로 검증

#### 주요 이동 패턴

```python
warehouse_pairs = [
    ("DSV Indoor", "DSV Al Markaz"),      # 실내 → 메인 창고
    ("DSV Indoor", "DSV Outdoor"),        # 실내 → 실외
    ("DSV Al Markaz", "DSV Outdoor"),     # 메인 → 실외
    ("AAA Storage", "DSV Al Markaz"),     # 외부 → 메인
    ("AAA Storage", "DSV Indoor"),        # 외부 → 실내
    ("DSV Indoor", "MOSB"),               # 실내 → Offshore
    ("DSV Al Markaz", "MOSB"),            # 메인 → Offshore
]
```

#### 알고리즘 상세

##### Step 1: 날짜 추출 및 동일 날짜 감지

```python
transfers = []

for from_wh, to_wh in warehouse_pairs:
    # 1-1. 출발 창고 날짜
    from_date = pd.to_datetime(row.get(from_wh))

    # 1-2. 도착 창고 날짜
    to_date = pd.to_datetime(row.get(to_wh))

    # 1-3. 둘 다 존재하고 동일 날짜인 경우
    if pd.notna(from_date) and pd.notna(to_date):
        if from_date.date() == to_date.date():
            # 동일 날짜 이동 후보 발견
            pass  # Step 2로 진행
```

##### Step 2: 논리적 검증

```python
            # 2-1. 위치 우선순위 기반 검증
            if self._validate_transfer_logic(from_wh, to_wh, from_date, to_date):
                pkg_quantity = self._get_pkg_quantity(row)

                # 2-2. 이동 기록 추가
                transfers.append({
                    "from_warehouse": from_wh,
                    "to_warehouse": to_wh,
                    "transfer_date": from_date,
                    "pkg_quantity": pkg_quantity,
                    "transfer_type": "warehouse_to_warehouse",
                    "Year_Month": from_date.strftime("%Y-%m")
                })
```

#### 검증 로직: `_validate_transfer_logic()`

```python
def _validate_transfer_logic(
    self,
    from_wh: str,
    to_wh: str,
    from_date: pd.Timestamp,
    to_date: pd.Timestamp
) -> bool:
    """창고간 이동의 논리적 타당성 검증"""

    # 위치 우선순위 맵
    location_priority = {
        "DSV Al Markaz": 1,   # 최우선
        "DSV Indoor": 2,
        "DSV Outdoor": 3,
        "AAA Storage": 4,
        "Hauler Indoor": 5,
        "DSV MZP": 6,
        "MOSB": 7,
        "DHL Warehouse": 8
    }

    from_priority = location_priority.get(from_wh, 99)
    to_priority = location_priority.get(to_wh, 99)

    # Rule 1: 일반적으로 낮은 우선순위 → 높은 우선순위로 이동
    if from_priority > to_priority:
        return True

    # Rule 2: 특별한 경우 (실제 운영 패턴)
    special_cases = [
        ("DSV Indoor", "DSV Al Markaz"),   # 실내 → 메인 (통합)
        ("AAA Storage", "DSV Al Markaz"),  # 외부 → 메인 (입고)
        ("DSV Outdoor", "MOSB"),           # 실외 → Offshore (선적)
    ]

    if (from_wh, to_wh) in special_cases:
        return True

    # Rule 3: MOSB는 최종 단계이므로 항상 허용
    if to_wh == "MOSB":
        return True

    return False
```

#### 반환값

```python
return transfers  # list of dicts
```

#### 출력 예시

```python
[
    {
        "from_warehouse": "DSV Indoor",
        "to_warehouse": "DSV Al Markaz",
        "transfer_date": Timestamp('2024-09-15'),
        "pkg_quantity": 12,
        "transfer_type": "warehouse_to_warehouse",
        "Year_Month": "2024-09"
    },
    {
        "from_warehouse": "DSV Al Markaz",
        "to_warehouse": "MOSB",
        "transfer_date": Timestamp('2024-10-01'),
        "pkg_quantity": 12,
        "transfer_type": "warehouse_to_warehouse",
        "Year_Month": "2024-10"
    }
]
```

---

## 📤 5. 창고 출고 계산

### 5.1 함수: `calculate_warehouse_outbound_corrected()`

**목적:** 실제 물리적 이동만 출고로 계산 (동일 날짜 제외)

#### 핵심 원칙

```yaml
Rule 1: 다음 날 이동만 출고로 인정
  - 창고 날짜 < 다음 위치 날짜 (>로 비교, ≥ 아님)
  - 동일 날짜는 창고간 이동으로 분류

Rule 2: 창고간 이동과 창고→현장 이동 구분
  - 창고간 이동: _detect_warehouse_transfers()로 감지
  - 창고→현장: 다음 현장 날짜를 찾아 출고로 계산

Rule 3: 중복 출고 방지
  - 이미 출고된 창고는 현장 출고 계산 제외
  - 가장 빠른 현장 이동 1건만 출고로 인정
```

#### 알고리즘 상세

##### Step 1: 창고간 이동 출고 처리

```python
outbound_items = []
total_outbound = 0
by_warehouse = {wh: 0 for wh in warehouse_columns}
by_month = {}

for idx, row in df.iterrows():
    # 1-1. 창고간 이동 감지
    transfers = self._detect_warehouse_transfers(row)

    # 1-2. 각 이동을 출고로 기록
    for transfer in transfers:
        from_wh = transfer["from_warehouse"]
        transfer_date = transfer["transfer_date"]
        pkg_quantity = transfer["pkg_quantity"]
        month_key = transfer_date.strftime("%Y-%m")

        # 집계
        total_outbound += pkg_quantity
        by_warehouse[from_wh] += pkg_quantity

        if month_key not in by_month:
            by_month[month_key] = 0
        by_month[month_key] += pkg_quantity

        # 상세 기록
        outbound_items.append({
            "Item_ID": idx,
            "From_Location": from_wh,
            "To_Location": transfer["to_warehouse"],
            "Outbound_Date": transfer_date,
            "Year_Month": month_key,
            "Pkg_Quantity": pkg_quantity,
            "Outbound_Type": "warehouse_transfer"
        })
```

##### Step 2: 창고→현장 출고 처리

```python
    # 2-1. 이미 출고된 창고 목록
    transferred_from_warehouses = [t["from_warehouse"] for t in transfers]

    # 2-2. 각 창고별로 순회
    for warehouse in warehouse_columns:
        # ✅ 중복 출고 방지
        if warehouse in transferred_from_warehouses:
            continue  # 이미 창고간 이동으로 출고됨

        # 2-3. 창고 날짜 확인
        if pd.notna(row[warehouse]):
            warehouse_date = pd.to_datetime(row[warehouse])

            # 2-4. 다음 현장 이동 찾기
            next_site_movements = []
            for site in site_columns:
                if pd.notna(row[site]):
                    site_date = pd.to_datetime(row[site])

                    # ✅ 다음 날 이동만 출고로 인정
                    if site_date > warehouse_date:  # 동일 날짜 제외
                        next_site_movements.append((site, site_date))

            # 2-5. 가장 빠른 현장 이동을 출고로 계산
            if next_site_movements:
                next_site, next_date = min(
                    next_site_movements,
                    key=lambda x: x[1]
                )

                pkg_quantity = self._get_pkg_quantity(row)
                month_key = next_date.strftime("%Y-%m")

                # 집계
                total_outbound += pkg_quantity
                by_warehouse[warehouse] += pkg_quantity

                if month_key not in by_month:
                    by_month[month_key] = 0
                by_month[month_key] += pkg_quantity

                # 상세 기록
                outbound_items.append({
                    "Item_ID": idx,
                    "From_Location": warehouse,
                    "To_Location": next_site,
                    "Outbound_Date": next_date,
                    "Year_Month": month_key,
                    "Pkg_Quantity": pkg_quantity,
                    "Outbound_Type": "warehouse_to_site"
                })

                # ✅ 중복 출고 방지를 위해 break
                break
```

#### 반환값 구조

```python
return {
    "total_outbound": total_outbound,      # int
    "by_warehouse": by_warehouse,          # dict
    "by_month": by_month,                  # dict
    "outbound_items": outbound_items       # list
}
```

---

계속해서 Part 2의 나머지 내용을 작성합니다...

**다음 섹션:**
- 6. 재고 계산 및 검증
- 7. SQM 기반 면적 관리
- 8. Flow Traceability

문서가 계속됩니다... *(Part 2는 총 8개 섹션으로 구성)*

