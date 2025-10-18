# ML Systems Integration - 개발자 가이드

## 개요

이 문서는 ML Systems Integration을 개발하고 확장하는 개발자를 위한 기술 가이드입니다. 프로젝트 구조, 개발 환경 설정, TDD 프로세스, 코드 스타일, 확장 포인트를 다룹니다.

## 프로젝트 구조

### 디렉토리 구조
```
ML/
├── docs/                          # 문서화
│   ├── ARCHITECTURE.md            # 시스템 아키텍처
│   ├── DIAGRAMS.md                # 다이어그램 컬렉션
│   ├── EXECUTION_LOGIC.md         # 실행 로직 상세
│   ├── EXECUTION_REPORT.md        # 실행 결과 보고서
│   ├── USER_GUIDE.md              # 사용자 가이드
│   ├── DEVELOPER_GUIDE.md         # 개발자 가이드 (이 파일)
│   └── INTEGRATION_SUMMARY.md     # 종합 요약
├── logi_costguard_ml_v2/          # CostGuard ML v2 시스템
│   ├── src/                       # 소스 코드
│   │   ├── model_reg.py           # 회귀 모델
│   │   ├── model_iso.py           # 이상탐지 모델
│   │   ├── similarity.py          # 유사도 계산
│   │   ├── rules_ref.py           # 참조 규칙
│   │   └── guard.py               # 밴딩 로직
│   ├── config/                    # 설정 파일
│   │   └── schema.json            # 데이터 스키마
│   ├── data/                      # 데이터 파일
│   │   └── DSV SHPT ALL.xlsx      # 송장 데이터
│   ├── ref/                       # 참조 데이터
│   │   └── inland_trucking_reference_rates_clean (2).json
│   ├── train.py                   # 학습 스크립트
│   └── predict.py                 # 예측 스크립트
├── unified_ml_pipeline.py         # 통합 ML 파이프라인 (핵심)
├── cli_unified.py                 # CLI 인터페이스
├── weight_optimizer.py            # 가중치 최적화
├── training_data_generator.py     # 학습 데이터 생성
├── ab_testing_framework.py        # A/B 테스트 프레임워크
├── test_integration_e2e.py        # E2E 통합 테스트
├── test_*.py                      # 단위 테스트들
├── training_data.json             # 매칭 학습 데이터
├── requirements.txt               # 의존성 패키지
├── README.md                      # 메인 README
└── INTEGRATION_GUIDE.md           # 통합 가이드
```

### 핵심 모듈 설명

#### 1. unified_ml_pipeline.py
- **역할**: 두 ML 시스템을 통합하는 핵심 오케스트레이터
- **주요 클래스**: `UnifiedMLPipeline`
- **핵심 메서드**: `train_all()`, `predict_all()`, `run_ab_test()`

#### 2. weight_optimizer.py
- **역할**: ML 기반 가중치 최적화
- **주요 클래스**: `WeightOptimizer`
- **지원 알고리즘**: Logistic Regression, Random Forest, Gradient Boosting

#### 3. ab_testing_framework.py
- **역할**: Default vs ML weights 성능 비교
- **주요 클래스**: `ABTestingFramework`
- **메트릭**: Accuracy, Precision, Recall, F1

#### 4. logi_costguard_ml_v2/
- **역할**: 회귀 예측 및 이상탐지
- **주요 모델**: RandomForest, GradientBoosting, IsolationForest
- **기능**: Rate 예측, Anomaly detection, Lane matching

## 개발 환경 설정

### 1. 필수 요구사항

#### 시스템 요구사항
- **Python**: 3.8 이상 (권장: 3.9+)
- **메모리**: 최소 4GB RAM (권장: 8GB+)
- **디스크**: 최소 1GB 여유 공간
- **OS**: Windows 10+, macOS 10.15+, Ubuntu 18.04+

#### Python 패키지
```bash
# 핵심 의존성
pytest==8.4.1
pandas==2.2.0
numpy==1.26.4
scikit-learn==1.4.0
joblib==1.3.2

# 개발 도구
black==23.12.1
flake8==7.0.0
mypy==1.8.0
pre-commit==3.6.0
```

### 2. 개발 환경 구축

#### 가상환경 설정
```bash
# Python 가상환경 생성
python -m venv venv

# 가상환경 활성화 (Windows)
venv\Scripts\activate

# 가상환경 활성화 (Linux/macOS)
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt
```

#### IDE 설정 (VSCode)
```json
// .vscode/settings.json
{
    "python.defaultInterpreterPath": "./venv/Scripts/python.exe",
    "python.formatting.provider": "black",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.linting.mypyEnabled": true,
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": [
        "."
    ]
}
```

#### Pre-commit 설정
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
        language_version: python3.9
  - repo: https://github.com/pycqa/flake8
    rev: 7.0.0
    hooks:
      - id: flake8
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
```

```bash
# Pre-commit 설치 및 설정
pip install pre-commit
pre-commit install
```

## TDD 개발 프로세스

### 1. TDD 사이클 (RED → GREEN → REFACTOR)

#### RED Phase: 실패 테스트 작성
```python
# test_new_feature.py
def test_should_calculate_weighted_similarity():
    """RED: 실패하는 테스트 작성"""
    # Given: 테스트 데이터
    origin_inv = "DSV Mussafah Yard"
    origin_lane = "DSV Mussafah Yard"

    # When: 가중치 적용 유사도 계산
    result = calculate_weighted_similarity(origin_inv, origin_lane, weights)

    # Then: 예상 결과 검증
    assert result == 1.0  # 이 테스트는 실패할 것
```

#### GREEN Phase: 최소 구현
```python
# weight_optimizer.py
def calculate_weighted_similarity(text1: str, text2: str, weights: dict) -> float:
    """GREEN: 테스트를 통과시키기 위한 최소 구현"""
    return 1.0  # 하드코딩된 값으로 테스트 통과
```

#### REFACTOR Phase: 구조 개선
```python
# weight_optimizer.py
def calculate_weighted_similarity(text1: str, text2: str, weights: dict) -> float:
    """REFACTOR: 구조 개선 (행위 불변)"""
    if text1 == text2:
        return 1.0

    # 실제 유사도 계산 로직
    token_set_sim = token_set_ratio(text1, text2) / 100.0
    levenshtein_sim = levenshtein_ratio(text1, text2) / 100.0
    fuzzy_sort_sim = fuzz.token_sort_ratio(text1, text2) / 100.0

    weighted_score = (
        weights['token_set'] * token_set_sim +
        weights['levenshtein'] * levenshtein_sim +
        weights['fuzzy_sort'] * fuzzy_sort_sim
    )

    return weighted_score
```

### 2. 테스트 작성 가이드라인

#### 테스트 명명 규칙
```python
# 패턴: test_should_[expected_behavior]_when_[condition]
def test_should_return_exact_match_when_origin_destination_identical():
    pass

def test_should_return_high_score_when_similarity_above_threshold():
    pass

def test_should_fallback_to_default_when_model_loading_fails():
    pass
```

#### 테스트 구조 (Given-When-Then)
```python
def test_should_predict_rate_with_high_confidence():
    """Given-When-Then 패턴으로 테스트 구조화"""
    # Given: 준비된 데이터와 모델
    invoice_data = create_sample_invoice_data()
    trained_model = load_trained_model()

    # When: 예측 실행
    result = predict_rate(invoice_data, trained_model)

    # Then: 결과 검증
    assert result['confidence'] > 0.9
    assert 'rate_prediction' in result
    assert result['rate_prediction'] > 0
```

#### Fixture 사용
```python
# conftest.py
@pytest.fixture
def sample_invoice_data():
    """테스트용 송장 데이터"""
    return pd.DataFrame({
        'Origin': ['DSV Mussafah Yard', 'Jebel Ali Port'],
        'Destination': ['Mirfa PMO Site', 'Shuweihat Power Station'],
        'Rate': [5000, 7500],
        'Qty': [1, 2]
    })

@pytest.fixture
def sample_weights():
    """테스트용 가중치"""
    return {
        'token_set': 0.4,
        'levenshtein': 0.3,
        'fuzzy_sort': 0.3
    }
```

### 3. TDD 모범 사례

#### 한 번에 하나씩
```python
# ❌ 나쁜 예: 여러 기능을 한 번에 테스트
def test_should_train_and_predict_and_evaluate():
    pass

# ✅ 좋은 예: 각 기능을 개별적으로 테스트
def test_should_train_model_successfully():
    pass

def test_should_predict_with_trained_model():
    pass

def test_should_evaluate_prediction_accuracy():
    pass
```

#### 명확한 실패 메시지
```python
def test_should_calculate_correct_mape():
    # Given
    actual = [100, 200, 300]
    predicted = [110, 190, 290]

    # When
    mape = calculate_mape(actual, predicted)

    # Then - 명확한 실패 메시지
    assert mape < 0.1, f"MAPE {mape} should be less than 10%"
```

## 코드 스타일 가이드

### 1. Black 포맷팅

#### 자동 포맷팅
```bash
# 전체 프로젝트 포맷팅
black .

# 특정 파일 포맷팅
black unified_ml_pipeline.py

# 체크만 (변경하지 않음)
black --check .
```

#### Black 설정 (.black.toml)
```toml
[tool.black]
line-length = 88
target-version = ['py39']
include = '\.pyi?$'
extend-exclude = '''
/(
  # directories
  \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | build
  | dist
)/
'''
```

### 2. 타입 힌트

#### 기본 타입 힌트
```python
from typing import Dict, List, Optional, Union
import pandas as pd

def train_model(
    data: pd.DataFrame,
    target_column: str,
    model_type: str = "random_forest"
) -> Dict[str, float]:
    """모델 학습 함수"""
    pass

def predict_batch(
    model: object,
    features: List[List[float]]
) -> List[float]:
    """배치 예측 함수"""
    pass
```

#### 복합 타입 힌트
```python
from typing import TypedDict, Protocol

class ModelMetrics(TypedDict):
    accuracy: float
    precision: float
    recall: float
    f1: float

class ModelProtocol(Protocol):
    def fit(self, X: pd.DataFrame, y: pd.Series) -> None:
        ...

    def predict(self, X: pd.DataFrame) -> List[float]:
        ...

def evaluate_model(
    model: ModelProtocol,
    X_test: pd.DataFrame,
    y_test: pd.Series
) -> ModelMetrics:
    """모델 평가 함수"""
    pass
```

### 3. 문서화 스타일

#### Docstring (Google 스타일)
```python
def calculate_weighted_similarity(
    text1: str,
    text2: str,
    weights: Dict[str, float]
) -> float:
    """
    가중치를 적용한 텍스트 유사도를 계산합니다.

    Args:
        text1: 첫 번째 텍스트
        text2: 두 번째 텍스트
        weights: 가중치 딕셔너리 (token_set, levenshtein, fuzzy_sort)

    Returns:
        float: 0.0 ~ 1.0 사이의 유사도 점수

    Raises:
        ValueError: weights에 필수 키가 없을 때
        TypeError: 입력 텍스트가 문자열이 아닐 때

    Example:
        >>> weights = {'token_set': 0.4, 'levenshtein': 0.3, 'fuzzy_sort': 0.3}
        >>> calculate_weighted_similarity("DSV Yard", "DSV Yard", weights)
        1.0
    """
    pass
```

#### 클래스 문서화
```python
class WeightOptimizer:
    """
    ML 기반 가중치 최적화 클래스.

    다양한 머신러닝 알고리즘을 사용하여 유사도 매칭에 최적화된
    가중치를 학습합니다.

    Attributes:
        models: 학습된 모델 딕셔너리
        weights: 최적화된 가중치
        training_results: 학습 결과 메트릭

    Example:
        >>> optimizer = WeightOptimizer()
        >>> optimizer.train(training_data)
        >>> weights = optimizer.extract_weights()
    """

    def __init__(self):
        """WeightOptimizer 인스턴스를 초기화합니다."""
        self.models = {}
        self.weights = {}
        self.training_results = {}
```

### 4. 에러 처리

#### 예외 계층 구조
```python
class MLIntegrationError(Exception):
    """ML 통합 시스템의 기본 예외 클래스"""
    pass

class ModelTrainingError(MLIntegrationError):
    """모델 학습 중 발생하는 예외"""
    pass

class PredictionError(MLIntegrationError):
    """예측 중 발생하는 예외"""
    pass

class DataValidationError(MLIntegrationError):
    """데이터 검증 중 발생하는 예외"""
    pass
```

#### 예외 처리 패턴
```python
def train_model_safely(data: pd.DataFrame) -> Dict[str, Any]:
    """안전한 모델 학습"""
    try:
        # 모델 학습 시도
        result = train_model(data)
        return result
    except FileNotFoundError as e:
        logger.error(f"데이터 파일을 찾을 수 없습니다: {e}")
        raise DataValidationError(f"데이터 파일 없음: {e}") from e
    except ValueError as e:
        logger.error(f"데이터 형식 오류: {e}")
        raise DataValidationError(f"데이터 형식 오류: {e}") from e
    except Exception as e:
        logger.error(f"예상치 못한 오류: {e}")
        raise ModelTrainingError(f"학습 실패: {e}") from e
```

## 확장 포인트

### 1. 새로운 ML 알고리즘 추가

#### 새로운 회귀 모델 추가
```python
# src/model_reg.py에 추가
def build_xgboost_regressor(df: pd.DataFrame) -> XGBRegressor:
    """XGBoost 회귀 모델 빌드"""
    features = ['origin_canon', 'dest_canon', 'category', 'uom', 'log_qty', 'log_wt', 'log_cbm']
    X = df[features].fillna(df[features].median())
    y = df['rate_usd']

    model = XGBRegressor(
        n_estimators=100,
        max_depth=6,
        learning_rate=0.1,
        random_state=42
    )

    model.fit(X, y)
    return model

# train_reg 함수에 통합
def train_reg(df: pd.DataFrame, models_dir: str) -> Dict[str, float]:
    """회귀 모델 학습 (확장된 버전)"""
    results = {}

    # 기존 모델들
    results['rf'] = build_rf(df)
    results['gb'] = build_gb_quantile(df)

    # 새로운 XGBoost 모델
    results['xgb'] = build_xgboost_regressor(df)

    # 모델 저장
    dump(results['xgb'], f"{models_dir}/rate_xgb.joblib")

    return results
```

#### 새로운 가중치 학습 알고리즘 추가
```python
# weight_optimizer.py에 추가
from sklearn.neural_network import MLPClassifier
from sklearn.svm import SVC

class WeightOptimizer:
    def __init__(self):
        self.models = {
            'logistic': LogisticRegression(random_state=42),
            'random_forest': RandomForestClassifier(random_state=42),
            'gradient_boosting': GradientBoostingClassifier(random_state=42),
            # 새로운 모델들
            'neural_network': MLPClassifier(hidden_layer_sizes=(100, 50), random_state=42),
            'svm': SVC(probability=True, random_state=42)
        }

    def train(self, data: pd.DataFrame, test_size: float = 0.2) -> Dict[str, Dict[str, float]]:
        """확장된 학습 메서드"""
        # 기존 로직 + 새로운 모델들도 학습
        pass
```

### 2. 새로운 유사도 메트릭 추가

#### 사용자 정의 유사도 함수
```python
# similarity.py에 추가
from sentence_transformers import SentenceTransformer
import numpy as np

class AdvancedSimilarityCalculator:
    """고급 유사도 계산 클래스"""

    def __init__(self):
        self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')

    def semantic_similarity(self, text1: str, text2: str) -> float:
        """의미적 유사도 계산 (Sentence Transformers 사용)"""
        embeddings = self.sentence_model.encode([text1, text2])
        similarity = np.dot(embeddings[0], embeddings[1]) / (
            np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1])
        )
        return float(similarity)

    def phonetic_similarity(self, text1: str, text2: str) -> float:
        """음성적 유사도 계산 (Soundex 알고리즘)"""
        from fuzzy import soundex
        return 1.0 if soundex(text1) == soundex(text2) else 0.0

# hybrid_similarity_ml 함수 확장
def hybrid_similarity_ml(text1: str, text2: str, weights: Dict[str, float]) -> float:
    """확장된 하이브리드 유사도 계산"""
    calculator = AdvancedSimilarityCalculator()

    # 기존 메트릭들
    token_set_sim = token_set_ratio(text1, text2) / 100.0
    levenshtein_sim = levenshtein_ratio(text1, text2) / 100.0
    fuzzy_sort_sim = fuzz.token_sort_ratio(text1, text2) / 100.0

    # 새로운 메트릭들
    semantic_sim = calculator.semantic_similarity(text1, text2)
    phonetic_sim = calculator.phonetic_similarity(text1, text2)

    # 가중 평균 계산
    weighted_score = (
        weights.get('token_set', 0.3) * token_set_sim +
        weights.get('levenshtein', 0.2) * levenshtein_sim +
        weights.get('fuzzy_sort', 0.2) * fuzzy_sort_sim +
        weights.get('semantic', 0.2) * semantic_sim +
        weights.get('phonetic', 0.1) * phonetic_sim
    )

    return weighted_score
```

### 3. 새로운 데이터 소스 통합

#### API 데이터 소스 추가
```python
# data_sources.py (새 파일)
import requests
from typing import Dict, List, Optional
import pandas as pd

class APIDataSource:
    """API를 통한 데이터 소스 클래스"""

    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({'Authorization': f'Bearer {api_key}'})

    def fetch_invoice_data(self, date_from: str, date_to: str) -> pd.DataFrame:
        """API에서 송장 데이터 가져오기"""
        url = f"{self.base_url}/invoices"
        params = {
            'date_from': date_from,
            'date_to': date_to,
            'format': 'json'
        }

        response = self.session.get(url, params=params)
        response.raise_for_status()

        data = response.json()
        return pd.DataFrame(data['invoices'])

    def fetch_reference_rates(self) -> List[Dict]:
        """API에서 참조 레이트 가져오기"""
        url = f"{self.base_url}/reference-rates"
        response = self.session.get(url)
        response.raise_for_status()

        return response.json()['rates']

# unified_ml_pipeline.py에 통합
class UnifiedMLPipeline:
    def __init__(self, config_path: str, data_source: Optional[APIDataSource] = None):
        self.config_path = config_path
        self.config = self._load_config()
        self.data_source = data_source
        # ... 기존 초기화 코드

    def train_from_api(self, date_from: str, date_to: str, output_dir: str) -> Dict[str, Any]:
        """API 데이터 소스에서 학습"""
        if not self.data_source:
            raise ValueError("API 데이터 소스가 설정되지 않았습니다")

        # API에서 데이터 가져오기
        invoice_data = self.data_source.fetch_invoice_data(date_from, date_to)
        reference_rates = self.data_source.fetch_reference_rates()

        # 기존 학습 로직 사용
        return self.train_all(invoice_data, None, output_dir)
```

### 4. 실시간 처리 파이프라인

#### 스트리밍 데이터 처리
```python
# streaming_pipeline.py (새 파일)
import asyncio
from typing import AsyncGenerator, Dict, Any
import pandas as pd

class StreamingMLPipeline:
    """실시간 스트리밍 ML 파이프라인"""

    def __init__(self, pipeline: UnifiedMLPipeline):
        self.pipeline = pipeline
        self.buffer = []
        self.buffer_size = 100

    async def process_stream(self, data_stream: AsyncGenerator[Dict, None]) -> AsyncGenerator[Dict, None]:
        """스트림 데이터 실시간 처리"""
        async for data_point in data_stream:
            self.buffer.append(data_point)

            # 버퍼가 가득 찼을 때 배치 처리
            if len(self.buffer) >= self.buffer_size:
                batch_df = pd.DataFrame(self.buffer)
                results = await self._process_batch(batch_df)

                # 결과 스트림으로 전송
                for result in results:
                    yield result

                self.buffer = []

    async def _process_batch(self, batch_df: pd.DataFrame) -> List[Dict]:
        """배치 데이터 처리"""
        # 비동기로 예측 실행
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            None,
            self.pipeline.predict_all,
            batch_df,
            [],  # approved_lanes
            "temp_output"
        )
        return results

# 사용 예시
async def main():
    pipeline = UnifiedMLPipeline("config/schema.json")
    streaming_pipeline = StreamingMLPipeline(pipeline)

    async def data_generator():
        """실시간 데이터 생성기 (예시)"""
        while True:
            yield {"Origin": "DSV Yard", "Destination": "Site", "Rate": 5000}
            await asyncio.sleep(1)

    async for result in streaming_pipeline.process_stream(data_generator()):
        print(f"Processed: {result}")

# 실행
asyncio.run(main())
```

## 성능 최적화

### 1. 메모리 최적화

#### 메모리 효율적인 데이터 처리
```python
def process_large_dataset_efficiently(file_path: str, chunk_size: int = 1000):
    """대용량 데이터셋을 메모리 효율적으로 처리"""

    # 청크 단위로 데이터 읽기
    chunks = pd.read_excel(file_path, chunksize=chunk_size)

    results = []
    for chunk in chunks:
        # 필요한 컬럼만 선택
        chunk = chunk[['Origin', 'Destination', 'Rate', 'Qty']]

        # 데이터 타입 최적화
        chunk['Rate'] = chunk['Rate'].astype('float32')
        chunk['Qty'] = chunk['Qty'].astype('int32')

        # 처리
        processed_chunk = process_chunk(chunk)
        results.append(processed_chunk)

    # 결과 합치기
    return pd.concat(results, ignore_index=True)
```

#### 메모리 프로파일링
```python
# memory_profiler 사용
from memory_profiler import profile

@profile
def memory_intensive_function(data: pd.DataFrame):
    """메모리 사용량 프로파일링"""
    # 메모리 집약적인 작업
    large_matrix = data.values @ data.values.T
    return large_matrix

# 실행: python -m memory_profiler script.py
```

### 2. 처리 속도 최적화

#### 병렬 처리
```python
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing as mp

def parallel_prediction(invoice_data: pd.DataFrame, approved_lanes: List[Dict],
                       models_dir: str, n_workers: int = None) -> List[Dict]:
    """병렬 예측 처리"""
    if n_workers is None:
        n_workers = mp.cpu_count()

    # 데이터를 청크로 분할
    chunk_size = len(invoice_data) // n_workers
    chunks = [invoice_data.iloc[i:i+chunk_size] for i in range(0, len(invoice_data), chunk_size)]

    # 병렬 처리
    with ProcessPoolExecutor(max_workers=n_workers) as executor:
        futures = [
            executor.submit(predict_chunk, chunk, approved_lanes, models_dir)
            for chunk in chunks
        ]

        results = []
        for future in futures:
            results.extend(future.result())

    return results

def predict_chunk(chunk: pd.DataFrame, approved_lanes: List[Dict], models_dir: str) -> List[Dict]:
    """청크 단위 예측"""
    # 청크에 대한 예측 로직
    pass
```

#### 캐싱 최적화
```python
from functools import lru_cache
import joblib

class CachedMLPipeline:
    """캐싱이 적용된 ML 파이프라인"""

    def __init__(self, models_dir: str):
        self.models_dir = models_dir
        self._model_cache = {}

    @lru_cache(maxsize=128)
    def get_model(self, model_name: str):
        """모델 캐싱"""
        if model_name not in self._model_cache:
            model_path = f"{self.models_dir}/{model_name}.joblib"
            self._model_cache[model_name] = joblib.load(model_path)
        return self._model_cache[model_name]

    def predict_with_cache(self, data: pd.DataFrame, model_name: str) -> List[float]:
        """캐싱된 모델로 예측"""
        model = self.get_model(model_name)
        return model.predict(data)
```

## 테스트 전략

### 1. 테스트 피라미드

```
        /\
       /  \
      /E2E \     (소수, 느림, 통합)
     /______\
    /        \
   /Integration\ (중간, 중간 속도, 컴포넌트 간)
  /______________\
 /                \
/     Unit Tests    \ (다수, 빠름, 단위)
/____________________\
```

#### Unit Tests (70%)
```python
def test_weight_calculation():
    """단위 테스트: 가중치 계산"""
    pass

def test_similarity_score():
    """단위 테스트: 유사도 점수"""
    pass
```

#### Integration Tests (20%)
```python
def test_model_training_integration():
    """통합 테스트: 모델 학습"""
    pass

def test_prediction_pipeline():
    """통합 테스트: 예측 파이프라인"""
    pass
```

#### E2E Tests (10%)
```python
def test_end_to_end_workflow():
    """E2E 테스트: 전체 워크플로우"""
    pass
```

### 2. 테스트 데이터 관리

#### 테스트 데이터 생성
```python
# test_data_factory.py
class TestDataFactory:
    """테스트 데이터 팩토리"""

    @staticmethod
    def create_invoice_data(n_samples: int = 100) -> pd.DataFrame:
        """송장 테스트 데이터 생성"""
        return pd.DataFrame({
            'Origin': [f"Origin_{i}" for i in range(n_samples)],
            'Destination': [f"Destination_{i}" for i in range(n_samples)],
            'Rate': np.random.uniform(1000, 10000, n_samples),
            'Qty': np.random.randint(1, 10, n_samples)
        })

    @staticmethod
    def create_matching_data(n_samples: int = 1000) -> pd.DataFrame:
        """매칭 테스트 데이터 생성"""
        return pd.DataFrame({
            'origin_invoice': [f"Origin_{i}" for i in range(n_samples)],
            'dest_invoice': [f"Destination_{i}" for i in range(n_samples)],
            'origin_lane': [f"Origin_{i}" for i in range(n_samples)],
            'dest_lane': [f"Destination_{i}" for i in range(n_samples)],
            'label': np.random.randint(0, 2, n_samples)
        })
```

### 3. 성능 테스트

#### 벤치마크 테스트
```python
import time
import pytest

@pytest.mark.benchmark
def test_prediction_performance(benchmark):
    """예측 성능 벤치마크"""
    pipeline = UnifiedMLPipeline("config/schema.json")
    test_data = TestDataFactory.create_invoice_data(1000)

    def predict_batch():
        return pipeline.predict_all(test_data, [], "temp_output")

    result = benchmark(predict_batch)
    assert len(result) == 1000

@pytest.mark.benchmark
def test_training_performance(benchmark):
    """학습 성능 벤치마크"""
    pipeline = UnifiedMLPipeline("config/schema.json")
    invoice_data = TestDataFactory.create_invoice_data(1000)
    matching_data = TestDataFactory.create_matching_data(1000)

    def train_models():
        return pipeline.train_all(invoice_data, matching_data, "temp_output")

    result = benchmark(train_models)
    assert result['costguard_mape'] < 0.25
```

## 배포 및 운영

### 1. Docker 컨테이너화

#### Dockerfile
```dockerfile
FROM python:3.9-slim

WORKDIR /app

# 시스템 의존성 설치
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 테스트 실행
RUN pytest

# 실행 권한 부여
RUN chmod +x cli_unified.py

# 기본 명령어
CMD ["python", "cli_unified.py", "--help"]
```

#### Docker Compose
```yaml
# docker-compose.yml
version: '3.8'

services:
  ml-pipeline:
    build: .
    volumes:
      - ./data:/app/data
      - ./output:/app/output
    environment:
      - PYTHONPATH=/app
    command: python cli_unified.py train --data data/invoice_data.xlsx

  ml-api:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./models:/app/models
    command: python -m uvicorn api:app --host 0.0.0.0 --port 8000
```

### 2. CI/CD 파이프라인

#### GitHub Actions
```yaml
# .github/workflows/ci.yml
name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt

    - name: Run tests
      run: |
        pytest --cov=. --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v3

    - name: Build Docker image
      run: docker build -t ml-pipeline .

    - name: Run integration tests
      run: docker run --rm ml-pipeline pytest test_integration_e2e.py
```

### 3. 모니터링 및 로깅

#### 로깅 설정
```python
# logging_config.py
import logging
import sys
from logging.handlers import RotatingFileHandler

def setup_logging(log_level: str = "INFO", log_file: str = "ml_pipeline.log"):
    """로깅 설정"""

    # 로거 생성
    logger = logging.getLogger("ml_pipeline")
    logger.setLevel(getattr(logging, log_level.upper()))

    # 포맷터 설정
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 콘솔 핸들러
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 파일 핸들러 (로테이션)
    file_handler = RotatingFileHandler(
        log_file, maxBytes=10*1024*1024, backupCount=5
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger

# 사용 예시
logger = setup_logging()
logger.info("ML Pipeline started")
logger.error("Training failed", exc_info=True)
```

#### 성능 모니터링
```python
# monitoring.py
import time
import psutil
from functools import wraps

def monitor_performance(func):
    """성능 모니터링 데코레이터"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024

        try:
            result = func(*args, **kwargs)
            return result
        finally:
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss / 1024 / 1024

            logger.info(f"{func.__name__} - "
                       f"Time: {end_time - start_time:.2f}s, "
                       f"Memory: {end_memory - start_memory:.2f}MB")

    return wrapper

# 사용 예시
@monitor_performance
def train_model(data):
    """성능 모니터링이 적용된 모델 학습"""
    pass
```

---

이 개발자 가이드를 통해 ML Systems Integration을 효과적으로 개발하고 확장할 수 있습니다. 추가 질문이나 개선 사항이 있으면 이슈를 등록해 주세요.
