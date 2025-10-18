#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Enhanced ML System
개선된 ML 시스템 통합 테스트
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path

# 테스트 결과 추적
test_results = {"passed": 0, "failed": 0, "errors": []}


def test_config_manager():
    """ConfigManager 테스트"""
    print("\n" + "=" * 60)
    print("TEST 1: ConfigManager - 데이터 의존성 해결")
    print("=" * 60)

    try:
        from config_manager import ConfigManager, get_config, reset_config

        # 1. 기본 초기화
        config = ConfigManager()
        assert config is not None, "ConfigManager initialization failed"
        print("OK ConfigManager 초기화 성공")

        # 2. 설정 가져오기
        threshold = config.get("ml.similarity_threshold", 0.65)
        assert threshold == 0.65, f"Expected 0.65, got {threshold}"
        print(f"OK 점 표기법 설정 조회: {threshold}")

        # 3. 경로 해석
        models_dir = config.get_path("models_dir")
        assert models_dir is not None, "Path resolution failed"
        print(f"OK 경로 해석: {models_dir}")

        # 4. 설정 검증
        is_valid = config.validate()
        print(f"OK 설정 검증: {'통과' if is_valid else '실패'}")

        # 5. 싱글톤 테스트
        config2 = get_config()
        assert config2.get("ml.similarity_threshold") == 0.65
        print("OK 싱글톤 패턴 작동")

        # 6. 디렉토리 생성
        config.create_directories()
        assert Path(config.get_path("logs_dir")).exists()
        print("OK 디렉토리 자동 생성")

        reset_config()

        test_results["passed"] += 1
        print("\nOK ConfigManager 테스트 통과")
        return True

    except Exception as e:
        test_results["failed"] += 1
        test_results["errors"].append(f"ConfigManager: {str(e)}")
        print(f"\nFAIL ConfigManager 테스트 실패: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_error_handling():
    """ErrorHandling 테스트"""
    print("\n" + "=" * 60)
    print("TEST 2: ErrorHandling - 강력한 에러 처리")
    print("=" * 60)

    try:
        from error_handling import (
            LoggerManager,
            handle_errors,
            get_error_tracker,
            ProgressLogger,
            safe_execute,
            MLError,
        )

        # 1. 로거 설정
        logger_mgr = LoggerManager()
        logger = logger_mgr.setup_logger(
            "test_logger", level="INFO", log_file="test_error_handling.log"
        )
        assert logger is not None
        print("OK 로거 설정 성공")

        # 2. 에러 핸들링 데코레이터
        @handle_errors(default_return=None, raise_on_error=False)
        def failing_function():
            raise ValueError("Test error")

        result = failing_function()
        assert result is None, "Expected None from error handler"
        print("OK 에러 핸들링 데코레이터 작동")

        # 3. 에러 트래커
        tracker = get_error_tracker()
        tracker.track_error(ValueError("Test"), {"context": "test"})
        stats = tracker.get_statistics()
        assert stats["total_errors"] > 0
        print(f"OK 에러 추적: {stats['total_errors']} errors tracked")

        # 4. 안전한 실행
        def risky_function(x):
            if x < 0:
                raise ValueError("Negative value")
            return x * 2

        success, result = safe_execute(risky_function, 5)
        assert success and result == 10
        print("OK 안전한 함수 실행 (성공 케이스)")

        success, error = safe_execute(risky_function, -1)
        assert not success
        print("OK 안전한 함수 실행 (실패 케이스)")

        # 5. 진행률 로거
        progress = ProgressLogger(total=10, name="Test", log_interval=50)
        for i in range(10):
            progress.update(1)
        progress.finish()
        print("OK 진행률 로깅 완료")

        tracker.clear()

        test_results["passed"] += 1
        print("\nOK ErrorHandling 테스트 통과")
        return True

    except Exception as e:
        test_results["failed"] += 1
        test_results["errors"].append(f"ErrorHandling: {str(e)}")
        print(f"\nFAIL ErrorHandling 테스트 실패: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_vectorized_processing():
    """VectorizedProcessing 테스트"""
    print("\n" + "=" * 60)
    print("TEST 3: VectorizedProcessing - 벡터화 연산")
    print("=" * 60)

    try:
        from vectorized_processing import (
            VectorizedSimilarity,
            BatchProcessor,
            FeatureVectorizer,
        )
        import time

        # 1. 벡터화된 유사도
        vectorized_sim = VectorizedSimilarity()

        # 단일 유사도 테스트
        score = vectorized_sim.token_set_similarity("DSV YARD", "DSV MUSSAFAH YARD")
        assert 0.0 <= score <= 1.0, f"Invalid similarity score: {score}"
        print(f"OK 단일 유사도 계산: {score:.3f}")

        # 2. 배치 유사도 (성능 테스트)
        sources = ["Origin " + str(i) for i in range(100)]
        targets = ["Target " + str(i) for i in range(50)]
        weights = {"token_set": 0.45, "levenshtein": 0.25, "fuzzy_sort": 0.30}

        start = time.time()
        similarity_matrix = vectorized_sim.batch_similarity(sources, targets, weights)
        elapsed = time.time() - start

        assert similarity_matrix.shape == (100, 50)
        print(f"OK 배치 유사도 계산: {similarity_matrix.shape} in {elapsed:.3f}s")
        print(f"   Rate: {100*50/elapsed:.0f} comparisons/sec")

        # 3. 최적 매칭 찾기
        matches = vectorized_sim.find_best_matches_vectorized(
            sources[:10], targets, weights, threshold=0.3
        )
        assert len(matches) == 10
        print(f"OK 최적 매칭 찾기: {len(matches)} matches")

        # 4. 배치 프로세서
        processor = BatchProcessor(chunk_size=25, n_workers=2)

        test_df = pd.DataFrame({"col1": range(100), "col2": range(100, 200)})

        def dummy_process(chunk):
            chunk["col3"] = chunk["col1"] + chunk["col2"]
            return chunk

        result = processor.process_dataframe(
            test_df, dummy_process, show_progress=False
        )
        assert len(result) == 100
        assert "col3" in result.columns
        print(f"OK 배치 처리: {len(result)} rows processed")

        # 5. 특징 벡터화
        feature_vectorizer = FeatureVectorizer()

        sample_df = pd.DataFrame(
            {
                "origin_invoice": ["DSV Yard", "Jebel Ali", "Abu Dhabi"],
                "dest_invoice": ["Mirfa", "Ruwais", "Dubai"],
                "vehicle_invoice": ["Truck"] * 3,
                "origin_lane": ["DSV MUSSAFAH YARD", "JEBEL ALI PORT", "ABU DHABI"],
                "dest_lane": ["MIRFA SITE", "RUWAIS SITE", "DUBAI SITE"],
                "vehicle_lane": ["FLATBED"] * 3,
                "label": [1, 0, 1],
            }
        )

        features_df = feature_vectorizer.compute_features_batch(sample_df)
        assert "token_set" in features_df.columns
        assert "levenshtein" in features_df.columns
        assert "fuzzy_sort" in features_df.columns
        print(f"OK 특징 벡터화: {len(features_df)} samples with 3 features")

        test_results["passed"] += 1
        print("\nOK VectorizedProcessing 테스트 통과")
        return True

    except Exception as e:
        test_results["failed"] += 1
        test_results["errors"].append(f"VectorizedProcessing: {str(e)}")
        print(f"\nFAIL VectorizedProcessing 테스트 실패: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_enhanced_pipeline():
    """EnhancedPipeline 통합 테스트"""
    print("\n" + "=" * 60)
    print("TEST 4: EnhancedPipeline - 통합 시스템")
    print("=" * 60)

    try:
        from enhanced_unified_ml_pipeline import EnhancedUnifiedMLPipeline
        from config_manager import reset_config

        # 파이프라인 초기화
        pipeline = EnhancedUnifiedMLPipeline()
        assert pipeline is not None
        print("OK 파이프라인 초기화")

        # 설정 확인
        threshold = pipeline.config.get("ml.similarity_threshold")
        assert threshold == 0.65
        print(f"OK 설정 로드: threshold={threshold}")

        # 통계 확인
        stats = pipeline.get_statistics()
        assert "configuration" in stats
        assert "errors" in stats
        print(f"OK 통계 수집: ML optimized={stats['configuration']['ml_optimized']}")

        # 간단한 예측 테스트
        test_invoice = pd.DataFrame(
            {
                "Origin": ["DSV Yard", "Jebel Ali"],
                "Destination": ["Mirfa", "Ruwais"],
                "UoM": ["per truck", "per truck"],
            }
        )

        test_lanes = [
            {"origin": "DSV MUSSAFAH YARD", "destination": "MIRFA SITE", "rate": 5000},
            {"origin": "JEBEL ALI PORT", "destination": "RUWAIS SITE", "rate": 8000},
        ]

        results = pipeline.predict_all(test_invoice, test_lanes, use_ml_weights=False)

        assert len(results) == 2
        print(f"OK 예측 실행: {len(results)} items processed")

        # 매칭 결과 확인
        matched = sum(1 for r in results if r["match_result"] is not None)
        print(f"   Matched: {matched}/{len(results)}")

        reset_config()

        test_results["passed"] += 1
        print("\nOK EnhancedPipeline 테스트 통과")
        return True

    except Exception as e:
        test_results["failed"] += 1
        test_results["errors"].append(f"EnhancedPipeline: {str(e)}")
        print(f"\nFAIL EnhancedPipeline 테스트 실패: {e}")
        import traceback

        traceback.print_exc()
        return False


def print_summary():
    """테스트 결과 요약"""
    print("\n" + "=" * 60)
    print("테스트 결과 요약")
    print("=" * 60)

    total = test_results["passed"] + test_results["failed"]
    print(f"총 테스트: {total}")
    print(f"OK 통과: {test_results['passed']}")
    print(f"FAIL 실패: {test_results['failed']}")

    if test_results["failed"] > 0:
        print("\n실패한 테스트:")
        for error in test_results["errors"]:
            print(f"  - {error}")
        return False
    else:
        print("\nSUCCESS 모든 테스트 통과!")
        print("\n다음 단계:")
        print("  1. 실제 데이터로 성능 테스트")
        print("  2. 프로덕션 설정 파일 작성")
        print("  3. 모니터링 시스템 설정")
        return True


def main():
    """메인 테스트 실행"""
    print("=" * 60)
    print("Enhanced ML System Integration Test")
    print("개선된 ML 시스템 통합 테스트")
    print("=" * 60)

    # 각 테스트 실행
    test_config_manager()
    test_error_handling()
    test_vectorized_processing()
    test_enhanced_pipeline()

    # 결과 요약
    success = print_summary()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
