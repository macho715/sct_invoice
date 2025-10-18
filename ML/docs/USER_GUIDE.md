# ML Systems Integration - 사용자 가이드

## 개요

이 가이드는 ML Systems Integration을 사용하는 사용자를 위한 실용적인 가이드입니다. 빠른 시작부터 고급 사용법까지 모든 내용을 다룹니다.

## 빠른 시작

### 1. 환경 설정

#### 필수 요구사항
- Python 3.8 이상
- 필요한 패키지 설치

```bash
pip install -r requirements.txt
```

#### 필수 패키지
```
pytest==8.4.1
pandas==2.2.0
numpy==1.26.4
scikit-learn==1.4.0
joblib==1.3.2
```

### 2. 첫 번째 실행

#### 데이터 준비
```bash
# 송장 데이터 확인
ls logi_costguard_ml_v2/data/DSV\ SHPT\ ALL.xlsx

# 참조 레인 데이터 확인
ls logi_costguard_ml_v2/ref/inland_trucking_reference_rates_clean*.json

# 설정 파일 확인
ls logi_costguard_ml_v2/config/schema.json
```

#### 빠른 테스트 실행
```bash
# E2E 테스트 실행
pytest test_integration_e2e.py -v

# 전체 테스트 실행
pytest -v
```

## CLI 명령어 상세

### train 명령 - 모델 학습

#### 기본 사용법
```bash
python cli_unified.py train \
  --data "logi_costguard_ml_v2/data/DSV SHPT ALL.xlsx" \
  --weights-training-data training_data.json \
  --config "logi_costguard_ml_v2/config/schema.json" \
  --output-dir output
```

#### 매개변수 설명

| 매개변수 | 설명 | 필수 | 기본값 | 예시 |
|----------|------|------|--------|------|
| `--data` | 송장 데이터 파일 경로 | ✅ | - | `DSV SHPT ALL.xlsx` |
| `--weights-training-data` | 매칭 학습 데이터 | ✅ | - | `training_data.json` |
| `--config` | 설정 파일 경로 | ✅ | - | `schema.json` |
| `--output-dir` | 출력 디렉토리 | ❌ | `output` | `results/` |
| `--retrain` | 재학습 플래그 | ❌ | False | `--retrain` |

#### 실행 예시
```bash
# 기본 학습
python cli_unified.py train \
  --data "data/invoice_data.xlsx" \
  --weights-training-data "data/matching_data.json" \
  --config "config/schema.json"

# 재학습 (기존 모델 덮어쓰기)
python cli_unified.py train \
  --data "data/new_invoice_data.xlsx" \
  --weights-training-data "data/updated_matching_data.json" \
  --config "config/schema.json" \
  --retrain
```

#### 예상 출력
```
[START] Starting Unified ML Pipeline Training...
[DATA] Loading invoice data from data/invoice_data.xlsx
[DATA] Loading matching training data from data/matching_data.json
[INIT] Initializing pipeline with config: config/schema.json
[TRAIN] Training CostGuard and Weight Optimizer models...
[SUCCESS] Training completed!
[RESULT] CostGuard MAPE: 0.200
[RESULT] Weight Optimizer Accuracy: 0.952
[SAVE] Models saved to: output/models/
[SAVE] Metrics saved to: output/out/metrics.json
```

### predict 명령 - 예측 실행

#### 기본 사용법
```bash
python cli_unified.py predict \
  --data "logi_costguard_ml_v2/data/DSV SHPT ALL.xlsx" \
  --approved-lanes "logi_costguard_ml_v2/ref/inland_trucking_reference_rates_clean (2).json" \
  --models-dir output/models \
  --output output/prediction_results.xlsx
```

#### 매개변수 설명

| 매개변수 | 설명 | 필수 | 기본값 | 예시 |
|----------|------|------|--------|------|
| `--data` | 예측할 송장 데이터 | ✅ | - | `invoice_data.xlsx` |
| `--approved-lanes` | 승인된 레인 데이터 | ✅ | - | `reference_rates.json` |
| `--models-dir` | 학습된 모델 디렉토리 | ✅ | - | `output/models/` |
| `--output` | 결과 출력 파일 | ❌ | `prediction_results.xlsx` | `results.xlsx` |
| `--use-ml-weights` | ML 가중치 사용 | ❌ | False | `--use-ml-weights` |

#### 실행 예시
```bash
# 기본 예측 (Default 가중치)
python cli_unified.py predict \
  --data "data/invoice_data.xlsx" \
  --approved-lanes "data/reference_rates.json" \
  --models-dir "output/models"

# ML 가중치 사용 예측
python cli_unified.py predict \
  --data "data/invoice_data.xlsx" \
  --approved-lanes "data/reference_rates.json" \
  --models-dir "output/models" \
  --use-ml-weights \
  --output "results_ml.xlsx"
```

#### 예상 출력
```
[START] Starting Unified ML Pipeline Prediction...
[DATA] Loading invoice data from data/invoice_data.xlsx
[DATA] Loading approved lanes from data/reference_rates.json
[INIT] Initializing pipeline with config: schema.json
[SUCCESS] ML optimized weights loaded from output/models/optimized_weights.pkl
[SUCCESS] ML-optimized weights loaded
[PREDICT] Running prediction pipeline...
[SAVE] Saving results to prediction_results.xlsx

[SUCCESS] Prediction completed!
[STATS] Total items: 2016
[STATS] Matched items: 150 (7.4%)
[STATS] No match items: 1866

[STATS] Band Distribution:
  PASS: 120 (80.0%)
  WARN: 20 (13.3%)
  HIGH: 8 (5.3%)
  CRITICAL: 2 (1.3%)
  NA: 1866 (92.6%)
```

### ab-test 명령 - A/B 테스트

#### 기본 사용법
```bash
python cli_unified.py ab-test \
  --data "logi_costguard_ml_v2/data/DSV SHPT ALL.xlsx" \
  --approved-lanes "logi_costguard_ml_v2/ref/inland_trucking_reference_rates_clean (2).json" \
  --config "logi_costguard_ml_v2/config/schema.json" \
  --output output/ab_test_results.json
```

#### 매개변수 설명

| 매개변수 | 설명 | 필수 | 기본값 | 예시 |
|----------|------|------|--------|------|
| `--data` | 테스트 데이터 | ✅ | - | `test_data.xlsx` |
| `--approved-lanes` | 참조 레인 데이터 | ✅ | - | `reference_rates.json` |
| `--config` | 설정 파일 | ✅ | - | `schema.json` |
| `--output` | 결과 출력 파일 | ❌ | `ab_test_results.json` | `comparison.json` |

#### 실행 예시
```bash
# 기본 A/B 테스트
python cli_unified.py ab-test \
  --data "data/test_invoices.xlsx" \
  --approved-lanes "data/reference_rates.json" \
  --config "config/schema.json"

# 결과를 다른 파일에 저장
python cli_unified.py ab-test \
  --data "data/test_invoices.xlsx" \
  --approved-lanes "data/reference_rates.json" \
  --config "config/schema.json" \
  --output "performance_comparison.json"
```

#### 예상 출력
```
[START] Starting A/B Test...
[DATA] Loading test data from data/test_invoices.xlsx
[DATA] Loading approved lanes from data/reference_rates.json
[INIT] Initializing pipeline with config: schema.json
[TEST] Running A/B test comparison...
[SAVE] Saving A/B test results to ab_test_results.json

[SUCCESS] A/B Test completed!

[STATS] Performance Comparison:
Metric          Default      ML Optimized  Improvement
-------------------------------------------------------
Accuracy        0.850       0.910     +7.1%
Precision       0.820       0.890     +8.5%
Recall          0.870       0.920     +5.7%
F1              0.844       0.905     +7.2%
```

### retrain 명령 - 재학습

#### 기본 사용법
```bash
python cli_unified.py retrain \
  --data "logi_costguard_ml_v2/data/DSV SHPT ALL.xlsx" \
  --weights-training-data training_data.json \
  --config "logi_costguard_ml_v2/config/schema.json" \
  --models-dir output/models \
  --output-dir output
```

#### 매개변수 설명

| 매개변수 | 설명 | 필수 | 기본값 | 예시 |
|----------|------|------|--------|------|
| `--data` | 새로운 송장 데이터 | ✅ | - | `new_data.xlsx` |
| `--weights-training-data` | 새로운 매칭 데이터 | ✅ | - | `new_matching.json` |
| `--config` | 설정 파일 | ✅ | - | `schema.json` |
| `--models-dir` | 기존 모델 디렉토리 | ✅ | - | `models/` |
| `--output-dir` | 출력 디렉토리 | ❌ | `output` | `retrained/` |

#### 실행 예시
```bash
# 기본 재학습
python cli_unified.py retrain \
  --data "data/updated_invoices.xlsx" \
  --weights-training-data "data/new_matching_data.json" \
  --config "config/schema.json" \
  --models-dir "output/models"

# 다른 출력 디렉토리에 저장
python cli_unified.py retrain \
  --data "data/updated_invoices.xlsx" \
  --weights-training-data "data/new_matching_data.json" \
  --config "config/schema.json" \
  --models-dir "output/models" \
  --output-dir "retrained_models"
```

## 실전 사용 예시

### 시나리오 1: 새로운 데이터로 모델 학습

```bash
# 1단계: 데이터 준비 확인
ls data/
# invoice_data.xlsx
# matching_training_data.json
# schema.json

# 2단계: 모델 학습
python cli_unified.py train \
  --data "data/invoice_data.xlsx" \
  --weights-training-data "data/matching_training_data.json" \
  --config "data/schema.json" \
  --output-dir "models_v1"

# 3단계: 학습 결과 확인
ls models_v1/
# models/
#   rate_rf.joblib
#   iforest.joblib
#   optimized_weights.pkl
# out/
#   metrics.json

# 4단계: 메트릭 확인
cat models_v1/out/metrics.json
```

### 시나리오 2: 배치 예측 실행

```bash
# 1단계: 예측 실행 (Default 가중치)
python cli_unified.py predict \
  --data "data/new_invoices.xlsx" \
  --approved-lanes "data/reference_rates.json" \
  --models-dir "models_v1/models" \
  --output "predictions_default.xlsx"

# 2단계: ML 가중치로 예측
python cli_unified.py predict \
  --data "data/new_invoices.xlsx" \
  --approved-lanes "data/reference_rates.json" \
  --models-dir "models_v1/models" \
  --use-ml-weights \
  --output "predictions_ml.xlsx"

# 3단계: 결과 비교
python cli_unified.py ab-test \
  --data "data/new_invoices.xlsx" \
  --approved-lanes "data/reference_rates.json" \
  --config "data/schema.json" \
  --output "performance_comparison.json"
```

### 시나리오 3: 정기 재학습 파이프라인

```bash
#!/bin/bash
# retrain_pipeline.sh

echo "Starting retraining pipeline..."

# 1단계: 백업
cp -r models_current models_backup_$(date +%Y%m%d)

# 2단계: 재학습
python cli_unified.py retrain \
  --data "data/monthly_invoices.xlsx" \
  --weights-training-data "data/updated_matching_data.json" \
  --config "data/schema.json" \
  --models-dir "models_current/models" \
  --output-dir "models_new"

# 3단계: 성능 검증
python cli_unified.py ab-test \
  --data "data/validation_data.xlsx" \
  --approved-lanes "data/reference_rates.json" \
  --config "data/schema.json" \
  --output "validation_results.json"

# 4단계: 성능 확인 후 배포
python -c "
import json
with open('validation_results.json', 'r') as f:
    results = json.load(f)
improvement = results['improvement']['accuracy']
if improvement > 0.02:  # 2% 이상 개선
    print('Performance improved, deploying new models')
    import shutil
    shutil.rmtree('models_current')
    shutil.move('models_new', 'models_current')
else:
    print('Performance not improved, keeping current models')
    shutil.rmtree('models_new')
"

echo "Retraining pipeline completed"
```

## 문제 해결 (Troubleshooting)

### 일반적인 오류와 해결 방법

#### 1. 파일을 찾을 수 없음 오류

**오류 메시지:**
```
FileNotFoundError: [Errno 2] No such file or directory: 'data/invoice_data.xlsx'
```

**해결 방법:**
```bash
# 파일 경로 확인
ls -la data/
ls -la logi_costguard_ml_v2/data/

# 올바른 경로로 수정
python cli_unified.py train \
  --data "logi_costguard_ml_v2/data/DSV SHPT ALL.xlsx" \
  --weights-training-data training_data.json \
  --config "logi_costguard_ml_v2/config/schema.json"
```

#### 2. 컬럼 매핑 오류

**오류 메시지:**
```
ValueError: 필수 컬럼 누락: ['origin', 'dest', 'uom', 'currency']
```

**해결 방법:**
```bash
# 1. 데이터 구조 확인
python -c "
import pandas as pd
df = pd.read_excel('data/invoice_data.xlsx')
print('Columns:', df.columns.tolist())
print('Sample data:')
print(df.head())
"

# 2. 설정 파일 확인
cat logi_costguard_ml_v2/config/schema.json | grep -A 10 "column_mapping"

# 3. 데이터 전처리 또는 설정 파일 수정
```

#### 3. 메모리 부족 오류

**오류 메시지:**
```
MemoryError: Unable to allocate array
```

**해결 방법:**
```bash
# 1. 데이터 크기 확인
python -c "
import pandas as pd
df = pd.read_excel('data/invoice_data.xlsx')
print(f'Data shape: {df.shape}')
print(f'Memory usage: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB')
"

# 2. 데이터 샘플링
python cli_unified.py train \
  --data "data/invoice_sample.xlsx" \  # 작은 샘플 사용
  --weights-training-data training_data.json \
  --config "logi_costguard_ml_v2/config/schema.json"

# 3. 청크 단위 처리 (향후 구현 예정)
```

#### 4. 모델 로딩 오류

**오류 메시지:**
```
ModuleNotFoundError: No module named 'sklearn'
```

**해결 방법:**
```bash
# 1. 패키지 설치 확인
pip list | grep sklearn

# 2. 패키지 재설치
pip install scikit-learn==1.4.0

# 3. 가상환경 확인
python -c "import sklearn; print(sklearn.__version__)"
```

### 성능 최적화 팁

#### 1. 데이터 전처리 최적화

```python
# 효율적인 데이터 로딩
import pandas as pd

# 큰 파일의 경우 청크 단위로 읽기
chunks = pd.read_excel('large_file.xlsx', chunksize=1000)
for chunk in chunks:
    # 처리 로직
    process_chunk(chunk)

# 필요한 컬럼만 로드
columns = ['Origin', 'Destination', 'Rate', 'Qty']
df = pd.read_excel('data.xlsx', usecols=columns)
```

#### 2. 메모리 사용량 최적화

```python
# 데이터 타입 최적화
df['Rate'] = df['Rate'].astype('float32')  # float64 -> float32
df['Qty'] = df['Qty'].astype('int32')      # int64 -> int32

# 불필요한 컬럼 제거
df = df.drop(['Unnamed: 0', 'temp_column'], axis=1)
```

#### 3. 병렬 처리 활용

```bash
# 여러 데이터 파일 병렬 처리
python cli_unified.py predict \
  --data "data/batch1.xlsx" \
  --approved-lanes "data/reference_rates.json" \
  --models-dir "models/" &

python cli_unified.py predict \
  --data "data/batch2.xlsx" \
  --approved-lanes "data/reference_rates.json" \
  --models-dir "models/" &

wait  # 모든 백그라운드 작업 완료 대기
```

## FAQ

### Q1: 학습에 얼마나 시간이 걸리나요?

**A:** 데이터 크기에 따라 다릅니다:
- 소규모 데이터 (1,000행): 1-2분
- 중간 규모 (10,000행): 5-10분
- 대규모 데이터 (100,000행): 30-60분

### Q2: ML 가중치와 Default 가중치의 차이는 무엇인가요?

**A:**
- **Default 가중치**: 고정된 값 (token_set: 0.4, levenshtein: 0.3, fuzzy_sort: 0.3)
- **ML 가중치**: 학습 데이터를 통해 최적화된 값 (token_set: 0.45, levenshtein: 0.25, fuzzy_sort: 0.30)

### Q3: 언제 재학습을 해야 하나요?

**A:** 다음 경우에 재학습을 권장합니다:
- 새로운 데이터가 20% 이상 누적되었을 때
- 성능이 5% 이상 저하되었을 때
- 새로운 레인이나 카테고리가 추가되었을 때
- 월 1회 정기적으로

### Q4: 예측 결과에서 NA 밴드가 많은 이유는 무엇인가요?

**A:** NA 밴드는 다음 경우에 발생합니다:
- 레인 매칭이 되지 않았을 때
- 참조 레이트가 0일 때
- 데이터 오류가 있을 때

### Q5: A/B 테스트 결과를 어떻게 해석하나요?

**A:**
- **개선율 5% 이상**: ML 가중치 사용 권장
- **개선율 2-5%**: 추가 검증 후 결정
- **개선율 2% 미만**: Default 가중치 유지

### Q6: 모델 파일이 손상되었을 때 어떻게 복구하나요?

**A:**
```bash
# 1. 백업에서 복구
cp models_backup/rate_rf.joblib models/rate_rf.joblib
cp models_backup/iforest.joblib models/iforest.joblib
cp models_backup/optimized_weights.pkl models/optimized_weights.pkl

# 2. 재학습으로 복구
python cli_unified.py train \
  --data "data/backup_data.xlsx" \
  --weights-training-data "data/backup_matching.json" \
  --config "config/schema.json" \
  --output-dir "models_recovered"
```

## 고급 사용법

### 1. 사용자 정의 가중치 설정

```python
# custom_weights.py
custom_weights = {
    'token_set': 0.5,
    'levenshtein': 0.2,
    'fuzzy_sort': 0.3
}

# 가중치 파일로 저장
import pickle
with open('custom_weights.pkl', 'wb') as f:
    pickle.dump(custom_weights, f)
```

### 2. 배치 처리 스크립트

```bash
#!/bin/bash
# batch_predict.sh

DATA_DIR="data/batch"
OUTPUT_DIR="results/batch"
MODELS_DIR="models"

mkdir -p $OUTPUT_DIR

for file in $DATA_DIR/*.xlsx; do
    filename=$(basename "$file" .xlsx)
    echo "Processing $filename..."

    python cli_unified.py predict \
        --data "$file" \
        --approved-lanes "data/reference_rates.json" \
        --models-dir "$MODELS_DIR" \
        --use-ml-weights \
        --output "$OUTPUT_DIR/${filename}_results.xlsx"
done

echo "Batch processing completed"
```

### 3. 성능 모니터링

```python
# monitor_performance.py
import json
import pandas as pd
from datetime import datetime

def monitor_performance():
    # 메트릭 로드
    with open('output/out/metrics.json', 'r') as f:
        metrics = json.load(f)

    # 성능 기록
    performance_log = {
        'timestamp': datetime.now().isoformat(),
        'costguard_mape': metrics['costguard_mape'],
        'weight_accuracy': metrics['weight_optimizer_accuracy']
    }

    # 로그 저장
    with open('performance_log.json', 'a') as f:
        f.write(json.dumps(performance_log) + '\n')

    # 알림 (성능 저하 시)
    if metrics['costguard_mape'] > 0.25:
        print("WARNING: CostGuard MAPE exceeds threshold!")

    if metrics['weight_optimizer_accuracy'] < 0.80:
        print("WARNING: Weight Optimizer accuracy below threshold!")

if __name__ == "__main__":
    monitor_performance()
```

---

이 사용자 가이드를 통해 ML Systems Integration을 효과적으로 활용할 수 있습니다. 추가 질문이나 문제가 있으면 개발자 가이드를 참고하거나 이슈를 등록해 주세요.
