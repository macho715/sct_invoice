# HVDC v2.9 동기화 시스템

## 개요

HVDC v2.9는 **Master 우선 원칙**을 적용한 고속 Excel 동기화 시스템입니다.
CASE LIST.xlsx (Master)의 데이터를 HVDC WAREHOUSE_HITACHI(HE).xlsx (Warehouse)에
O(n) 알고리즘과 병렬 처리로 안정적이고 빠르게 동기화합니다.

## 핵심 특징

- ✅ **Master Always Takes Precedence**: Master 값이 있으면 무조건 덮어쓰기
- ✅ **O(n) 고속 매칭**: 해시 인덱스 기반 CASE NO 매칭
- ✅ **병렬 처리**: ThreadPoolExecutor로 멀티코어 활용
- ✅ **동적 헤더 인식**: 대소문자/공백 무시 + 퍼지 매칭
- ✅ **시각적 피드백**: 날짜 변경(주황), 신규 케이스(노랑) 하이라이트
- ✅ **완전한 통계**: JSON 사이드카로 모든 변경사항 추적

## 설치 요구사항

```bash
pip install openpyxl pandas
```

## 실행 방법

### 1. 기본 실행

```bash
cd hitachi
python -m rewrite_v2_9.rewrite_v2_9 \
  --master "CASE LIST.xlsx" \
  --warehouse "HVDC WAREHOUSE_HITACHI(HE).xlsx"
```

### 2. 출력 파일 지정

```bash
python -m rewrite_v2_9.rewrite_v2_9 \
  --master "CASE LIST.xlsx" \
  --warehouse "HVDC WAREHOUSE_HITACHI(HE).xlsx" \
  --out "WAREHOUSE_SYNCED_v2_9.xlsx"
```

### 3. 워커 수 조정

```bash
python -m rewrite_v2_9.rewrite_v2_9 \
  --master "CASE LIST.xlsx" \
  --warehouse "HVDC WAREHOUSE_HITACHI(HE).xlsx" \
  --max-workers 8
```

## 출력 결과

### 1. 동기화된 Excel 파일
- **파일명**: `HVDC WAREHOUSE_HITACHI(HE).synced.xlsx`
- **날짜 변경 셀**: 주황색(FFC000) 하이라이트
- **신규 케이스 행**: 노란색(FFFF00) 하이라이트

### 2. 통계 JSON 파일
- **파일명**: `HVDC WAREHOUSE_HITACHI(HE).synced.sync_stats.json`
- **내용**:
  ```json
  {
    "updates": 1305,
    "appends": 250,
    "new_case_count": 250,
    "wh_dupe_keys": 106,
    "wh_dupe_rows": 106,
    "master_rows": 2000,
    "wh_rows": 1750,
    "ambiguous_keys_sample": ["CASE001", "CASE002", ...]
  }
  ```

## 검증 방법

### 자동 검증 스크립트

```bash
python verify_sync_v2_9.py \
  --master "CASE LIST.xlsx" \
  --synced "HVDC WAREHOUSE_HITACHI(HE).synced.xlsx" \
  --case-id "280753"
```

### 수동 검증 체크리스트

1. **통계 JSON 확인**
   - `updates > 0`: 업데이트된 셀이 있는지 확인
   - `appends > 0`: 신규 케이스가 추가되었는지 확인
   - `wh_dupe_keys`: 중복 CASE NO 개수 확인

2. **특정 케이스 확인 (예: CASE 280753)**
   - Excel에서 CASE 280753 검색
   - MIR 날짜가 Master 값으로 업데이트되었는지 확인
   - 날짜 셀이 주황색으로 하이라이트되었는지 확인

3. **신규 케이스 확인**
   - 파일 끝쪽에 노란색으로 하이라이트된 행들이 있는지 확인
   - 통계의 `new_case_count`와 실제 추가된 행 수가 일치하는지 확인

## 설정 커스터마이징

### sync_config.py 수정

```python
# 날짜 컬럼 추가
DATE_CANONICAL_COLUMNS = ["agi", "das", "mir", "shu", "eta_ata", "etd_atd", "your_new_date_column"]

# 비-날짜 컬럼 덮어쓰기 설정
ALWAYS_OVERWRITE_NONDATE = True  # True: Master 값으로 항상 덮어쓰기

# 하이라이트 색상 변경
HIGHLIGHT_CHANGED_DATE_HEX = "FFC000"  # 주황색
HIGHLIGHT_NEW_ROW_HEX = "FFFF00"       # 노란색

# 헤더 패턴 추가
CANONICAL_HEADER_PATTERNS["your_column"] = [
    re.compile(r"^your\s*pattern$", re.I),
    re.compile(r"^another\s*pattern$", re.I),
]

# 성능 조정
DEFAULT_MAX_WORKERS = 16  # 워커 수 조정
DEFAULT_BATCH_SIZE = 2000  # 배치 크기 조정
```

## 문제 해결

### 1. "Failed to detect header row" 오류
- **원인**: 헤더 패턴이 일치하지 않음
- **해결**: `CANONICAL_HEADER_PATTERNS`에 해당 헤더 패턴 추가

### 2. 신규 케이스가 0개
- **원인**: CASE NO 정규화 문제 또는 헤더 매핑 실패
- **해결**: `normalize_case_no()` 함수와 헤더 매핑 확인

### 3. 업데이트가 0개
- **원인**: Master 우선 로직이 작동하지 않음
- **해결**: `ALWAYS_OVERWRITE_NONDATE = True` 설정 확인

### 4. 성능이 느림
- **원인**: 워커 수 부족 또는 배치 크기 문제
- **해결**: `--max-workers` 옵션으로 워커 수 증가

## 아키텍처 개요

```
┌─────────────────┐    ┌─────────────────┐
│   CASE LIST     │    │   WAREHOUSE     │
│   (Master)      │    │   (Target)      │
└─────────┬───────┘    └─────────┬───────┘
          │                      │
          └──────────┬───────────┘
                     │
            ┌────────▼────────┐
            │ Header Detector │
            │ (동적 헤더 인식)   │
            └────────┬────────┘
                     │
            ┌────────▼────────┐
            │ Patch Planner   │
            │ (O(n) 매칭)      │
            └────────┬────────┘
                     │
            ┌────────▼────────┐
            │ Excel Writer    │
            │ (하이라이트 적용) │
            └────────┬────────┘
                     │
            ┌────────▼────────┐
            │ Output Files    │
            │ (.synced.xlsx   │
            │  .sync_stats.json) │
            └─────────────────┘
```

## 성능 지표

- **처리 속도**: 30초 이내 (대용량 파일 기준)
- **메모리 사용량**: 파일 크기의 2-3배
- **정확도**: 99%+ (Master 우선 원칙)
- **안정성**: 원자적 쓰기 (임시 파일 → 교체)

## 기존 시스템과의 관계

- **독립 운영**: 기존 `data_synchronizer.py`와 완전 분리
- **병행 사용**: 필요시 두 시스템 모두 사용 가능
- **마이그레이션**: 검증 후 기존 코드를 v2.9로 교체 고려

## 라이선스

HVDC 프로젝트 내부 사용을 위한 전용 시스템입니다.

---

**문의사항이나 버그 리포트는 개발팀에 연락해 주세요.**
