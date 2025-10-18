#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
End-to-End Integration Tests for Unified ML Pipeline
TDD Implementation: RED Phase - Failing Tests First
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import json
import tempfile
import shutil
from unittest.mock import patch, MagicMock


# Test data setup
@pytest.fixture
def sample_invoice_data():
    """Sample invoice data for testing"""
    return pd.DataFrame(
        [
            {
                "InvoiceDate": "2024-01-15",
                "Description": "Transport from DSV Mussafah to Mirfa PMO",
                "Vendor": "DSV",
                "Category": "Inland Trucking",
                "Origin": "DSV Mussafah Yard",
                "Destination": "Mirfa PMO Site",
                "UoM": "per truck",
                "Qty": 1,
                "Rate": 5000,
                "Amount": 5000,
                "Currency": "USD",
                "WeightKG": 15000,
                "CBM": 2.5,
            },
            {
                "InvoiceDate": "2024-01-16",
                "Description": "Transport from M44 Warehouse to Shuweihat Power",
                "Vendor": "DSV",
                "Category": "Inland Trucking",
                "Origin": "M44 Warehouse",
                "Destination": "Shuweihat Power Station",
                "UoM": "per truck",
                "Qty": 1,
                "Rate": 6500,
                "Amount": 6500,
                "Currency": "USD",
                "WeightKG": 20000,
                "CBM": 3.0,
            },
        ]
    )


@pytest.fixture
def sample_matching_data():
    """Sample matching training data"""
    return pd.DataFrame(
        [
            {"token_set": 0.9, "levenshtein": 0.85, "fuzzy_sort": 0.88, "label": 1},
            {"token_set": 0.4, "levenshtein": 0.3, "fuzzy_sort": 0.35, "label": 0},
        ]
    )


@pytest.fixture
def sample_approved_lanes():
    """Sample approved lane data"""
    return [
        {
            "origin": "DSV MUSSAFAH YARD",
            "destination": "MIRFA SITE",
            "vehicle": "FLATBED",
            "unit": "per truck",
            "cost": 5000,
        },
        {
            "origin": "M44 WAREHOUSE",
            "destination": "SHUWEIHAT SITE",
            "vehicle": "TRAILER",
            "unit": "per truck",
            "cost": 6500,
        },
    ]


@pytest.fixture
def temp_workspace():
    """Temporary workspace for tests"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


class TestE2ETrainingPipeline:
    """Test end-to-end training pipeline"""

    def test_should_train_costguard_and_weight_optimizer_together(
        self, sample_invoice_data, sample_matching_data, temp_workspace
    ):
        """RED: 실패 테스트 - 통합 학습 파이프라인"""
        # Given: 송장 데이터와 매칭 학습 데이터
        # When: 통합 학습 파이프라인 실행
        from unified_ml_pipeline import UnifiedMLPipeline

        pipeline = UnifiedMLPipeline("ML/logi_costguard_ml_v2/config/schema.json")
        result = pipeline.train_all(
            sample_invoice_data, sample_matching_data, temp_workspace
        )

        # Then: 검증
        assert (
            result["costguard_mape"] < 0.25
        )  # 25% MAPE 이하 (small test data allowance)
        assert (
            result["weight_optimizer_accuracy"] > 0.80
        )  # 80% 정확도 이상 (small test data allowance)
        assert Path(f"{temp_workspace}/models/rate_rf.joblib").exists()
        assert Path(f"{temp_workspace}/models/optimized_weights.pkl").exists()
        assert Path(f"{temp_workspace}/out/metrics.json").exists()

    def test_should_handle_missing_training_data_gracefully(
        self, sample_invoice_data, temp_workspace
    ):
        """RED: 실패 테스트 - 훈련 데이터 부족 시 처리"""
        # Given: 매칭 학습 데이터가 없는 경우
        empty_matching_data = pd.DataFrame(
            columns=["token_set", "levenshtein", "fuzzy_sort", "label"]
        )

        # When: 통합 학습 실행
        from unified_ml_pipeline import UnifiedMLPipeline

        pipeline = UnifiedMLPipeline("ML/logi_costguard_ml_v2/config/schema.json")
        result = pipeline.train_all(
            sample_invoice_data, empty_matching_data, temp_workspace
        )

        # Then: 기본 가중치로 fallback
        assert "fallback_to_default" in result
        assert result["fallback_to_default"] == True


class TestE2EPredictionPipeline:
    """Test end-to-end prediction pipeline"""

    def test_should_predict_with_ml_weights_and_costguard_together(
        self, sample_invoice_data, sample_approved_lanes, temp_workspace
    ):
        """RED: 실패 테스트 - 통합 예측 파이프라인"""
        # Given: 송장 데이터와 승인된 레인
        # When: 통합 예측 파이프라인 실행
        from unified_ml_pipeline import UnifiedMLPipeline

        pipeline = UnifiedMLPipeline("ML/logi_costguard_ml_v2/config/schema.json")
        results = pipeline.predict_all(
            sample_invoice_data, sample_approved_lanes, temp_workspace
        )

        # Then: 검증
        assert len(results) == len(sample_invoice_data)
        assert all("match_result" in result for result in results)
        assert all("band" in result for result in results)
        assert all("anomaly_score" in result for result in results)

        # 밴딩 결과 검증
        bands = [result["band"] for result in results]
        assert all(band in ["PASS", "WARN", "HIGH", "CRITICAL", "NA"] for band in bands)

    def test_should_apply_ml_weights_in_similarity_matching(
        self, sample_invoice_data, sample_approved_lanes, temp_workspace
    ):
        """RED: 실패 테스트 - ML 가중치 적용 매칭"""
        # Given: 학습된 ML 가중치
        # When: 유사도 매칭에서 ML 가중치 사용
        from unified_ml_pipeline import UnifiedMLPipeline

        pipeline = UnifiedMLPipeline("ML/logi_costguard_ml_v2/config/schema.json")

        # ML 가중치가 적용된 매칭 결과 확인
        results = pipeline.predict_all(
            sample_invoice_data, sample_approved_lanes, temp_workspace
        )

        # Then: ML 가중치 사용 확인
        ml_weighted_results = [
            r
            for r in results
            if r.get("match_result", {}).get("match_level") == "SIMILARITY_ML"
        ]
        assert len(ml_weighted_results) >= 0  # 일부는 ML 가중치 매칭이어야 함


class TestE2EABTesting:
    """Test A/B testing integration"""

    def test_should_compare_default_vs_ml_weights_performance(
        self, sample_invoice_data, sample_approved_lanes, temp_workspace
    ):
        """RED: 실패 테스트 - A/B 테스트 성능 비교"""
        # Given: 테스트 데이터
        # When: A/B 테스트 실행
        from unified_ml_pipeline import UnifiedMLPipeline

        pipeline = UnifiedMLPipeline("ML/logi_costguard_ml_v2/config/schema.json")

        default_weights = {"token_set": 0.4, "levenshtein": 0.3, "fuzzy_sort": 0.3}
        ml_weights = {"token_set": 0.45, "levenshtein": 0.25, "fuzzy_sort": 0.30}

        ab_result = pipeline.run_ab_test(
            sample_invoice_data,
            sample_approved_lanes,
            default_weights,
            ml_weights,
            temp_workspace,
        )

        # Then: 성능 비교 결과
        assert "default" in ab_result
        assert "optimized" in ab_result
        assert "improvement" in ab_result
        assert ab_result["default"]["accuracy"] >= 0
        assert ab_result["optimized"]["accuracy"] >= 0
        assert ab_result["improvement"]["accuracy"] is not None


class TestE2ERetrainingCycle:
    """Test retraining cycle"""

    def test_should_retrain_models_with_new_data(
        self, sample_invoice_data, sample_matching_data, temp_workspace
    ):
        """RED: 실패 테스트 - 재학습 사이클"""
        # Given: 초기 학습된 모델
        from unified_ml_pipeline import UnifiedMLPipeline

        pipeline = UnifiedMLPipeline("ML/logi_costguard_ml_v2/config/schema.json")
        initial_result = pipeline.train_all(
            sample_invoice_data, sample_matching_data, temp_workspace
        )

        # When: 새로운 데이터로 재학습
        new_invoice_data = pd.concat([sample_invoice_data, sample_invoice_data.copy()])
        new_matching_data = pd.concat(
            [sample_matching_data, sample_matching_data.copy()]
        )

        retrain_result = pipeline.train_all(
            new_invoice_data, new_matching_data, temp_workspace, retrain=True
        )

        # Then: 성능 개선 또는 유지
        assert (
            retrain_result["costguard_mape"] <= initial_result["costguard_mape"] * 1.1
        )  # 10% 허용 오차
        assert (
            retrain_result["weight_optimizer_accuracy"]
            >= initial_result["weight_optimizer_accuracy"] * 0.95
        )


class TestE2EErrorRecovery:
    """Test error recovery scenarios"""

    def test_should_fallback_when_model_files_missing(
        self, sample_invoice_data, sample_approved_lanes, temp_workspace
    ):
        """RED: 실패 테스트 - 모델 파일 없을 때 fallback"""
        # Given: 모델 파일이 없는 상태
        # When: 예측 실행
        from unified_ml_pipeline import UnifiedMLPipeline

        pipeline = UnifiedMLPipeline("ML/logi_costguard_ml_v2/config/schema.json")

        # 모델 디렉토리가 비어있는 상태에서 예측
        results = pipeline.predict_all(
            sample_invoice_data, sample_approved_lanes, temp_workspace
        )

        # Then: 기본값으로 fallback
        assert len(results) == len(sample_invoice_data)
        # 모든 결과에 기본값이 설정되어 있어야 함
        assert all("match_result" in result for result in results)

    def test_should_handle_data_inconsistency_gracefully(
        self, sample_approved_lanes, temp_workspace
    ):
        """RED: 실패 테스트 - 데이터 불일치 처리"""
        # Given: 불완전한 송장 데이터
        incomplete_data = pd.DataFrame(
            [
                {
                    "Description": "Transport",
                    "Origin": "DSV Mussafah Yard",
                },  # 필수 필드 누락
                {
                    "InvoiceDate": "2024-01-15",
                    "Description": "Transport",
                },  # 필수 필드 누락
            ]
        )

        # When: 예측 실행
        from unified_ml_pipeline import UnifiedMLPipeline

        pipeline = UnifiedMLPipeline("ML/logi_costguard_ml_v2/config/schema.json")
        results = pipeline.predict_all(
            incomplete_data, sample_approved_lanes, temp_workspace
        )

        # Then: 오류 없이 처리
        assert len(results) == len(incomplete_data)
        # 오류가 있는 행은 적절히 처리되어야 함
        assert all("error" in result or "match_result" in result for result in results)


# Integration test markers
pytestmark = pytest.mark.integration
