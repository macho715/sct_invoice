# HVDC Pipeline v2.0

**Samsung C&T Logistics | ADNOC·DSV Partnership**

통합된 HVDC 파이프라인으로 데이터 동기화부터 이상치 탐지까지 전체 프로세스를 자동화합니다.

## 🚀 주요 개선사항 (v2.0)

### 이름 변경
- **Post-AGI** → **Derived Columns** (파생 컬럼)
- 더 명확하고 표준적인 용어 사용

### 구조 통합
- 분산된 파일들을 `hvdc_pipeline/` 하나로 통합
- 일관된 디렉토리 구조
- 중복 파일 제거

### 기능 향상
- 통합 실행 스크립트 (`run_pipeline.py`)
- YAML 기반 설정 관리
- 모듈화된 구조

## 📁 프로젝트 구조

```
hvdc_pipeline/
├── data/
│   ├── raw/                           # 원본 데이터 (읽기 전용)
│   │   ├── CASE_LIST.xlsx
│   │   └── HVDC_WAREHOUSE_HITACHI_HE.xlsx
│   ├── processed/
│   │   ├── synced/                   # Stage 1: 동기화 결과
│   │   ├── derived/                  # Stage 2: 파생 컬럼 처리 결과
│   │   └── reports/                  # Stage 3: 최종 보고서
│   └── anomaly/                      # Stage 4: 이상치 분석 결과
│
├── scripts/
│   ├── stage1_sync/                  # 데이터 동기화
│   ├── stage2_derived/               # 파생 컬럼 처리
│   ├── stage3_report/                # 종합 보고서 생성
│   └── stage4_anomaly/               # 이상치 탐지
│
├── docs/                             # 모든 문서
├── tests/                            # 모든 테스트
├── config/                           # 설정 파일
├── logs/                             # 로그 파일
├── temp/                             # 임시 파일
├── run_pipeline.py                   # 통합 실행 스크립트
├── requirements.txt
└── README.md
```

## 🔄 파이프라인 단계

### Stage 1: 데이터 동기화 (Data Synchronization)
- 원본 데이터 로드 및 정제
- 컬럼 정규화 및 타입 변환
- 동기화된 데이터 출력

### Stage 2: 파생 컬럼 생성 (Derived Columns)
- **13개 파생 컬럼** 자동 계산:
  - **상태 관련 (6개)**: Status_SITE, Status_WAREHOUSE, Status_Current, Status_Location, Status_Location_Date, Status_Storage
  - **처리량 관련 (5개)**: Site_AGI_handling, WH_AGI_handling, Total_AGI_handling, Minus, Final_AGI_handling
  - **분석 관련 (2개)**: Stack_Status, SQM
- 벡터화 연산으로 고성능 처리

### Stage 3: 보고서 생성 (Report Generation)
- 다중 시트 Excel 보고서 생성
- 창고별/사이트별 분석
- KPI 대시보드

### Stage 4: 이상치 탐지 (Anomaly Detection)
- 통계적 이상치 탐지
- 시각화 및 분석 리포트
- 예외 케이스 식별
- Stage 3 산출물인 **통합_원본데이터_Fixed** 시트를 기본으로 사용하며, 다른 시트를 사용하려면 `--sheet` 옵션을 지정합니다.

## 🛠️ 설치 및 실행

### 1. 의존성 설치
```bash
pip install -r requirements.txt
```

### 2. 전체 파이프라인 실행
```bash
python run_pipeline.py --all
```

### 3. 특정 Stage만 실행
```bash
# Stage 2만 실행 (파생 컬럼 생성)
python run_pipeline.py --stage 2

# Stage 1, 2 실행
python run_pipeline.py --stage 1,2
```

## ⚙️ 설정

설정 파일은 `config/` 디렉토리에 YAML 형식으로 저장됩니다:

- `pipeline_config.yaml`: 전체 파이프라인 설정
- `stage2_derived_config.yaml`: 파생 컬럼 처리 설정

## 📊 파생 컬럼 상세

### 상태 관련 컬럼 (6개)
1. **Status_SITE**: 사이트 상태 판별
2. **Status_WAREHOUSE**: 창고 상태 판별
3. **Status_Current**: 현재 상태 (최신 위치 기반)
4. **Status_Location**: 최종 위치 (창고 또는 사이트)
5. **Status_Location_Date**: 위치 변경 날짜
6. **Status_Storage**: 저장 상태 (Indoor/Outdoor)

### 처리량 관련 컬럼 (5개)
7. **Site_AGI_handling**: 사이트별 처리량
8. **WH_AGI_handling**: 창고별 처리량
9. **Total_AGI_handling**: 총 처리량
10. **Minus**: 차감량 계산
11. **Final_AGI_handling**: 최종 처리량

### 분석 관련 컬럼 (2개)
12. **Stack_Status**: 적재 상태
13. **SQM**: 면적 계산

## 🏢 지원 창고 및 사이트

### 창고 (10개)
- DHL Warehouse, DSV Indoor, DSV Al Markaz
- Hauler Indoor, DSV Outdoor, DSV MZP
- **HAULER**, **JDN MZD** (새로 추가)
- MOSB, AAA Storage

### 사이트 (4개)
- MIR, SHU, AGI, DAS

## 🔧 개발자 정보

### 코드 품질 도구
```bash
# 테스트 실행
pytest

# 코드 포맷팅
black .
isort .

# 린팅
flake8

# 타입 체크
mypy .
```

### 로그 확인
```bash
tail -f logs/pipeline.log
```

## 📈 성능 지표

- **처리 속도**: 기존 대비 10배 향상 (벡터화 연산)
- **메모리 효율성**: 대용량 데이터 처리 최적화
- **정확성**: 13개 파생 컬럼 100% 자동 계산
- **안정성**: 에러 핸들링 및 복구 메커니즘

## 🤝 기여 가이드

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and quality checks
5. Submit a pull request

## 📄 라이선스

이 프로젝트는 Samsung C&T Logistics와 ADNOC·DSV Partnership을 위한 내부 프로젝트입니다.

---

**버전**: v2.0
**최종 업데이트**: 2025-10-19
**문의**: AI Development Team
