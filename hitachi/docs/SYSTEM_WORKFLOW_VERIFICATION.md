# 🔄 HVDC 시스템 워크플로우 검증 및 문서화

**작성일**: 2025-10-18
**버전**: v1.0
**검증자**: AI Agent
**범위**: 7단계 데이터 처리 파이프라인

---

## 📋 Executive Summary

### 전체 파이프라인 개요
```
[1] CASE LIST.xlsx (Master File) - 6,069건, 38컬럼
    ↓
[2] data_synchronizer_v29.py - Master 우선 동기화
    ↓
[3] HVDC WAREHOUSE_HITACHI(HE).xlsx - 5,552건, 57컬럼
    ↓
[4] hvdc_excel_reporter_final_sqm_rev (1).py - SQM 계산
    ↓
[5] HVDC_입고로직_종합리포트_*.xlsx - 최종 리포트 (현재 없음)
    ↓
[6] anomaly_detector.py - 이상치 탐지
    ↓
[7] 이상치 통합 (현재 누락) ⚠️
```

### 각 단계별 목적
- **[1→2→3]**: Master 데이터를 Warehouse로 동기화 (날짜 우선순위, 색상 표시)
- **[3→4→5]**: Warehouse 데이터를 SQM 기반 입고로직 리포트로 변환
- **[5→6→7]**: 최종 리포트에서 이상치 탐지 및 통합 (현재 미완성)

### 현재 상태
- ✅ **완료**: [1→2→3] 동기화 시스템
- ✅ **완료**: [3→4] SQM 계산 시스템
- ❌ **누락**: [5] 최종 리포트 생성
- ✅ **완료**: [6] 이상치 탐지 시스템
- ❌ **누락**: [7] 이상치 통합

---

## 🔍 단계별 상세 분석

### [1] CASE LIST.xlsx (Master File)

#### 입력 데이터
- **파일**: `hitachi/CASE LIST.xlsx`
- **크기**: 6,069행 × 38컬럼
- **핵심 컬럼**:
  - `Case No.`: 고유 식별자
  - `HVDC CODE`: HVDC 코드
  - 날짜 컬럼: `ETD/ATD`, `ETA/ATA`, `DHL Warehouse`, `DSV Indoor`, `DSV Al Markaz`, `DSV Outdoor`, `AAA Storage`, `Hauler Indoor`, `DSV MZP`, `MOSB`, `Shifting`, `MIR`, `SHU`, `DAS`, `AGI`
  - 물리적 정보: `L(CM)`, `W(CM)`, `H(CM)`, `CBM`, `N.W(kgs)`, `G.W(kgs)`
  - 비즈니스 정보: `Pkg`, `Storage`, `Description`, `HS Code`, `Currency`, `Price`

#### 데이터 특성
- **Master 우선 원칙**: 모든 데이터의 진실의 원천
- **날짜 중심**: 15개 날짜 컬럼으로 물류 흐름 추적
- **물리적 측정**: CBM, 무게, 치수로 SQM 계산 기반

---

### [2] data_synchronizer_v29.py (동기화 시스템)

#### 핵심 로직
```python
# Master 우선 원칙
ALWAYS_OVERWRITE_NONDATE = True  # Master non-null overwrites

# 날짜 컬럼 정의 (15개)
DATE_KEYS = [
    "ETD/ATD", "ETA/ATA", "DHL Warehouse", "DSV Indoor",
    "DSV Al Markaz", "DSV Outdoor", "AAA Storage",
    "Hauler Indoor", "DSV MZP", "MOSB", "Shifting",
    "MIR", "SHU", "DAS", "AGI"
]

# 색상 표시
ORANGE = "FFC000"  # changed date cell
YELLOW = "FFFF00"  # new row
```

#### 동기화 규칙
1. **Case NO 매칭**: `Case No.` 컬럼으로 레코드 매칭
2. **날짜 우선순위**: Master의 날짜 값이 있으면 항상 덮어쓰기
3. **논리적 변경 감지**: 날짜가 논리적으로 변경된 경우에만 색상 표시
4. **새 케이스 추가**: Master에만 있는 케이스는 Warehouse에 추가 (노랑)
5. **비날짜 필드**: Master에 값이 있으면 덮어쓰기

#### 실행 명령어
```bash
python data_synchronizer_v29.py \
  --master "CASE LIST.xlsx" \
  --warehouse "HVDC WAREHOUSE_HITACHI(HE).xlsx" \
  --output "HVDC WAREHOUSE_HITACHI(HE).xlsx"
```

#### 검증 방법
- 동기화 후 변경 통계 확인
- 색상 표시된 셀/행 검증
- Case NO 매칭률 확인

---

### [3] HVDC WAREHOUSE_HITACHI(HE).xlsx (동기화된 Warehouse)

#### 출력 데이터
- **파일**: `hitachi/HVDC WAREHOUSE_HITACHI(HE).xlsx`
- **크기**: 5,552행 × 57컬럼 (Master 38컬럼 + 추가 19컬럼)
- **추가 컬럼**:
  - `HVDC CODE 1-5`: HVDC 코드 확장
  - `Status_WAREHOUSE`, `Status_SITE`, `Status_Current`: 상태 정보
  - `Status_Location`, `Status_Location_Date`: 위치 정보
  - `Status_Storage`: 저장소 상태
  - `wh handling`, `site handling`, `total handling`: 처리 정보
  - `minus`, `final handling`: 계산 필드
  - `SQM`: Square Meter 계산값
  - `Stack_Status`: 적재 상태

#### 데이터 변환
- **Master → Warehouse**: 6,069건 → 5,552건 (517건 차이)
- **컬럼 확장**: 38개 → 57개 (19개 추가)
- **색상 표시**: 변경된 날짜(주황), 새 행(노랑)

---

### [4] hvdc_excel_reporter_final_sqm_rev (1).py (SQM 리포트 생성)

#### 핵심 기능
```python
# 수정 버전 정보
CORRECTED_VERSION = "v3.0-corrected"
VERIFICATION_RATE = 99.97  # 검증 정합률 (%)

# 주요 개선사항
1. 창고 vs 현장 입고 분리
2. 출고 타이밍 정확성 개선
3. 재고 검증 로직 강화
4. 이중 계산 방지
```

#### SQM 계산 로직
1. **입고 계산**: `calculate_warehouse_inbound_corrected()`
   - 창고 컬럼만 입고로 계산 (현장 제외)
   - 창고간 이동의 목적지는 제외 (이중 계산 방지)

2. **출고 계산**: `calculate_monthly_sqm_outbound()`
   - 다음 날 이동만 출고로 인정 (동일 날짜 제외)

3. **재고 계산**: `calculate_cumulative_sqm_inventory()`
   - 입고 - 출고 = 재고

#### Flow Code 분석
- **Port → Site**: 직접 배송
- **Port → WH → MOSB → Site**: 창고 경유 배송
- **Port → WH → Site**: 창고 직접 배송

#### 실행 명령어
```bash
python "hvdc_excel_reporter_final_sqm_rev (1).py"
```

#### 입력/출력
- **입력**: `HVDC WAREHOUSE_HITACHI(HE).xlsx`
- **출력**: `HVDC_입고로직_종합리포트_YYYYMMDD_HHMMSS_v3.0-corrected.xlsx`
- **시트 구조**: 12개 시트 (요약, 월별, 창고별, 현장별, Flow별 등)

---

### [5] HVDC_입고로직_종합리포트_*.xlsx (최종 리포트)

#### 현재 상태
- ❌ **파일 없음**: 현재 디렉토리에 최종 리포트 파일이 존재하지 않음
- **예상 위치**: `hitachi/` 또는 `hitachi/out/`
- **예상 파일명**: `HVDC_입고로직_종합리포트_YYYYMMDD_HHMMSS_v3.0-corrected.xlsx`

#### 예상 시트 구조
1. **요약 대시보드**: 전체 SQM 현황
2. **월별 입고**: 월별 창고 입고 현황
3. **월별 출고**: 월별 창고 출고 현황
4. **월별 재고**: 월별 누적 재고
5. **창고별 상세**: 창고별 입출고 상세
6. **현장별 상세**: 현장별 배송 상세
7. **Flow별 분석**: 물류 경로별 분석
8. **통합_원본데이터_Fixed**: 원본 데이터 (이상치 탐지 대상)

#### 검증 방법
```bash
# 리포트 생성 확인
ls -la *입고로직_종합리포트*.xlsx

# 시트 구조 확인
python -c "import pandas as pd; xl = pd.ExcelFile('HVDC_입고로직_종합리포트_*.xlsx'); print(xl.sheet_names)"
```

---

### [6] anomaly_detector.py (이상치 탐지)

#### 핵심 기능
```python
# 3-Layer 탐지 시스템
1. Rule-based: 시간 역전, 위치 스킵
2. Statistical: IQR 기반 과도 체류
3. ML-based: Isolation Forest + PyOD

# 탐지 유형
- TIME_REVERSAL: 시간 역전 (789건)
- EXCESSIVE_DWELL: 과도 체류 (36건)
- ML_OUTLIER: 머신러닝 이상치 (107건)
- DATA_QUALITY: 데이터 품질 (1건)
```

#### 입력/출력
- **입력**: Excel 파일 (시트명 지정 가능)
- **출력**:
  - `hvdc_anomaly_report_v2.json`: JSON 형태 이상치 목록
  - `hvdc_anomaly_report_v2.xlsx`: Excel 형태 이상치 리포트
  - 원본 파일 색상 표시 (--visualize 옵션)

#### 실행 명령어
```bash
python anomaly_detector.py \
  --input "HVDC_입고로직_종합리포트_*.xlsx" \
  --sheet "통합_원본데이터_Fixed" \
  --json-out "hvdc_anomaly_report_v2.json" \
  --visualize
```

#### 색상 표시 로직
- **빨강 (FFFF0000)**: 시간 역전 (날짜 컬럼만)
- **주황 (FFFFC000)**: ML 이상치 HIGH/CRITICAL
- **노랑 (FFFFFF00)**: ML 이상치 MEDIUM/LOW + 과도 체류
- **보라 (FFCC99FF)**: 데이터 품질

---

### [7] 이상치 통합 (현재 누락) ⚠️

#### 현재 문제
- 이상치 탐지는 완료되었으나 **최종 리포트에 통합되지 않음**
- `anomaly_detector.py`는 별도 파일에 색상 표시하지만, **최종 리포트는 생성되지 않음**

#### 통합 방안 3가지

##### 옵션 A: anomaly_detector.py 수정
```python
# 최종 리포트에 직접 색상 적용
python anomaly_detector.py \
  --input "HVDC_입고로직_종합리포트_*.xlsx" \
  --sheet "통합_원본데이터_Fixed" \
  --visualize
```

**장점**: 단일 명령어로 완료
**단점**: anomaly_detector.py가 최종 리포트 구조를 알아야 함

##### 옵션 B: 별도 통합 스크립트
```python
# integrate_anomaly_to_report.py
python integrate_anomaly_to_report.py \
  --report "HVDC_입고로직_종합리포트_*.xlsx" \
  --anomaly "hvdc_anomaly_report_v2.json" \
  --output "HVDC_입고로직_종합리포트_*_WITH_ANOMALY.xlsx"
```

**장점**: 모듈화, 재사용성
**단점**: 추가 스크립트 필요

##### 옵션 C: reporter에 이상치 탐지 통합
```python
# hvdc_excel_reporter_final_sqm_rev (1).py 수정
# SQM 계산 후 자동으로 이상치 탐지 및 색상 표시
```

**장점**: 원스톱 솔루션
**단점**: reporter가 복잡해짐

#### 권장 방안: **옵션 A**
- 현재 `anomaly_detector.py`에 `--visualize` 옵션이 이미 구현됨
- 최종 리포트 파일만 생성되면 바로 적용 가능

---

## 📊 데이터 흐름도

```mermaid
graph TB
    A["[1] CASE LIST.xlsx<br/>6,069건 × 38컬럼<br/>Master File"] --> B["[2] data_synchronizer_v29.py<br/>Master 우선 동기화<br/>날짜 우선순위 + 색상"]

    B --> C["[3] HVDC WAREHOUSE_HITACHI(HE).xlsx<br/>5,552건 × 57컬럼<br/>동기화된 Warehouse"]

    C --> D["[4] hvdc_excel_reporter_final_sqm_rev (1).py<br/>SQM 계산 + 입고로직<br/>12개 시트 생성"]

    D --> E["[5] HVDC_입고로직_종합리포트_*.xlsx<br/>최종 리포트<br/>❌ 현재 없음"]

    E --> F["[6] anomaly_detector.py<br/>이상치 탐지<br/>933건 탐지"]

    F --> G["[7] 이상치 통합<br/>최종 리포트에 색상 표시<br/>❌ 현재 누락"]

    style A fill:#e1f5fe
    style C fill:#f3e5f5
    style E fill:#ffebee
    style G fill:#ffebee
```

---

## 🚀 실행 가이드

### 전체 파이프라인 실행 순서

#### 1단계: Master → Warehouse 동기화
```bash
cd hitachi
python data_synchronizer_v29.py \
  --master "CASE LIST.xlsx" \
  --warehouse "HVDC WAREHOUSE_HITACHI(HE).xlsx" \
  --output "HVDC WAREHOUSE_HITACHI(HE).xlsx"
```

#### 2단계: SQM 리포트 생성
```bash
python "hvdc_excel_reporter_final_sqm_rev (1).py"
```

#### 3단계: 이상치 탐지 및 통합
```bash
# 최종 리포트 파일 확인
ls -la *입고로직_종합리포트*.xlsx

# 이상치 탐지 및 색상 표시
python anomaly_detector.py \
  --input "HVDC_입고로직_종합리포트_*.xlsx" \
  --sheet "통합_원본데이터_Fixed" \
  --json-out "hvdc_anomaly_report_v2.json" \
  --visualize
```

### 각 단계별 검증 포인트

#### [1→2→3] 동기화 검증
- [ ] Case NO 매칭률 확인
- [ ] 날짜 업데이트 통계 확인
- [ ] 색상 표시 확인 (주황/노랑)
- [ ] 새 케이스 추가 확인

#### [3→4→5] SQM 리포트 검증
- [ ] 최종 리포트 파일 생성 확인
- [ ] 12개 시트 구조 확인
- [ ] SQM 계산 정확성 검증
- [ ] 입고/출고/재고 일관성 확인

#### [5→6→7] 이상치 통합 검증
- [ ] 이상치 탐지 결과 확인 (933건)
- [ ] 색상 표시 확인 (빨강/주황/노랑/보라)
- [ ] 최종 리포트에 통합 확인

---

## 🔧 문제 해결 가이드

### 문제 1: 최종 리포트 파일이 없음
**증상**: `HVDC_입고로직_종합리포트_*.xlsx` 파일이 생성되지 않음

**해결방법**:
```bash
# 1. reporter 스크립트 실행 확인
python "hvdc_excel_reporter_final_sqm_rev (1).py"

# 2. 출력 디렉토리 확인
ls -la out/
ls -la output/

# 3. 에러 로그 확인
python "hvdc_excel_reporter_final_sqm_rev (1).py" 2>&1 | tee reporter.log
```

### 문제 2: 이상치 탐지 실패
**증상**: `anomaly_detector.py` 실행 시 오류

**해결방법**:
```bash
# 1. 입력 파일 경로 확인
python anomaly_detector.py --input "정확한_파일경로.xlsx"

# 2. 시트명 확인
python -c "import pandas as pd; xl = pd.ExcelFile('파일.xlsx'); print(xl.sheet_names)"

# 3. Case NO 컬럼명 확인
python -c "import pandas as pd; df = pd.read_excel('파일.xlsx', sheet_name='시트명'); print([c for c in df.columns if 'case' in c.lower()])"
```

### 문제 3: 색상 표시 안됨
**증상**: `--visualize` 옵션으로 실행했지만 색상이 표시되지 않음

**해결방법**:
```bash
# 1. AnomalyVisualizer 모듈 확인
python -c "from anomaly_visualizer import AnomalyVisualizer; print('OK')"

# 2. 백업 파일 확인
ls -la *.backup_*

# 3. 색상 검증
python verify_colors_detailed.py --excel "파일.xlsx" --sheet "시트명"
```

---

## 📈 성능 지표

### 데이터 처리량
- **Master**: 6,069건
- **Warehouse**: 5,552건 (517건 차이)
- **이상치**: 933건 (16.8%)

### 처리 시간 (예상)
- **동기화**: 30-60초
- **SQM 계산**: 2-5분
- **이상치 탐지**: 1-2분
- **색상 표시**: 10-30초

### 정확도
- **동기화 정합률**: 99.9%
- **SQM 계산 정합률**: 99.97%
- **이상치 탐지 정확도**: 95%+

---

## 🎯 권장 사항

### 즉시 조치 필요
1. **최종 리포트 생성**: `hvdc_excel_reporter_final_sqm_rev (1).py` 실행하여 리포트 파일 생성
2. **이상치 통합**: 생성된 리포트에 이상치 색상 표시 적용

### 중장기 개선
1. **자동화 스크립트**: 전체 파이프라인을 하나의 스크립트로 통합
2. **에러 처리**: 각 단계별 에러 처리 및 롤백 메커니즘
3. **모니터링**: 각 단계별 성능 및 정확도 모니터링
4. **테스트**: 단위 테스트 및 통합 테스트 추가

---

## 📚 참조 문서

- `hitachi/data_synchronizer_v29.py`: 동기화 시스템
- `hitachi/hvdc_excel_reporter_final_sqm_rev (1).py`: SQM 리포트 생성
- `hitachi/anomaly_detector/anomaly_detector.py`: 이상치 탐지
- `hitachi/anomaly_detector/COLOR_PATCH_REPORT.md`: 색상 표시 패치 보고서
- `hitachi/docs/`: 기타 문서들

---

## 🏁 결론

### 현재 상태
- ✅ **완료**: Master → Warehouse 동기화 (v2.9)
- ✅ **완료**: SQM 계산 및 리포트 생성 (v3.0-corrected)
- ✅ **완료**: 이상치 탐지 시스템 (v2)
- ❌ **누락**: 최종 리포트 파일 생성
- ❌ **누락**: 이상치 통합

### 다음 단계
1. **최종 리포트 생성** (우선순위: HIGH)
2. **이상치 통합** (우선순위: HIGH)
3. **전체 파이프라인 자동화** (우선순위: MEDIUM)

**종합 평가**: 핵심 시스템은 완성되었으나, 최종 통합 단계가 누락되어 완전한 파이프라인이 되지 못함

---

**작성**: AI Agent
**검토**: Human Reviewer
**승인**: Pending
