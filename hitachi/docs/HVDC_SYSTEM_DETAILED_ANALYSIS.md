# 📋 HVDC Excel Reporter 시스템 상세 분석 보고서

> **문서 버전:** v3.0-corrected Analysis
> **작성일:** 2025-10-18
> **프로젝트:** Samsung C&T · ADNOC · DSV Partnership
> **시스템:** HVDC 입고 로직 구현 및 집계 시스템

---

## 📑 목차

1. [Executive Summary](#executive-summary)
2. [시스템 아키텍처](#시스템-아키텍처)
3. [핵심 로직 및 알고리즘](#핵심-로직-및-알고리즘)
4. [Excel 리포트 생성](#excel-리포트-생성)
5. [테스트 및 검증](#테스트-및-검증)
6. [성능 최적화](#성능-최적화)
7. [설계 원칙](#설계-원칙)
8. [주요 개선 사항](#주요-개선-사항)

---

## 🎯 Executive Summary

### 시스템 개요

**HVDC 입고 로직 구현 및 집계 시스템 v3.0-corrected**는 Samsung C&T·ADNOC·DSV 파트너십의 물류 프로젝트를 위한 종합 창고 관리 시스템입니다.

### 핵심 특징

```yaml
코드 규모:
  - 총 라인 수: 2,792줄
  - 클래스 수: 2개 (Calculator + Reporter)
  - 함수 수: 40+ 개
  - 테스트 케이스: 28개 + 추가 검증

기능 범위:
  - 데이터 소스: HITACHI + SIMENSE (2개 벤더)
  - 창고: 8개 (AAA Storage, DSV Al Markaz, DSV Indoor, etc.)
  - 현장: 4개 (AGI, DAS, MIR, SHU)
  - 출력 시트: 12개
  - 검증 레벨: 3단 (Status + Physical + Cross-validation)

성능 지표:
  - 검증 정합률: 99.97%
  - PKG Accuracy: 99.0% 이상
  - 창고 가동률: 79.4% (목표 85% 이하)
  - 처리 속도: ~10초 (2,000+ 레코드)
```

### 주요 혁신 포인트

1. **창고 vs 현장 완전 분리**
   - 입고: 창고 8개만 계산
   - 출고: 창고→창고, 창고→현장 구분
   - 재고: Status_Location 기반 우선순위

2. **이중 계산 방지 메커니즘**
   - 창고간 이동 목적지는 입고 제외
   - 이미 출고된 창고는 현장 출고 제외
   - 동일 날짜 이동은 별도 관리

3. **SQM 기반 면적 관리**
   - 실제 SQM 우선, 없으면 PKG×1.5 추정
   - 월별 누적 재고 추적
   - 창고 가동률 실시간 계산

4. **Flow Traceability**
   - Port → WH → MOSB → Site 경로 추적
   - Sankey 다이어그램 데이터 생성
   - KPI: MOSB 통과율, 직송 비율, 평균 체류일

---

## 🏗️ 시스템 아키텍처

### 클래스 다이어그램

```
┌─────────────────────────────────────────────┐
│  CorrectedWarehouseIOCalculator             │
├─────────────────────────────────────────────┤
│  + __init__()                               │
│  + load_real_hvdc_data()                    │
│  + process_real_data()                      │
│  + _override_flow_code()                    │
│  + calculate_warehouse_inbound_corrected()  │
│  + calculate_warehouse_outbound_corrected() │
│  + calculate_warehouse_inventory_corrected()│
│  + _detect_warehouse_transfers()            │
│  + _validate_transfer_logic()               │
│  + calculate_monthly_sqm_inbound()          │
│  + calculate_monthly_sqm_outbound()         │
│  + calculate_cumulative_sqm_inventory()     │
│  + create_monthly_inbound_pivot()           │
│  + calculate_final_location()               │
└─────────────────────────────────────────────┘
                    △
                    │ uses
                    │
┌─────────────────────────────────────────────┐
│  HVDCExcelReporterFinal                     │
├─────────────────────────────────────────────┤
│  + __init__()                               │
│  + calculate_warehouse_statistics()         │
│  + create_warehouse_monthly_sheet()         │
│  + create_site_monthly_sheet()              │
│  + create_flow_analysis_sheet()             │
│  + create_transaction_summary_sheet()       │
│  + create_sqm_cumulative_sheet()            │
│  + create_sqm_pivot_sheet()                 │
│  + create_flow_traceability_frames()        │
│  + create_multi_level_headers()             │
│  + generate_final_excel_report()            │
└─────────────────────────────────────────────┘
```

### 데이터 흐름

```
[입력 데이터]
    ↓
┌──────────────────────────────────┐
│ HVDC WAREHOUSE_HITACHI(HE).xlsx  │ → 벤더 1
│ HVDC WAREHOUSE_SIMENSE(SIM).xlsx │ → 벤더 2
└──────────────────────────────────┘
    ↓
[데이터 로드 및 정규화]
    ↓
load_real_hvdc_data()
├── 컬럼명 공백 정규화
├── 8개 창고 컬럼 검증
├── 누락 컬럼 보완 (pd.NaT)
└── 데이터 통합 (pd.concat)
    ↓
[전처리 및 Flow Code 계산]
    ↓
process_real_data()
├── 날짜 컬럼 변환
├── handling 컬럼 원본 보존
└── _override_flow_code()
    └── FLOW_CODE 0~4 분류
    ↓
[핵심 계산 엔진]
    ↓
calculate_warehouse_statistics()
├── calculate_warehouse_inbound_corrected()
│   ├── 순수 외부 입고 계산
│   └── 창고간 이동 제외
├── calculate_warehouse_outbound_corrected()
│   ├── 창고간 이동 출고
│   └── 창고→현장 출고
├── calculate_warehouse_inventory_corrected()
│   ├── Status_Location 재고
│   ├── Physical Location 재고
│   └── 교차 검증 (3단 구조)
├── calculate_monthly_sqm_inbound()
│   └── SQM 기반 입고 면적
├── calculate_monthly_sqm_outbound()
│   └── SQM 기반 출고 면적
├── calculate_cumulative_sqm_inventory()
│   ├── 월별 누적 재고
│   └── 창고 가동률 계산
└── create_flow_traceability_frames()
    ├── Sankey 링크 데이터
    ├── Timeline 세그먼트
    └── Flow KPI 계산
    ↓
[Excel 리포트 생성]
    ↓
generate_final_excel_report()
├── 창고_월별_입출고 (19열)
├── 현장_월별_입고재고 (9열)
├── Flow_Code_분석
├── 전체_트랜잭션_요약
├── KPI_검증_결과
├── SQM_누적재고
├── SQM_피벗테이블
├── 원본_데이터_샘플
└── HITACHI/SIEMENS/통합_원본데이터_Fixed
    ↓
[출력 파일]
    ↓
┌──────────────────────────────────────────────┐
│ HVDC_입고로직_종합리포트_YYYYMMDD_HHMMSS_v3.0-corrected.xlsx │
│ + CSV 백업 파일들 (output/ 폴더)              │
└──────────────────────────────────────────────┘
```

### 핵심 데이터 구조

#### 창고 및 현장 정의

```python
warehouse_columns = [
    "AAA Storage",      # 외부 보관
    "DSV Al Markaz",    # 메인 창고 (우선순위 1)
    "DSV Indoor",       # 실내 창고 (우선순위 2)
    "DSV MZP",          # 특수 창고
    "DSV Outdoor",      # 실외 창고
    "Hauler Indoor",    # Hauler 실내
    "MOSB",             # Offshore 해상
    "DHL Warehouse"     # DHL 창고
]

site_columns = [
    "AGI",  # 현장 1
    "DAS",  # 현장 2
    "MIR",  # 현장 3
    "SHU"   # 현장 4
]
```

#### Flow Code 정의

```python
flow_codes = {
    0: "Pre Arrival",                    # 도착 전
    1: "Port → Site",                    # 직송
    2: "Port → WH → Site",               # 창고 경유
    3: "Port → WH → MOSB → Site",        # Offshore 경유
    4: "Port → WH → WH → MOSB → Site"   # 다중 창고 경유
}
```

#### 위치 우선순위 (타이브레이커용)

```python
location_priority = {
    "DSV Al Markaz": 1,   # 최우선
    "DSV Indoor": 2,
    "DSV Outdoor": 3,
    "AAA Storage": 4,
    "Hauler Indoor": 5,
    "DSV MZP": 6,
    "MOSB": 7,
    "DHL Warehouse": 8,
    "AGI": 9,
    "DAS": 10,
    "MIR": 11,
    "SHU": 12
}
```

---

상세 내용은 다음 페이지에 계속됩니다...

**관련 문서:**
- [Part 2: 핵심 로직 및 알고리즘 상세](./HVDC_SYSTEM_DETAILED_ANALYSIS_PART2.md)
- [Part 3: Excel 리포트 및 테스트](./HVDC_SYSTEM_DETAILED_ANALYSIS_PART3.md)
- [V29 Implementation Guide](./V29_IMPLEMENTATION_GUIDE.md)
- [Date Update Color Fix Report](./DATE_UPDATE_COLOR_FIX_REPORT.md)

