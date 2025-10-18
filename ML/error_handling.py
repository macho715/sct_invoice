#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Error Handling & Logging System
구조화된 에러 핸들링 및 로깅
"""

import logging
import sys
import traceback
from pathlib import Path
from typing import Optional, Any, Callable
from functools import wraps
from datetime import datetime
import json


class MLError(Exception):
    """ML 시스템 기본 예외 클래스"""
    pass


class ConfigurationError(MLError):
    """설정 관련 에러"""
    pass


class DataLoadError(MLError):
    """데이터 로딩 에러"""
    pass


class ModelError(MLError):
    """모델 관련 에러"""
    pass


class ValidationError(MLError):
    """데이터 검증 에러"""
    pass


class LoggerManager:
    """
    중앙화된 로거 관리 시스템
    
    Features:
    - 구조화된 로깅
    - 파일/콘솔 동시 출력
    - JSON 형식 로그 지원
    - 성능 메트릭 추적
    """
    
    _instance: Optional['LoggerManager'] = None
    _loggers: dict = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.initialized = True
            self.log_dir = Path("logs")
            self.log_dir.mkdir(exist_ok=True)
    
    def setup_logger(
        self,
        name: str,
        level: str = "INFO",
        log_file: Optional[str] = None,
        console_output: bool = True,
        json_format: bool = False
    ) -> logging.Logger:
        """
        로거 설정
        
        Args:
            name: 로거 이름
            level: 로그 레벨 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: 로그 파일 경로 (optional)
            console_output: 콘솔 출력 여부
            json_format: JSON 형식 로깅 여부
        
        Returns:
            설정된 Logger 객체
        """
        if name in self._loggers:
            return self._loggers[name]
        
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, level.upper()))
        logger.handlers.clear()  # 기존 핸들러 제거
        
        # Formatter 설정
        if json_format:
            formatter = JsonFormatter()
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        
        # Console Handler
        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        
        # File Handler
        if log_file:
            log_path = self.log_dir / log_file
            file_handler = logging.FileHandler(log_path, encoding='utf-8')
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        self._loggers[name] = logger
        return logger
    
    def get_logger(self, name: str) -> logging.Logger:
        """
        로거 가져오기 (없으면 기본 설정으로 생성)
        
        Args:
            name: 로거 이름
        
        Returns:
            Logger 객체
        """
        if name not in self._loggers:
            return self.setup_logger(name)
        return self._loggers[name]


class JsonFormatter(logging.Formatter):
    """JSON 형식 로그 포매터"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # 예외 정보 포함
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        # 추가 필드
        if hasattr(record, 'extra_data'):
            log_data['extra'] = record.extra_data
        
        return json.dumps(log_data, ensure_ascii=False)


def handle_errors(
    default_return: Any = None,
    raise_on_error: bool = False,
    log_traceback: bool = True
):
    """
    에러 핸들링 데코레이터
    
    Args:
        default_return: 에러 발생 시 반환할 기본값
        raise_on_error: 에러를 다시 raise할지 여부
        log_traceback: 전체 traceback을 로깅할지 여부
    
    Examples:
        >>> @handle_errors(default_return=[], raise_on_error=False)
        >>> def load_data(path):
        >>>     return pd.read_csv(path)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger_mgr = LoggerManager()
            logger = logger_mgr.get_logger(func.__module__)
            
            try:
                return func(*args, **kwargs)
            
            except FileNotFoundError as e:
                logger.error(f"File not found in {func.__name__}: {e}")
                if log_traceback:
                    logger.debug(traceback.format_exc())
                if raise_on_error:
                    raise DataLoadError(f"Required file not found: {e}") from e
                return default_return
            
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error in {func.__name__}: {e}")
                if log_traceback:
                    logger.debug(traceback.format_exc())
                if raise_on_error:
                    raise DataLoadError(f"Invalid JSON format: {e}") from e
                return default_return
            
            except KeyError as e:
                logger.error(f"Missing key in {func.__name__}: {e}")
                if log_traceback:
                    logger.debug(traceback.format_exc())
                if raise_on_error:
                    raise ValidationError(f"Required key missing: {e}") from e
                return default_return
            
            except Exception as e:
                logger.error(f"Unexpected error in {func.__name__}: {type(e).__name__}: {e}")
                if log_traceback:
                    logger.error(traceback.format_exc())
                if raise_on_error:
                    raise MLError(f"Unexpected error in {func.__name__}: {e}") from e
                return default_return
        
        return wrapper
    return decorator


class ErrorTracker:
    """
    에러 추적 및 통계
    
    Features:
    - 에러 카운트
    - 에러 타입별 분류
    - 최근 에러 기록
    """
    
    def __init__(self, max_recent_errors: int = 100):
        self.error_counts = {}
        self.recent_errors = []
        self.max_recent_errors = max_recent_errors
        self.logger = LoggerManager().get_logger(__name__)
    
    def track_error(self, error: Exception, context: Optional[dict] = None):
        """
        에러 추적
        
        Args:
            error: 발생한 예외
            context: 추가 컨텍스트 정보
        """
        error_type = type(error).__name__
        
        # 카운트 증가
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        
        # 최근 에러 기록
        error_record = {
            'timestamp': datetime.now().isoformat(),
            'type': error_type,
            'message': str(error),
            'context': context or {}
        }
        
        self.recent_errors.append(error_record)
        
        # 최대 개수 초과 시 오래된 것 제거
        if len(self.recent_errors) > self.max_recent_errors:
            self.recent_errors.pop(0)
        
        self.logger.debug(f"Error tracked: {error_type}")
    
    def get_statistics(self) -> dict:
        """
        에러 통계 반환
        
        Returns:
            에러 통계 딕셔너리
        """
        total_errors = sum(self.error_counts.values())
        
        return {
            'total_errors': total_errors,
            'error_counts': self.error_counts.copy(),
            'recent_errors_count': len(self.recent_errors),
            'most_common_error': max(self.error_counts.items(), key=lambda x: x[1])[0] 
                                 if self.error_counts else None
        }
    
    def get_recent_errors(self, n: int = 10) -> list:
        """
        최근 n개 에러 반환
        
        Args:
            n: 반환할 에러 개수
        
        Returns:
            최근 에러 리스트
        """
        return self.recent_errors[-n:]
    
    def clear(self):
        """에러 기록 초기화"""
        self.error_counts.clear()
        self.recent_errors.clear()
        self.logger.info("Error tracker cleared")


# 전역 에러 트래커
_error_tracker = ErrorTracker()


def get_error_tracker() -> ErrorTracker:
    """전역 에러 트래커 인스턴스 반환"""
    return _error_tracker


def safe_execute(func: Callable, *args, **kwargs) -> tuple[bool, Any]:
    """
    안전한 함수 실행 (에러 발생 시에도 프로그램 중단 없음)
    
    Args:
        func: 실행할 함수
        *args: 함수 인자
        **kwargs: 함수 키워드 인자
    
    Returns:
        (성공 여부, 결과 또는 에러)
    
    Examples:
        >>> success, result = safe_execute(risky_function, arg1, arg2)
        >>> if success:
        >>>     print(f"Success: {result}")
        >>> else:
        >>>     print(f"Error: {result}")
    """
    logger = LoggerManager().get_logger(__name__)
    
    try:
        result = func(*args, **kwargs)
        return True, result
    except Exception as e:
        logger.error(f"Error in safe_execute: {type(e).__name__}: {e}")
        get_error_tracker().track_error(e, {'function': func.__name__})
        return False, e


class ProgressLogger:
    """
    진행 상황 로깅
    
    Features:
    - 배치 처리 진행률 표시
    - 성능 메트릭 추적
    - 예상 완료 시간 계산
    """
    
    def __init__(self, total: int, name: str = "Processing", log_interval: int = 10):
        """
        초기화
        
        Args:
            total: 전체 아이템 수
            name: 작업 이름
            log_interval: 로그 출력 간격 (%)
        """
        self.total = total
        self.name = name
        self.log_interval = log_interval
        self.current = 0
        self.start_time = datetime.now()
        self.logger = LoggerManager().get_logger(__name__)
        
        self.logger.info(f"{self.name} started: {total} items to process")
    
    def update(self, n: int = 1):
        """
        진행 상황 업데이트
        
        Args:
            n: 처리한 아이템 수
        """
        self.current += n
        progress = (self.current / self.total) * 100
        
        # log_interval마다 출력
        if int(progress) % self.log_interval == 0 and progress > 0:
            elapsed = (datetime.now() - self.start_time).total_seconds()
            rate = self.current / elapsed if elapsed > 0 else 0
            eta = (self.total - self.current) / rate if rate > 0 else 0
            
            self.logger.info(
                f"{self.name}: {progress:.1f}% ({self.current}/{self.total}) | "
                f"Rate: {rate:.2f} items/sec | ETA: {eta:.0f}s"
            )
    
    def finish(self):
        """완료 로그"""
        elapsed = (datetime.now() - self.start_time).total_seconds()
        rate = self.total / elapsed if elapsed > 0 else 0
        
        self.logger.info(
            f"{self.name} completed: {self.total} items in {elapsed:.2f}s "
            f"(avg: {rate:.2f} items/sec)"
        )


if __name__ == "__main__":
    # 테스트
    logger_mgr = LoggerManager()
    logger = logger_mgr.setup_logger(
        "test",
        level="DEBUG",
        log_file="test.log",
        console_output=True
    )
    
    # 기본 로깅 테스트
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    
    # 에러 핸들링 데코레이터 테스트
    @handle_errors(default_return=None, raise_on_error=False)
    def test_function():
        raise ValueError("Test error")
    
    result = test_function()
    print(f"Result: {result}")
    
    # 에러 트래커 테스트
    tracker = get_error_tracker()
    tracker.track_error(ValueError("Test error"), {'context': 'test'})
    print(f"Error statistics: {tracker.get_statistics()}")
    
    # 진행률 로거 테스트
    progress = ProgressLogger(total=100, name="Test Processing")
    for i in range(100):
        progress.update(1)
    progress.finish()
