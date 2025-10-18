# 날짜 업데이트 및 색상 표시 문제 해결 보고서

**작성일**: 2025-10-18
**버전**: v2.9
**상태**: ✅ 완료

---

## 📋 개요

HVDC 데이터 동기화 시스템에서 날짜 컬럼 인식 실패 및 색상 표시 문제를 해결하여, Master 파일의 날짜 데이터가 정상적으로 업데이트되고 변경사항이 시각적으로 표시되도록 개선했습니다.

---

## 🔍 문제 분석

### 문제 1: 날짜 컬럼 인식 실패

**원인**:
- 기존 `header_matcher.py`의 `date_keywords` 목록에 특정 창고명 누락
- DAS, SHU, MIR, AGI, Hauler Indoor, DSV MZP 등이 날짜 컬럼으로 인식되지 않음

**영향**:
- 총 15개 날짜 컬럼 중 일부만 인식
- 날짜 업데이트가 제대로 작동하지 않음

### 문제 2: CASE NO 컬럼 매칭 실패

**원인**:
- `header_matcher.find_column()`의 패턴 매칭 로직 문제
- `case_no` 패턴이 `["case", "no"]`로 설정되어 있어 정규화 후 매칭 실패

**영향**:
- `case_to_row` 매핑 생성 실패
- 색상이 잘못된 행에 적용됨

### 문제 3: pd.NaT 처리 오류

**원인**:
- `_dates_equal()` 메서드에서 `pd.NaT` 객체의 `normalize()` 호출 시 오류

**영향**:
- 동기화 프로세스 중단

---

## ✅ 해결 방법

### 해결책: v2.9 기반 새로운 동기화 시스템 구축

더 간단하고 명확한 구조의 새로운 시스템을 구축하여 모든 문제를 해결했습니다.

#### 1. 날짜 컬럼 명시적 정의

**파일**: `data_synchronizer_v29.py` (라인 26-42)

```python
DATE_KEYS = [
    "ETD/ATD",
    "ETA/ATA",
    "DHL Warehouse",
    "DSV Indoor",
    "DSV Al Markaz",
    "DSV Outdoor",
    "AAA  Storage",
    "Hauler Indoor",
    "DSV MZP",
    "MOSB",
    "Shifting",
    "MIR",
    "SHU",
    "DAS",
    "AGI",
]
```

#### 2. 정규화 기반 날짜 컬럼 판정

**파일**: `data_synchronizer_v29.py` (라인 36-41)

```python
def _is_date_col(col_name: str) -> bool:
    def norm(s: str) -> str:
        # 대소문자/공백/슬래시/하이픈 차이 제거
        return re.sub(r"[^a-z0-9]", "", str(s).strip().lower())

    cn = norm(col_name)
    return any(norm(k) == cn for k in DATE_KEYS)
```

**효과**:
- "ETD/ATD", "ETD / ATD", "etd-atd" 모두 동일하게 인식
- 공백/대소문자/슬래시 차이 무시

#### 3. pd.NaT 처리 개선

**파일**: `data_synchronizer_v29.py` (라인 109-119)

```python
def _dates_equal(self, a, b) -> bool:
    da = _to_date(a)
    db = _to_date(b)
    if da is None and db is None:
        return True
    if da is None or db is None:
        return False
    # Handle pd.NaT
    if pd.isna(da) or pd.isna(db):
        return pd.isna(da) and pd.isna(db)
    return da.normalize() == db.normalize()
```

#### 4. 내장 ExcelFormatter

**파일**: `data_synchronizer_v29.py` (라인 231-290)

ExcelFormatter를 내장하여 import 문제 해결:
- 날짜 변경 셀: 주황색(FFC000)
- 신규 케이스 행: 노란색(FFFF00)

---

## 📊 구현 결과

### 최종 실행 결과

```bash
python data_synchronizer_v29.py \
  --master "CASE LIST.xlsx" \
  --warehouse "HVDC WAREHOUSE_HITACHI(HE).xlsx" \
  --out "HVDC WAREHOUSE_HITACHI(HE).synced.xlsx"
```

**출력**:
```
success: True
message: Sync & colorize done.
stats: {
    'updates': 42620,
    'date_updates': 1247,
    'field_updates': 41373,
    'appends': 258,
    'output_file': 'HVDC WAREHOUSE_HITACHI(HE).synced.xlsx'
}
```

### 상세 통계

| 항목 | 수량 | 설명 |
|------|------|------|
| **총 업데이트** | 42,620 | 전체 셀 업데이트 수 |
| **날짜 업데이트** | 1,247 | 날짜 컬럼 업데이트 (주황색) |
| **필드 업데이트** | 41,373 | 일반 필드 업데이트 |
| **신규 케이스** | 258 | 새로 추가된 케이스 (노란색) |

### 색상 적용 결과

#### 1. 주황색(FFC000) - 날짜 변경
- **적용 셀 수**: 1,247개
- **적용 컬럼**: ETD/ATD, ETA/ATA, DHL Warehouse, DSV Indoor, DSV Al Markaz, DSV Outdoor, AAA Storage, Hauler Indoor, DSV MZP, MOSB, Shifting, MIR, SHU, DAS, AGI
- **예시**:
  - Row 61, Col 43 (DAS): 2025-07-08
  - Row 221-239, Col 43 (DAS): 2024-01-01
  - 기타 다수 행에서 날짜 변경 감지

#### 2. 노란색(FFFF00) - 신규 케이스
- **적용 행 수**: 258개 행
- **케이스 범위**: Case 5390 ~ Case 5834
- **적용 위치**: Row 5554 ~ Row 5811
- **전체 행 하이라이트**: 모든 열에 노란색 적용

---

## 🎯 구현된 기능

### 1. Master 우선 원칙
- Master 파일에 값이 있으면 **항상** Warehouse에 기록
- 날짜 컬럼: Master 값이 있으면 무조건 업데이트
- 일반 컬럼: Master에 non-null 값이 있으면 덮어쓰기

### 2. 스마트 날짜 인식
- **15개 날짜 컬럼 자동 인식**:
  - 선적 관련: ETD/ATD, ETA/ATA
  - 창고 관련: DHL Warehouse, DSV Indoor, DSV Al Markaz, DSV Outdoor, AAA Storage
  - 운송 관련: Hauler Indoor, DSV MZP
  - 현장 관련: MOSB, Shifting, MIR, SHU, DAS, AGI

### 3. 정규화 매칭
- 공백/대소문자/슬래시/하이픈 차이 자동 처리
- 예: "ETD/ATD" = "ETD / ATD" = "etd-atd" = "ETDATD"

### 4. 시각적 변경사항 표시
- **주황색(FFC000)**: 날짜가 실제로 변경된 셀
- **노란색(FFFF00)**: 신규로 추가된 케이스 행 전체

### 5. 유연한 CASE NO 매칭
- 정규표현식 기반 CASE NO 컬럼 자동 인식
- 대소문자/공백 무시
- "Case No.", "case_no", "CASE", "SKU" 모두 인식

---

## 📁 파일 구조

```
hitachi/
├── data_synchronizer_v29.py       # 메인 동기화 엔진 (v2.9)
├── CASE LIST.xlsx                 # Master 파일 (입력)
├── HVDC WAREHOUSE_HITACHI(HE).xlsx # Warehouse 파일 (입력)
├── HVDC WAREHOUSE_HITACHI(HE).synced.xlsx # 결과 파일 (출력)
├── debug_v29.py                   # 디버깅 스크립트
├── check_date_colors.py           # 색상 검증 스크립트
├── check_synced_colors.py         # 동기화 결과 검증
└── docs/
    └── DATE_UPDATE_COLOR_FIX_REPORT.md # 본 문서
```

---

## 🔧 사용 방법

### 기본 실행

```bash
cd hitachi
python data_synchronizer_v29.py \
  --master "CASE LIST.xlsx" \
  --warehouse "HVDC WAREHOUSE_HITACHI(HE).xlsx" \
  --out "HVDC WAREHOUSE_HITACHI(HE).synced.xlsx"
```

### 출력 파일 기본값

출력 파일을 지정하지 않으면 자동으로 `{원본파일명}.synced.xlsx`로 저장:

```bash
python data_synchronizer_v29.py \
  --master "CASE LIST.xlsx" \
  --warehouse "HVDC WAREHOUSE_HITACHI(HE).xlsx"
# 출력: HVDC WAREHOUSE_HITACHI(HE).synced.xlsx
```

### 결과 검증

```bash
# 색상 적용 확인
python check_date_colors.py

# 전체 결과 확인
python check_synced_colors.py

# 디버깅 정보 확인
python debug_v29.py
```

---

## 📈 성능 개선

### 이전 시스템 대비

| 항목 | 이전 | v2.9 | 개선 |
|------|------|------|------|
| 날짜 컬럼 인식 | 부분 인식 | 15개 전체 인식 | ✅ 100% |
| 색상 표시 | 실패 | 정상 작동 | ✅ 완료 |
| 신규 케이스 추가 | 0개 | 258개 | ✅ 정상 |
| 날짜 업데이트 | 6개 | 1,247개 | ✅ 208배 증가 |
| 전체 업데이트 | 9,188개 | 42,620개 | ✅ 4.6배 증가 |

### 코드 품질

- **간결성**: 300줄 이하의 단일 파일
- **독립성**: 외부 의존성 최소화 (내장 ExcelFormatter)
- **명확성**: 명시적 DATE_KEYS 정의
- **안정성**: pd.NaT, None, NaN 모두 처리

---

## ⚠️ 주의사항

### 1. FutureWarning

실행 시 pandas FutureWarning이 표시될 수 있습니다:
```
FutureWarning: Setting an item of incompatible dtype is deprecated
```

**영향**: 없음 (정상 작동, 향후 pandas 버전에서 수정 예정)

### 2. 데이터 백업

원본 파일은 수정되지 않으며, 새 파일(`.synced.xlsx`)이 생성됩니다.

### 3. Excel 파일 열림 상태

실행 중 Excel 파일이 열려 있으면 저장 실패할 수 있습니다. 실행 전 파일을 닫아주세요.

---

## 🔄 향후 개선 사항

### 단기 (1주일)
- [ ] FutureWarning 해결 (pandas dtype 명시)
- [ ] 백업 파일 자동 생성 옵션
- [ ] 로그 파일 출력

### 중기 (1개월)
- [ ] GUI 인터페이스 추가
- [ ] 배치 처리 기능
- [ ] 변경사항 요약 리포트 자동 생성

### 장기 (3개월)
- [ ] 웹 기반 대시보드
- [ ] 실시간 동기화 모니터링
- [ ] 다중 파일 동시 처리

---

## 📞 문의

문제 발생 시:
1. `debug_v29.py` 실행하여 상세 로그 확인
2. `check_date_colors.py`로 색상 적용 상태 확인
3. 출력 파일의 통계 정보 확인

---

## ✨ 결론

v2.9 시스템을 통해:
- ✅ 날짜 컬럼 15개 전체 인식
- ✅ 1,247개 날짜 업데이트 및 주황색 표시
- ✅ 258개 신규 케이스 추가 및 노란색 표시
- ✅ 총 42,620개 셀 업데이트 성공
- ✅ Master 우선 원칙 100% 준수

**모든 요구사항이 성공적으로 구현되었습니다.**

---

*보고서 작성: 2025-10-18*
*최종 검증: PASSED ✅*

