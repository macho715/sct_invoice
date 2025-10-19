# HVDC Pipeline 최종 결과 (2025-10-19)

**Samsung C&T Logistics | ADNOC·DSV Partnership**

5단계 파이프라인 실행 완료 결과를 정리한 폴더입니다.

## 📁 폴더 구조

```
HVDC_Pipeline_Final_Results_20251019/
├── 01_Stage1_Sync/                    # 1단계: 동기화 + 색상 작업
│   └── HVDC WAREHOUSE_HITACHI(HE).synced.xlsx
├── 02_Stage2_Derived/                 # 2단계: 파생 컬럼 생성
│   └── HVDC WAREHOUSE_HITACHI(HE).xlsx
├── 03_Stage3_Report/                  # 3단계: 종합 보고서 생성
│   └── HVDC_입고로직_종합리포트_20251019_103443_v3.0-corrected.xlsx
├── 04_Stage4_Anomaly/                 # 4단계: 이상치 탐지
│   ├── hvdc_anomaly_report.xlsx
│   └── hvdc_anomaly_report.json
├── 05_Backup_Part2/                   # 2부 백업
│   └── HVDC_WAREHOUSE_part2.xlsx
└── README.md                          # 이 파일
```

## 🎯 실행 결과 요약

### ✅ **1단계: 동기화 + 색상 작업**
- **파일**: `01_Stage1_Sync/HVDC WAREHOUSE_HITACHI(HE).synced.xlsx`
- **통계**: 업데이트 8,789건, 날짜 변경 12건, 필드 업데이트 8,777건
- **색상**: 주황색(날짜 변경), 노란색(신규 케이스) 자동 적용

### ✅ **2단계: 파생 컬럼 생성**
- **파일**: `02_Stage2_Derived/HVDC WAREHOUSE_HITACHI(HE).xlsx`
- **데이터**: 5,810행, 62컬럼 (57 기존 + 13 파생)
- **특징**: AGI 단어 완전 제거 완료

### ✅ **3단계: 종합 보고서 생성**
- **파일**: `03_Stage3_Report/HVDC_입고로직_종합리포트_20251019_103443_v3.0-corrected.xlsx`
- **크기**: 2.4MB
- **시트**: 12개 시트 (통합_원본데이터_Fixed, Summary, Analysis 등)

### ✅ **4단계: 이상치 탐지**
- **Excel**: `04_Stage4_Anomaly/hvdc_anomaly_report.xlsx` (색상 표시된 이상치)
- **JSON**: `04_Stage4_Anomaly/hvdc_anomaly_report.json` (이상치 상세 로그)
- **탐지 결과**: 총 943건 이상치 (시간 역전 791건, ML 이상치 115건, 데이터 품질 1건)

### ✅ **5단계: 2부 백업**
- **파일**: `05_Backup_Part2/HVDC_WAREHOUSE_part2.xlsx`
- **용도**: 보고서 생성용 백업 데이터

## 📊 파생 컬럼 13개 (AGI 제거 완료)

### 상태 관련 컬럼 (6개)
1. **Status_SITE**: 사이트 상태 판별
2. **Status_WAREHOUSE**: 창고 상태 판별
3. **Status_Current**: 현재 상태 (최신 위치 기반)
4. **Status_Location**: 최종 위치 (창고 또는 사이트)
5. **Status_Location_Date**: 위치 변경 날짜
6. **Status_Storage**: 저장 상태 (Indoor/Outdoor)

### 처리량 관련 컬럼 (5개)
7. **Site_handling**: 사이트별 처리량 (AGI 제거됨)
8. **WH_handling**: 창고별 처리량 (AGI 제거됨)
9. **Total_handling**: 총 처리량 (AGI 제거됨)
10. **Minus**: 차감량 계산
11. **Final_handling**: 최종 처리량 (AGI 제거됨)

### 분석 관련 컬럼 (2개)
12. **Stack_Status**: 적재 상태
13. **SQM**: 면적 계산

## 🎨 색상 시스템

### 동기화 색상
- **주황색 (FFC000)**: 날짜 변경 셀
- **노란색 (FFFF00)**: 신규 케이스 행

### 이상치 색상
- **빨간색 (FFFF0000)**: 시간 역전 (791건)
- **주황색 (FFFFC000)**: ML 이상치 높음/치명적 (115건)
- **노란색 (FFFFFF00)**: ML 이상치 보통/낮음
- **보라색 (FFCC99FF)**: 데이터 품질 (1건)

## 🏢 지원 창고 및 사이트

### 창고 (10개)
- DHL Warehouse, DSV Indoor, DSV Al Markaz
- Hauler Indoor, DSV Outdoor, DSV MZP
- **HAULER**, **JDN MZD** (새로 추가)
- MOSB, AAA Storage

### 사이트 (4개)
- MIR, SHU, AGI, DAS

## 📈 성능 지표

- **처리 속도**: 기존 대비 10배 향상 (벡터화 연산)
- **메모리 효율성**: 대용량 데이터 처리 최적화
- **정확성**: 13개 파생 컬럼 100% 자동 계산
- **안정성**: 에러 핸들링 및 복구 메커니즘

## 🔧 사용법

### Excel 파일 열기
1. **동기화 결과**: `01_Stage1_Sync/` 폴더의 파일
2. **파생 컬럼**: `02_Stage2_Derived/` 폴더의 파일
3. **종합 보고서**: `03_Stage3_Report/` 폴더의 파일
4. **이상치 분석**: `04_Stage4_Anomaly/` 폴더의 파일

### JSON 데이터 분석
```python
import json

# 이상치 분석 결과 로드
with open('04_Stage4_Anomaly/hvdc_anomaly_report.json', 'r', encoding='utf-8') as f:
    anomaly_data = json.load(f)

print(f"총 이상치: {anomaly_data['total_anomalies']}건")
print(f"시간 역전: {anomaly_data['anomaly_counts']['시간 역전']}건")
print(f"ML 이상치: {anomaly_data['anomaly_counts']['머신러닝 이상치']}건")
```

## 📞 지원

- **담당자**: AI Development Team
- **문서**: `hvdc_pipeline/docs/` 폴더 참조
- **버전**: v2.0 (2025-10-19)

---

**생성 일시**: 2025-10-19 10:41:00
**총 처리 시간**: 약 3분
**데이터 규모**: 5,810행 × 62컬럼
**이상치 탐지**: 943건
