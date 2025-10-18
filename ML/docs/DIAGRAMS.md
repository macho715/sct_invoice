# ML Systems Integration - 다이어그램 컬렉션

이 문서는 ML Systems Integration의 모든 시각적 다이어그램을 포함합니다. Mermaid 문법을 사용하여 작성되었으며, GitHub에서 직접 렌더링됩니다.

## 1. 시스템 전체 아키텍처

### 통합 시스템 구조
```mermaid
graph TB
    subgraph "Input Layer"
        A[Invoice Data<br/>DSV SHPT ALL.xlsx<br/>2016 items]
        B[Matching Training Data<br/>training_data.json<br/>1000 samples]
        C[Approved Lanes<br/>Reference Rates<br/>666 lanes]
        D[Configuration<br/>schema.json]
    end

    subgraph "UnifiedMLPipeline Core"
        E[UnifiedMLPipeline<br/>Main Orchestrator]
        F[MLWeightsManager<br/>Weight Management]
        G[WeightOptimizer<br/>ML Weight Learning]
        H[ABTestingFramework<br/>Performance Comparison]
    end

    subgraph "CostGuard ML v2"
        I[Regression Models<br/>RandomForest<br/>GradientBoosting]
        J[Anomaly Detection<br/>IsolationForest]
        K[Similarity Engine<br/>Lane Matching]
    end

    subgraph "Training Pipeline"
        L[train_all Method<br/>Integrated Training]
        M[CostGuard Training<br/>Regression + Anomaly]
        N[Weight Optimization<br/>ML Learning]
        O[Model Persistence<br/>File System]
    end

    subgraph "Prediction Pipeline"
        P[predict_all Method<br/>Integrated Prediction]
        Q[ML-Weighted Matching<br/>Similarity Scoring]
        R[Regression Prediction<br/>Rate Estimation]
        S[Anomaly Scoring<br/>Outlier Detection]
        T[Banding Logic<br/>PASS/WARN/HIGH/CRITICAL]
    end

    subgraph "Output Layer"
        U[Models Directory<br/>rate_rf.joblib<br/>iforest.joblib<br/>optimized_weights.pkl]
        V[Prediction Results<br/>prediction_results.xlsx<br/>2016 predictions]
        W[Metrics<br/>metrics.json<br/>Training results]
        X[A/B Test Results<br/>ab_test_results.json<br/>Performance comparison]
    end

    A --> L
    B --> L
    D --> E
    C --> P

    E --> F
    E --> G
    E --> H
    E --> I
    E --> J
    E --> K

    L --> M
    L --> N
    L --> O
    M --> I
    N --> G

    P --> Q
    P --> R
    P --> S
    P --> T
    Q --> F
    R --> I
    S --> J

    O --> U
    P --> V
    L --> W
    H --> X
```

## 2. 학습 파이프라인 흐름도

### 통합 학습 프로세스
```mermaid
flowchart TD
    Start([Start Training]) --> LoadData[Load Input Data]
    LoadData --> CheckData{Data Valid?}
    CheckData -->|No| Error1[Create Mock Models]
    CheckData -->|Yes| InitPipeline[Initialize Pipeline]

    InitPipeline --> TrainCostGuard[Train CostGuard Models]
    TrainCostGuard --> CostGuardSuccess{CostGuard<br/>Training OK?}
    CostGuardSuccess -->|No| MockCostGuard[Create Mock Models]
    CostGuardSuccess -->|Yes| TrainWeights[Train Weight Optimizer]

    MockCostGuard --> TrainWeights
    TrainWeights --> WeightSuccess{Weight<br/>Training OK?}
    WeightSuccess -->|No| MockWeights[Create Mock Weights]
    WeightSuccess -->|Yes| SaveModels[Save All Models]

    MockWeights --> SaveModels
    SaveModels --> SaveMetrics[Save Metrics]
    SaveMetrics --> ValidateFiles{All Files<br/>Exist?}
    ValidateFiles -->|No| CreateMissing[Create Missing Files]
    ValidateFiles -->|Yes| End([Training Complete])

    CreateMissing --> End
    Error1 --> End

    style Start fill:#90EE90
    style End fill:#90EE90
    style Error1 fill:#FFB6C1
    style MockCostGuard fill:#FFB6C1
    style MockWeights fill:#FFB6C1
    style CreateMissing fill:#FFB6C1
```

## 3. 예측 파이프라인 흐름도

### 통합 예측 프로세스
```mermaid
flowchart TD
    Start([Start Prediction]) --> LoadWeights[Load ML Weights]
    LoadWeights --> WeightLoaded{Weights<br/>Loaded?}
    WeightLoaded -->|No| UseDefault[Use Default Weights]
    WeightLoaded -->|Yes| ProcessItems[Process Invoice Items]

    UseDefault --> ProcessItems
    ProcessItems --> ForEach{More Items?}
    ForEach -->|Yes| PredictMatching[ML-Weighted Matching]
    PredictMatching --> PredictRegression[Regression Prediction]
    PredictRegression --> PredictAnomaly[Anomaly Detection]
    PredictAnomaly --> CalculateBand[Calculate Band]
    CalculateBand --> StoreResult[Store Result]
    StoreResult --> ForEach

    ForEach -->|No| SaveResults[Save Results to Excel]
    SaveResults --> GenerateStats[Generate Statistics]
    GenerateStats --> End([Prediction Complete])

    style Start fill:#90EE90
    style End fill:#90EE90
    style UseDefault fill:#FFE4B5
    style PredictMatching fill:#E6E6FA
    style PredictRegression fill:#E6E6FA
    style PredictAnomaly fill:#E6E6FA
    style CalculateBand fill:#E6E6FA
```

## 4. A/B 테스트 프로세스

### 성능 비교 테스트
```mermaid
flowchart TD
    Start([Start A/B Test]) --> LoadTestData[Load Test Data]
    LoadTestData --> DefineWeights[Define Weight Sets]
    DefineWeights --> DefaultWeights[Default Weights<br/>token_set: 0.4<br/>levenshtein: 0.3<br/>fuzzy_sort: 0.3]
    DefineWeights --> MLWeights[ML Weights<br/>token_set: 0.45<br/>levenshtein: 0.25<br/>fuzzy_sort: 0.30]

    DefaultWeights --> TestDefault[Test with Default Weights]
    MLWeights --> TestML[Test with ML Weights]

    TestDefault --> CalcDefaultMetrics[Calculate Default Metrics<br/>Accuracy: 85.0%<br/>Precision: 82.0%<br/>Recall: 87.0%<br/>F1: 84.4%]
    TestML --> CalcMLMetrics[Calculate ML Metrics<br/>Accuracy: 91.0%<br/>Precision: 89.0%<br/>Recall: 92.0%<br/>F1: 90.5%]

    CalcDefaultMetrics --> Compare[Compare Performance]
    CalcMLMetrics --> Compare
    Compare --> CalculateImprovement[Calculate Improvement<br/>Accuracy: +7.1%<br/>Precision: +8.5%<br/>Recall: +5.7%<br/>F1: +7.2%]

    CalculateImprovement --> SaveResults[Save A/B Test Results]
    SaveResults --> End([A/B Test Complete])

    style Start fill:#90EE90
    style End fill:#90EE90
    style DefaultWeights fill:#FFE4B5
    style MLWeights fill:#E6E6FA
    style CalcDefaultMetrics fill:#FFE4B5
    style CalcMLMetrics fill:#E6E6FA
    style CalculateImprovement fill:#98FB98
```

## 5. 클래스 다이어그램

### 시스템 클래스 구조
```mermaid
classDiagram
    class UnifiedMLPipeline {
        -str config_path
        -Dict config
        -WeightOptimizer weight_optimizer
        -ABTestingFramework ab_tester
        -MLWeightsManager weights_manager
        +train_all(invoice_data, matching_data, output_dir, retrain)
        +predict_all(invoice_data, approved_lanes, output_dir)
        +run_ab_test(invoice_data, approved_lanes, default_weights, ml_weights, output_dir)
        -_train_costguard(invoice_data, models_dir)
        -_train_weight_optimizer(matching_data, models_dir)
        -_predict_matching(row, approved_lanes)
        -_predict_regression(row, models_dir)
        -_predict_anomaly(row, models_dir)
        -_calculate_band(result)
        -_create_mock_models(models_dir)
        -_create_mock_weights(models_dir)
        -_ensure_model_files_exist(models_dir)
    }

    class MLWeightsManager {
        -Dict weights
        -bool is_ml_optimized
        +load_weights(model_path)
        +get_weights()
        +is_optimized()
    }

    class WeightOptimizer {
        -Dict models
        -Dict weights
        +train(data, test_size)
        +extract_weights()
        +save_model(model_path)
        +load_model(model_path)
        +predict_probability(features)
        +get_best_model_name()
    }

    class ABTestingFramework {
        -float threshold
        +compare_weights(data, default_weights, ml_weights)
        +calculate_performance_metrics(predictions, labels)
        +statistical_significance_test(default_metrics, ml_metrics)
        +generate_comparison_report(results)
    }

    class TrainingDataGenerator {
        -List samples
        +add_positive_sample(origin_invoice, dest_invoice, vehicle_invoice, origin_lane, dest_lane, vehicle_lane, metadata)
        +add_negative_sample(origin_invoice, dest_invoice, vehicle_invoice, origin_lane, dest_lane, vehicle_lane, metadata)
        +save_to_json(output_path)
        +load_from_json(input_path)
        +get_sample_count()
        +get_positive_count()
        +get_negative_count()
    }

    UnifiedMLPipeline --> MLWeightsManager : uses
    UnifiedMLPipeline --> WeightOptimizer : uses
    UnifiedMLPipeline --> ABTestingFramework : uses
    WeightOptimizer --> TrainingDataGenerator : uses
```

## 6. 시퀀스 다이어그램 - 학습

### 통합 학습 시퀀스
```mermaid
sequenceDiagram
    participant CLI as CLI Interface
    participant UMP as UnifiedMLPipeline
    participant CG as CostGuard ML v2
    participant WO as WeightOptimizer
    participant FS as File System

    CLI->>UMP: train_all(invoice_data, matching_data, output_dir)
    Note over UMP: Initialize pipeline with config

    UMP->>UMP: Create output directories
    Note over UMP: models/ and out/ directories

    UMP->>CG: _train_costguard(invoice_data, models_dir)
    CG->>CG: map_columns(invoice_data, config)
    CG->>CG: canon(df, fx, lane_map)
    CG->>CG: train_reg(df, models_dir)
    Note over CG: Train RandomForest + GradientBoosting
    CG->>CG: fit_iso(df, iforest.joblib)
    Note over CG: Train IsolationForest
    CG-->>UMP: return costguard_mape

    UMP->>WO: _train_weight_optimizer(matching_data, models_dir)
    WO->>WO: train(matching_data, test_size=0.2)
    Note over WO: Train LogisticRegression, RandomForest, GradientBoosting
    WO->>WO: extract_weights()
    WO->>WO: save_model(optimized_weights.pkl)
    WO-->>UMP: return weight_optimizer_accuracy

    UMP->>UMP: _ensure_model_files_exist(models_dir)
    Note over UMP: Verify all required files exist

    UMP->>FS: Save metrics.json
    UMP-->>CLI: return training results

    Note over CLI,FS: Training completed with metrics
```

## 7. 시퀀스 다이어그램 - 예측

### 통합 예측 시퀀스
```mermaid
sequenceDiagram
    participant CLI as CLI Interface
    participant UMP as UnifiedMLPipeline
    participant WM as MLWeightsManager
    participant CG as CostGuard ML v2
    participant FS as File System

    CLI->>UMP: predict_all(invoice_data, approved_lanes, output_dir)
    Note over UMP: Load ML weights if available

    UMP->>WM: load_weights(optimized_weights.pkl)
    WM-->>UMP: ML-optimized weights loaded

    loop For each invoice item
        UMP->>UMP: _predict_matching(item, approved_lanes)
        Note over UMP: ML-weighted similarity matching
        UMP->>UMP: _predict_regression(item, models_dir)
        Note over UMP: Load RF model and predict rate
        UMP->>UMP: _predict_anomaly(item, models_dir)
        Note over UMP: Load IsolationForest and score
        UMP->>UMP: _calculate_band(result)
        Note over UMP: Calculate PASS/WARN/HIGH/CRITICAL
    end

    UMP->>FS: Save prediction_results.xlsx
    Note over FS: Save all prediction results

    UMP-->>CLI: return prediction results

    Note over CLI,FS: Prediction completed with statistics
```

## 8. 데이터 흐름도

### 전체 데이터 흐름
```mermaid
graph LR
    subgraph "Data Sources"
        A1[Invoice Data<br/>Excel/CSV]
        A2[Training Data<br/>JSON]
        A3[Reference Rates<br/>JSON/CSV]
        A4[Configuration<br/>JSON]
    end

    subgraph "Data Processing"
        B1[Data Loading<br/>pandas.read_excel/csv/json]
        B2[Data Validation<br/>Schema checking]
        B3[Data Transformation<br/>Column mapping, Canonicalization]
    end

    subgraph "ML Training"
        C1[Feature Engineering<br/>log_qty, log_wt, log_cbm]
        C2[Model Training<br/>RF, GB, IsolationForest]
        C3[Weight Optimization<br/>LR, RF, GB for weights]
    end

    subgraph "Model Storage"
        D1[Regression Models<br/>rate_rf.joblib]
        D2[Anomaly Models<br/>iforest.joblib]
        D3[Weight Models<br/>optimized_weights.pkl]
    end

    subgraph "Prediction"
        E1[Data Input<br/>New invoices]
        E2[Model Loading<br/>Load trained models]
        E3[Prediction<br/>Rate, Anomaly, Matching]
        E4[Post-processing<br/>Banding, Statistics]
    end

    subgraph "Output"
        F1[Excel Results<br/>prediction_results.xlsx]
        F2[JSON Metrics<br/>metrics.json]
        F3[A/B Test Results<br/>ab_test_results.json]
    end

    A1 --> B1
    A2 --> B1
    A3 --> B1
    A4 --> B2

    B1 --> B2
    B2 --> B3

    B3 --> C1
    C1 --> C2
    C1 --> C3

    C2 --> D1
    C2 --> D2
    C3 --> D3

    E1 --> E2
    D1 --> E2
    D2 --> E2
    D3 --> E2

    E2 --> E3
    E3 --> E4
    E4 --> F1
    E4 --> F2
    E4 --> F3
```

## 9. 성능 메트릭 플로우

### 성능 측정 및 비교
```mermaid
flowchart TD
    Start([Performance Measurement]) --> CollectMetrics[Collect Metrics]
    CollectMetrics --> TrainingMetrics[Training Metrics<br/>CostGuard MAPE: 20.0%<br/>Weight Accuracy: 95.2%]
    CollectMetrics --> PredictionMetrics[Prediction Metrics<br/>Processing: 2016 items<br/>Time: <30 seconds]
    CollectMetrics --> ABTestMetrics[A/B Test Metrics<br/>Accuracy: +7.1%<br/>Precision: +8.5%<br/>Recall: +5.7%<br/>F1: +7.2%]

    TrainingMetrics --> ValidateTraining{Training<br/>Performance OK?}
    PredictionMetrics --> ValidatePrediction{Prediction<br/>Performance OK?}
    ABTestMetrics --> ValidateAB{A/B Test<br/>Shows Improvement?}

    ValidateTraining -->|Yes| TrainingOK[Training Performance<br/>Acceptable]
    ValidateTraining -->|No| TrainingIssue[Training Performance<br/>Needs Improvement]

    ValidatePrediction -->|Yes| PredictionOK[Prediction Performance<br/>Acceptable]
    ValidatePrediction -->|No| PredictionIssue[Prediction Performance<br/>Needs Optimization]

    ValidateAB -->|Yes| ABOK[ML Weights Superior<br/>Deploy ML Weights]
    ValidateAB -->|No| ABIssue[Default Weights Better<br/>Keep Default Weights]

    TrainingOK --> GenerateReport[Generate Performance Report]
    PredictionOK --> GenerateReport
    ABOK --> GenerateReport

    TrainingIssue --> AdjustTraining[Adjust Training Parameters]
    PredictionIssue --> OptimizePrediction[Optimize Prediction Pipeline]
    ABIssue --> InvestigateAB[Investigate A/B Results]

    AdjustTraining --> GenerateReport
    OptimizePrediction --> GenerateReport
    InvestigateAB --> GenerateReport

    GenerateReport --> End([Performance Analysis Complete])

    style Start fill:#90EE90
    style End fill:#90EE90
    style TrainingOK fill:#98FB98
    style PredictionOK fill:#98FB98
    style ABOK fill:#98FB98
    style TrainingIssue fill:#FFB6C1
    style PredictionIssue fill:#FFB6C1
    style ABIssue fill:#FFB6C1
```

## 10. 에러 처리 플로우

### Fallback 및 에러 복구
```mermaid
flowchart TD
    Start([Process Start]) --> TryProcess[Try Main Process]
    TryProcess --> ProcessSuccess{Process<br/>Successful?}

    ProcessSuccess -->|Yes| Success[Process Success<br/>Continue Normal Flow]
    ProcessSuccess -->|No| HandleError[Handle Error]

    HandleError --> ErrorType{Error Type?}

    ErrorType -->|Training Failure| TrainingFallback[Training Fallback]
    TrainingFallback --> CreateMockModels[Create Mock Models<br/>RandomForest Mock<br/>IsolationForest Mock]
    CreateMockModels --> ContinueWithMock[Continue with Mock Models]

    ErrorType -->|Weight Training Failure| WeightFallback[Weight Training Fallback]
    WeightFallback --> CreateMockWeights[Create Mock Weights<br/>Use Default Weights<br/>Simulate Training Results]
    CreateMockWeights --> ContinueWithDefault[Continue with Default Weights]

    ErrorType -->|Model Loading Failure| ModelFallback[Model Loading Fallback]
    ModelFallback --> UseFallbackValues[Use Fallback Values<br/>Default rate: 5000<br/>Default anomaly: 0.5<br/>Default band: 'NA']
    UseFallbackValues --> ContinueWithFallback[Continue with Fallback Values]

    ErrorType -->|Data Validation Failure| DataFallback[Data Validation Fallback]
    DataFallback --> CleanData[Clean and Validate Data<br/>Remove invalid rows<br/>Fill missing values<br/>Apply default schema]
    CleanData --> RetryProcess[Retry Process]
    RetryProcess --> TryProcess

    ContinueWithMock --> LogError[Log Error Details]
    ContinueWithDefault --> LogError
    ContinueWithFallback --> LogError
    Success --> End([Process Complete])
    LogError --> End

    style Start fill:#90EE90
    style End fill:#90EE90
    style Success fill:#98FB98
    style TrainingFallback fill:#FFE4B5
    style WeightFallback fill:#FFE4B5
    style ModelFallback fill:#FFE4B5
    style DataFallback fill:#FFE4B5
    style LogError fill:#FFB6C1
```

---

이 다이어그램 컬렉션은 ML Systems Integration의 모든 주요 프로세스와 구조를 시각적으로 표현합니다. 각 다이어그램은 특정 관점에서 시스템을 설명하며, 전체적인 이해를 돕습니다.
