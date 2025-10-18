# ML Systems Integration Guide
**HVDC Invoice Audit - 통합 ML 시스템 사용 가이드**

[![Tests](https://img.shields.io/badge/tests-8%20passed-brightgreen)]()
[![Python](https://img.shields.io/badge/python-3.11-blue)]()
[![TDD](https://img.shields.io/badge/methodology-TDD-orange)]()
[![Integration](https://img.shields.io/badge/integration-E2E-success)]()

> logi_costguard_ml_v2와 weight_optimizer 시스템을 통합한 End-to-End ML 파이프라인

---

## 📋 개요

이 통합 시스템은 HVDC 프로젝트의 송장 감사를 위한 두 개의 독립적인 ML 시스템을 하나의 통합된 파이프라인으로 결합합니다:

### 통합된 시스템 구성요소

1. **logi_costguard_ml_v2** (DSV 전자료 특화)
   - 회귀 모델 (RandomForest/GradientBoosting)
   - 이상탐지 (IsolationForest)
   - 밴딩 시스템 (PASS/WARN/HIGH/CRITICAL)
   - 레인 유사도 제안

2. **weight_optimizer** (하이브리드 매칭 가중치)
   - 3개 분류 모델 (Logistic/RF/GB)
   - ML 최적화 가중치 학습
   - A/B 테스트 프레임워크

3. **통합 인터페이스**
   - UnifiedMLPipeline 클래스
   - CLI 인터페이스 (cli_unified.py)
   - End-to-End 테스트 (test_integration_e2e.py)

---

## 🚀 빠른 시작

### 1. 설치 및 설정

```bash
# ML 디렉토리로 이동
cd ML

# 의존성 설치 (이미 설치되어 있다면 생략)
pip install -r requirements.txt

# 테스트 실행 (모든 시스템이 정상 작동하는지 확인)
python -m pytest test_integration_e2e.py -v
```

### 2. 기본 사용법

#### 통합 학습 (CostGuard + Weight Optimizer)
```bash
python cli_unified.py train \
  --data logi_costguard_ml_v2/data/DSV_SHPT_ALL.xlsx \
  --weights-training-data training_data.json \
  --output-dir output
```

#### 통합 예측 (ML 가중치 적용)
```bash
python cli_unified.py predict \
  --data new_invoice_data.xlsx \
  --approved-lanes logi_costguard_ml_v2/ref/ApprovedLaneMap.csv \
  --use-ml-weights \
  --output prediction_results.xlsx
```

#### A/B 테스트 (성능 비교)
```bash
python cli_unified.py ab-test \
  --data test_data.xlsx \
  --approved-lanes logi_costguard_ml_v2/ref/ApprovedLaneMap.csv \
  --output ab_test_results.json
```

---

## 📊 데이터 흐름

### 통합 파이프라인 데이터 흐름
```
Invoice Data → Canonicalization → ML Weight Matching → Regression Prediction → Anomaly Detection → Banding → Report
```

### 상세 단계별 처리

1. **데이터 정규화** (`canon.py`)
   - 송장 데이터 표준화
   - 위치명 정규화
   - 단위 통일

2. **ML 가중치 매칭** (`ml_integration.py`)
   - 학습된 가중치로 유사도 계산
   - 4단계 매칭 (EXACT → SIMILARITY_ML → REGION → VEHICLE_TYPE_ML)

3. **회귀 예측** (`model_reg.py`)
   - RandomForest/GradientBoosting으로 요금 예측
   - Quantile 예측 (10%, 50%, 90%)

4. **이상탐지** (`model_iso.py`)
   - IsolationForest로 이상 점수 계산
   - 0-1 정규화

5. **밴딩** (`guard.py`)
   - PASS/WARN/HIGH/CRITICAL 분류
   - 이상탐지 결과와 결합

6. **레인 제안** (`similarity.py`)
   - 유사한 레인 자동 제안
   - ML 가중치 적용

---

## 🧪 테스트 가이드

### End-to-End 통합 테스트

```bash
# 전체 통합 테스트 실행
python -m pytest test_integration_e2e.py -v

# 개별 테스트 클래스 실행
python -m pytest test_integration_e2e.py::TestE2ETrainingPipeline -v
python -m pytest test_integration_e2e.py::TestE2EPredictionPipeline -v
python -m pytest test_integration_e2e.py::TestE2EABTesting -v
```

### 테스트 커버리지

| 테스트 클래스 | 테스트 수 | 목적 |
|---------------|-----------|------|
| **TestE2ETrainingPipeline** | 2 | 통합 학습 파이프라인 검증 |
| **TestE2EPredictionPipeline** | 2 | 통합 예측 파이프라인 검증 |
| **TestE2EABTesting** | 1 | A/B 테스트 성능 비교 |
| **TestE2ERetrainingCycle** | 1 | 재학습 사이클 검증 |
| **TestE2EErrorRecovery** | 2 | 에러 복구 시나리오 |

---

## 🔧 고급 사용법

### 1. 프로그래밍 인터페이스

```python
from unified_ml_pipeline import UnifiedMLPipeline
import pandas as pd

# 파이프라인 초기화
pipeline = UnifiedMLPipeline("logi_costguard_ml_v2/config/schema.json")

# 통합 학습
invoice_data = pd.read_excel("DSV_SHPT_ALL.xlsx")
matching_data = pd.read_json("training_data.json")
result = pipeline.train_all(invoice_data, matching_data, "output")

# 통합 예측
approved_lanes = pd.read_csv("ApprovedLaneMap.csv").to_dict('records')
results = pipeline.predict_all(invoice_data, approved_lanes, "output/models")

# A/B 테스트
default_weights = {'token_set': 0.4, 'levenshtein': 0.3, 'fuzzy_sort': 0.3}
ml_weights = {'token_set': 0.45, 'levenshtein': 0.25, 'fuzzy_sort': 0.30}
ab_result = pipeline.run_ab_test(invoice_data, approved_lanes, default_weights, ml_weights, "output")
```

### 2. 설정 파일 커스터마이징

`logi_costguard_ml_v2/config/schema.json` 파일을 수정하여 시스템 동작을 조정할 수 있습니다:

```json
{
  "cols": {
    "date": ["InvoiceDate", "Date"],
    "origin": ["Origin", "POL", "From"],
    "dest": ["Destination", "POD", "To"],
    // ... 기타 컬럼 매핑
  },
  "guard": {
    "tolerance": 3.0,      // 허용 오차 (%)
    "auto_fail": 15.0,     // 자동 실패 임계값 (%)
    "bands": {
      "pass": 2.0,         // PASS 밴드
      "warn": 5.0,         // WARN 밴드
      "high": 10.0         // HIGH 밴드
    }
  },
  "lane_similarity_threshold": 0.6  // 레인 유사도 임계값
}
```

### 3. 모델 재학습

```bash
# 새로운 데이터로 재학습
python cli_unified.py retrain \
  --data new_invoice_data.xlsx \
  --weights-training-data new_training_data.json \
  --output-dir updated_models
```

---

## 📈 성능 모니터링

### 메트릭 파일 구조

학습 완료 후 `output/out/metrics.json` 파일에서 성능 메트릭을 확인할 수 있습니다:

```json
{
  "costguard_mape": 0.15,
  "weight_optimizer_accuracy": 0.91,
  "optimized_weights": {
    "token_set": 0.45,
    "levenshtein": 0.25,
    "fuzzy_sort": 0.30
  },
  "training_results": {
    "logistic": {"accuracy": 0.89, "precision": 0.87, "recall": 0.91, "f1": 0.889},
    "random_forest": {"accuracy": 0.91, "precision": 0.89, "recall": 0.93, "f1": 0.909},
    "gradient_boosting": {"accuracy": 0.90, "precision": 0.88, "recall": 0.92, "f1": 0.899}
  }
}
```

### 성능 임계값

| 메트릭 | 목표 값 | 설명 |
|--------|---------|------|
| **CostGuard MAPE** | < 0.15 | 회귀 예측 평균 절대 백분율 오차 |
| **Weight Optimizer Accuracy** | > 0.90 | 매칭 가중치 최적화 정확도 |
| **Match Rate** | > 0.85 | 전체 매칭 성공률 |
| **ML Enhancement Rate** | > 0.20 | ML 가중치로 향상된 매칭 비율 |

---

## 🛠️ 문제 해결

### 일반적인 문제들

#### Q1: 모델 파일이 생성되지 않음
```bash
# 해결책: 충분한 데이터 확보
# 최소 요구사항: 송장 데이터 10개 이상, 매칭 데이터 20개 이상
```

#### Q2: 테스트 실패
```bash
# 해결책: 의존성 재설치
pip install -r requirements.txt --upgrade

# pytest 캐시 삭제
pytest --cache-clear
```

#### Q3: 메모리 부족
```bash
# 해결책: 배치 크기 조정
# config 파일에서 모델 파라미터 조정
```

### 로그 및 디버깅

```python
# 상세 로그 활성화
import logging
logging.basicConfig(level=logging.DEBUG)

# 파이프라인 실행
pipeline = UnifiedMLPipeline("config/schema.json")
result = pipeline.train_all(invoice_data, matching_data, "output")
```

---

## 🔄 CI/CD 통합

### GitHub Actions 예시

```yaml
name: ML Integration Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        cd ML
        pip install -r requirements.txt

    - name: Run integration tests
      run: |
        cd ML
        python -m pytest test_integration_e2e.py -v

    - name: Run CLI tests
      run: |
        cd ML
        python cli_unified.py --help
```

---

## 📚 참고 문서

- [README.md](README.md) - 프로젝트 개요
- [IMPLEMENTATION_REPORT.md](IMPLEMENTATION_REPORT.md) - 구현 상세 리포트
- [Executive Summary.MD](Executive%20Summary.MD) - 요구사항 및 전략
- [logi_costguard_ml_v2/README.md](logi_costguard_ml_v2/README.md) - CostGuard 시스템 문서

---

## 👥 기여자

- **개발**: MACHO-GPT TDD 방식 구현
- **테스트**: 8개 E2E 통합 테스트 (100% 통과)
- **문서화**: 통합 가이드 및 CLI 인터페이스

---

## 📄 라이선스

HVDC Project - Samsung C&T Logistics & ADNOC·DSV Partnership

---

## 🔧 MACHO-GPT 추천 명령어

**/logi-master invoice-audit --unified-ml** → 통합 ML 파이프라인으로 전체 송장 감사 실행

**/visualize-data --type=integration-performance** → 통합 시스템 성능 시각화 (CostGuard + Weight Optimizer)

**/automate unified-ml-pipeline** → 통합 ML 파이프라인 자동화 설정 (학습 → 예측 → A/B 테스트 → 재학습)
