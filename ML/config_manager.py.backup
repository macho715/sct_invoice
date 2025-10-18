#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Config Manager - 중앙화된 설정 관리
데이터 의존성 문제 해결
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ConfigManager:
    """
    중앙화된 설정 관리 시스템
    
    Features:
    - 환경 변수 지원
    - 기본값 설정
    - 경로 자동 해석
    - 설정 검증
    """
    
    DEFAULT_CONFIG = {
        "paths": {
            "approved_lanes": "logi_costguard_ml_v2/ref/inland_trucking_reference_rates_clean (2).json",
            "lane_map": "logi_costguard_ml_v2/ref/ApprovedLaneMap.csv",
            "schema": "logi_costguard_ml_v2/config/schema.json",
            "models_dir": "output/models",
            "output_dir": "output",
            "logs_dir": "logs",
            "training_data": "training_data.json"
        },
        "ml": {
            "default_weights": {
                "token_set": 0.4,
                "levenshtein": 0.3,
                "fuzzy_sort": 0.3
            },
            "similarity_threshold": 0.65,
            "use_ml_weights": True,
            "fallback_to_default": True,
            "test_size": 0.2,
            "random_state": 42
        },
        "costguard": {
            "tolerance": 3.0,
            "auto_fail": 15.0,
            "bands": {
                "pass": 2.0,
                "warn": 5.0,
                "high": 10.0
            },
            "mape_target": 0.15
        },
        "monitoring": {
            "log_level": "INFO",
            "enable_monitoring": True,
            "alert_threshold": {
                "match_rate": 0.80,
                "avg_score": 0.70
            }
        }
    }
    
    def __init__(self, config_path: Optional[str] = None, base_dir: Optional[str] = None):
        """
        초기화
        
        Args:
            config_path: 설정 파일 경로 (optional)
            base_dir: 기본 디렉토리 (optional, 기본값: 현재 스크립트 디렉토리)
        """
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).parent
        self.config = self.DEFAULT_CONFIG.copy()
        
        # 설정 파일이 제공된 경우 로드
        if config_path:
            self.load_config(config_path)
        
        # 환경 변수 오버라이드
        self._apply_env_overrides()
        
        # 경로 해석
        self._resolve_paths()
    
    def load_config(self, config_path: str):
        """
        설정 파일 로드
        
        Args:
            config_path: JSON 설정 파일 경로
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
            
            # Deep merge
            self._deep_merge(self.config, user_config)
            logger.info(f"Configuration loaded from {config_path}")
        
        except FileNotFoundError:
            logger.warning(f"Config file not found: {config_path}, using defaults")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {e}")
            raise
    
    def _deep_merge(self, base: Dict, override: Dict):
        """
        딕셔너리 deep merge
        
        Args:
            base: 기본 딕셔너리
            override: 오버라이드 딕셔너리
        """
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def _apply_env_overrides(self):
        """환경 변수로 설정 오버라이드"""
        
        # ML_MODELS_DIR 환경 변수
        models_dir = os.getenv('ML_MODELS_DIR')
        if models_dir:
            self.config['paths']['models_dir'] = models_dir
            logger.info(f"Using ML_MODELS_DIR from environment: {models_dir}")
        
        # ML_USE_ML_WEIGHTS 환경 변수
        use_ml_weights = os.getenv('ML_USE_ML_WEIGHTS')
        if use_ml_weights:
            self.config['ml']['use_ml_weights'] = use_ml_weights.lower() == 'true'
        
        # ML_LOG_LEVEL 환경 변수
        log_level = os.getenv('ML_LOG_LEVEL')
        if log_level:
            self.config['monitoring']['log_level'] = log_level.upper()
    
    def _resolve_paths(self):
        """상대 경로를 절대 경로로 해석"""
        for key, path in self.config['paths'].items():
            if not Path(path).is_absolute():
                self.config['paths'][key] = str(self.base_dir / path)
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        점 표기법으로 설정 값 가져오기
        
        Args:
            key_path: 점으로 구분된 키 경로 (예: "ml.default_weights.token_set")
            default: 기본값
        
        Returns:
            설정 값
        
        Examples:
            >>> config.get("ml.similarity_threshold")
            0.65
            >>> config.get("paths.models_dir")
            "/path/to/output/models"
        """
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def get_path(self, path_key: str) -> Path:
        """
        경로 가져오기 (Path 객체로 반환)
        
        Args:
            path_key: 경로 키 (예: "models_dir", "approved_lanes")
        
        Returns:
            Path 객체
        """
        path_str = self.config['paths'].get(path_key)
        if not path_str:
            raise ValueError(f"Path key '{path_key}' not found in configuration")
        
        return Path(path_str)
    
    def validate(self) -> bool:
        """
        설정 검증
        
        Returns:
            검증 성공 여부
        """
        errors = []
        
        # 필수 경로 존재 확인
        optional_paths = ['training_data', 'models_dir', 'output_dir', 'logs_dir']
        
        for key, path in self.config['paths'].items():
            if key not in optional_paths:
                if not Path(path).exists():
                    errors.append(f"Required path does not exist: {path} (key: {key})")
        
        # 가중치 합 검증
        weights = self.config['ml']['default_weights']
        weight_sum = sum(weights.values())
        if not (0.99 <= weight_sum <= 1.01):  # 부동소수점 오차 허용
            errors.append(f"ML weights sum should be 1.0, got {weight_sum}")
        
        # 임계값 범위 검증
        threshold = self.config['ml']['similarity_threshold']
        if not (0.0 <= threshold <= 1.0):
            errors.append(f"Similarity threshold should be between 0 and 1, got {threshold}")
        
        if errors:
            for error in errors:
                logger.error(error)
            return False
        
        logger.info("Configuration validation passed")
        return True
    
    def save(self, output_path: str):
        """
        현재 설정을 파일로 저장
        
        Args:
            output_path: 저장할 파일 경로
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Configuration saved to {output_path}")
    
    def create_directories(self):
        """필요한 디렉토리 생성"""
        for key in ['models_dir', 'output_dir', 'logs_dir']:
            path = self.get_path(key)
            path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created directory: {path}")


# 싱글톤 인스턴스
_config_instance: Optional[ConfigManager] = None


def get_config(config_path: Optional[str] = None, base_dir: Optional[str] = None) -> ConfigManager:
    """
    ConfigManager 싱글톤 인스턴스 가져오기
    
    Args:
        config_path: 설정 파일 경로 (optional)
        base_dir: 기본 디렉토리 (optional)
    
    Returns:
        ConfigManager 인스턴스
    """
    global _config_instance
    
    if _config_instance is None:
        _config_instance = ConfigManager(config_path, base_dir)
    
    return _config_instance


def reset_config():
    """ConfigManager 인스턴스 리셋 (주로 테스트용)"""
    global _config_instance
    _config_instance = None


if __name__ == "__main__":
    # 테스트
    config = ConfigManager()
    
    print("=== Configuration Test ===")
    print(f"Models dir: {config.get_path('models_dir')}")
    print(f"ML similarity threshold: {config.get('ml.similarity_threshold')}")
    print(f"Default weights: {config.get('ml.default_weights')}")
    print(f"Validation: {config.validate()}")
    
    # 설정 저장 테스트
    config.save("config_example.json")
    print("Configuration saved to config_example.json")
